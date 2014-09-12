from collections import OrderedDict
from json import dumps as toJS
from string import Template

from rorn.ResponseWriter import ResponseWriter

from Settings import settings
from Task import statuses, statusMenu
from utils import *

# Possible cells: [debug index goal status] [name] [assigned] [hours -2] [hours -1] [hours 0] [actions]
# The first and last will always exist; the others might not

class TaskTable:
	def __init__(self, sprint, editable, tasks = None, tableID = None, dateline = None, assignedList = None, taskClasses = {}, **show):
		self.sprint = sprint
		self.editable = editable
		self.tasks = tasks or self.sprint.getTasks()
		self.tableID = tableID
		self.dateline = dateline
		self.assignedList = assignedList or self.sprint.members
		self.taskClasses = taskClasses
		self.show = show # groupActions, taskModActions, index, goal, status, name, assigned, historicalHours, hours, debug, devEdit

		if not isinstance(self.tasks, dict):
			groupedTasks = OrderedDict()
			for group in self.sprint.getGroups():
				groupedTasks[group] = []
			for task in self.tasks:
				groupedTasks[task.group].append(task)
			self.tasks = groupedTasks

	def check(self, name):
		return self.show.get(name, False)

	def __str__(self):
		writer = ResponseWriter()
		try:
			self.out()
		finally:
			rtn = writer.done()
		return rtn

	def out(self):
		sprintDays = [day.date() for day in self.sprint.getDays()]

		# Make sure only people in assignedList are assigned to tasks
		# If everyone assigned to the task is missing from assignedList, assign it to the first person in the list
		# (this should probably be the scrummaster)
		for tasks in self.tasks.values():
			for task in tasks:
				task.assigned &= set(self.assignedList)
				if len(task.assigned) == 0:
					task.assigned = {self.assignedList[0]}

		if self.check('historicalHours'):
			if self.sprint.isActive() or self.check('devEdit'):
				days = [
					('ereyesterday', Weekday.shift(-2)),
					('yesterday', Weekday.shift(-1)),
					('today', Weekday.today())
				]
			elif self.sprint.isPlanning():
				start = tsToDate(self.sprint.start)
				ereyesterday, yesterday, today = Weekday.shift(-2, start), Weekday.shift(-1, start), start
				days = [
					('pre-plan', ereyesterday),
					('pre-plan', yesterday),
					('planning', today)
				]
			else:
				end = tsToDate(self.sprint.end)
				ereyesterday, yesterday, today = Weekday.shift(-2, end), Weekday.shift(-1, end), end
				days = [
					(ereyesterday.strftime('%A').lower(), ereyesterday),
					(yesterday.strftime('%A').lower(), yesterday),
					(today.strftime('%A').lower(), today)
				]
		elif self.check('hours'):
			days = [(None, None)]
		else:
			days = []

		print "<script type=\"text/javascript\">"
		print "status_texts = Array();"
		for statusBlock in statusMenu:
			for statusName in statusBlock:
				status = statuses[statusName]
				print "status_texts['%s'] = '%s';" % (status.name, status.text)
		print "goal_imgs = Array();"
		print "goal_imgs[0] = '/static/images/tag-none.png';"
		for goal in self.sprint.getGoals():
			print "goal_imgs[%d] = '/static/images/tag-%s.png';" % (goal.id, goal.color)
		print "goal_texts = Array();"
		print "goal_texts[0] = \"None\";"
		for goal in self.sprint.getGoals():
			print "goal_texts[%d] = %s;" % (goal.id, toJS(goal.name))
		print "</script>"

		print "<ul id=\"status-menu\" class=\"contextMenu\">"
		for statusBlock in statusMenu:
			for statusName in statusBlock:
				status = statuses[statusName]
				cls = 'separator' if statusBlock != statusMenu[0] and statusName == statusBlock[0] else ''
				print "<li class=\"%s\"><a href=\"#%s\" style=\"background-image:url('%s');\">%s</a></li>" % (cls, status.name, status.getIcon(), status.text)
		print "</ul>"

		print "<ul id=\"goal-menu\" class=\"contextMenu\">"
		print "<li><a href=\"#0\" style=\"background-image:url('/static/images/tag-none.png');\">None</a></li>"
		for goal in self.sprint.getGoals():
			if goal.name != '':
				print "<li><a href=\"#%s\" style=\"background-image:url('/static/images/tag-%s.png');\">%s</a></li>" % (goal.id, goal.color, goal.safe.name if len(goal.safe.name) <= 40 else "%s..." % goal.safe.name[:37])
		print "</ul>"

		print "<ul id=\"assigned-menu\" class=\"contextMenu\">"
		for user in sorted(self.assignedList):
			print "<li><a href=\"#%s\" style=\"background-image:url('%s');\">%s</a></li>" % (user.username, user.getAvatar(16), user.username)
		print "</ul>"

		tblClasses = ['tasktable']
		if self.editable:
			tblClasses.append('editable')
		print "<table border=0 cellspacing=0 cellpadding=2 %sclass=\"%s\">" % (('id="%s" ' % self.tableID) if self.tableID else '', ' '.join(tblClasses))
		print "<thead>"
		if any(x for x, y in days):
			print "<tr class=\"dateline nodrop nodrag\">"
			print "<td colspan=\"%d\">&nbsp;</td>" % (1 + self.check('name') + self.check('assigned'))
			for (x, y) in days:
				if x is not None:
					print "<td class=\"%s\">%s</td>" % (x, x)
			print "<td>&nbsp;</td>"
			print "</tr>"
		if any(y for x, y in days) or self.dateline is not None:
			print "<tr class=\"dateline2 nodrop nodrag\">"
			print "<td colspan=\"%d\">" % (1 + self.check('name') + self.check('assigned'))
			if self.dateline is not None:
				print self.dateline
			print "</td>"
			for (x, y) in days:
				if y is None:
					print "<td>&nbsp;</td>"
				else:
					print "<td class=\"%s\">%s<br>Day %s of %s</td>" % (x, formatDate(y), sprintDays.index(y.date())+1 if y.date() in sprintDays else 0, len(sprintDays))
			print "<td>&nbsp;</td>"
			print "</tr>"
		print "</thead>"

		print "<tbody>"
		for (group, groupTasks) in self.tasks.iteritems():
			cls = ['group']
			if not group.deletable:
				cls.append('fixed')
			print "<tr class=\"%s\" id=\"group%d\" groupid=\"%d\">" % (' '.join(cls), group.id, group.id)
			print "<td colspan=\"%d\">" % (1 + self.check('name') + self.check('assigned') + len(days))
			if self.check('debug'):
				print "<small class=\"debugtext\">(%d, %d)</small>&nbsp;" % (group.id, group.seq)
			if self.check('checkbox'):
				print "<input type=\"checkbox\"></input>"
			print "<img src=\"/static/images/collapse.png\">"
			print "<span>%s</span>" % group.name
			print "</td>"
			print "<td class=\"actions\">"
			if self.editable and self.check('groupActions'):
				print "<a href=\"/groups/new?after=%d\"><img src=\"/static/images/group-new.png\" title=\"New Group\"></a>" % group.id
				print "<a href=\"/groups/%d\"><img src=\"/static/images/group-edit.png\" title=\"Edit Group\"></a>" % group.id
				print "<a href=\"/tasks/new?group=%d\"><img src=\"/static/images/task-new.png\" title=\"New Task\"></a>" % group.id
			print "</td>"
			print "</tr>"

			for task in groupTasks:
				classes = ['task']
				if task in self.taskClasses:
					classes += self.taskClasses[task]
				if getNow() - tsToDate(task.timestamp) < timedelta(hours = 23):
					classes.append('changed-today')

				print "<tr class=\"%s\" id=\"task%d\" taskid=\"%d\" revid=\"%d\" groupid=\"%d\" goalid=\"%d\" status=\"%s\" assigned=\"%s\">" % (' '.join(classes), task.id, task.id, task.revision, task.groupid or 0, task.goal.id if task.goal else 0, task.stat.name, ' '.join(sorted(user.username for user in task.assigned)))

				print "<td class=\"flags\">"
				if self.check('debug'):
					print "<small class=\"debugtext\">(%d, %d, %d)</small>&nbsp;" % (task.id, task.seq, task.revision)
				if self.check('checkbox'):
					print "<input type=\"checkbox\"></input>"
				if self.check('index'):
					print "<span class=\"task-index badge\"></span>&nbsp;"
				if self.check('goal'):
					print "<img id=\"goal_%d\" class=\"goal\" src=\"/static/images/tag-%s.png\" title=\"%s\">&nbsp;" % ((task.goal.id, task.goal.color, task.goal.safe.name) if task.goal else (0, 'none', 'None'))
				if self.check('status'):
					print "<img id=\"status_%d\" class=\"status\" src=\"%s\" title=\"%s\">" % (task.id, task.stat.icon, task.stat.text)
				print "</td>"

				if self.check('name'):
					print "<td class=\"name\"><span id=\"name_span_%d\">%s</span></td>" % (task.id, task.safe.name)
				if self.check('assigned'):
					print "<td class=\"assigned\"><span>"
					if len(task.assigned) == 1:
						print list(task.assigned)[0].str('member', False, "assigned_span_%d" % task.id)
					else:
						assignedStr = ' '.join(sorted(user.username for user in task.assigned))
						print "<img src=\"/static/images/team.png\" class=\"user\">"
						print "<span id=\"assigned_span_%d\" class=\"username\" username=\"%s\" title=\"%s\">team (%d)</span>" % (task.id, assignedStr, assignedStr, len(task.assigned))
					print "</span></td>"

				for lbl, day in days:
					dayTask = task.getRevisionAt(day) if day else task
					previousTask = task.getRevisionAt(Weekday.shift(-1, day)) if day else None
					classes = ['hours']
					if lbl is not None:
						classes.append(lbl)
					if dayTask and previousTask and dayTask.hours != previousTask.hours:
						classes.append('changed')

					if not dayTask:
						print "<td class=\"%s\">&ndash;</td>" % ' '.join(classes)
					elif self.editable and lbl in ('today', 'planning', None):
						print "<td class=\"%s\" nowrap>" % ' '.join(classes)
						print "<div>"
						print "<img amt=\"4\" src=\"/static/images/arrow-up.png\">"
						print "<img amt=\"-4\" src=\"/static/images/arrow-down.png\">"
						print "</div>"
						print "<input type=\"text\" name=\"hours[%d]\" value=\"%d\">" % (task.id, task.hours)
						print "<div>"
						print "<img amt=\"8\" src=\"/static/images/arrow-top.png\">"
						print "<img amt=\"-8\" src=\"/static/images/arrow-bottom.png\">"
						print "</div>"
						print "</td>"
						print "</td>"
					else:
						print "<td class=\"%s\">%s</td>" % (' '.join(classes), dayTask.hours)

				print "<td class=\"actions\">"
				if task.id:
					print "<a href=\"/tasks/%d\" target=\"_blank\"><img src=\"/static/images/task-history.png\" title=\"History\"></a>" % task.id
				if self.check('taskModActions') and self.editable:
					print "<a href=\"javascript:TaskTable.delete_task(%d);\"><img src=\"/static/images/task-delete.png\" title=\"Delete Task\"></a>" % task.id
				for icon, pattern, url in zip(*settings.autolink):
					for match in re.finditer(pattern, task.name, re.IGNORECASE):
						print "<a href=\"%s\" target=\"_blank\"><img src=\"/static/images/%s.png\"></a>" % (Template(url).safe_substitute(match.groupdict()), icon)
				print "<img class=\"saving\" src=\"/static/images/loading.gif\">"
				print "</td>"
				print "</tr>"

		# Spacer so rows can be dragged to the bottom
		print "<tr><td colspan=\"%d\">&nbsp;</td></tr>" % (2 + self.check('name') + self.check('assigned') + len(days))
		print "</tbody>"
		print "</table>"
