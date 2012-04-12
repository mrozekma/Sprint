from __future__ import with_statement, division
from datetime import datetime, date, timedelta
from json import dumps as toJS

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
from Tabs import Tabs
from Goal import Goal
from Availability import Availability
from Chart import Chart
from SprintCharts import *
from ProgressBar import ProgressBar
from History import showHistory
from Export import exports
from LoadValues import isDevMode
from Search import Search
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
def showBacklog(handler, request, id, search = None, devEdit = False):
	requirePriv(handler, 'User')
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)

	# Redirect to search help page if searched for empty string
	if search == '':
		redirect('/search')

	handler.title(sprint.safe.name)

	tasks = sprint.getTasks()
	groups = sprint.getGroups()
	editable = sprint.canEdit(handler.session['user']) or (devEdit and isDevMode(handler))
	search = Search(sprint, search)

	print "<link href=\"/prefs/backlog.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/jquery.editable-1.3.3.js\" type=\"text/javascript\"></script>"
	# print "<script src=\"/static/jquery.uitablefilter.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/jquery.tablednd_0_5.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/sprints.js\" type=\"text/javascript\"></script>"

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
	print "    $('.cancel-search').css('display', search.length > 0 ? 'inline' : 'none');"
	print "    if(search.length > 0) {txt += ' ' + search.join(', ');}"
	print "    $('#task-count').text(txt);"
	print "}"
	print "$('document').ready(function() {"
	if search.has('assigned'):
		print "    $('%s').addClass('selected');" % ', '.join("#filter-assigned a[assigned=\"%s\"]" % user.username for user in search.get('assigned').users)
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

	print "<div class=\"backlog-tabs\">"
	print (tabs << 'backlog') % id
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

	print InfoBox('Loading...', id = 'post-status', close = True)

	print "<div id=\"filter-assigned\">"
	print Button('None').simple().negative()
	for member in sorted(sprint.members):
		print "<a class=\"fancy\" assigned=\"%s\" href=\"/sprints/%d?search=assigned:%s\"><img src=\"%s\">&nbsp;%s</a>" % (member.username, id, member.username, member.getAvatar(16), member.username)
	print "</div><br>"

	print "<div id=\"filter-status\">"
	print Button('None').simple().negative()
	for status in sorted(statuses.values()):
		print "<a class=\"fancy\" status=\"%s\" href=\"/sprints/%d?search=status:%s\"><img src=\"%s\">%s</a>" % (status.name, id, status.name.replace(' ', '-'), status.getIcon(), status.text)
	print "</div><br>"

	tasks = search.filter(tasks)

	if sprint.isPlanning():
		if sprint.isActive():
			print InfoBox("Today is <b>sprint planning</b> &mdash; tasks aren't finalized until the end of the day")
		else:
			daysTillPlanning = (tsToDate(sprint.start) - getNow()).days + 1
			print InfoBox("The sprint has <b>not begun</b> &mdash; planning is %s. All changes are considered to have been made midnight of plan day" % ('tomorrow' if daysTillPlanning == 1 else "in %d days" % daysTillPlanning))
	elif sprint.isReview():
		print InfoBox("Today is <b>sprint review</b> &mdash; this is the last day to make changes to the backlog")

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
	print "<a href=\"/sprints/%d\"><img class=\"cancel-search\" src=\"/static/images/cross.png\"></a>" % id
	print "</td>"
	for (x, y) in days:
		print "<td class=\"%s\">%s<br>Day %s of %s</td>" % (x, formatDate(y), sprintDays.index(y.date())+1 if y.date() in sprintDays else 0, len(sprintDays))
	print "<td>&nbsp;</td>"
	print "</tr>"
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

		groupTasks = filter(lambda task: task.group == group, tasks)
		for task in groupTasks:
			printTask(handler, task, days, group = task.group, highlight = (search.has('highlight') and task in search.get('highlight').tasks), editable = editable)

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
	print "<span class=\"task-index badge badge-info\"></span>&nbsp;"
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
			# If we're in pre-planning, the task's timestamp will be in the future, so (ts - task.timestamp) will be negative, which satisfies the check
			ts = dateToTs(getNow())
			if task.creator == handler.session['user'] and (ts - task.timestamp) < 5*60:
				task.save()
			else:
				task.creator = handler.session['user']
				task.timestamp = max(task.timestamp, ts)
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

		# If we're moving up, we want to be after the predecessor
		# If we're moving down, we want to replace it (since it will shift up on its own)
		#TODO I can't decide if this logic belongs in Task.move()
		pos = (predTask.seq + (1 if predTask.seq < task.seq else 0)) if predTask else 0
		task.move(pos, predGroup)
	else:
		die("Unexpected field name: %s" % stripTags(p_field))

	# 299 - good
	# 298 - warning
	# 200 - error
	request['code'] = 299
	print task.revision

@get('sprints/active')
def findActiveSprint(handler, request, project = None, search = None):
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

	sprints = Sprint.loadAll()
	sprints = filter(lambda s: handler.session['user'] in s.members and s.isActive() and (s.project == project if project else True), sprints)

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
				print "<a href=\"/%s\">%s</a><br>" % (url % sprint.id, sprint.safe.name)
			break

