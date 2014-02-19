from __future__ import with_statement, division
from datetime import datetime, date, timedelta
from json import dumps as toJS
from collections import OrderedDict
from itertools import product

from rorn.Session import delay, undelay
from rorn.ResponseWriter import ResponseWriter
from rorn.Box import CollapsibleBox, ErrorBox, InfoBox, SuccessBox, WarningBox

from Privilege import requirePriv
from Project import Project
from Sprint import Sprint
from Button import Button
from Table import Table
from Task import Task, statuses, statusMenu
from User import User
from Group import Group
from Tabs import Tabs, parseName as parseTabName
from Goal import Goal
from Availability import Availability
from Chart import Chart
from SprintCharts import *
from History import showHistory
from Export import exports
from LoadValues import isDevMode
from Search import Search
from Event import Event
from Retrospective import Retrospective, Category as RetroCategory, Entry as RetroEntry
from Markdown import Markdown
from utils import *

def tabs(sprint = None, where = None):
	base, name = parseTabName(where) if where is not None else (None, None)

	tabs = Tabs()
	tabs['info'] = '/sprints/%d/info'
	tabs['backlog'] = '/sprints/%d'
	tabs['metrics'] = '/sprints/%d/metrics'
	if sprint is not None and (sprint.isPlanning() or base == 'planning'):
		tabs['planning', 'history'] = '/sprints/%d/history'
		tabs.add(('planning', 'checklist'), path = '/sprints/%d/checklist', num = len(sprint.getWarnings()) or None)
		tabs['planning', 'distribute'] = '/tasks/distribute?sprint=%d'
	elif sprint is not None and (sprint.isOver() or base == 'wrapup'):
		tabs['wrapup', 'history'] = '/sprints/%d/history'
		tabs['wrapup', 'results'] = '/sprints/%d/results'
		tabs['wrapup', 'retrospective'] = '/sprints/%d/retrospective'
	else:
		tabs['history'] = '/sprints/%d/history'
	tabs['availability'] = '/sprints/%d/availability'

	if sprint is not None:
		tabs = tabs.format(sprint.id)

	# Special case tabs that move around based on sprint status
	if name == 'history' and sprint is not None:
		if sprint.isPlanning():
			tabs = tabs.where(('planning', 'history'))
		elif sprint.isOver():
			tabs = tabs.where(('wrapup', 'history'))
		else:
			tabs = tabs.where('history')
	elif name == 'distribute' and sprint is not None and sprint.isPlanning():
		tabs = tabs.where(('planning', 'distribute'))
	elif where is not None:
		tabs = tabs.where(where)

	return tabs

def drawNavArrows(sprint, tab):
	print "<div id=\"sprint-nav\"><div>"
	sprints = sprint.project.getSprints()
	thisIdx = sprints.index(sprint)
	if thisIdx > 0:
		print "<a href=\"/sprints/%d/%s\"><img src=\"/static/images/prev.png\" title=\"%s\"></a>" % (sprints[thisIdx - 1].id, tab, sprints[thisIdx - 1].safe.name.replace('"', '&quot;'))
	if thisIdx < len(sprints) - 1:
		print "<a href=\"/sprints/%d/%s\"><img src=\"/static/images/next.png\" title=\"%s\"></a>" % (sprints[thisIdx + 1].id, tab, sprints[thisIdx + 1].safe.name.replace('"', '&quot;'))
	print "</div></div>"

@get('sprints')
def sprint(handler):
	redirect('/projects')

