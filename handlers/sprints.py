from __future__ import with_statement, division
from datetime import datetime, date, timedelta
from json import dumps as toJS

from rorn.Session import delay, undelay
from rorn.ResponseWriter import ResponseWriter
from rorn.Box import CollapsibleBox, ErrorBox, InfoBox

from Privilege import requirePriv
from Project import Project
from Sprint import Sprint
from Button import Button
from Table import Table
from Task import Task, statuses, statusMenu
from User import User
from Group import Group
from Tabs import Tabs
from Goal import Goal
from Availability import Availability
from Chart import Chart
from SprintCharts import *
from ProgressBar import ProgressBar
from History import showHistory
from Export import exports
from LoadValues import isDevMode
from utils import *

# groupings = ['status', 'owner', 'hours']

tabs = Tabs()
tabs['info'] = '/sprints/%d/info'
tabs['backlog'] = '/sprints/%d'
tabs['metrics'] = '/sprints/%d/metrics'
tabs['history'] = '/sprints/%d/history'
tabs['availability'] = '/sprints/%d/availability'

@get('sprints')
def sprint(handler, request):
	redirect('/projects')

@get('sprints/(?P<id>[0-9]+)')
def showBacklog(handler, request, id, assigned = None, highlight = None):
	requirePriv(handler, 'User')
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	highlight = map(int, highlight.split(',')) if highlight else []

	# handler.title(sprint.project.safe.name)
	handler.title(sprint.safe.name)

	print "<link href=\"/prefs/backlog.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/jquery.editable-1.3.3.js\" type=\"text/javascript\"></script>"
	# print "<script src=\"/static/jquery.uitablefilter.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/jquery.tablednd_0_5.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/sprints.js\" type=\"text/javascript\"></script>"

	print "<script type=\"text/javascript\">"
	print "var sprintid = %d;" % id
	print "var isPlanning = %s;" % ('true' if sprint.isPlanning() else 'false')
	if assigned:
		print "$('document').ready(function() {"
		print "    $('#filter-assigned a[assigned=\"%s\"]').click();" % assigned
		print "});"
	print "</script>"

	print (tabs << 'backlog') % id
	print "<br>"

	if sprint.isActive():
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

	tasks = sprint.getTasks()
	groups = sprint.getGroups()
	editable = sprint.canEdit(handler.session['user'])

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

	print InfoBox('Loading...', id = 'post-status', close = True)

	print "<script type=\"text/javascript\">"
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

	print "<div id=\"filter-assigned\">"
	print Button('None').simple().negative()
	for member in sorted(sprint.members):
		print "<a class=\"fancy\" assigned=\"%s\" href=\"/sprints/%d?assigned=%s\"><img src=\"%s\">&nbsp;%s</a>" % (member.username, id, member.username, member.getAvatar(16), member.username)
	print "</div><br>"

	print "<div id=\"filter-status\">"
	print Button('None').simple().negative()
	for status in sorted(statuses.values()):
		print "<a class=\"fancy\" status=\"%s\" href=\"#\"><img src=\"%s\">%s</a>" % (status.name, status.getIcon(), status.text)
	print "</div><br>"

	if sprint.isPlanning():
		if sprint.isActive():
			print InfoBox("Today is <b>sprint planning</b> &mdash; all changes will be collapsed into one revision")
		else:
			daysTillPlanning = (tsToDate(sprint.start) - getNow()).days + 1
			print InfoBox("The sprint has <b>not begun</b> &mdash; planning is %s. Until planning is over all changes will be collapsed into one revision made midnight of plan day" % ('tomorrow' if daysTillPlanning == 1 else "in %d days" % daysTillPlanning))
	elif sprint.isReview():
		print InfoBox("Today is <b>sprint review</b> &mdash; this is the last day to make changes to the backlog")

	if isDevMode(handler):
		print Button('#all-tasks borders', "javascript:$('#all-tasks, #all-tasks tr td').css('border', '1px solid #f00').css('border-collapse', 'collapse');", type = 'button').negative()
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
	print "<tr class=\"dateline nodrop nodrag\"><td colspan=\"3\">&nbsp;</td>" + ''.join(map(lambda (x,y): "<td class=\"%s\">%s</td>" % (x, x), days)) + "<td>&nbsp;</td></tr>"
	print "<tr class=\"dateline2 nodrop nodrag\"><td colspan=\"3\">&nbsp;</td>" + ''.join(map(lambda (x,y): "<td class=\"%s\">%s<br>Day %s of %s</td>" % (x, formatDate(y), sprintDays.index(y.date())+1 if y.date() in sprintDays else 0, len(sprintDays)), days)) + "<td>&nbsp;</td></tr>"
	print "</thead>"
	print "<tbody>"

	for group in groups:
		print "<tr class=\"group\" id=\"group%d\" groupid=\"%d\">" % (group.id, group.id)
		print "<td colspan=\"6\"><img src=\"/static/images/collapse.png\">&nbsp;<span>%s</span></td>" % group.name
		print "<td class=\"actions\">"
		if editable:
			print "<a href=\"/groups/new?after=%d\"><img src=\"/static/images/group-new.png\" title=\"New Group\"></a>" % group.id
			print "<a href=\"/groups/edit/%d\"><img src=\"/static/images/group-edit.png\" title=\"Edit Group\"></a>" % group.id
			print "<a href=\"/tasks/new?group=%d\"><img src=\"/static/images/task-new.png\" title=\"New Task\"></a>" % group.id
		print "</td>"
		print "</tr>"
		for task in group.getTasks():
			printTask(handler, task, days, group = task.group, highlight = (task.id in highlight), editable = editable)

	print "<tr><td colspan=\"7\">&nbsp;</td></tr>" # Spacer so rows can be dragged to the bottom
	print "</tbody>"
	print "</table>"
	print "</form>"

