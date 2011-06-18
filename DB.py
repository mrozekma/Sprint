from sqlite3 import connect, Row
from inspect import getargspec, getmembers
import sys
from utils import stripTags

class DB:
	def __init__(self):
		self.conn = connect('db')
		self.conn.row_factory = Row

	def cursor(self, expr = None, *args):
		# print >>sys.__stdout__, "Cursoring `%s' with bound args `%s'" % (expr, args)
		cur = self.conn.cursor()
		if expr:
			cur.execute(expr, args)
		return cur

	def selectRow(self, expr, *args):
		# print "Executing `%s' with bound args `%s'" % (expr, args)
		cur = self.cursor(expr, *args)
		for row in cur:
			yield row
		cur.close()
		raise StopIteration

	def select(self, expr, *args):
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
		cur = self.cursor(expr, *args)
		self.conn.commit()
		cur.close()

singleton = None
def db():
	global singleton
	if not singleton:
		singleton = DB()
	return singleton

class DBError(Exception): pass
# class NoRecordsError(DBError): pass
class TooManyRecordsError(DBError): pass
class ArgumentMismatchError(DBError): pass

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
	def loadAll(cls, orderby = None, groupby = None, **attrs):
		sql = "SELECT * FROM %s" % cls.table()
		if len(attrs):
			placeholders = ["%s = ?" % k for k in attrs.keys()]
			sql += " WHERE %s" % ' AND '.join(placeholders)
		if groupby:
			sql += " GROUP BY %s" % groupby
		if orderby:
			sql += " ORDER BY %s" % orderby

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

	@staticmethod
	def saveAll(objs):
		for obj in objs:
			obj.save()

	def __getitem__(self, name):
		return self.__getattribute__(name)

	# getter
	@staticmethod
	def idToObj(cls, field):
		return lambda self: cls.load(self.__getattribute__(field))

	# setter
	@staticmethod
	def objToId(var):
		def fn(self, obj):
			if not obj.id:
				raise ValueError("Attempted to pull id from unsaved object")
			self.__setattr__(var, obj.id)
		return fn

	@staticmethod
	def idObjLink(cls, field):
		return property(ActiveRecord.idToObj(cls, field), ActiveRecord.objToId(field), None)

	def loadLink(self, table, col, otherCls, otherCol):
		if not self.id: return []

		rows = db().select("SELECT %s FROM %s WHERE %s = ?" % (otherCol, table, col), self.id)
		return map(lambda x: otherCls.load(x[otherCol]), rows)

	def saveLink(self, link, table, col, otherCls, otherCol):
		if not self.id: raise ValuerError("Attempted to save link before saving object")
		for i in link:
			db().update("INSERT INTO %s(%s, %s) VALUES(?, ?)" % (table, col, otherCol), self.id, i.id)

	def __eq__(self, other):
		return self.id == other.id

class Safe(object):
	def __init__(self, ar):
		self.ar = ar

	def __getattribute__(self, var):
		if var == 'ar': return object.__getattribute__(self, var)
		return stripTags(self.ar.__getattribute__(var))