@get('sprints/(?P<id>[0-9]+)', statics = 'sprints-backlog')
def showBacklog(handler, id, search = None, devEdit = False):
	requirePriv(handler, 'User')
	id = int(id)
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)

	# Redirect to search help page if searched for empty string
	if search == '':
		redirect('/help/search')

	handler.title(sprint.safe.name)
	drawNavArrows(sprint, '')

	tasks = sprint.getTasks()
	groups = sprint.getGroups()
	editable = sprint.canEdit(handler.session['user']) or (devEdit and isDevMode(handler))
	search = Search(sprint, search)

	print "<script src=\"/settings/sprints.js\" type=\"text/javascript\"></script>"

	print "<script type=\"text/javascript\">"
	print "var sprintid = %d;" % id
	print "var isPlanning = %s;" % ('true' if sprint.isPlanning() else 'false')
	print "var totalTasks = %d;" % len(tasks)
	print "function update_task_count() {"
	print "    var vis = $('#all-tasks .task:visible');"
	print "    var assigned = $.makeArray($('#filter-assigned .selected').map(function() {return $(this).attr('assigned');}));"
	print "    var status = $.makeArray($('#filter-status .selected').map(function() {return $(this).attr('status');}));";
	print "    txt = 'Showing ' + vis.length + ' of ' + totalTasks + (totalTasks == 1 ? ' task' : ' tasks');"
	print
	print "    search = Array();"
	if search.hasBaseString(): print "    search.push('matching \"%s\"');" % search.getBaseString().replace("'", "\\'").replace('"', '\\"')
	print "    if(status.length > 0) {search.push(status.join(' or '));}"
	print "    if(assigned.length > 0) {search.push('assigned to ' + assigned.join(' or '));}"
	for filt in search.getAll():
		if filt.description():
			print "    search.push('%s');" % filt.description().replace("'", "\\'").replace('"', '\\"')
	print
	print "    $('.save-search, .cancel-search').css('display', search.length > 0 ? 'inline' : 'none');"
	print "    if(search.length > 0) {txt += ' ' + search.join(', ');}"
	print "    $('#task-count').text(txt);"
	print "}"
	print "$('document').ready(function() {"
	if search.has('assigned'):
		print "    $('%s').addClass('selected');" % ', '.join("#filter-assigned a[assigned=\"%s\"]" % user.username for user in search.get('assigned').users + ([handler.session['user']] if search.get('assigned').currentUser else []))
	if search.has('status'):
		print "    $('%s').addClass('selected');" % ', '.join("#filter-status a[status=\"%s\"]" % status.name for status in search.get('status').statuses)
	print "    apply_filters();"
	print "});"

	print "usernames = Array(%s);" % ', '.join("'%s'" % user.username for user in sorted(sprint.members))
	print "status_texts = Array();"
	for statusBlock in statusMenu:
		for statusName in statusBlock:
			status = statuses[statusName]
			print "status_texts['%s'] = '%s';" % (status.name, status.text)
	print "goal_imgs = Array();"
	print "goal_imgs[0] = '/static/images/tag-none.png';"
	for goal in sprint.getGoals():
		print "goal_imgs[%d] = '/static/images/tag-%s.png';" % (goal.id, goal.color)
	print "goal_texts = Array();"
	print "goal_texts[0] = \"None\";"
	for goal in sprint.getGoals():
		print "goal_texts[%d] = %s;" % (goal.id, toJS(goal.name))
	print "</script>"

	print "<div id=\"selected-task-box\">"
	print "<span></span>"
	print Button('history', id = 'selected-history').positive()
	print Button('highlight', id = 'selected-highlight').positive()
	print Button('mass edit', id = 'selected-edit').positive()
	print Button('cancel', id = 'selected-cancel') #.negative()
	print "</div>"

	print "<div class=\"backlog-tabs\">"
	print tabs(sprint, 'backlog')
	print "<input type=\"text\" id=\"search\" value=\"%s\">" % search.getFullString().replace('"', '&quot;')
	print "</div>"

	if sprint.isActive() or devEdit:
		days = [
			('ereyesterday', Weekday.shift(-2)),
			('yesterday', Weekday.shift(-1)),
			('today', Weekday.today())
		]
	elif sprint.isPlanning():
		start = tsToDate(sprint.start)
		ereyesterday, yesterday, today = Weekday.shift(-2, start), Weekday.shift(-1, start), start
		days = [
			('pre-plan', ereyesterday),
			('pre-plan', yesterday),
			('planning', today)
		]
	else:
		end = tsToDate(sprint.end)
		ereyesterday, yesterday, today = Weekday.shift(-2, end), Weekday.shift(-1, end), end
		days = [
			(ereyesterday.strftime('%A').lower(), ereyesterday),
			(yesterday.strftime('%A').lower(), yesterday),
			(today.strftime('%A').lower(), today)
		]

	undelay(handler)

	print "<ul id=\"status-menu\" class=\"contextMenu\">"
	for statusBlock in statusMenu:
		for statusName in statusBlock:
			status = statuses[statusName]
			cls = 'separator' if statusBlock != statusMenu[0] and statusName == statusBlock[0] else ''
			print "<li class=\"%s\"><a href=\"#%s\" style=\"background-image:url('%s');\">%s</a></li>" % (cls, status.name, status.getIcon(), status.text)
	print "</ul>"

	print "<ul id=\"goal-menu\" class=\"contextMenu\">"
	print "<li><a href=\"#0\" style=\"background-image:url('/static/images/tag-none.png');\">None</a></li>"
	for goal in sprint.getGoals():
		if goal.name != '':
			print "<li><a href=\"#%s\" style=\"background-image:url('/static/images/tag-%s.png');\">%s</a></li>" % (goal.id, goal.color, goal.safe.name if len(goal.safe.name) <= 40 else "%s..." % goal.safe.name[:37])
	print "</ul>"

	print "<ul id=\"assigned-menu\" class=\"contextMenu\">"
	for user in sorted(sprint.members):
		print "<li><a href=\"#%s\" style=\"background-image:url('%s');\">%s</a></li>" % (user.username, user.getAvatar(16), user.username)
	print "</ul>"

	print InfoBox('Loading...', id = 'post-status', close = True)

	avail = Availability(sprint) if sprint.isActive() else None
	dayStart = Weekday.today().date()
	print "<div id=\"filter-assigned\">"
	print "<a class=\"fancy danger\" href=\"#\"><img src=\"/static/images/cross.png\">&nbsp;None</a>"
	for member in sorted(sprint.members):
		cls = ['fancy']
		if not sprint.isPlanning() and avail and avail.get(member, dayStart) == 0:
			cls.append('away')
		print "<a class=\"%s\" assigned=\"%s\" href=\"/sprints/%d?search=assigned:%s\"><img src=\"%s\">&nbsp;%s</a>" % (' '.join(cls), member.username, id, member.username, member.getAvatar(16), member.username)
	print "</div><br>"

	print "<div id=\"filter-status\">"
	print "<a class=\"fancy danger\" href=\"#\"><img src=\"/static/images/cross.png\">&nbsp;None</a>"
	for status in sorted(statuses.values()):
		print "<a class=\"fancy\" status=\"%s\" href=\"/sprints/%d?search=status:%s\"><img src=\"%s\">%s</a>" % (status.name, id, status.name.replace(' ', '-'), status.getIcon(), status.text)
	print "</div><br>"

	if sprint.isPlanning():
		if sprint.isActive():
			print InfoBox("Today is <b>sprint planning</b> &mdash; tasks aren't finalized until the end of the day")
		else:
			daysTillPlanning = (tsToDate(sprint.start) - getNow()).days + 1
			print InfoBox("The sprint has <b>not begun</b> &mdash; planning is %s. All changes are considered to have been made midnight of plan day" % ('tomorrow' if daysTillPlanning == 1 else "in %d days" % daysTillPlanning))
	elif sprint.isReview():
		print InfoBox("Today is <b>sprint review</b> &mdash; this is the last day to make changes to the backlog")
	elif not sprint.isOver():
		noHours = filter(lambda task: task.stillOpen() and task.hours == 0, tasks)
		if noHours != []:
			print WarningBox("There are <a href=\"/sprints/%d?search=status:not-started,in-progress,blocked hours:0\">open tasks with no hour estimate</a>" % sprint.id)

	tasks = search.filter(tasks)

	if isDevMode(handler):
		print Button('#all-tasks borders', "javascript:$('#all-tasks, #all-tasks tr td').css('border', '1px solid #f00').css('border-collapse', 'collapse');").negative()
		if not editable:
			print Button('make editable', "/sprints/%d?devEdit" % id).negative()
		elif devEdit:
			print Button('make uneditable', "/sprints/%d" % id).negative()

		print "<div class=\"debugtext\">"
		print "start: %d (%s)<br>" % (sprint.start, tsToDate(sprint.start))
		print "end: %d (%s)<br>" % (sprint.end, tsToDate(sprint.end))
		print "</div>"

	#TODO I think this form (and possibly the hidden inputs right after) can be removed
	print "<form method=\"post\" action=\"/sprints/%d\">" % id
	# print Button('Save', image = 'tick.png', id = 'save-button').positive()

	for task in tasks:
		print "<input type=\"hidden\" name=\"status[%d]\" value=\"%s\">" % (task.id, task.status)
		print "<input type=\"hidden\" name=\"goal[%d]\" value=\"%s\">" % (task.id, task.goal.id if task.goal else 0)

	tblClasses = ['tasks']
	if editable:
		tblClasses.append('editable')
	sprintDays = [day.date() for day in sprint.getDays()]
	print "<table border=0 cellspacing=0 cellpadding=2 id=\"all-tasks\" class=\"%s\">" % ' '.join(tblClasses)
	print "<thead>"
	print "<tr class=\"dateline nodrop nodrag\">"
	print "<td colspan=\"3\">&nbsp;</td>"
	for (x, y) in days:
		print "<td class=\"%s\">%s</td>" % (x, x)
	print "<td>&nbsp;</td>"
	print "</tr>"
	print "<tr class=\"dateline2 nodrop nodrag\">"
	print "<td colspan=\"3\">"
	print "<span id=\"task-count\"></span>"
	print "<a href=\"/search/saved/new?sprintid=%d&query=%s\"><img class=\"save-search\" src=\"/static/images/save.png\" title=\"Save search\"></a>" % (id, search.getFullString().replace('"', '&quot;'))
	print "<a href=\"/sprints/%d\"><img class=\"cancel-search\" src=\"/static/images/cross.png\" title=\"Clear search\"></a>" % id
	print "</td>"
	for (x, y) in days:
		print "<td class=\"%s\">%s<br>Day %s of %s</td>" % (x, formatDate(y), sprintDays.index(y.date())+1 if y.date() in sprintDays else 0, len(sprintDays))
	print "<td>&nbsp;</td>"
	print "</tr>"
	print "</thead>"

	print "<tbody>"
	for group in groups:
		cls = ['group']
		if not group.deletable:
			cls.append('fixed')
		print "<tr class=\"%s\" id=\"group%d\" groupid=\"%d\">" % (' '.join(cls), group.id, group.id)
		print "<td colspan=\"6\">"
		if isDevMode(handler):
			print "<small class=\"debugtext\">(%d, %d)</small>&nbsp;" % (group.id, group.seq)
		print "<img src=\"/static/images/collapse.png\">&nbsp;<span>%s</span>" % group.name
		print "</td>"
		print "<td class=\"actions\">"
		if editable:
			print "<a href=\"/groups/new?after=%d\"><img src=\"/static/images/group-new.png\" title=\"New Group\"></a>" % group.id
			print "<a href=\"/groups/%d\"><img src=\"/static/images/group-edit.png\" title=\"Edit Group\"></a>" % group.id
			print "<a href=\"/tasks/new?group=%d\"><img src=\"/static/images/task-new.png\" title=\"New Task\"></a>" % group.id
		print "</td>"
		print "</tr>"

		groupTasks = filter(lambda task: task.group == group, tasks)
		for task in groupTasks:
			printTask(handler, task, days, group = task.group, highlight = (search.has('highlight') and task in search.get('highlight').tasks), editable = editable)

	print "<tr><td colspan=\"7\">&nbsp;</td></tr>" # Spacer so rows can be dragged to the bottom
	print "</tbody>"
	print "</table>"
	print "</form>"