def printTask(handler, task, days, group = None, highlight = False, editable = True):
	print "<tr class=\"task%s\" id=\"task%d\" taskid=\"%d\" revid=\"%d\" groupid=\"%d\" goalid=\"%d\" status=\"%s\" assigned=\"%s\">" % (' highlight' if highlight else '', task.id, task.id, task.revision, group.id if group else 0, task.goal.id if task.goal else 0, task.stat.name, task.assigned.username)

	print "<td class=\"flags\">"
	if isDevMode(handler):
		print "<small class=\"debugtext\">(%d, %d, %d)</small>&nbsp;" % (task.id, task.seq, task.revision)
	# print "<img src=\"/static/images/star.png\">&nbsp;"
	print "<img id=\"goal_%d\" class=\"goal\" src=\"/static/images/tag-%s.png\" title=\"%s\">&nbsp;" % ((task.goal.id, task.goal.color, task.goal.safe.name) if task.goal else (0, 'none', 'None'))
	print "<img id=\"status_%d\" class=\"status\" src=\"%s\" title=\"%s\">" % (task.id, task.stat.icon, task.stat.text)
	print "</td>"

	print "<td class=\"name\"><span id=\"name_span_%d\">%s</span></td>" % (task.id, task.name)
	# print "<td class=\"assigned\">%s</td>" % task.assigned.str('member')
	print "<td class=\"assigned\"><span>%s</span></td>" % (task.assigned.str('member', False, "assigned_span_%d" % task.id))
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
def sprintPost(handler, request, sprintid, p_id, p_rev_id, p_field, p_value):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False
	p_id = int(p_id)
	p_rev_id = int(p_rev_id)

	if not handler.session['user']:
		die("You must be logged in to modify tasks")

	sprint = Sprint.load(sprintid)
	if not sprint:
		die("There is no sprint with ID %d" % sprintid)

	if not (sprint.isActive() or sprint.isPlanning()):
		die("Unable to modify inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		die("You don't have permission to modify this sprint")

	task = Task.load(p_id)
	if task.sprint != sprint:
		die("Attempting to modify task outside the specified sprint")

	# print "%d, %d, %s, %s" % (p_id, p_rev_id, p_field, p_value)

	# self.__setattr__(var, obj.id)
	# hours, taskmove, name, assigned, status
	if task.revision != p_rev_id: #TODO Implement collision support
		die("Collision with %s detected. Changes not saved" % task.creator)

	if p_field in ['status', 'name', 'goal', 'assigned', 'hours', 'deleted']:
		for case in switch(p_field):
			if case('status') or case('name') or case('deleted'):
				parsedValue = p_value
				break
			elif case('goal'):
				parsedValue = Goal.load(p_value)
				if not parsedValue:
					die("Unknown goal: <b>%s</b>" % stripTags(p_value))
				if parsedValue.sprint != sprint:
					die("Attempting to use goal output the specified sprint")
				break
			elif case('assigned'):
				parsedValue = User.load(username = p_value)
				if not parsedValue:
					die("Unknown user: <b>%s</b>" % stripTags(p_value))
				break
			elif case('hours'):
				parsedValue = int(p_value)

		if task.__getattribute__(p_field) != parsedValue: # Only save if the field has changed
			task.__setattr__(p_field, parsedValue)

			# Is this within the 5-minute window, by the same user?
			ts = dateToTs(getNow())
			if (task.creator == handler.session['user'] and (ts - task.timestamp) < 5*60) or sprint.isPlanning():
				task.save()
			else:
				task.creator = handler.session['user']
				task.timestamp = ts
				task.revise()

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

		task.move((predTask.seq if predTask else 0) + 1, predGroup)
	else:
		die("Unexpected field name: %s" % stripTags(p_field))

	# 299 - good
	# 298 - warning
	# 200 - error
	request['code'] = 299
	print task.revision

@get('sprints/active')
def findActiveSprint(handler, request, project = None):
	handler.title('Active Sprint')
	requirePriv(handler, 'User')
	if project:
		projectid = int(project)
		project = Project.load(projectid)
		if not project:
			ErrorBox.die('Load project', "No project with ID <b>%d</b>" % projectid)

	sprints = Sprint.loadAll()
	sprints = filter(lambda s: handler.session['user'] in s.members and s.isActive() and (s.project == project if project else True), sprints)

	for case in switch(len(sprints)):
		if case(0):
			ErrorBox.die('Active sprint', 'No active sprints found')
			break
		if case(1):
			redirect("/sprints/%d" % sprints[0].id)
			break
		if case():
			print "You are active in multiple sprints%s:<br><br>" % (" in the %s project" % project.safe.name if project else '')
			for sprint in sprints:
				print "<a href=\"/sprints/%d\">%s</a><br>" % (sprint.id, sprint.safe.name)
			break

@get('sprints/(?P<id>[0-9]+)/info')
def showInfo(handler, request, id):
	requirePriv(handler, 'User')
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	tasks = sprint.getTasks()
	editable = sprint.canEdit(handler.session['user']) and sprint.project.owner == handler.session['user']

	handler.title(sprint.safe.name)

	print "<style type=\"text/css\">"
	print "input.goal {"
	print "    width: 400px;"
	print "    background: url(/static/images/tag-none.png) no-repeat 2px 2px;"
	print "    padding-left: 24px;"
	print "}"
	print "input.name, #select-members, #save-button {width: 424px}"
	print "</style>"
	print "<script src=\"/static/sprint-info.js\" type=\"text/javascript\"></script>"
	print "<script type=\"text/javascript\">"
	print "$(document).ready(function() {"
	print "    $('input.date').datepicker({"
	print "        minDate: '%s'," % tsToDate(sprint.end).strftime('%m/%d/%Y')
	print "        beforeShowDay: $.datepicker.noWeekends"
	print "    });"
	print "});"
	print "</script>"

	print InfoBox('Loading...', id = 'post-status', close = True)

	print (tabs << 'info') % id

	print "<form method=\"post\" action=\"/sprints/info?id=%d\">" % sprint.id
	print "<b>Name</b><br>"
	if editable:
		print "<input type=\"text\" name=\"name\" class=\"name\" value=\"%s\"><br><br>" % sprint.safe.name
	else:
		print "%s<br><br>" % sprint.safe.name
	print "<b>Duration</b><br>"
	if editable:
		print "%s - <input type=\"text\" name=\"end\" class=\"date\" value=\"%s\"><br><br>" % (tsToDate(sprint.start).strftime('%m/%d/%Y'), tsToDate(sprint.end).strftime('%m/%d/%Y'))
	else:
		print "%s - %s<br><br>" % (tsToDate(sprint.start).strftime('%m/%d/%Y'), tsToDate(sprint.end).strftime('%m/%d/%Y'))
	print "<b>Sprint goals</b><br>"
	for goal in sprint.getGoals():
		if editable:
			print "<input type=\"text\" class=\"goal\" style=\"background-image: url(/static/images/tag-%s.png)\" name=\"goals[%d]\" goalid=\"%d\" value=\"%s\"><br>" % (goal.color, goal.id, goal.id, goal.safe.name)
		elif goal.name:
			print "<img class=\"bumpdown\" src=\"/static/images/tag-%s.png\">&nbsp;%s<br>" % (goal.color, goal.safe.name)
	print "</table>"
	print "<br>"
	print "<b>Members</b><br>"
	if editable:
		print "<select name=\"members[]\" id=\"select-members\" multiple>"
		for user in sorted(User.loadAll()):
			print "<option value=\"%d\"%s>%s</option>" % (user.id, ' selected' if user in sprint.members else '', user.safe.username)
		print "</select>"
	else:
		print ', '.join(map(str, sorted(sprint.members)))
	print "<br>"

	if editable:
		print Button('Save', id = 'save-button', type = 'button').positive()
	print "</form>"

@post('sprints/info')
def sprintInfoPost(handler, request, id, p_name, p_end, p_goals, p_members = None):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False

	if not handler.session['user']:
		die("You must be logged in to modify sprint info")

	sprint = Sprint.load(id)
	if not sprint:
		die("There is no sprint with ID %d" % id)

	if sprint.project.owner != handler.session['user']:
		die("You must be the scrummaster to modify sprint information")

	if not (sprint.isActive() or sprint.isPlanning()):
		die("You cannot modify an inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		die("You don't have permission to modify this sprint")

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

	goals = map(Goal.load, p_goals)
	if not all(goals):
		die("One or more goals do not exist")

	members = map(User.load, p_members) if p_members else []
	if not all(members):
		die("One or more members do not exist")
	if sprint.project.owner not in members:
		die("The scrummaster (%s) must be a sprint member" % project.owner)

	avail = Availability(sprint)
	addMembers = list(set(members) - set(sprint.members))
	delMembers = list(set(sprint.members) - set(members))
	for user in delMembers:
		for task in filter(lambda task: task.assigned == user, sprint.getTasks()):
			task.assigned = sprint.project.owner
			task.creator = handler.session['user']
			task.timestamp = dateToTs(getNow())
			task.revise()
		avail.delete(user)
		sprint.members.remove(user)

	sprint.members += addMembers
	sprint.name = p_name
	sprint.end = dateToTs(end)
	sprint.save()

	for id in p_goals:
		goal = Goal.load(id)
		goal.name = p_goals[id]
		goal.save()

	request['code'] = 299
	print "Saved changes"

@get('sprints/(?P<id>[0-9]+)/metrics')
def showMetrics(handler, request, id):
	requirePriv(handler, 'User')
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	tasks = sprint.getTasks()

	handler.title(sprint.safe.name)

	print "<style type=\"text/css\">"
	print "h2 a {color: #000;}"
	print "</style>"

	charts = [
		('general', 'Hours (general)', HoursChart('chart-general', sprint)),
		('earned-value', 'Earned Value', EarnedValueChart('chart-earned-value', sprint)),
		('by-user', 'Hours (by user)', HoursByUserChart('chart-by-user', sprint)),
		('commitment', 'Total commitment', CommitmentChart('chart-commitment', sprint)),
		# ('goals', 'Sprint goals', SprintGoalsChart('chart-sprint-goals', sprint)),
	]

	Chart.include()
	map(lambda (anchor, title, chart): chart.js(), charts)
	print (tabs << 'metrics') % id
	for anchor, title, chart in charts:
		print "<a name=\"%s\">" % anchor
		print "<h2><a href=\"#%s\">%s</a></h2>" % (anchor, title)
		chart.placeholder()

	print "<a name=\"commitment-by-user\">"
	print "<h2><a href=\"#commitment-by-user\">Commitment (by user)</a></h2>"
	avail = Availability(sprint)
	for user in sorted(sprint.members):
		hours = sum(t.hours for t in tasks if t.assigned == user)
		total = avail.getAllForward(getNow().date(), user)
		print ProgressBar(user.safe.username, hours, total, zeroDivZero = True, style = {100.01: 'progress-current-red'})

	originalTasks = Task.loadAll(sprintid = sprint.id, revision = 1)
	taskMap = dict([(task.id, task) for task in tasks])
	print "<a name=\"goals\">"
	print "<h2><a href=\"#goals\">Sprint goals</a></h2>"
	for goal in sprint.getGoals() + [None]:
		if goal and goal.name == '':
			continue
		start = sum(t.hours for t in originalTasks if t.id in taskMap and taskMap[t.id].goalid == (goal.id if goal else 0))
		now = sum(t.hours for t in tasks if t.goalid == (goal.id if goal else 0))
		if not goal and start == now == 0:
			continue
		print ProgressBar("<img class=\"bumpdown\" src=\"/static/images/tag-%s.png\">&nbsp;%s" % (goal.color if goal else 'none', goal.safe.name if goal else 'Other'), start - now, start, zeroDivZero = False, style = {100: 'progress-current-green'})

	print "<a name=\"averages\">"
	print "<h2><a href=\"#averages\">Averages</a></h2>"
	avail = Availability(sprint)
	# numDays = (tsToDate(sprint.end) - tsToDate(sprint.start)).days + 1
	numDays = len([day for day in sprint.getDays()])
	availability = (avail.getAllForward(tsToDate(sprint.start)) / numDays)
	tasking = (sum(task.hours if task else 0 for task in [task.getRevisionAt(tsToDate(sprint.start)) for task in sprint.getTasks()]) / numDays)
	pcnt = 100 * tasking / availability if availability > 0 else 0
	print "Daily availability: <b>%2.2f hours</b><br>" % availability
	print "Daily tasking: %2.2f hours (%2.2f%%)" % (tasking, pcnt)
	print "<br><br>"

@get('sprints/(?P<id>[0-9]+)/history')
def showSprintHistory(handler, request, id):
	requirePriv(handler, 'User')
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)

	handler.title(sprint.safe.name)
	Chart.include()
	chart = TaskChart('chart', sprint.getTasks())
	chart.js()

	print (tabs << 'history') % id
	chart.placeholder()
	showHistory(sprint.getTasks(includeDeleted = True), True)
	print "<br>"

@get('sprints/(?P<id>[0-9]+)/availability')
def showAvailability(handler, request, id):
	requirePriv(handler, 'User')
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	tasks = sprint.getTasks()

	handler.title(sprint.safe.name)
	print (tabs << 'availability') % id

	print "<script src=\"/static/sprint-availability.js\" type=\"text/javascript\"></script>"
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
	seek = start
	while seek <= end:
		if seek.weekday() < 5: # Weekday
			print "<td>%s<br>%s</td>" % (seek.strftime('%d'), seek.strftime('%a'))
		seek += oneday
	if editable:
		print "<td>%s</td>" % Button('set all 8', type = 'button').info()
	print "</tr>"

	for user in sorted(sprint.members):
		print "<tr class=\"userline\">"
		print "<td class=\"username\">%s</td>" % user.safe.username
		seek = start
		while seek <= end:
			if seek.weekday() < 5: # Weekday
				if editable:
					print "<td><input type=\"text\" name=\"hours[%d,%d]\" value=\"%d\"></td>" % (user.id, dateToTs(seek), avail.get(user, seek))
				else:
					print "<td style=\"text-align: center\">%d</td>" % avail.get(user, seek)
			seek += oneday
		if editable:
			print "<td>%s</td>" % Button('copy first', type = 'button').info()
		print "</tr>"

	print "</table>"
	if editable:
		print Button('Save', id = 'save-button', type = 'button').positive()
	print "</form>"

@post('sprints/(?P<id>[0-9]+)/availability')
def sprintAvailabilityPost(handler, request, id, p_hours):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False

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

	request['code'] = 299
	print "Saved changes"

@get('sprints/new')
def newSprint(handler, request, project):
	id = int(project)
	handler.title('New Sprint')
	requirePriv(handler, 'User')
	project = Project.load(id)
	if not project:
		ErrorBox.die('Invalid project', "No project with ID <b>%d</b>" % id)

	print "<style type=\"text/css\">"
	print "table.list td.right > * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
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
		print "<option value=\"%d\"%s>%s</option>" % (user.id, ' selected' if user == handler.session['user'] or user == project.owner else '', user.safe.username)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'button').positive()
	print Button('Cancel', id = 'cancel-button', type = 'button').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

