from __future__ import with_statement

from rorn.Session import delay
from rorn.Box import TintedBox, ErrorBox
from rorn.ResponseWriter import ResponseWriter

from Privilege import requirePriv
from Task import Task, statuses, statusMenu
from Group import Group
from Goal import Goal
from User import User
from Table import LRTable
from Button import Button
from Tabs import Tabs
from utils import *

@get('tasks/(?P<id>[0-9]+)')
def task(handler, request, id):
	requirePriv(handler, 'User')
	task = Task.load(id)
	if not task:
		ErrorBox.die('Tasks', "No task with ID <b>%d</b>" % id)

	handler.title(task.safe.name)

	def start(rev, icon):
		print "<img class=\"bullet\" src=\"/static/images/%s.png\">&nbsp;<span class=\"timestamp\">[%s]</span>" % (icon, tsToDate(rev.timestamp).strftime('%Y-%m-%d %H:%M:%S')),

	print "<div class=\"revision-history\">"
	fields = set(Task.fields()) - set(['creatorid', 'timestamp', 'revision'])
	revs = task.getRevisions()
	for rev in revs:
		w = ResponseWriter()
		if rev.revision == 1:
			start(rev, 'revision-create')
			print "Task created by %s." % rev.creator,
			print "Assigned to %s," % rev.assigned,
			print "%s," % rev.getStatus().text.lower(),
			print "%d %s remain" % (rev.hours, 'hour' if rev.hours == 1 else 'hours'),
		else:
			changedFields = filter(lambda f: oldRev.__getattribute__(f) != rev.__getattribute__(f), fields)
			for field in changedFields:
				old, new = oldRev.__getattribute__(field), rev.__getattribute__(field)
				for case in switch(field):
					if case('status'):
						start(rev, "revision-%s" % rev.getStatus().name.replace(' ', '-'))
						print "%s by %s" % (rev.getStatus().revisionVerb, rev.creator)
						if 'hours' in changedFields:
							print "(<span class=\"hours-%s\">%+d</span> to %d)" % ('up' if rev.hours > oldRev.hours else 'down', rev.hours - oldRev.hours, rev.hours)
						break
					if case('hours'):
						if 'status' in changedFields:
							continue # Already showed the hours change in the status line
						start(rev, 'revision-in-progress')
						print "%s changed hours <span class=\"hours-%s\">%+d</span> to %d" % (rev.creator, 'up' if rev.hours > oldRev.hours else 'down', rev.hours - oldRev.hours, rev.hours)
						break
					if case('name'):
						start(rev, 'revision-renamed')
						print "Renamed <b>%s</b> by %s" % (rev.safe.name, rev.creator)
						break
					if case('deleted'):
						start(rev, 'revision-deleted' if rev.deleted else 'revision-undeleted')
						print "%s by %s" % ('Deleted' if rev.deleted else 'Undeleted', rev.creator)
						break
					if case('assignedid'):
						start(rev, 'revision-assigned')
						print "Assigned to %s by %s" % (rev.assigned, rev.creator)
						break
					if case('goalid'):
						start(rev, 'tag-blue')
						print "Set sprint goal <b>%s</b> by %s" % (rev.goal.safe.name, rev.creator)
						break
					if case('group'):
						# Nobody cares
						break
					if case():
						start(rev, 'revision-unknown')
						print "Field '%s' changed: %s -> %s" % (field, stripTags(str(old)), stripTags(str(new)))
						break
		if w.data != '':
			print "<br>"
		print w.done()
		oldRev = rev
	print "</div>"

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
	print "<tr><td class=\"left\">Sprint Goal:</td><td class=\"right\">"
	print "<select id=\"select-goal\" name=\"goal\" size=\"5\">"
	print "<option value=\"0\" selected>None</option>"
	for goal in group.sprint.getGoals():
		print "<option value=\"%d\">%s</option>" % (goal.id, goal.safe.name)
	print "</select>"
	print "</td></tr>"
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
def newTaskPost(handler, request, p_group, p_name, p_goal, p_status, p_assigned, p_hours):
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

	goalid = to_int(p_goal, 'goal', die)
	if goalid != 0:
		goal = Goal.load(goalid)
		if not goal:
			die("No goal with ID <b>%d</b>" % goalid)
		if goal.sprint != group.sprint:
			die("Goal does not belong to the correct sprint")

	hours = to_int(p_hours, 'hours', die)

	task = Task(groupid, group.sprintid, handler.session['user'].id, assignedid, goalid, p_name, p_status, hours)
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