def printTask(handler, task, days, group = None, highlight = False, editable = True):
	classes = ['task']
	if highlight:
		classes.append('highlight')
	if getNow() - tsToDate(task.timestamp) < timedelta(hours = 23):
		classes.append('changed-today')

	print "<tr class=\"%s\" id=\"task%d\" taskid=\"%d\" revid=\"%d\" groupid=\"%d\" goalid=\"%d\" status=\"%s\" assigned=\"%s\">" % (' '.join(classes), task.id, task.id, task.revision, group.id if group else 0, task.goal.id if task.goal else 0, task.stat.name, ' '.join(sorted(user.username for user in task.assigned)))

	print "<td class=\"flags\">"
	if isDevMode(handler):
		print "<small class=\"debugtext\">(%d, %d, %d)</small>&nbsp;" % (task.id, task.seq, task.revision)
	# print "<img src=\"/static/images/star.png\">&nbsp;"
	print "<span class=\"task-index badge\"></span>&nbsp;"
	print "<img id=\"goal_%d\" class=\"goal\" src=\"/static/images/tag-%s.png\" title=\"%s\">&nbsp;" % ((task.goal.id, task.goal.color, task.goal.safe.name) if task.goal else (0, 'none', 'None'))
	print "<img id=\"status_%d\" class=\"status\" src=\"%s\" title=\"%s\">" % (task.id, task.stat.icon, task.stat.text)
	print "</td>"

	print "<td class=\"name\"><span id=\"name_span_%d\">%s</span></td>" % (task.id, task.safe.name)
	print "<td class=\"assigned\"><span>"
	if len(task.assigned) == 1:
		print list(task.assigned)[0].str('member', False, "assigned_span_%d" % task.id)
	else:
		assignedStr = ' '.join(sorted(user.username for user in task.assigned))
		print "<img src=\"/static/images/team.png\" class=\"user\">"
		print "<span id=\"assigned_span_%d\" class=\"username\" username=\"%s\" title=\"%s\">team (%d)</span>" % (task.id, assignedStr, assignedStr, len(task.assigned))
	print "</span></td>"
	for lbl, day in days:
		dayTask = task.getRevisionAt(day)
		previousTask = task.getRevisionAt(Weekday.shift(-1, day))
		classes = ['hours', lbl]
		if dayTask and previousTask and dayTask.hours != previousTask.hours:
			classes.append('changed')

		if not dayTask:
			print "<td class=\"%s\">&ndash;</td>" % ' '.join(classes)
		elif editable and (lbl == 'today' or lbl == 'planning'):
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
	print "<a href=\"/tasks/%d\" target=\"_blank\"><img src=\"/static/images/task-history.png\" title=\"History\"></a>" % task.id
	if editable:
		print "<a href=\"javascript:delete_task(%d);\"><img src=\"/static/images/task-delete.png\" title=\"Delete Task\"></a>" % task.id
	print "<a href=\"#\" class=\"bugzilla\" target=\"_blank\"><img src=\"/static/images/bugzilla.png\" title=\"Link to bug\"></a>"
	print "<img class=\"saving\" src=\"/static/images/loading.gif\">"
	print "</td>"
	print "</tr>"

