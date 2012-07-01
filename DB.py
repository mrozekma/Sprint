from sqlite3 import connect, Row
from inspect import getargspec, getmembers
from os import listdir
from os.path import isdir, isfile, splitext
from threading import Timer
from StringIO import StringIO

from LoadValues import brick
from Lock import getLock
from utils import stripTags

filename = 'db'

class DBError(Exception): pass
class TooManyRecordsError(DBError): pass
class ArgumentMismatchError(DBError): pass

class DiskQueue:
	PERIOD = 30 # commit every __ seconds
	SIZE   = 10 # commit every __ updates

	def __init__(self, conn):
		self.conn = conn
		self.cursor = None
		self.size = 0
		self.timer = None
		self.schedule()

	def update(self, expr, *args):
		try:
			if not self.cursor:
				self.cursor = self.conn.cursor()
			self.cursor.execute(expr, args)
		except Exception, e:
			self.handleException(e)
			raise

		self.size += 1
		if self.size >= DiskQueue.SIZE:
			self.trigger()

	def schedule(self, wait = None):
		if self.timer:
			self.timer.cancel()
		self.timer = Timer(DiskQueue.PERIOD if wait is None else wait, self.tick)
		self.timer.name = 'db disk queue'
		self.timer.daemon = True
		self.timer.start()

	def flush(self):
		if self.timer:
			self.timer.cancel()
		if self.size > 0:
			with getLock('global'):
				# Make sure another thread hasn't already flushed the DB
				if self.size > 0:
					from Log import console
					console('db', "Writing %d %s to disk", self.size, 'entry' if self.size == 1 else 'entries')
					db().counts['flush'] += 1
					self.conn.commit()
					self.cursor.close()
					self.cursor, self.size = None, 0

	def trigger(self):
		self.schedule(0)

	# This runs in the DiskQueue thread
	# If the main thread needs to call this, it should use DiskQueue.trigger()
	def tick(self):
		try:
			with getLock('global'):
				self.flush()
				self.schedule()
		except Exception, e:
			self.handleException(e)
			raise

	def handleException(self, e):
		brick("An unrecoverable problem was encountered while commiting queued database updates to disk: \"%s\". Recent changes may be permanently lost, and the tool must be restarted to correct the memory mapped database" % e)

class DB:
	def __init__(self):
		self.diskConn = connect(filename, check_same_thread = False)
		self.conn = connect(':memory:')

		from Log import console
		console('db', 'Starting memory backfill')
		sql = StringIO()
		for line in self.diskConn.iterdump():
			sql.write(line)
			sql.write('\n')

		cur = self.conn.cursor()
		cur.executescript(sql.getvalue())
		self.conn.commit()
		cur.close()
		console('db', 'Database loaded')

		self.diskQueue = DiskQueue(self.diskConn)
		self.conn.row_factory = Row
		self.counts = dict((k, 0) for k in ('select', 'update', 'total', 'flush'))

	def cursor(self, expr = None, *args):
		cur = self.conn.cursor()
		if expr:
			cur.execute(expr, args)

			# Attempt to detect certain types of operations to update the counts
			# Not really important if this misses things
			if expr.startswith('SELECT'):
				self.counts['select'] += 1
			elif expr.startswith('INSERT') or expr.startswith('UPDATE'):
				self.counts['update'] += 1
			self.counts['total'] += 1

		return cur

	def selectRow(self, expr, *args):
		# print "Executing `%s' with bound args `%s'" % (expr, args)
		cur = self.cursor(expr, *args)
		for row in cur:
			yield row
		cur.close()
		raise StopIteration

	def select(self, expr, *args):
		self.counts['select'] += 1
		self.counts['total'] += 1
		for row in self.selectRow(expr, *args):
			yield dict([(k, row[k]) for k in row.keys()])
		raise StopIteration

	def matches(self, expr, *args):
		cur = self.cursor(expr, *args)
		rtn = not not cur.fetchone()
		cur.close()
		return rtn

	def update(self, expr, *args):
		# print "Updating `%s' with bound args `%s'" % (expr, args)
		self.counts['update'] += 1
		self.counts['total'] += 1

		# Disk
		self.diskQueue.update(expr, *args)

		# Memory
		cur = self.cursor(expr, *args)
		self.conn.commit()
		cur.close()

	def resetCount(self):
		rtn = self.counts['select'], self.counts['update']
		self.counts['select'] = self.counts['update'] = 0
		return rtn

	@staticmethod
	def getTemplates():
		if not isdir('db-templates'):
			raise DBError("Unable to find db-templates directory")

		templates = []
		for script in listdir('db-templates'):
			index, ext = splitext(script)
			if ext != '.sql':
				raise DBError("Unexpected template file: %s" % script)
			try:
				templates.append(int(index, 0))
			except ValueError:
				raise DBError("Unexpected template file: %s" % script)
		return sorted(templates)

singleton = None
def db():
	global singleton
	if not singleton:
		if not isfile(filename):
			raise DBError("Database %s does not exist" % filename)
		singleton = DB()
	return singleton

def dbReconnect():
	global singleton
	singleton = None
	return db()

