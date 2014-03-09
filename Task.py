from inspect import getmembers
from datetime import datetime, date

from User import User
from Project import Project
from Sprint import Sprint
from Group import Group
from Goal import Goal
from utils import *

from stasis.Singleton import get as db
from stasis.ActiveRecord import ActiveRecord, link
from stasis.StasisError import StasisError

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
	sprint = link(Sprint, 'sprintid')
	creator = link(User, 'creatorid')
	group = link(Group, 'groupid')
	goal = link(Goal, 'goalid')
	assigned = link(User, 'assignedids')

	def getStatus(self): return statuses[self.status]
	def setStatus(self, stat): self.status = stat.name
	stat = property(getStatus, setStatus)

	def __init__(self, groupid, sprintid, creatorid, goalid, name, status, hours, assignedids = set(), seq = None, timestamp = None, deleted = 0, revision = 1, id = None):
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
		self.assignedids = assignedids
		self.timestamp = timestamp if timestamp else max(dateToTs(getNow()), self.sprint.start)
		self.seq = seq if seq else maxOr(task.seq for task in self.group.getTasks())+1
		self.deleted = deleted

	def __str__(self):
		return self.safe.name

	def getRevision(self, revision):
		data = db()['tasks'][self.id]
		return Task(**data[revision]) if revision < len(data) else None

	def getRevisions(self):
		data = db()['tasks'][self.id]
		return map(lambda x: Task(**x), data)

	# This returns the revision at the end of the specified day
	def getRevisionAt(self, date):
		timestamp = tsEnd(dateToTs(date))
		for rev in reversed(self.getRevisions()):
			if rev.timestamp <= timestamp:
				return rev
		return None

	def getStartRevision(self, includeAfterPlanning = True):
		return self.getRevisionAt(tsToDate(self.sprint.start)) or (self.getRevision(1) if includeAfterPlanning else None)

	def getNotes(self):
		from Note import Note
		return Note.loadAll(taskid = self.id, orderby = 'timestamp')

	def effectiveHours(self):
		return self.hours if self.stillOpen() else 0

	def manHours(self):
		return self.effectiveHours() * len(self.assigned)

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
	def loadDataFilter(cls, data, **attrs):
		rev = attrs['revision'] - 1 if 'revision' in attrs else -1
		return data[rev] if rev < len(data) else None

	@classmethod
	def saveDataFilter(cls, data):
		if data['id']:
			if data['id'] not in db()['tasks']:
				return [data]
			rev = data['revision'] - 1
			revs = db()['tasks'][data['id']]
			if rev < len(revs):
				revs[rev] = data
			elif rev == len(revs):
				revs.append(data)
			else:
				raise StasisError("Invalid revision %d for task %d" % (data['revision'], data['id']))
			return revs
		else:
			if data['revision'] != 1:
				raise StasisError("Invalid first revision (%d)" % data['revision'])
			return [data]

	def save(self):
		#DEBUG #NO
		if not isinstance(self.assignedids, (set, frozenset)):
			raise RuntimeError("Broken type (%s)" % type(self.assignedids).__name__)
		if not isinstance(self.assigned, (set, frozenset)):
			raise RuntimeError("Broken type (%s)" % type(self.assigned).__name__)

		if not self.id:
			# Shift everything after this sequence
			for id, task in db()['tasks'].iteritems():
				rev = task[-1]
				if rev['groupid'] == self.groupid and rev['seq'] >= self.seq:
					with db()['tasks'].change(id) as data:
						data[-1]['seq'] += 1
		return ActiveRecord.save(self)

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
		for id, task in db()['tasks'].iteritems():
			rev = task[-1]
			if rev['groupid'] == self.groupid and rev['seq'] > self.seq:
				with db()['tasks'].change(id) as data:
					for rev in data:
						rev['seq'] -= 1

		# Switch group (for all revisions)
		if(self.group != newGroup):
			self.group = newGroup
			with db()['tasks'].change(self.id) as data:
				for rev in data:
					rev['groupid'] = self.groupid

		# Add to new group (shift all later tasks down)
		# Reload newPred in case its sequence has changed
		self.seq = Task.load(newPred.id).seq + 1 if newPred else 1
		for id, task in db()['tasks'].iteritems():
			rev = task[-1]
			if rev['groupid'] == self.groupid and rev['seq'] >= self.seq:
				with db()['tasks'].change(id) as data:
					for rev in data:
						rev['seq'] += 1
		with db()['tasks'].change(self.id) as data:
			for rev in data:
				rev['seq'] = self.seq

	def revise(self):
		self.revision += 1 # Bump the revision number
		self.save()

	def saveRevision(self, author):
		self.creator = author
		self.timestamp = max(self.timestamp, dateToTs(getNow()))
		self.revise()