@post('sprints/(?P<sprintid>[0-9]+)')
def sprintPost(handler, sprintid, p_id, p_rev_id, p_field, p_value):
	def die(msg):
		print msg
		done()

	handler.wrappers = False
	sprintid = int(sprintid)
	p_id = int(p_id)
	p_rev_id = int(p_rev_id)

	if not handler.session['user']:
		die("You must be logged in to modify tasks")

	sprint = Sprint.load(sprintid)
	if not sprint:
		die("There is no sprint with ID %d" % sprintid)
	elif not (sprint.isActive() or sprint.isPlanning()):
		die("Unable to modify inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		die("You don't have permission to modify this sprint")

	task = Task.load(p_id)
	if task.sprint != sprint:
		die("Attempting to modify task outside the specified sprint")

	# hours, taskmove, name, assigned, status
	if task.revision != p_rev_id: #TODO Implement collision support
		die("Collision with %s detected. Changes not saved" % task.creator)

	if p_value.strip() == '':
		die("Task name cannot be empty")

	if p_field in ['status', 'name', 'goal', 'assigned', 'hours', 'deleted']:
		for case in switch(p_field):
			if case('status') or case('name') or case('deleted'):
				parsedValue = p_value
				break
			elif case('goal'):
				parsedValue = None
				if p_value != '0':
					parsedValue = Goal.load(to_int(p_value, 'goal', die))
					if not parsedValue:
						die("Unknown goal: <b>%s</b>" % stripTags(p_value))
					if parsedValue.sprint != sprint:
						die("Attempting to use goal outside the specified sprint")
				break
			elif case('assigned'):
				parsedValue = set(User.load(username = username) for username in p_value.split(' '))
				if not all(parsedValue):
					die("Unknown user(s): <b>%s</b>" % stripTags(p_value))
				break
			elif case('hours'):
				parsedValue = int(p_value)

		if task.__getattribute__(p_field) != parsedValue: # Only save if the field has changed
			task.__setattr__(p_field, parsedValue)

			# Is this within the 5-minute window, by the same user?
			# If we're in pre-planning, the task's timestamp will be in the future, so (ts - task.timestamp) will be negative, which satisfies the check
			if task.creator == handler.session['user'] and (dateToTs(getNow()) - task.timestamp) < 5*60:
				task.save()
			else:
				task.saveRevision(handler.session['user'])

			Event.taskUpdate(handler, task, p_field, parsedValue)

	elif p_field == 'taskmove':
		if p_value[0] == ':': # Beginning of the group
			predTask = None
			predGroupID = int(p_value[1:])
			predGroup = Group.load(predGroupID)
			if not predGroup:
				die("No group with ID %d" % predGroupID)
		else:
			predTask = Task.load(int(p_value))
			predGroup = predTask.group

		if predGroup.sprint != sprint:
			die("Group/task sprint mismatch")

		task.move(predTask, predGroup)
	else:
		die("Unexpected field name: %s" % stripTags(p_field))

	# 299 - good
	# 298 - warning
	# 200 - error
	handler.responseCode = 299
	print task.revision

@get('sprints/active')
def findActiveSprint(handler, project = None, search = None):
	handler.title('Active Sprint')
	requirePriv(handler, 'User')
	if project:
		projectid = int(project)
		project = Project.load(projectid)
		if not project:
			ErrorBox.die('Load project', "No project with ID <b>%d</b>" % projectid)

	url = "/sprints/%d"
	if search:
		url += "?search=%s" % search

	sprints = Sprint.loadAllActive(handler.session['user'], project)
	for case in switch(len(sprints)):
		if case(0):
			ErrorBox.die('Active sprint', 'No active sprints found')
			break
		if case(1):
			redirect(url % sprints[0].id)
			break
		if case():
			print "You are active in multiple sprints%s:<br><br>" % (" in the %s project" % project.safe.name if project else '')
			for sprint in sprints:
				print "<a href=\"%s\">%s</a><br>" % (url % sprint.id, sprint.safe.name)
			break

@get('sprints/(?P<id>[0-9]+)/info', statics = 'sprints-info')
def showInfo(handler, id):
	requirePriv(handler, 'User')
	id = int(id)
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	tasks = sprint.getTasks()
	editable = sprint.owner == handler.session['user'] # Info can be edited even after the sprint closes

	handler.title(sprint.safe.name)
	drawNavArrows(sprint, 'info')

	print "<script type=\"text/javascript\">"
	print "var sprintid = %d;" % id
	print "var startMin = '%s';" % min(tsToDate(sprint.start), getNow()).strftime('%m/%d/%Y')
	print "var endMin = '%s';" % tsToDate(sprint.end).strftime('%m/%d/%Y')
	print "</script>"

	print InfoBox('Loading...', id = 'post-status', close = True)

	print tabs(sprint, 'info')

	print "<form method=\"post\" action=\"/sprints/info?id=%d\">" % sprint.id
	print "<b>Name</b><br>"
	if editable:
		print "<input type=\"text\" name=\"name\" class=\"name\" value=\"%s\"><br><br>" % sprint.safe.name
	else:
		print "%s<br><br>" % sprint.safe.name
	print "<b>Duration</b><br>"
	if editable:
		print "<input type=\"text\" name=\"start\" class=\"date\" value=\"%s\">" % (tsToDate(sprint.start).strftime('%m/%d/%Y')),
	else:
		print tsToDate(sprint.start).strftime('%m/%d/%Y'),
	print '-',
	if editable:
		print "<input type=\"text\" name=\"end\" class=\"date\" value=\"%s\">" % (tsToDate(sprint.end).strftime('%m/%d/%Y')),
	else:
		print tsToDate(sprint.end).strftime('%m/%d/%Y'),
	print "<br><br>"
	print "<b>Sprint goals</b><br>"
	for goal in sprint.getGoals():
		if editable:
			print "<input type=\"text\" class=\"goal\" style=\"background-image: url(/static/images/tag-%s.png)\" name=\"goals[%d]\" goalid=\"%d\" value=\"%s\"><br>" % (goal.color, goal.id, goal.id, goal.safe.name)
			numTasks = len(filter(lambda task: task.goal == goal, tasks))
			if numTasks > 0:
				print "<div class=\"clear-goal-tasks\" id=\"clear-tasks-%d\"><input type=\"checkbox\" id=\"clear-tasks-check-%d\" name=\"clear[]\" value=\"%d\"><label for=\"clear-tasks-check-%d\">Clear the %s currently assigned to this goal (%s will no longer contribute to a sprint goal)</label></div>" % (goal.id, goal.id, goal.id, goal.id, pluralize(numTasks, 'task', 'tasks'), 'it' if numTasks == 1 else 'they')
		elif goal.name:
			print "<img class=\"bumpdown\" src=\"/static/images/tag-%s.png\">&nbsp;%s<br>" % (goal.color, goal.safe.name)
	print "</table>"
	print "<br>"
	print "<b>Members</b><br>"
	if editable:
		print "<select name=\"members[]\" id=\"select-members\" multiple>"
		for user in sorted(User.loadAll()):
			if user.hasPrivilege('User') or user in sprint.members:
				print "<option value=\"%d\"%s>%s</option>" % (user.id, ' selected' if user in sprint.members else '', user.safe.username)
		print "</select>"
	else:
		print ', '.join(member.str('scrummaster' if member == sprint.owner else 'member') for member in sorted(sprint.members))
	print "<br>"

	if editable:
		print Button('Save', id = 'save-button', type = 'button').positive()
	print "</form>"

@post('sprints/info')
def sprintInfoPost(handler, id, p_name, p_end, p_goals, p_start = None, p_members = None, p_clear = []):
	def die(msg):
		print msg
		done()

	handler.wrappers = False

	if not handler.session['user']:
		die("You must be logged in to modify sprint info")

	id = to_int(id, 'id', die)
	p_members = to_int(p_members, 'members', die)
	sprint = Sprint.load(id)
	if not sprint:
		die("There is no sprint with ID %d" % id)

	if sprint.owner != handler.session['user']:
		die("You must be the scrummaster to modify sprint information")

	if p_start:
		try:
			start = re.match("^(\d{1,2})/(\d{1,2})/(\d{4})$", p_start)
			if not start:
				raise ValueError
			month, day, year = map(int, start.groups())
			start = datetime(year, month, day, 0, 0, 0)
		except ValueError:
			die("Malformed start date: %s" % stripTags(p_start))
		minDate = tsToDate(tsStripHours(min(dateToTs(getNow()), sprint.start)))
		if start < minDate:
			die("You cannot start the sprint before %s" % minDate.strftime('%d %b %Y'))
	else:
		start = None

	try:
		end = re.match("^(\d{1,2})/(\d{1,2})/(\d{4})$", p_end)
		if not end:
			raise ValueError
		month, day, year = map(int, end.groups())
		end = datetime(year, month, day, 23, 59, 59)
	except ValueError:
		die("Malformed end date: %s" % stripTags(p_end))
	if end < tsToDate(sprint.end):
		die("You cannot shorten the length of the sprint")

	goals = map(Goal.load, to_int(p_goals.keys(), 'goals', die))
	if not all(goals):
		die("One or more goals do not exist")

	members = set(map(User.load, p_members)) if p_members else set()
	if not all(members):
		die("One or more members do not exist")
	if sprint.owner not in members:
		die("The scrummaster (%s) must be a sprint member" % sprint.owner)

	if (dateToTs(start) if start else sprint.start) > sprint.end:
		die("Start date cannot be after end date")

	tasks = sprint.getTasks()
	changedTasks = set()
	avail = Availability(sprint)
	addMembers = set(members) - set(sprint.members)
	delMembers = set(sprint.members) - set(members)
	for user in delMembers:
		for task in filter(lambda task: user in task.assigned, tasks):
			print "Removing %s from %d<br>" % (user, task.id)
			task.assigned -= {user}
			if len(task.assigned) == 0:
				print "Adding %s to %d<br>" % (sprint.owner, task.id)
				task.assigned = {sprint.owner}
			changedTasks.add(task)
		avail.delete(user)
		sprint.members -= {user}

	# For event dispatching
	changes = OrderedDict([
		('name', None if sprint.name == p_name else p_name),
		('start', None if tsToDate(sprint.start) == start else start),
		('end', None if tsToDate(sprint.end) == end else end),
		('addMembers', addMembers),
		('delMembers', delMembers),

		# Updated later
		('addGoals', []),
		('removeGoals', [])
	])

	sprint.members |= addMembers
	sprint.name = p_name
	sprint.end = dateToTs(end)

	if dateToTs(start) != sprint.start:
		sprint.start = dateToTs(start)
		avail.trim()

	sprint.save()

	for id in p_goals:
		goal = Goal.load(int(id))
		if goal.name != p_goals[id]:
			if goal.name:
				changes['removeGoals'].append(goal.name)
			if p_goals[id]:
				changes['addGoals'].append(p_goals[id])

		goal.name = p_goals[id]
		goal.save()

	if start:
		for task in sprint.getTasks(includeDeleted = True):
			for rev in task.getRevisions():
				if rev.timestamp < sprint.start:
					rev.timestamp = sprint.start
					rev.save()
				else:
					break
		for task in changedTasks:
			if task.timestamp < sprint.start:
				task.timestamp = sprint.start

	if p_clear:
		ids = [to_int(goalid, 'p_clear', die) for goalid in p_clear]
		for task in tasks:
			if task.goal and task.goal.id in ids:
				task.goal = None
				changedTasks.add(task)

	for task in changedTasks:
		print "Saving new revision for %d<br>" % task.id
		task.saveRevision(handler.session['user'])

	handler.responseCode = 299
	delay(handler, SuccessBox("Updated info", close = 3, fixed = True))
	Event.sprintInfoUpdate(handler, sprint, changes)


@get('sprints/(?P<id>[0-9]+)/metrics', statics = 'sprints')
def showMetrics(handler, id):
	requirePriv(handler, 'User')
	id = int(id)
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)

	context = {}
	context['sprint'] = sprint
	context['allTasks'] = sprint.getTasks(includeDeleted = True)
	context['tasks'] = tasks = filter(lambda task: not task.deleted, context['allTasks'])
	context['revisions'] = {(task.id, day): task.getRevisionAt(day) for task, day in product(context['allTasks'], sprint.getDays())}

	handler.title(sprint.safe.name)
	drawNavArrows(sprint, 'metrics')

	print "<style type=\"text/css\">"
	print "h2 a {color: #000;}"
	print "</style>"

	charts = [
		('general', 'Hours (general)', HoursChart('chart-general', **context)),
		('commitment-by-user', 'Commitment (by user)', CommitmentByUserChart(**context)),
		('earned-value', 'Earned Value', EarnedValueChart('chart-earned-value', **context)),
		('by-user', 'Hours (by user)', HoursByUserChart('chart-by-user', **context)),
		('status', 'Task status', StatusChart('chart-status', **context)),
		('commitment', 'Total commitment', CommitmentChart('chart-commitment', **context)),
		('goals', 'Sprint goals', GoalsChart(**context)),
	]

	Chart.include()
	map(lambda (anchor, title, chart): chart.js(), charts)
	print tabs(sprint, 'metrics')

	if not sprint.isOver():
		noHours = filter(lambda task: task.stillOpen() and task.hours == 0, tasks)
		if noHours != []:
			print WarningBox("There are <a href=\"/sprints/%d?search=status:not-started,in-progress,blocked hours:0\">open tasks with no hour estimate</a>. These unestimated tasks can artifically lower the tasking lines in the following charts" % sprint.id)

	for anchor, title, chart in charts:
		print "<a name=\"%s\">" % anchor
		print "<h2><a href=\"#%s\">%s</a></h2>" % (anchor, title)
		chart.placeholder()

	print "<br><br>"

