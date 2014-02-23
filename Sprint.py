from __future__ import division
from datetime import timedelta

from User import User
from Project import Project
from utils import *

from stasis.ActiveRecord import ActiveRecord, link

class Sprint(ActiveRecord):
	project = link(Project, 'projectid')
	owner = link(User, 'ownerid')
	members = link(User, 'memberids')

	def __init__(self, projectid, name, ownerid, start, end, memberids = set(), id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.projectid = projectid
		self.name = name
		self.ownerid = ownerid
		self.start = start
		self.end = end
		self.memberids = memberids

	@classmethod
	def loadAllActive(cls, member = None, project = None):
		rtn = filter(lambda s: s.isActive() or s.isPlanning(), Sprint.loadAll())
		if member:
			rtn = filter(lambda s: member in s.members, rtn)
		if project:
			rtn = filter(lambda s: s.project == project, rtn)
		return rtn

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
		return Weekday.nextWeekday(tsToDate(self.start).date()) >= getNow().date()

	def isReview(self):
		return tsToDate(self.end).date() == Weekday.nextWeekday(getNow().date())

	def isActive(self):
		return tsToDate(self.start) <= getNow() <= tsToDate(self.end)

	def isOver(self):
		return getNow() > tsToDate(self.end)

	def canEdit(self, user):
		return (self.isActive() or self.isPlanning()) and user and user.hasPrivilege('Write')

	def getTasks(self, orderby = 'seq', includeDeleted = False):
		from Task import Task
		tasks = Task.loadAll(sprintid = self.id, orderby = orderby)
		# This is filtered here instead of in Task.loadAll to prevent loading old revisions
		if not includeDeleted:
			tasks = filter(lambda t: not t.deleted, tasks)
		return tasks

	def getGroups(self, orderby = 'seq'):
		from Group import Group
		return Group.loadAll(sprintid = self.id, orderby = orderby)

	def getGoals(self):
		from Goal import Goal
		return Goal.loadAll(sprintid = self.id)

	def getFormattedName(self):
		cls = 'sprint-name active' if self.isActive() else 'sprint-name'
		return "<span class=\"%s\">%s</span>" % (cls, self.safe.name)

	def link(self, currentUser, icon = 'sprint'):
		from handlers.sprints import tabs as sprintTabs
		from Prefs import Prefs
		page = currentUser.getPrefs().defaultSprintTab if currentUser else 'backlog'

		return "<img src=\"/static/images/%s.png\" class=\"sprint\"><a href=\"%s\">%s</a>" % (icon, sprintTabs()[page].getPath(self.id), self.getFormattedName())

	def __str__(self):
		return self.getFormattedName()

	def getWarnings(self):
		rtn = {}

		from Availability import Availability
		tasks = self.getTasks()
		avail = Availability(self)
		timestamp = tsToDate(self.start)
		userAvails = dict((user, avail.getAllForward(timestamp, user)) for user in self.members)

		# Users with 0 availability
		zeroes = [user for (user, hours) in userAvails.iteritems() if hours == 0]
		if zeroes != []:
			rtn['no-availability'] = zeroes

		# Users with >100% commitment
		overcommitted = filter(lambda user: userAvails[user] < sum(task.hours for task in tasks if user in task.assigned), self.members)
		if overcommitted != []:
			rtn['overcommitted'] = overcommitted

		# Users with no tasks
		noTasks = filter(lambda user: filter(lambda task: user in task.assigned, tasks) == [], self.members)
		if noTasks != []:
			rtn['users-no-tasks'] = noTasks

		# No sprint goals, or too many tasks (at least 10 tasks and more than 20% of all tasks) without a goal
		unaffiliated = filter(lambda task: not task.goal, tasks)
		if filter(lambda goal: goal.name != '', self.getGoals()) == []:
			rtn['no-sprint-goals'] = True
		elif len(unaffiliated) >= 10 and len(unaffiliated) / len(tasks) > .20:
			rtn['tasks-without-goals'] = unaffiliated

		# Goals with no tasks
		noTasks = filter(lambda goal: goal.name and filter(lambda task: task.goal == goal, tasks) == [], self.getGoals())
		if noTasks != []:
			rtn['goals-no-tasks'] = noTasks

		# Open tasks with 0 hours
		noHours = filter(lambda task: task.stillOpen() and task.hours == 0, tasks)
		if noHours != []:
			rtn['open-without-hours'] = noHours

		# Closed tasks with >0 hours
		haveHours = filter(lambda task: not task.stillOpen() and task.hours > 0, tasks)
		if haveHours != []:
			rtn['closed-with-hours'] = haveHours

		# Tasks with too many hours
		tooManyHours = filter(lambda task: task.hours > 24, tasks)
		if tooManyHours != []:
			rtn['too-many-hours'] = tooManyHours

		return rtn
