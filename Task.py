from utils import *
from DB import ActiveRecord, db
from User import User
from Project import Project
from Sprint import Sprint
from Group import Group
from Goal import Goal
from inspect import getmembers
from datetime import datetime, date

class Status(object):
	def getIcon(self): return "/static/images/status-%s.png" % self.name.replace(' ', '-')
	icon = property(getIcon)

	def __init__(self, name, text, revVerb):
		self.name = name
		self.text = text
		self.revVerb = revVerb

	def getRevisionVerb(self, oldStatus):
		return self.revVerb
		wasOpen = (oldStatus not in ('complete', 'canceled', 'deferred', 'split'))
		return self.revVerbWasOpen if wasOpen else self.revVerbWasClosed

class NotStartedStatus(Status):
	def getRevisionVerb(self, oldStatus):
		if oldStatus in ('complete', 'canceled', 'deferred', 'split'):
			return 'Reopened'
		elif oldStatus == 'blocked':
			return 'Unblocked'
		else:
			return super(NotStartedStatus, self).getRevisionVerb(oldStatus)

statuses = [
	Status('blocked', 'Blocked', 'Blocked'),
	Status('canceled', 'Canceled', 'Canceled'),
	Status('complete', 'Complete', 'Completed'),
	Status('deferred', 'Deferred', 'Deferred'),
	Status('in progress', 'In Progress', 'Started'),
	NotStartedStatus('not started', 'Not Started', 'Aborted'),
	Status('split', 'Split', 'Split'),
]
statuses = dict([(s.name, s) for s in statuses])

statusMenu = [('not started', 'in progress', 'complete'), ('blocked',), ('deferred', 'canceled', 'split')]
assert sum(map(len, statusMenu)) == len(statuses)

def getStatuses(tag = None):
	return [name for (name, status) in statuses.iteritems() if tag in status.tags] if tag else [name for block in statusMenu for name in block]