@get('sprints/(?P<id>[0-9]+)/history', statics = 'sprints-history')
def showSprintHistory(handler, id, assigned = None):
	requirePriv(handler, 'User')
	id = int(id)
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	tasks = sprint.getTasks(includeDeleted = True)

	handler.title(sprint.safe.name)
	drawNavArrows(sprint, 'history')

	Chart.include()
	chart = TaskChart('chart', sprint.getTasks())
	chart.js()
	print "<script type=\"text/javascript\">"
	tasksByAssigned = {member.username: [task.id for task in tasks if member in task.assigned] for member in sprint.members}
	print "var tasks_by_assigned = %s;" % toJS(tasksByAssigned)
	print "$(document).ready(function() {"
	if assigned:
		print "    $('%s').addClass('selected');" % ', '.join("#filter-assigned a[assigned=\"%s\"]" % username for username in assigned.split(','))
	print "    setup_filter_buttons();"
	print "    apply_filters();"
	print "});"
	print "</script>"

	print tabs(sprint, 'history')
	if len(tasks) == 0:
		print ErrorBox("This sprint has no tasks")
		print "<br>"
		return

	print "<div id=\"filter-assigned\">"
	print "<a class=\"fancy danger\" href=\"#\"><img src=\"/static/images/cross.png\">&nbsp;None</a>"
	for member in sorted(sprint.members):
		print "<a class=\"fancy\" assigned=\"%s\" href=\"/sprints/%d/history?assigned=%s\"><img src=\"%s\">&nbsp;%s</a>" % (member.username, id, member.username, member.getAvatar(16), member.username)
	print "</div><br>"

	chart.placeholder()
	showHistory(tasks, True)
	print "<br>"

