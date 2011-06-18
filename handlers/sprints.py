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

@post('sprints')
def sprintPost(handler, request,
			   p_revision, p_status, p_name, p_assigned, p_hours,
			   p_taskmove = [], p_new_name = [], p_new_hours = []):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False
	request['code'] = 299

	# die("%s" % p_revision)
	# die("%s" % p_assigned)
	# die("%s" % p_status)
	die("(%d) %s<br> (%d) %s" % (len(p_new_name), p_new_name, len(p_new_hours), p_new_hours))

	if not handler.session['user']:
		die("You must be logged in to modify tasks")

	if len(request['path']) != 2 or request['path'][1] != 'post':
		die("Unexpected POST to %s" % stripTags('/'.join(request['path'])))

	sprintid = int(request['path'][0])
	sprint = Sprint.load(sprintid)
	if not sprint:
		die("There is no sprint with ID %d" % sprintid)

	ids = p_name.keys()
	if ids != p_assigned.keys() or ids != p_hours.keys():
		die("POST key mismatch")

	tasks = Task.loadSet(*ids)
	if not all(map(lambda task: task.sprint == sprint, tasks.values())):
		die("Attempting to modify tasks outside the specified sprint")

	assignedUsers = map(lambda username: User.load(username = username), set(p_assigned.values()))
	if not all(assignedUsers):
		m = zip(set(p_assigned.values()), assignedUsers)
		m = filter(lambda (x,y): not y, m)
		m = [x for (x,y) in m]
		die("Unknown assignee usernames: %s" % ', '.join(m))

	assignedUsers = dict([(user.username, user) for user in assignedUsers])

	hours = dict([(id, int(hours)) for (id, hours) in p_hours.iteritems()])

	count = 0
	collisions = []
	for (taskID, task) in tasks.iteritems():
		#TODO Change creator to current user's ID
		#TODO Change timestamp to current time
		changed = False

		if task.revision != int(p_revision[taskID]):
			collisions.append(task)

		if task.status != p_status[taskID]:
			task.status = p_status[taskID]
			changed = True

		if task.name != p_name[taskID]:
			task.name = p_name[taskID]
			changed = True

		if task.assigned != assignedUsers[p_assigned[taskID]]:
			task.assigned = assignedUsers[p_assigned[taskID]]
			changed = True

		if task.hours != hours[taskID]:
			task.hours = hours[taskID]
			changed = True

		if changed:
			if not task in collisions:
				count += 1
				task.creator = handler.session['user']
				task.timestamp = dateToTs(datetime.now())
				task.revise() #TODO
		elif task in collisions: # No collision if there were no changes
			collisions.remove(task)

	if len(collisions) > 0: #TODO Make this less fatal, and improve the error message
		die("Collisions on: %s" % ', '.join(map(lambda c: str(c.id), collisions)))

	if not type(p_taskmove) is list: p_taskmove = [p_taskmove]
	if len(p_taskmove) > 0:
		moves = []
		for move in p_taskmove:
			movingID, targetID = move.split(':', 1)
			movingID = int(movingID)
			if targetID[0] == '[' and targetID[-1] == ']':
				groupID = int(targetID[1:-1])
				targetID = 0
			else:
				targetID = int(targetID)
				groupID = tasks[targetID].groupid
			moves.append({'from': movingID, 'to': targetID, 'group': groupID})

		groups = set([move['group'] for move in moves] + [tasks[move['from']].groupid for move in moves])
		tasksByGroup = dict([(group, filter(lambda task: task.groupid == group, tasks.values())) for group in groups])
		for move in moves:
			mfrom = tasks[move['from']]
			tasksByGroup[mfrom.groupid].remove(mfrom)
			if move['to'] == 0:
				tasksByGroup[move['group']].insert(0, mfrom)
			else:
				mto = tasks[move['to']]
				move['group'] = mto.groupid
				tasksByGroup[move['group']].insert(tasksByGroup[move['group']].index(mto)+1, mfrom)
			mfrom.groupid = move['group']

		for tasks in tasksByGroup.values():
			counter = itertools.count(1)
			for task in tasks:
				task.seq = counter.next()
				# print "%s - %d<br>" % (task.name, task.seq)
				task.save()

	if count > 0:
		request['code'] = 200
		print "Updated %s" % pluralize(count, 'task', 'tasks')
	elif len(p_taskmove) > 0:
		request['code'] = 200
		print "Performed %s" % pluralize(len(p_taskmove), 'move', 'moves')
	else:
		request['code'] = 298
		print "No tasks changed"

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

	if assigned:
		print "<script type=\"text/javascript\">"
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
	print Button('Save', image = 'tick.png', id = 'save-button').positive()

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

	print "<tr class=\"group\" groupid=\"0\"><td colspan=\"7\"><img src=\"/static/images/collapse.png\">&nbsp;<span>Other</span></td></tr>"
	for task in filter(lambda t: not t.group, tasks):
		printTask(task, days)

	print "</tbody>"
	print "</table>"
	print "</form>"

def printTask(task, days, group = None):
	print "<tr class=\"task\" taskid=\"%d\" groupid=\"%d\" status=\"%s\" assigned=\"%s\">" % (task.id, group.id if group else 0, task.stat.name, task.assigned.username)
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
