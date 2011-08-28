from datetime import timedelta

from utils import *
from DB import ActiveRecord, db
from User import User
from Project import Project

class Sprint(ActiveRecord):
	project = ActiveRecord.idObjLink(Project, 'projectid')

	def __init__(self, projectid, name, start, end, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.projectid = projectid
		self.name = name
		self.start = start
		self.end = end
		self.members = ActiveRecord.loadLink(self, 'members', 'sprintid', User, 'userid')

	@classmethod
	def loadAllActive(cls):
		return filter(lambda s: s.isActive(), Sprint.loadAll())

	def save(self):
		ActiveRecord.save(self)
		ActiveRecord.saveLink(self, self.members, 'members', 'sprintid', User, 'userid')

	def getStartStr(self):
		return formatDate(tsToDate(self.start))

	def getEndStr(self):
		return formatDate(tsToDate(self.end))

	def getDays(self, includeWeekends = False):
		oneday = timedelta(1)
		start, end = tsToDate(self.start), tsToDate(self.end)
		seek = start
		while seek <= end:
			if includeWeekends or seek.weekday() < 5:
				yield seek
			seek += oneday

	def isActive(self):
		now = dateToTs(datetime.now())
		return self.start <= now <= self.end

	def getTasks(self, orderby = 'seq ASC', includeDeleted = False):
		from Task import Task
		tasks = Task.loadAll(sprintid = self.id, orderby = orderby)
		# This is filtered here instead of in Task.loadAll to prevent loading old revisions
		if not includeDeleted:
			tasks = filter(lambda t: not t.deleted, tasks)
		return tasks

	def getGroups(self, orderby = 'seq ASC'):
		from Group import Group
		return Group.loadAll(sprintid = self.id, orderby = orderby)

	def getGoals(self):
		from Goal import Goal
		return Goal.loadAll(sprintid = self.id)

	def getFormattedName(self):
		cls = 'sprint-name active' if self.isActive() else 'sprint-name'
		return "<span class=\"%s\">%s</span>" % (cls, self.safe.name)

	def link(self):
		return "<img src=\"/static/images/sprint.png\" class=\"sprint\"><a href=\"/sprints/%d\">%s</a>" % (self.id, self.getFormattedName())

	def __str__(self):
		return self.getFormattedName()