@post('sprints/new')
def newSprintPost(handler, request, p_project, p_name, p_start, p_end, p_members = None):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False

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

	members = map(User.load, p_members) if p_members else []
	if None in members:
		die("Unknown username")
	if project.owner not in members:
		die("The scrummaster (%s) must be a sprint member" % project.owner)

	sprint = Sprint(project.id, p_name, dateToTs(start), dateToTs(end))
	sprint.members += members
	sprint.save()
	# Make a default 'Miscellaneous' group so there's something to add tasks to
	Group(sprint.id, 'Miscellaneous', 1, False).save()
	# Make the standard set of sprint goals
	Goal.newSet(sprint)

	request['code'] = 299
	print "/sprints/%d" % sprint.id

@get('sprints/export')
def exportSprints(handler, request, project):
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
def exportRender(handler, request, sprints, format):
	ids = map(int, sprints.split(','))
	sprints = map(Sprint.load, ids)

	try:
		export = exports[format]
	except KeyError:
		ErrorBox.die('Export format', "No format named <b>%s</b>" % stripTags(format))

	for sprint in sprints:
		export.process(sprint)

	request['wrappers'] = False
	request['forceDownload'] = "%s.%s" % (sprints[0].name if len(sprints) == 1 else 'sprints', export.getExtension())