class ActiveRecord(object):
	def __init__(self):
		self.safe = Safe(self)

	@classmethod
	def table(cls):
		return cls.__name__ + 's'

	@classmethod
	def fields(cls):
		return getargspec(cls.__init__).args[1:]

	@classmethod
	def load(cls, *id, **attrs):
		if len(id): # Searching by id
			if len(id) != 1:
				raise ArgumentMismatchError
			cur = db().cursor("SELECT * FROM %s WHERE id = ?" % cls.table(), id[0])
		else: # Searching by attributes
			placeholders = ["%s = ?" % k for k in attrs.keys()]
			vals = attrs.values()
			cur = db().cursor("SELECT * FROM %s WHERE %s" % (cls.table(), ' AND '.join(placeholders)), *vals)

		row = cur.fetchone()
		cur.close()
		if row: # Checking in case rowcount == -1 (unsupported)
			return cls(**row)
		else:
			return None

	@classmethod
	def loadIf(cls, *id, **attrs):
		try:
			return cls.load(*id, **attrs);
		except ArgumentMismatchError:
			return None

	@classmethod
	def loadSet(cls, *ids):
		return dict([(id, cls.load(id)) for id in ids])

	@classmethod
	def loadAll(cls, orderby = None, groupby = None, limit = None, **attrs):
		sql = "SELECT * FROM %s" % cls.table()
		if len(attrs):
			placeholders = ["%s = ?" % k for k in attrs.keys()]
			sql += " WHERE %s" % ' AND '.join(placeholders)
		if groupby:
			sql += " GROUP BY %s" % groupby
		if orderby:
			sql += " ORDER BY %s" % orderby
		if limit:
			sql += " LIMIT %d, %d" % limit

		vals = attrs.values()
		rows = db().select(sql, *vals)
		return map(lambda x: cls(**x), rows)

	def save(self, pks = ['id']):
		cls = self.__class__
		fields = set(cls.fields()) - set(['id'])
		vals = dict(getmembers(self))

		boundArgs = [vals[k] for k in fields]

		if self.id: # Update
			placeholders = ', '.join(map(lambda x: "%s = ?" % x, fields))
			pkPlaceholders = ' AND '.join(map(lambda x: "%s = ?" % x, pks))
			db().update("UPDATE %s SET %s WHERE %s" % (cls.table(), placeholders, pkPlaceholders), *(boundArgs + [vals[field] for field in pks]))
		else: # Insert
			placeholders = ', '.join(map(lambda x: "?", fields))
			db().update("INSERT INTO %s(%s) VALUES(%s)" % (cls.table(), ', '.join(fields), placeholders), *boundArgs)

			# Damn triggers mess this up :(
			# rows = [x for x in db().select("SELECT last_insert_rowid()")]
			# self.id = rows[0]['last_insert_rowid()']

			# And this is painfully inefficient
			# self.id = cls.loadAll(orderby = None)[-1].id

			self.id = list(db().select("SELECT MAX(id) AS max_id FROM %s" % cls.table()))[0]['max_id']

	def delete(self):
		cls = self.__class__
		if self.id:
			db().update("DELETE FROM %s WHERE %s = ?" % (cls.table(), 'id'), self.id)

	@staticmethod
	def saveAll(objs):
		for obj in objs:
			obj.save()

	def __getitem__(self, name):
		return self.__getattribute__(name)

	# getter
	@staticmethod
	def idToObj(cls, field):
		return lambda self: cls.load(self.__getattribute__(field)) if self else None

	# setter
	@staticmethod
	def objToId(var):
		def fn(self, obj):
			if obj:
				if not obj.id:
					raise ValueError("Attempted to pull id from unsaved object")
				self.__setattr__(var, obj.id)
			else:
				self.__setattr__(var, 0)
		return fn

	@staticmethod
	def idObjLink(cls, field):
		return property(ActiveRecord.idToObj(cls, field), ActiveRecord.objToId(field), None)

	def loadLink(self, table, col, otherCls, otherCol):
		if not self.id: return []

		rows = db().select("SELECT %s FROM %s WHERE %s = ?" % (otherCol, table, col), self.id)
		return map(lambda x: otherCls.load(x[otherCol]), rows)

	def saveLink(self, link, table, col, otherCls, otherCol):
		if not self.id: raise ValueError("Attempted to save link before saving object")
		for i in link:
			db().update("INSERT OR REPLACE INTO %s(%s, %s) VALUES(?, ?)" % (table, col, otherCol), self.id, i.id)

		placeholders = ' AND '.join("%s != ?" % otherCol for i in link)
		vals = [i.id for i in link]
		db().update("DELETE FROM %s WHERE %s = ? AND %s" % (table, col, placeholders), self.id, *vals)

	def __eq__(self, other):
		return self and other and self.id == other.id

	def __ne__(self, other):
		return not (self == other)

	def __hash__(self):
		return self.id or object.__hash__(self)

class Safe(object):
	def __init__(self, ar):
		self.ar = ar

	def __getattribute__(self, var):
		entities = {
			'&': '&amp;',
			'"': '&quot;',
			"'": '&apos;',
			'<': '&lt;',
			'>': '&gt;'
		}

		if var == 'ar': return object.__getattribute__(self, var)
		# return stripTags(self.ar.__getattribute__(var))
		return ''.join(entities.get(c, c) for c in self.ar.__getattribute__(var))
