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

	def save(self):
		ActiveRecord.save(self)
		ActiveRecord.saveLink(self, self.members, 'members', 'sprintid', User, 'userid')

	def getStartStr(self):
		return formatDate(tsToDate(self.start))

	def getEndStr(self):
		return formatDate(tsToDate(self.end))

	def isActive(self):
		now = dateToTs(datetime.now())
		return self.start <= now <= self.end

	def getTasks(self, orderby = 'seq ASC'):
		from Task import Task
		return Task.loadAll(sprintid = self.id, orderby = orderby)

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
