from __future__ import with_statement
from datetime import datetime, date
import itertools

from rorn.Session import delay, undelay
from rorn.ResponseWriter import ResponseWriter
from rorn.Box import CollapsibleBox, ErrorBox, TintedBox

from Privilege import requirePriv
from Project import Project
from Sprint import Sprint
from Button import Button
from Table import Table
from Task import Task, statuses, statusMenu
from User import User
from Group import Group
from Tabs import Tabs
from utils import *

# groupings = ['status', 'owner', 'hours']

tabs = Tabs()
tabs['info'] = '/sprints/%d/info'
tabs['backlog'] = '/sprints/%d'

@get('sprints')
def sprint(handler, request):
	for case in switch(len(request['path'])):
		if case(0):
			redirect('/projects')
		elif case(1):
			showSprint(handler, request, int(request['path'][0]), None)
		elif case(2) and request['path'][1] == 'info':
			showInfo(handler, request, int(request['path'][0]))
		else:
			print ErrorBox('Sprints', "Unable to handle request for <b>%s</b>" % stripTags('/'.join(request['path'])))
			break

def showSprint(handler, request, id, assigned):
	requirePriv(handler, 'User')
	sprint = Sprint.load(id)
	if not sprint:
		print ErrorBox('Sprints', "No sprint with ID <b>%d</b>" % id)
		done()

	# handler.title(sprint.project.safe.name)
	handler.title(sprint.safe.name)

	print "<script src=\"/static/jquery.editable-1.3.3.js\" type=\"text/javascript\"></script>"
	# print "<script src=\"/static/jquery.uitablefilter.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/jquery.tablednd_0_5.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/sprints.js\" type=\"text/javascript\"></script>"

	print TintedBox('Loading...', scheme = 'blue', id = 'post-status')

	print "<script type=\"text/javascript\">"
	print "var sprintid = %d;" % id
	if assigned:
		print "$('document').ready(function() {"
		print "    $('#filter-assigned a[assigned=\"%s\"]').click();" % assigned
		print "});"
	print "</script>"

	# print "<div class=\"group-buttons\">"
	# for g in groupings:
		# btn = Button(g, "/sprints/%d?grouping=%s" % (id, g))#.mini()
		# if g == grouping:
			# btn = btn.selected()
		# print btn
	# print "</div>"
	# print "<div class=\"clear\"></div>"

	# print "Filter: "
	# print "<input type=\"text\" id=\"filter\">"

	days = [
		('ereyesterday', Weekday.shift(-2)),
		('yesterday', Weekday.shift(-1)),
		('today', Weekday.today())
	]

	tasks = sprint.getTasks()
	groups = sprint.getGroups()

	undelay(handler)

	print "<ul id=\"status-menu\" class=\"contextMenu\">"
	for statusBlock in statusMenu:
		for statusName in statusBlock:
			status = statuses[statusName]
			cls = 'separator' if statusBlock != statusMenu[0] and statusName == statusBlock[0] else ''
			print "<li class=\"%s\"><a href=\"#%s\" style=\"background-image:url('%s');\">%s</a></li>" % (cls, status.name, status.getIcon(), status.text)
	print "</ul>"

	print "<div id=\"filter-assigned\">"
	print Button('None').negative()
	for member in sorted(sprint.members):
		print "<a class=\"fancy\" assigned=\"%s\" href=\"/sprints/%d?assigned=%s\">%s</a>" % (member.username, id, member.username, member.username)
	print "</div><br>"

	print "<div id=\"filter-status\">"
	print Button('None').negative()
	for status in sorted(statuses.values()):
		print "<a class=\"fancy\" status=\"%s\" href=\"#\"><img src=\"%s\">%s</a>" % (status.name, status.getIcon(), status.text)
	print "</div><br>"

	print (tabs << 'backlog') % id

	print "<form method=\"post\" action=\"/sprints/%d/post\">" % id
	# print Button('Save', image = 'tick.png', id = 'save-button').positive()

	# for task in tasks:
		# print "<input type=\"hidden\" name=\"revision[%d]\" value=\"%d\">" % (task.id, task.revision)
		# print "<input type=\"hidden\" name=\"status[%d]\" value=\"%s\">" % (task.id, task.status)
		# print "<input type=\"hidden\" name=\"name[%d]\" value=\"%s\">" % (task.id, task.name)
		# print "<input type=\"hidden\" name=\"assigned[%d]\" value=\"%s\">" % (task.id, task.assigned.username)

	print "<table border=0 id=\"all-tasks\" class=\"tasks\">"
	print "<thead>"
	print "<tr class=\"dateline nodrop nodrag\"><td colspan=\"3\">&nbsp;</td>" + ''.join(map(lambda (x,y): "<td class=\"%s\">%s</td>" % (x, x), days)) + "<td>&nbsp;</td></tr>"
	print "<tr class=\"dateline2 nodrop nodrag\"><td colspan=\"3\">&nbsp;</td>" + ''.join(map(lambda (x,y): "<td class=\"%s\">%s</td>" % (x, formatDate(y)), days)) + "<td>&nbsp;</td></tr>"
	print "</thead>"
	print "<tbody>"

	for group in groups:
		print "<tr class=\"group\" id=\"group%d\" groupid=\"%d\">" % (group.id, group.id)
		print "<td colspan=\"6\"><img src=\"/static/images/collapse.png\">&nbsp;<span>%s</span></td>" % group.name
		print "<td class=\"actions\">"
		print "<a href=\"/groups/new?after=%d\"><img src=\"/static/images/group-new.png\" title=\"New Group\"></a>" % group.id
		print "<a href=\"/tasks/new?group=%d\"><img src=\"/static/images/task-new.png\" title=\"New Task\"></a>" % group.id
		print "</td>"
		print "</tr>"
		for task in group.getTasks():
			printTask(task, days, group = task.group)

	# print "<tr class=\"group\" groupid=\"0\"><td colspan=\"7\"><img src=\"/static/images/collapse.png\">&nbsp;<span>Other</span></td></tr>"
	# for task in filter(lambda t: not t.group, tasks):
		# printTask(task, days)

	print "</tbody>"
	print "</table>"
	print "</form>"