@get('sprints/(?P<id>[0-9]+)/info')
def showInfo(handler, request, id):
	requirePriv(handler, 'User')
	sprint = Sprint.load(id)
	if not sprint:
		ErrorBox.die('Sprints', "No sprint with ID <b>%d</b>" % id)
	tasks = sprint.getTasks()
	editable = sprint.project.owner == handler.session['user'] # Info can be edited even after the sprint closes

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
	print "var sprintid = %d;" % id
	print "$(document).ready(function() {"
	print "    $('input.date[name=start]').datepicker({"
	print "        minDate: '%s'," % getNow().strftime('%m/%d/%Y')
	print "        beforeShowDay: $.datepicker.noWeekends"
	print "    });"
	print "    $('input.date[name=end]').datepicker({"
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
	if editable and dateToTs(getNow()) < sprint.start: # Pre-planning:
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
def sprintInfoPost(handler, request, id, p_name, p_end, p_goals, p_start = None, p_members = None):
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

	if p_start:
		if getNow() > tsToDate(sprint.start):
			die("You cannot change the sprint's start date once the sprint has begun")
		try:
			start = re.match("^(\d{1,2})/(\d{1,2})/(\d{4})$", p_start)
			if not start:
				raise ValueError
			month, day, year = map(int, start.groups())
			start = datetime(year, month, day, 0, 0, 0)
		except ValueError:
			die("Malformed start date: %s" % stripTags(p_start))
		if start < tsToDate(tsStripHours(dateToTs(getNow()))):
			die("You cannot start the sprint before today")
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

	goals = map(Goal.load, p_goals)
	if not all(goals):
		die("One or more goals do not exist")

	members = map(User.load, p_members) if p_members else []
	if not all(members):
		die("One or more members do not exist")
	if sprint.project.owner not in members:
		die("The scrummaster (%s) must be a sprint member" % project.owner)

	if (dateToTs(start) if start else sprint.start) > sprint.end:
		die("Start date cannot be after end date")

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

	if start:
		sprint.start = dateToTs(start)

	sprint.save()

	for id in p_goals:
		goal = Goal.load(id)
		goal.name = p_goals[id]
		goal.save()

	if start:
		for task in sprint.getTasks():
			task.timestamp = sprint.start
			task.save()

	request['code'] = 299
	delay(handler, SuccessBox("Updated info", close = 3, fixed = True))


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
	]

	Chart.include()
	map(lambda (anchor, title, chart): chart.js(), charts)
	print (tabs << 'metrics') % id
	for anchor, title, chart in charts:
		print "<a name=\"%s\">" % anchor
		print "<h2><a href=\"#%s\">%s</a></h2>" % (anchor, title)
		chart.placeholder()

	print "<a name=\"commitment-by-user\">"
	print "<div style=\"position: relative\">"
	print "<h2><a href=\"#commitment-by-user\">Commitment (by user)</a></h2>"
	print "<div style=\"position: absolute; top: 0px; right: 16px;\">"
	if sprint.canEdit(handler.session['user']):
		print Button('Redistribute', "/tasks/distribute?sprint=%d" % sprint.id)
	print "</div>"
	print "</div>"
	avail = Availability(sprint)
	for user in sorted(sprint.members):
		hours = sum(t.hours for t in tasks if t.assigned == user)
		total = avail.getAllForward(getNow().date(), user)
		print ProgressBar("<a style=\"color: #000\" href=\"/sprints/%d?search=assigned:%s\">%s</a>" % (sprint.id, user.safe.username, user.safe.username), hours, total, zeroDivZero = True, style = {100.01: 'progress-current-red'})

	originalTasks = filter(None, (task.getStartRevision(False) for task in tasks))
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
		print ProgressBar("<img class=\"bumpdown\" src=\"/static/images/tag-%s.png\">&nbsp;<a style=\"color: #000\" href=\"/sprints/%d?search=goal:%s\">%s</a>" % (goal.color if goal else 'none', sprint.id, goal.color if goal else 'none', goal.safe.name if goal else 'Other'), start - now, start, zeroDivZero = False, style = {100: 'progress-current-green'})

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
	tasks = sprint.getTasks(includeDeleted = True)

	handler.title(sprint.safe.name)
	Chart.include()
	chart = TaskChart('chart', sprint.getTasks())
	chart.js()

	print (tabs << 'history') % id
	if len(tasks) == 0:
		print ErrorBox("This sprint has no tasks")
	else:
		chart.placeholder()
		showHistory(tasks, True)
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
	for day in sprint.getDays():
		print "<td>%s<br>%s</td>" % (day.strftime('%d'), day.strftime('%a'))
		if day.weekday() == 4:
			print "<td class=\"spacer\">&nbsp;</td>"
	if editable:
		print "<td class=\"buttons\">%s</td>" % Button('set all 8', id = 'set-all-8', type = 'button').info()
	print "</tr>"

	for user in sorted(sprint.members):
		print "<tr class=\"userline\">"
		print "<td class=\"username\">%s</td>" % user.safe.username
		for day in sprint.getDays():
			if editable:
				print "<td><input type=\"text\" name=\"hours[%d,%d]\" value=\"%d\"></td>" % (user.id, dateToTs(day), avail.get(user, day))
			else:
				print "<td style=\"text-align: center\">%d</td>" % avail.get(user, day)

			if day.weekday() == 4:
				print "<td class=\"spacer\">&nbsp;</td>"
		if editable:
			print "<td class=\"buttons\">%s</td>" % Button('copy first', id = 'copy-first', type = 'button').info()
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
	delay(handler, SuccessBox("Updated availability", close = 3, fixed = True))

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