@get('sprints/(?P<id>[0-9]+)/availability', statics = 'sprints-availability')
def showAvailability(handler, id):
	requirePriv(handler, 'User')
	id = int(id)
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	tasks = sprint.getTasks()

	handler.title(sprint.safe.name)
	drawNavArrows(sprint, 'availability')
	print tabs(sprint, 'availability')

	print "<script type=\"text/javascript\">"
	print "var sprintid = %d;" % id
	print "</script>"

	print InfoBox('Loading...', id = 'post-status', close = True)

	avail = Availability(sprint)
	oneday = timedelta(1)
	start, end = tsToDate(sprint.start), tsToDate(sprint.end)
	editable = sprint.canEdit(handler.session['user'])

	print "<form method=\"post\" action=\"/sprints/%d/availability\">" % sprint.id
	print "<table class=\"availability\">"
	print "<tr class=\"dateline\">"
	print "<td>&nbsp;</td>"
	for day in sprint.getDays():
		print "<td>%s<br>%s</td>" % (day.strftime('%d'), day.strftime('%a'))
		if day.weekday() == 4:
			print "<td class=\"spacer\">&nbsp;</td>"
	print "<td class=\"buttons\"></td>" # The stylesheet counts cells from the right, so it's important that this be here to match the other rows
	print "</tr>"
	if editable:
		print "<tr class=\"dateline\">"
		print "<td class=\"buttons\">"
		if editable:
			print Button('set all 8', id = 'set-all-8', type = 'button').info()
		print "</td>"
		for day in sprint.getDays():
			print "<td class=\"buttons\"><img src=\"/static/images/clipboard.png\" title=\"Copy first down\"></td>"
			if day.weekday() == 4:
				print "<td class=\"spacer\">&nbsp;</td>"
		print "<td class=\"buttons\"></td>"
		print "</tr>"

	for user in sorted(sprint.members):
		print "<tr class=\"userline\">"
		print "<td class=\"username\">%s&nbsp;<img src=\"%s\"></td>" % (user.safe.username, user.getAvatar(16))
		for day in sprint.getDays():
			if editable:
				print "<td><input type=\"text\" name=\"hours[%d,%d]\" value=\"%d\"></td>" % (user.id, dateToTs(day), avail.get(user, day))
			else:
				print "<td style=\"text-align: center\">%d</td>" % avail.get(user, day)

			if day.weekday() == 4:
				print "<td class=\"spacer\">&nbsp;</td>"
		if editable:
			print "<td class=\"buttons\"><img src=\"/static/images/clipboard.png\" title=\"Copy first right\"></td>"
		print "</tr>"

	if editable:
		print "<tr><td>%s</td></tr>" % Button('Save', id = 'save-button', type = 'button').positive()
	print "</table>"
	print "</form>"