def printTask(task, days, group = None):
	print "<tr class=\"task\" id=\"task%d\" taskid=\"%d\" revid=\"%d\" groupid=\"%d\" status=\"%s\" assigned=\"%s\">" % (task.id, task.id, task.revision, group.id if group else 0, task.stat.name, task.assigned.username)

	print "<td class=\"flags\">"
	if task.id == 11:
		print "<img src=\"/static/images/star.png\">&nbsp;"
	print "<img src=\"/static/images/tag-blue.png\">&nbsp;<img id=\"status_%d\" class=\"status\" src=\"%s\">" % (task.id, task.stat.icon)
	print "</td>"

	print "<td class=\"name\"><span id=\"name_span_%d\">%s</span></td>" % (task.id, task.name)
	# print "<td class=\"assigned\">%s</td>" % task.assigned.str('member')
	print "<td class=\"assigned\">%s</td>" % (task.assigned.str('member', False, "assigned_span_%d" % task.id))
	for lbl, day in days:
		dayTask = task.getRevisionAt(day)
		previousTask = task.getRevisionAt(Weekday.shift(-1, day))
		classes = ['hours', lbl]
		if dayTask and previousTask and dayTask.hours != previousTask.hours:
			classes.append('changed')

		if not dayTask:
			print "<td class=\"%s\">&ndash;</td>" % ' '.join(classes)
		elif lbl == 'today':
			print "<td class=\"%s\" nowrap>" % ' '.join(classes)
			print "<table border=0 cellspacing=0 cellpadding=0 style=\"padding: 0px; margin: 0px\">"
			print "<tr>"
			print "<td><img amt=\"4\" src=\"/static/images/arrow-up.png\"></td>"
			print "<td rowspan=2><input type=\"text\" name=\"hours[%d]\" value=\"%d\"></td>" % (task.id, task.hours)
			print "<td><img amt=\"8\" src=\"/static/images/arrow-top.png\"></td>"
			print "</tr>"
			print "<tr>"
			print "<td><img amt=\"-4\" src=\"/static/images/arrow-down.png\"></td>"
			print "<td><img amt=\"-8\" src=\"/static/images/arrow-bottom.png\"></td>"
			print "</tr>"
			print "</table>"
			print "</td>"
		else:
			print "<td class=\"%s\">%s</td>" % (' '.join(classes), dayTask.hours)
	print "<td class=\"actions\">"
	print "<a href=\"/tasks/%d\" target=\"_new\"><img src=\"/static/images/task-history.png\" title=\"History\"></a>" % task.id
	print "<a href=\"javascript:delete_task(%d);\"><img src=\"/static/images/task-delete.png\" title=\"Delete Task\"></a>" % task.id
	print "</td>"
	print "</tr>"

@post('sprints')
def sprintPost(handler, request, p_id, p_rev_id, p_field, p_value):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False
	request['code'] = 299
	p_id = int(p_id)
	p_rev_id = int(p_rev_id)

	if not handler.session['user']:
		die("You must be logged in to modify tasks")

	if len(request['path']) != 2 or request['path'][1] != 'post':
		die("Unexpected POST to %s" % stripTags('/'.join(request['path'])))

	sprintid = int(request['path'][0])
	sprint = Sprint.load(sprintid)
	if not sprint:
		die("There is no sprint with ID %d" % sprintid)

	task = Task.load(p_id)
	if task.sprint != sprint:
		die("Attempting to modify task outside the specified sprint")

	print "%d, %d, %s, %s" % (p_id, p_rev_id, p_field, p_value)
	print "<br>"

	# self.__setattr__(var, obj.id)
	# hours, taskmove, name, assigned, status
	if task.revision != p_rev_id: #TODO Implement collision support
		die("Collision with %s detected" % task.creator)

	if p_field in ['status', 'name', 'assigned', 'hours']:
		for case in switch(p_field):
			if case('status') or case('name'):
				parsedValue = p_value
				break
			elif case('assigned'):
				parsedValue = User.load(username = p_value)
				if not parsedValue:
					die("Unknown user: <b>%s</b>" % stripTags(p_value))
				break
			elif case('hours'):
				parsedValue = int(p_value)

		if task.__getattribute__(p_field) == parsedValue: # No change
			return
		task.__setattr__(p_field, parsedValue)
	elif p_field == 'taskmove':
		die("Unimplemented: taskmove")
	else:
		die("Unexpected field name: %s" % stripTags(p_field))

	# Is this within the 5-minute window, by the same user?
	ts = dateToTs(datetime.now())
	if task.creator == handler.session['user'] and (ts - task.timestamp) < 5*60:
		task.save()
	else:
		task.creator = handler.session['user']
		task.timestamp = ts
		task.revise()

	# 200 - good
	# 298 - warning
	# 299 - error
	request['code'] = 200
	print "Done"

