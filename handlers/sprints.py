from __future__ import with_statement
from utils import *
from datetime import datetime
import itertools
from Privilege import requirePriv
from Project import Project
from Sprint import Sprint
from Box import ErrorBox, TintedBox
from Button import Button
from Table import Table
from Task import Task, statuses, statusMenu
from User import User

# groupings = ['status', 'owner', 'hours']

@get('sprints')
def sprint(handler, request, assigned = None):
	for case in switch(len(request['path'])):
		if case(0):
			redirect('/projects')
			break
		if case(1):
			showSprint(handler, request, int(request['path'][0]), assigned)
			break
		if case(2):
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

	print "<form method=\"post\" action=\"/sprints/%d/post\">" % id
	# print Button('Save', image = 'tick.png', id = 'save-button').positive()

	for task in tasks:
		print "<input type=\"hidden\" name=\"revision[%d]\" value=\"%d\">" % (task.id, task.revision)
		print "<input type=\"hidden\" name=\"status[%d]\" value=\"%s\">" % (task.id, task.status)
		print "<input type=\"hidden\" name=\"name[%d]\" value=\"%s\">" % (task.id, task.name)
		print "<input type=\"hidden\" name=\"assigned[%d]\" value=\"%s\">" % (task.id, task.assigned.username)

	print "<table border=0 id=\"all-tasks\" class=\"tasks\">"
	print "<thead>"
	print "<tr class=\"dateline nodrop nodrag\"><td colspan=2>&nbsp;</td>" + ''.join(map(lambda (x,y): "<td class=\"%s\">%s</td>" % (x, x), days)) + "<td>&nbsp;</td></tr>"
	print "<tr class=\"dateline2 nodrop nodrag\"><td colspan=2>&nbsp;</td>" + ''.join(map(lambda (x,y): "<td class=\"%s\">%s</td>" % (x, formatDate(y)), days)) + "<td>&nbsp;</td></tr>"
	print "</thead>"
	print "<tbody>"

	for group in groups:
		print "<tr class=\"group\" groupid=\"%d\"><td colspan=\"7\"><img src=\"/static/images/collapse.png\">&nbsp;<span>%s</span></td></tr>" % (group.id, group.name)
		for task in filter(lambda t: t.group and t.group == group, tasks):
			printTask(task, days, group = task.group)
			# print "<tr><td colspan=\"7\">x</td></tr>"

	print "<tr class=\"group\" groupid=\"0\"><td colspan=\"7\"><img src=\"/static/images/collapse.png\">&nbsp;<span>Other</span></td></tr>"
	for task in filter(lambda t: not t.group, tasks):
		printTask(task, days)

	print "</tbody>"
	print "</table>"
	print "</form>"

def printTask(task, days, group = None):
	print "<tr class=\"task\" taskid=\"%d\" revid=\"%d\" groupid=\"%d\" status=\"%s\" assigned=\"%s\">" % (task.id, task.revision, group.id if group else 0, task.stat.name, task.assigned.username)
	print "<td class=\"name\"><img id=\"status_%d\" src=\"%s\">&nbsp;<span id=\"name_span_%d\">(%d,%d) %s</span></td>" % (task.id, task.stat.icon, task.id, task.id, task.seq, task.name)
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
	print "<img class=\"task-new\" src=\"/static/images/task-new.png\" title=\"New Task\">"
	print "<img src=\"/static/images/task-history.png\">"
	print "<img src=\"/static/images/task-history.png\">"
	print "<img src=\"/static/images/task-history.png\">"
	# print "(actions)"
	# print Button('history', "/tasks/%d" % task.id, image = 'sprint-history.png')
	# print Button('temp1', '#', image = 'sprint.png')
	# print Button('temp2', '#', image = 'sprint.png')
	# print Button('temp3', '#', image = 'sprint.png')
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