class Task(ActiveRecord):
	sprint = ActiveRecord.idObjLink(Sprint, 'sprintid')
	creator = ActiveRecord.idObjLink(User, 'creatorid')
	group = ActiveRecord.idObjLink(Group, 'groupid')
	goal = ActiveRecord.idObjLink(Goal, 'goalid')

	def getStatus(self): return statuses[self.status]
	def setStatus(self, stat): self.status = stat.name
	stat = property(getStatus, setStatus)

	def __init__(self, groupid, sprintid, creatorid, goalid, name, status, hours, seq = None, timestamp = None, deleted = 0, revision = 1, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.revision = revision
		self.groupid = groupid
		self.sprintid = sprintid
		self.creatorid = creatorid
		self.goalid = goalid
		self.name = name
		self.status = status
		self.hours = hours
		self.timestamp = timestamp if timestamp else max(dateToTs(getNow()), self.sprint.start)
		self.seq = seq if seq else maxOr(task.seq for task in self.group.getTasks())+1
		self.deleted = deleted
		self.assigned = ActiveRecord.loadLink(self, 'assigned', [('taskid', self.id), ('revision', self.revision)], User, 'userid')

	def __str__(self):
		return self.safe.name

	def getRevision(self, revision):
		rows = db().select("SELECT * FROM %s WHERE id = ? AND revision = ? LIMIT 1" % Task.table(), self.id, revision)
		rows = [x for x in rows]
		return Task(**rows[0]) if len(rows) > 0 else None

	def getRevisions(self):
		rows = db().select("SELECT * FROM %s WHERE id = ? ORDER BY revision" % Task.table(), self.id)
		return map(lambda x: Task(**x), rows)

	# This returns the revision at the end of the specified day
	def getRevisionAt(self, date):
		timestamp = tsEnd(dateToTs(date))
		rows = db().select("SELECT * FROM %s WHERE id = ? AND timestamp <= ? ORDER BY revision DESC LIMIT 1" % Task.table(), self.id, timestamp)
		rows = [x for x in rows]
		return Task(**rows[0]) if len(rows) > 0 else None

	def getStartRevision(self, includeAfterPlanning = True):
		return self.getRevisionAt(tsToDate(self.sprint.start)) or (self.getRevision(1) if includeAfterPlanning else None)

	def getNotes(self):
		from Note import Note
		return Note.loadAll(taskid = self.id, orderby = 'timestamp ASC')

	def manHours(self):
		return self.hours * len(self.assigned)

	### Data that depends on task status/history

	def earnedValueHours(self):
		if self.status != 'complete': return 0
		tOrig = self.getRevisionAt(tsToDate(self.sprint.start))
		return tOrig.hours * min(len(tOrig.assigned), len(self.assigned)) if tOrig else 0

	def historyEndsOn(self):
		return self.sprint.end if self.stillOpen() else self.timestamp

	def shouldImport(self):
		return self.status not in ('complete', 'canceled', 'split')

	def stillOpen(self):
		return self.status not in ('complete', 'canceled', 'deferred', 'split') and not self.deleted

	def link(self):
		return "<a href=\"/tasks/%d\">%s</a>" % (self.id, self.safe.name)

	### ActiveRecord methods

	@classmethod
	def load(cls, *id, **attrs):
		if len(id): # Searching by id
			if len(id) != 1:
				raise ArgumentMismatchError
			cur = db().cursor("SELECT * FROM %s WHERE id = ? ORDER BY revision DESC LIMIT 1" % cls.table(), id[0])
		else: # Searching by attributes
			placeholders = ["%s = ?" % k for k in attrs.keys()]
			vals = attrs.values()
			cur = db().cursor("SELECT * FROM %s WHERE %s ORDER BY revision DESC LIMIT 1" % (cls.table(), ' AND '.join(placeholders)), *vals)

		row = cur.fetchone()
		cur.close()
		if row: # Checking in case rowcount == -1 (unsupported)
			return cls(**row)
		else:
			return None

	@classmethod
	def loadAll(cls, orderby = None, **attrs):
		return super(Task, cls).loadAll(groupby = 'id', orderby = orderby, **attrs)

	def save(self):
		if not self.id:
			# Pre-insert since tasks.id isn't autoincrementing
			rows = db().select("SELECT MAX(id) FROM tasks");
			rows = [x for x in rows]
			self.id = (rows[0]['MAX(id)'] or 0) + 1
			db().update("INSERT INTO tasks(id, revision, seq) VALUES(?, ?, ?)", self.id, 1, self.seq)

			# Shift everything after this sequence
			db().update("UPDATE tasks SET seq = seq + 1 WHERE groupid = ? AND seq >= ?", self.groupid, self.seq)
		ActiveRecord.save(self, pks = ['id', 'revision'])
		ActiveRecord.saveLink(self, self.assigned, 'assigned', [('taskid', self.id), ('revision', self.revision)], User, 'userid')

	def move(self, newPred, newGroup):
		# newPred = None means move to the top of newGroup
		# newGroup = None means the group is newPred's group
		if newPred:
			if not newGroup:
				newGroup = newPred.group
			elif newGroup and newPred.group != newGroup:
				raise ValueError("Incompatible predecessor and group")
		elif not newGroup:
			raise ValueError("Neither predecessor nor group specified")

		# Remove from current group (shift all later tasks up)
		db().update("UPDATE tasks SET seq = seq - 1 WHERE groupid = ? AND seq > ?", self.groupid, self.seq)

		# Switch group (for all revisions)
		if(self.group != newGroup):
			self.group = newGroup
			db().update("UPDATE tasks SET groupid = ? WHERE id = ?", self.groupid, self.id)

		# Add to new group (shift all later tasks down)
		# Reload newPred in case its sequence has changed
		self.seq = Task.load(newPred.id).seq + 1 if newPred else 1
		db().update("UPDATE tasks SET seq = seq + 1 WHERE groupid = ? AND seq >= ?", self.groupid, self.seq)
		db().update("UPDATE tasks SET seq = ? WHERE id = ?", self.seq, self.id)


	# @classmethod
	# def loadAll(cls, **attrs):
		# if len(attrs):
			# placeholders = ["%s = ?" % k for k in attrs.keys()]
			# vals = attrs.values()
			# rows = db().select("SELECT * FROM %s WHERE %s GROUP BY id" % (cls.table(), ' AND '.join(placeholders)), *vals)
		# else:
			# rows = db().select("SELECT * FROM %s GROUP BY id" % cls.table())
		# return map(lambda x: cls(**x), rows)

	def revise(self):
		cls = self.__class__

		self.revision += 1 # Bump the revision number

		fields = [x for x in set(cls.fields())]
		vals = dict(getmembers(self))
		boundArgs = [vals[k] for k in fields]

		placeholders = ', '.join(map(lambda x: "?", fields))
		db().update("INSERT INTO %s(%s) VALUES(%s)" % (cls.table(), ', '.join(fields), placeholders), *boundArgs)
		ActiveRecord.saveLink(self, self.assigned, 'assigned', [('taskid', self.id), ('revision', self.revision)], User, 'userid')

	def saveRevision(self, author):
		self.creator = author
		self.timestamp = max(self.timestamp, dateToTs(getNow()))
		self.revise()