@post('sprints/(?P<id>[0-9]+)/availability')
def sprintAvailabilityPost(handler, id, p_hours):
	def die(msg):
		print msg
		done()

	handler.wrappers = False
	id = int(id)

	if not handler.session['user']:
		die("You must be logged in to modify sprint info")

	sprint = Sprint.load(id)
	if not sprint:
		die("There is no sprint with ID %d" % id)

	if not (sprint.isActive() or sprint.isPlanning()):
		die("Unable to modify inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		die("You don't have permission to modify this sprint")

	avail = Availability(sprint)
	for k, hours in p_hours.items():
		userid, timestamp = map(int, k.split(',', 1))
		hours = int(hours)

		user = User.load(userid)
		if not user in sprint.members:
			die("Trying to set availability of non-member %s" % user.safe.username)
		time = tsToDate(timestamp)
		if not sprint.start <= timestamp <= sprint.end:
			die("Trying to set availability outside of sprint window")

		avail.set(user, time, hours)

	handler.responseCode = 299
	delay(handler, SuccessBox("Updated availability", close = 3, fixed = True))
	Event.sprintAvailUpdate(handler, sprint)

@get('sprints/(?P<id>[0-9]+)/checklist', statics = 'sprints-checklist')
def showSprintChecklist(handler, id):
	requirePriv(handler, 'User')
	id = int(id)
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	tasks = sprint.getTasks()

	handler.title(sprint.safe.name)
	drawNavArrows(sprint, 'checklist')
	print tabs(sprint, ('planning', 'checklist'))

	warnings = sprint.getWarnings()

	def good(text): print "<div class=\"good\">%s</div>" % text
	def warn(text): print "<div class=\"warn\">%s</div>" % text
	def bad(text): print "<div class=\"bad\">%s</div>" % text
	def userStr(l):
		l = map(str, sorted(l))
		for case in switch(len(l)):
			if case(0):
				return ''
			if case(1):
				return l[0]
			if case(2):
				return "%s and %s" % tuple(l)
			if case():
				front, last = l[:-1], l[-1]
				return "%s, and %s" % (', '.join(front), last)

	print "<div class=\"sprint-warnings\">"
	print "<h1>Members</h1>"

	if 'no-availability' in warnings:
		bad("%s %s no <a href=\"/sprints/%d/availability\">availability</a>" % (userStr(warnings['no-availability']), 'has' if len(warnings['no-availability']) == 1 else 'have', sprint.id))
	else:
		good("All members have some availability during the sprint")

	if 'overcommitted' in warnings:
		bad("%s %s <a href=\"/sprints/%d/metrics#commitment-by-user\">overcommitted</a>" % (userStr(warnings['overcommitted']), 'is' if len(warnings['overcommitted']) == 1 else 'are', sprint.id))
	else:
		good("All members have enough availability for their tasks")

	if 'no-tasks' in warnings:
		bad("%s %s <a href=\"/sprints/%d/metrics#commitment-by-user\">no tasks</a>" % (userStr(warnings['no-tasks']), 'has' if len(warnings['no-tasks']) == 1 else 'have', sprint.id))
	else:
		good("All members have tasks assigned")

	print "<br><h1>Goals</h1>"

	if 'no-sprint-goals' in warnings:
		bad("There are no <a href=\"/sprints/%d/info\">sprint goals</a>" % sprint.id)
	else:
		goals = filter(lambda goal: goal.name != '', sprint.getGoals())
		good(pluralize(len(goals), 'sprint goal is defined', 'sprint goals are defined'))

	if 'tasks-without-goals' in warnings:
		bad("There are many <a href=\"/sprints/%d?search=goal:none\">tasks unrelated to the sprint goals</a>" % sprint.id)
	elif 'no-sprint-goals' in warnings and tasks != []:
		warn("There are %s waiting for goals" % pluralize(len(tasks), 'task', 'tasks'))
	else:
		unaffiliated = filter(lambda task: not task.goal, tasks)
		if unaffiliated == []:
			good("All tasks contribute to the sprint goals")
		else:
			good("Most tasks contribute to the sprint goals (<a href=\"/sprints/%d?search=goal:none\">%d left</a>)" % (sprint.id, len(unaffiliated)))

	print "<br><h1>Tasks</h1>"

	if 'open-without-hours' in warnings:
		bad("There are <a href=\"/sprints/%d?search=status:not-started,in-progress,blocked hours:0\">open tasks with no hour estimate</a>" % sprint.id)
	else:
		good("All open tasks have hours estimated")

	if 'closed-with-hours' in warnings:
		bad("There are <a href=\"/sprints/%d?search=status:deferred,split hours:>0\">deferred tasks with hours</a>. These hours are counted as part of the sprint commitment" % sprint.id)
	else:
		good("All closed tasks have 0 hours")

	if 'too-many-hours' in warnings:
		bad("There are <a href=\"/sprints/%d?search=hours:>24\">tasks with too many hours</a>" % sprint.id)
	else:
		good("All tasks have at most 24 hours estimated")

	print "</div>"

@get('sprints/(?P<id>[0-9]+)/results', statics = 'sprints')
def showSprintResults(handler, id):
	requirePriv(handler, 'User')
	id = int(id)
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)

	tasksNow = sprint.getTasks()
	tasksStart = filter(None, (task.getRevisionAt(tsToDate(sprint.start)) for task in tasksNow))
	tasksNow = {task.id: task for task in tasksNow}
	tasksStart = {task.id: task for task in tasksStart}

	handler.title(sprint.safe.name)
	drawNavArrows(sprint, 'results')
	print tabs(sprint, ('wrapup', 'results'))

	if not sprint.isOver():
		ErrorBox.die('Sprint Open', "Results aren't available until the sprint has closed")

	from rorn.Box import WarningBox
	print WarningBox("This feature is still under development")

	print "<ul>"

	completed = filter(lambda task: task.status == 'complete', tasksNow.values())
	print "<li><a href=\"/sprints/%d?search=status:complete\">%s completed</a> (%d%% of the original hourly commitment)</li>" % (sprint.id, pluralize(len(completed), 'task', 'tasks'), sum(tasksStart[task.id].hours if task.id in tasksStart else 0 for task in completed) * 100 / sum(task.hours for task in tasksStart.values()))

	planned = filter(lambda task: task.id in tasksStart, tasksNow.values())
	print "<li>%d%% of tasks were planned from the start</li>" % (len(planned) * 100 / len(tasksNow))

	print "</ul>"

@get('sprints/(?P<id>[0-9]+)/retrospective', statics = 'sprints-retrospective')
def showSprintRetrospective(handler, id):
	requirePriv(handler, 'User')
	id = int(id)
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	editing = (sprint.owner == handler.session['user'])

	handler.title(sprint.safe.name)
	drawNavArrows(sprint, 'retrospective')
	print tabs(sprint, ('wrapup', 'retrospective'))

	Markdown.head()
	print "<script type=\"text/javascript\">"
	print "var sprint_id = %d;" % sprint.id
	print "var editing = %s;" % toJS(editing)
	print "</script>"

	if not sprint.isOver():
		ErrorBox.die('Sprint Open', "The retrospective isn't available until the sprint has closed")

	retro = Retrospective.load(sprint)
	if retro is None:
		if editing:
			print "<form method=\"post\" action=\"/sprints/%d/retrospective/start\">" % sprint.id
			print Button("Start Retrospective").post().positive()
			print "</form>"
		else:
			print ErrorBox("This sprint has no retrospective")
		done()

	print "The sprint retrospective asks two main questions:<br>"
	print "<ul class=\"retrospective-list\">"
	print "<li class=\"good\">What went well during the sprint?</li>"
	print "<li class=\"bad\">What could be improved in the next sprint?</li>"
	print "</ul>"
	if editing:
		print "For now the list of categories is fixed; eventually you'll be able to modify them per-sprint. Click an existing item to edit it, or the margin icon to toggle it. Fill in the text area at the end of the category to add a new item; clear a text area to delete it. <a href=\"/help/markdown\">Markdown</a> is available if necessary"

	print "<div class=\"retrospective markdown\">"
	for category, entries in retro.iteritems():
		print "<div class=\"category\" data-id=\"%d\">" % category.id
		print "<div class=\"name\">%s</div>" % stripTags(category.name)
		for entry in sorted(entries, key = lambda entry: 0 if entry.good else 1):
			print "<div class=\"entry %s\" data-id=\"%d\"><textarea>%s</textarea></div>" % ('good' if entry.good else 'bad', entry.id, stripTags(entry.body))
		if not editing and len(entries) == 0:
			print "<div class=\"none\">No entries</div>"
		print "</div>"
	print "</div>"

@post('sprints/(?P<id>[0-9]+)/retrospective/start')
def sprintRetrospectiveStart(handler, id):
	if not handler.session['user']:
		ErrorBox.die('Forbidden', "You must be logged in to modify sprint info")

	id = int(id)
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "There is no sprint with ID %d" % id)
	elif sprint.owner != handler.session['user']:
		ErrorBox.die('Forbidden', "Only the scrummaster can edit the retrospective")

	Retrospective.init(sprint)
	redirect("/sprints/%d/retrospective" % sprint.id)