def showInfo(handler, request, id):
	requirePriv(handler, 'User')
	sprint = Sprint.load(id)
	if not sprint:
		print ErrorBox('Sprints', "No sprint with ID <b>%d</b>" % id)
		done()
	tasks = sprint.getTasks()

	handler.title(sprint.safe.name)

	print (tabs << 'info') % id

	print "<b>Hours</b><br>"
	print "Remaining: %d<br>" % sum(task.hours for task in tasks)
	print "<br>"
	print "<b>Sprint goals</b><br>"
	print "<table border=0>"
	for clr in ['red', 'orange', 'yellow', 'green', 'blue', 'purple']:
		print "<tr><td><img src=\"/static/images/tag-%s.png\"></td><td>Sprint goal %s</td></tr>" % (clr, clr)
	print "</table>"
	print "<br>"
	print "<b>Members</b><br>"
	print "<select name=\"members\" id=\"select-members\" multiple>"
	for user in sorted(User.loadAll()):
		print "<option value=\"%d\"%s>%s</option>" % (user.id, ' selected' if user in sprint.members else '', user.safe.username)
	print "</select>"

@get('sprints/new')
def newSprint(handler, request, project):
	id = int(project)
	handler.title('New Sprint')
	requirePriv(handler, 'User')
	project = Project.load(id)
	if not project:
		print ErrorBox('Invalid project', "No project with ID <b>%d</b>" % id)
		done()

	from Privilege import dev
	dev(handler)

	print "<style type=\"text/css\">"
	print "#post-status {display: none}"
	print "table.list td.left {position: relative; top: 4px;}"
	print "table.list td.right > * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "</style>"
	print "<script src=\"/static/sprints-new.js\" type=\"text/javascript\"></script>"

	print TintedBox('', scheme = 'blue', id = 'post-status')

	print "<form method=\"post\" action=\"/sprints/new\">"
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">Project:</td><td class=\"right\">"
	print "<select id=\"select-project\" name=\"project\">"
	for thisProject in Project.loadAll():
		print "<option value=\"%d\"%s>%s</option>" % (thisProject.id, ' selected' if thisProject == project else '', thisProject.safe.name)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">Name:</td><td class=\"right\"><input type=\"text\" name=\"name\" id=\"defaultfocus\"></td></tr>"
	print "<tr><td class=\"left\">Start:</td><td class=\"right\"><input type=\"text\" name=\"start\" class=\"date\"></td></tr>"
	print "<tr><td class=\"left\">End:</td><td class=\"right\"><input type=\"text\" name=\"end\" class=\"date\"></td></tr>"
	print "<tr><td class=\"left\">Members:</td><td class=\"right\">"
	print "<select name=\"members\" id=\"select-members\" multiple>"
	for user in sorted(User.loadAll()):
		print "<option value=\"%d\"%s>%s</option>" % (user.id, ' selected' if user == handler.session['user'] else '', user.safe.username)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'button').positive()
	print Button('Cancel', id = 'cancel-button', type = 'button').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

@post('sprints/new')
def newSprintPost(handler, request, p_project, p_name, p_start, p_end, p_members):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False

	project = Project.load(p_project)
	if not project:
		die("Unknown project ID: %d" % p_project)

	try:
		start = re.match("^(\d{1,2})/(\d{1,2})/(\d{4})$", p_start)
		if not start:
			raise ValueError
		month, day, year = map(int, start.groups())
		start = date(year, month, day)
	except ValueError:
		die("Malformed start date: %s" % stripTags(p_start))

	try:
		end = re.match("^(\d{1,2})/(\d{1,2})/(\d{4})$", p_end)
		if not end:
			raise ValueError
		month, day, year = map(int, end.groups())
		end = date(year, month, day)
	except ValueError:
		die("Malformed end date: %s" % stripTags(p_end))

	members = map(User.load, p_members)
	if None in members:
		die("Unknown username")

	sprint = Sprint(project.id, p_name, dateToTs(start), dateToTs(end))
	sprint.members += members
	sprint.save()
	# Make a default 'Miscellaneous' group so there's something to add tasks to
	Group(sprint.id, 'Miscellaneous', 1, False).save()

	request['code'] = 299
	# delay(handler, TintedBox("Added sprint <b>%s</b>" % sprint.safe.name, 'green'))
	print "/sprints/%d" % sprint.id
