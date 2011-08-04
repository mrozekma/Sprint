from __future__ import with_statement
from utils import *
from Session import delay
from Privilege import requirePriv
from Task import Task, statuses, statusMenu
from Group import Group
from User import User
from Box import TintedBox, ErrorBox
from Table import LRTable
from Button import Button
from Tabs import Tabs

@get('tasks')
def task(handler, request):
	for case in switch(len(request['path'])):
		if case(0):
			ErrorBox.die("Tasks", "No task specified")
			break
		if case(1):
			showTask(handler, request, int(request['path'][0]))
			break

def showTask(handler, request, id):
	requirePriv(handler, 'User')
	task = Task.load(id)
	if not task:
		ErrorBox.die('Tasks', "No task with ID <b>%d</b>" % id)

	handler.title(task.safe.name)

	# print "<script src=\"/static/tasks.js\" type=\"text/javascript\"></script>"
	print TintedBox('Unimplemented', scheme = 'blood')
	print "<br>"

	m = ['id', 'revision', 'sprintid', 'sprint', 'creatorid', 'creator', 'assignedid', 'assigned', 'name', 'status', 'hours', 'timestamp']
	revs = task.getRevisions()

	from Table import Table
	tbl = Table()
	tbl *= ['Field'] + [x for x in range(1, len(revs)+1)]
	for k in m:
		tbl += [k] + [str(x.__getattribute__(k)) for x in revs]
	print tbl

	# for rev in task.getRevisions():
		# print "<hr>"
		# print "<h2>%s</h2>" % rev.revision
		# tbl = LRTable()
		# for k in m:
			# tbl[k] = str(rev.__getattribute__(k))
		# print tbl

tabs = Tabs()
tabs['single'] = '/tasks/new/single?group=%d'
tabs['many'] = '/tasks/new/many?group=%d'
tabs['import'] = '/tasks/new/import?group=%d'

@get('tasks/new')
def newTaskGeneric(handler, request, group):
	redirect("/tasks/new/single?group=%s" % group)

@get('tasks/new/single')
def newTaskSingle(handler, request, group):
	requirePriv(handler, 'User')
	handler.title("New Task")
	id = int(group)

	print (tabs << 'single') % id

	group = Group.load(group)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)

	# name, assigned, hours, status, sprint, group

	print "<style type=\"text/css\">"
	print "#post-status {display: none}"
	print "table.list td.left {position: relative; top: 4px;}"
	print "table.list td.right * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "</style>"
	print "<script type=\"text/javascript\">"
	print "next_url = '/sprints/%d#group%d';" % (group.sprint.id, group.id)
	print "</script>"
	print "<script src=\"/static/tasks.js\" type=\"text/javascript\"></script>"

	print TintedBox('', scheme = 'blue', id = 'post-status')

	print "<form method=\"post\" action=\"/tasks/new/single\">"
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">Sprint:</td><td class=\"right\"><select id=\"selectSprint\" disabled><option>%s</option></select></td></tr>" % group.sprint
	print "<tr><td class=\"left\">Group:</td><td class=\"right\">"
	print "<select id=\"select-group\" name=\"group\" size=\"5\">"
	for sGroup in group.sprint.getGroups('name'):
		print "<option value=\"%d\"%s>%s</option>" % (sGroup.id, ' selected' if sGroup == group else '', sGroup.safe.name)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">Name:</td><td class=\"right\"><input type=\"text\" name=\"name\" id=\"defaultfocus\"></td></tr>"
	print "<tr><td class=\"left\">Status:</td><td class=\"right\">"
	print "<select id=\"select-status\" name=\"status\" size=\"10\">"
	first = True
	for statusSet in statusMenu:
		for name in statusSet:
			print "<option value=\"%s\"%s>%s</option>" % (name, ' selected' if first else '', statuses[name].text)
			first = False
	print "</status>"
	print "</td></tr>"
	print "<tr><td class=\"left\">Assigned:</td><td class=\"right\">"
	print "<select id=\"select-assigned\" name=\"assigned\" size=\"10\">"
	for user in sorted(group.sprint.members):
		print "<option value=\"%d\"%s>%s</option>" % (user.id, ' selected' if user == handler.session['user'] else '', user.safe.username)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">Hours:</td><td class=\"right\"><input type=\"text\" name=\"hours\" value=\"8\"></td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'button').positive()
	print Button('Cancel', id = 'cancel-button', type = 'button').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

@post('tasks/new/single')
def newTaskPost(handler, request, p_group, p_name, p_status, p_assigned, p_hours):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False

	groupid = to_int(p_group, 'group', die)
	group = Group.load(groupid)
	if not group:
		die("No group with ID <b>%d</b>" % groupid)

	assignedid = to_int(p_assigned, 'assigned', die)
	assigned = User.load(assignedid)
	if not assigned:
		die("No user with ID <b>%d</b>" % assignedid)

	hours = to_int(p_hours, 'hours', die)

	task = Task(groupid, group.sprintid, handler.session['user'].id, assignedid, p_name, p_status, hours)
	task.save()

	request['code'] = 299
	delay(handler, """
<script type=\"text/javascript\">
$(document).ready(function() {
	$('#task%d').effect('highlight', {}, 3000);
});
</script>""" % task.id)
	delay(handler, TintedBox("Added task <b>%s</b>" % task.safe.name, 'green'))

@get('tasks/new/many')
def newTaskMany(handler, request, group):
	requirePriv(handler, 'User')
	handler.title("New Tasks")
	id = int(group)

	print (tabs << 'many') % id

	group = Group.load(group)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)

	print TintedBox('Unimplemented', scheme = 'blood')
	print "<br>"
	print "sprint: %s<br>" % group.sprint
	print "group: %s" % group

@get('tasks/new/import')
def newTaskImport(handler, request, group):
	requirePriv(handler, 'User')
	handler.title("Import Tasks")
	id = int(group)

	print (tabs << 'import') % id

	group = Group.load(group)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)

	print TintedBox('Unimplemented', scheme = 'blood')
	print "<br>"
	print "sprint: %s<br>" % group.sprint
	print "group: %s" % group