@post('sprints/(?P<sprintid>[0-9]+)/retrospective/render')
def sprintRetrospectiveRender(handler, sprintid, p_id, p_catid, p_body = None, p_good = None):
	def die(msg):
		print msg
		done()

	handler.wrappers = False
	if p_id != 'new':
		p_id = to_int(p_id, 'id', die)
	p_catid = to_int(p_catid, 'catid', die)
	if p_good is not None:
		p_good = to_bool(p_good)
	if not handler.session['user']:
		die("You must be logged in to modify sprint info")

	sprintid = int(sprintid)
	sprint = Sprint.load(sprintid)
	if not sprint:
		die("There is no sprint with ID %d" % sprintid)
	elif sprint.owner != handler.session['user'] and (p_body is not None or p_good is not None):
		die("Only the scrummaster can edit the retrospective")

	if p_id == 'new':
		if p_body is None or p_good is None:
			die("Missing body/good")
		entry = RetroEntry(p_catid, p_body, p_good)
	else:
		entry = RetroEntry.load(p_id)
		if p_body is not None:
			entry.body = p_body
		if p_good is not None:
			entry.good = p_good

		if entry.body == '':
			entry.delete()
			handler.responseCode = 299
			print toJS({'id': entry.id, 'deleted': True});
			return

	entry.save()
	handler.responseCode = 299
	print toJS({'id': entry.id, 'body': Markdown.render(entry.body), 'good': entry.good})


@get('sprints/new')
def newSprint(handler, project):
	id = int(project)
	handler.title('New Sprint')
	requirePriv(handler, 'User')
	project = Project.load(id)
	if not project:
		ErrorBox.die('Invalid project', "No project with ID <b>%d</b>" % id)

	print "<style type=\"text/css\">"
	print "table.list td.right > * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "#select-members {padding-right: 5px;}"
	print "</style>"
	print "<script src=\"/static/sprints-new.js\" type=\"text/javascript\"></script>"

	print InfoBox('', id = 'post-status')

	print "<form method=\"post\" action=\"/sprints/new\">"
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">Project:</td><td class=\"right\">"
	print "<select id=\"select-project\" name=\"project\">"
	for thisProject in Project.loadAll():
		print "<option value=\"%d\"%s>%s</option>" % (thisProject.id, ' selected' if thisProject == project else '', thisProject.safe.name)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">Name:</td><td class=\"right\"><input type=\"text\" name=\"name\" class=\"defaultfocus\"></td></tr>"
	print "<tr><td class=\"left\">Planning:</td><td class=\"right\"><input type=\"text\" name=\"start\" class=\"date\" value=\"%s\"></td></tr>" % date.today().strftime('%m/%d/%Y')
	print "<tr><td class=\"left\">Wrapup:</td><td class=\"right\"><input type=\"text\" name=\"end\" class=\"date\"></td></tr>"
	print "<tr><td class=\"left\">Members:</td><td class=\"right\">"
	print "<select name=\"members[]\" id=\"select-members\" multiple>"
	for user in sorted(User.loadAll()):
		if user.hasPrivilege('User'):
			print "<option value=\"%d\"%s>%s</option>" % (user.id, ' selected' if user == handler.session['user'] or user == handler.session['user'] else '', user.safe.username)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'button').positive()
	print Button('Cancel', id = 'cancel-button', type = 'button').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

@post('sprints/new')
def newSprintPost(handler, p_project, p_name, p_start, p_end, p_members = None):
	def die(msg):
		print msg
		done()

	handler.wrappers = False
	p_project = int(p_project)

	project = Project.load(p_project)
	if not project:
		die("Unknown project ID: %d" % p_project)

	if p_name == '':
		die("The sprint name cannot be empty")

	try:
		start = re.match("^(\d{1,2})/(\d{1,2})/(\d{4})$", p_start)
		if not start:
			raise ValueError
		month, day, year = map(int, start.groups())
		start = datetime(year, month, day)
	except ValueError:
		die("Malformed start date: %s" % stripTags(p_start))

	try:
		end = re.match("^(\d{1,2})/(\d{1,2})/(\d{4})$", p_end)
		if not end:
			raise ValueError
		month, day, year = map(int, end.groups())
		end = datetime(year, month, day)
		end += timedelta(days = 1, seconds = -1)
	except ValueError:
		die("Malformed end date: %s" % stripTags(p_end))

	if start.weekday() >= 5:
		die("Sprints cannot start on a weekend")
	if end.weekday() >= 5:
		die("Sprints cannot start on a weekend")

	members = set(User.load(int(memberid)) for memberid in p_members)
	if None in members:
		die("Unknown username")
	if handler.session['user'] not in members:
		die("The scrummaster (%s) must be a sprint member" % handler.session['user'])

	sprint = Sprint(project.id, p_name, handler.session['user'].id, dateToTs(start), dateToTs(end))
	sprint.members |= members
	sprint.save()
	# Make a default 'Miscellaneous' group so there's something to add tasks to
	Group(sprint.id, 'Miscellaneous', 1, False).save()
	# Make the standard set of sprint goals
	Goal.newSet(sprint)

	handler.responseCode = 299
	print "/sprints/%d" % sprint.id
	Event.newSprint(handler, sprint)

@get('sprints/export')
def exportSprints(handler, project):
	id = int(project)
	handler.title('Export Sprint')
	requirePriv(handler, 'User')
	project = Project.load(id)
	if not project:
		ErrorBox.die('Invalid project', "No project with ID <b>%d</b>" % id)

	print "<link href=\"/static/jquery.multiselect.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/jquery.multiselect.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/sprints-export.js\" type=\"text/javascript\"></script>"
	print "<style type=\"text/css\">"
	print "select {width: 50%;}"
	print "img.format {"
	print "    width: 64px;"
	print "    cursor: pointer;"
	print "    padding: 5px;"
	print "    border: 3px solid #fff;"
	print "}"
	print "img.format.selected, .ui-effects-transfer {border: 3px solid #f00;}"
	print "</style>"

	print "<h2>Sprints</h2>"
	print "<select name=\"sprints\" multiple>"
	for sprint in project.getSprints():
		print "<option value=\"%d\"%s>%s</option>" % (sprint.id, ' selected' if sprint.isActive() else '', sprint.safe.name)
	print "</select>"

	print "<h2>Format</h2>"
	for export in exports.values():
		print "<img class=\"format\" src=\"/static/images/%s.png\" title=\"%s\" export-name=\"%s\">" % (export.getIcon(), export.getFriendlyName(), export.getName())

	print "<br><br>"
	print Button('Export', id = 'export-button').positive()

@get('sprints/export/render')
def exportRender(handler, sprints, format):
	ids = map(int, sprints.split(','))
	sprints = map(Sprint.load, ids)

	try:
		export = exports[format]
	except KeyError:
		ErrorBox.die('Export format', "No format named <b>%s</b>" % stripTags(format))

	for sprint in sprints:
		export.process(sprint)

	handler.wrappers = False
	handler.forceDownload = "%s.%s" % (sprints[0].name if len(sprints) == 1 else 'sprints', export.getExtension())
