from __future__ import division
from datetime import timedelta

from utils import *
from DB import ActiveRecord, db
from User import User
from Project import Project

class Sprint(ActiveRecord):
	project = ActiveRecord.idObjLink(Project, 'projectid')
	owner = ActiveRecord.idObjLink(User, 'ownerid')

	def __init__(self, projectid, name, ownerid, start, end, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.projectid = projectid
		self.name = name
		self.ownerid = ownerid
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

	def isPlanning(self):
		return tsToDate(self.start).date() >= getNow().date()

	def isReview(self):
		return tsToDate(self.end).date() == getNow().date()

	def isActive(self):
		now = dateToTs(getNow())
		return self.start <= now <= self.end

	def canEdit(self, user):
		return (self.isActive() or self.isPlanning()) and user.hasPrivilege('Write')

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

	def link(self, currentUser):
		from handlers.sprints import tabs as sprintTabs
		from Prefs import Prefs
		page = currentUser.getPrefs().defaultSprintTab if currentUser else 'backlog'

		return "<img src=\"/static/images/sprint.png\" class=\"sprint\"><a href=\"%s\">%s</a>" % (sprintTabs[page]['path'] % self.id, self.getFormattedName())

	def __str__(self):
		return self.getFormattedName()

	def getWarnings(self):
		rtn = []

		from Availability import Availability
		tasks = self.getTasks()
		avail = Availability(self)
		timestamp = tsToDate(self.start)
		userAvails = dict((user, avail.getAllForward(timestamp, user)) for user in self.members)

		# Users with 0 availability
		zeroes = [user for (user, hours) in userAvails.iteritems() if hours == 0]
		if len(zeroes) == 1:
			rtn.append("%s has no <a href=\"/sprints/%d/availability\">availability</a>" % (zeroes[0], self.id))
		elif len(zeroes) > 0:
			rtn.append("%d members have no <a href=\"/sprints/%d/availability\">availability</a>" % (len(zeroes), self.id))

		# Users with >100% commitment
		overcommitted = filter(lambda user: userAvails[user] < sum(task.hours for task in tasks if task.assigned == user), self.members)
		if len(overcommitted) == 1:
			rtn.append("%s is <a href=\"/sprints/%d/metrics#commitment-by-user\">overcommitted</a>" % (overcommitted[0], self.id))
		elif len(overcommitted) > 0:
			rtn.append("%d members are <a href=\"/sprints/%d/metrics#commitment-by-user\">overcommitted</a>" % (len(overcommitted), self.id))

		# No sprint goals, or too many tasks (at least 10 tasks and more than 20% of all tasks) without a goal
		unaffiliated = filter(lambda task: not task.goal, tasks)
		if len(filter(lambda goal: goal.name != '', self.getGoals())) == 0:
			rtn.append("There are no <a href=\"/sprints/%d/info\">sprint goals</a>" % self.id)
		elif len(unaffiliated) >= 10 and len(unaffiliated) / len(tasks) > .20:
			rtn.append("There are many <a href=\"/sprints/%d?search=goal:none\">tasks unrelated to the sprint goals</a>" % self.id)

		# Incomplete tasks with 0 hours
		if len(filter(lambda task: task.stillOpen() and task.hours == 0, tasks)) > 0:
			rtn.append("There are <a href=\"/sprints/%d?search=status:not-started,in-progress,blocked hours:0\">open tasks with no hour estimate</a>" % self.id)

		# Deferred/split tasks with >0 hours
		if len(filter(lambda task: (task.status == 'deferred' or task.status == 'split') and task.hours > 0, tasks)) > 0:
			rtn.append("There are <a href=\"/sprints/%d?search=status:deferred,split hours:>0\">deferred tasks with hours</a>. These hours are counted as part of the sprint commitment" % self.id)

		return rtn
