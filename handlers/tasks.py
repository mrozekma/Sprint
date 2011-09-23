from __future__ import with_statement

from rorn.Session import delay
from rorn.Box import TintedBox, ErrorBox, CollapsibleBox
from rorn.ResponseWriter import ResponseWriter

from Privilege import requirePriv
from Task import Task, statuses, statusMenu
from Group import Group
from Goal import Goal
from User import User
from Button import Button
from Tabs import Tabs
from History import showHistory
from utils import *

@get('tasks/(?P<id>[0-9]+)')
def task(handler, request, id):
	requirePriv(handler, 'User')
	task = Task.load(id)
	if not task:
		ErrorBox.die('Tasks', "No task with ID <b>%d</b>" % id)

	handler.title(task.safe.name)
	showHistory(task, False)
	print "<br>"

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
	print "<tr><td class=\"left\">Name:</td><td class=\"right\"><input type=\"text\" name=\"name\" class=\"defaultfocus\"></td></tr>"
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
	handler.title("New Tasks")
	requirePriv(handler, 'User')
	id = int(group)

	defaultGroup = Group.load(group)
	if not defaultGroup:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)
	sprint = defaultGroup.sprint

	print "<script src=\"/static/jquery.typing-0.2.0.min.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/tasks.js\" type=\"text/javascript\"></script>"
	print "<script type=\"text/javascript\">"
	print "next_url = '/sprints/%d';" % sprint.id
	print "</script>"

	print (tabs << 'many') % id

	help = ResponseWriter()
	print "Each line needs to match the following syntax. Unparseable lines generate an error message but are otherwise ignored"
	print "<ul>"
	print "<li><b>X</b> -- A single character changes the field separator to that character. The default field separator is |, so that's used in the examples here</li>"
	print "<li><b>X...X:</b> -- A line ending in a colon is a group name. All tasks after that line will be added to that group. If no group of that name exists, it will be created (the preview will label that group as \"(NEW)\"). A blank line switches back to the default group, which is the group you clicked the new task button on, %s" % defaultGroup.safe.name
	print "<li><b>X...X|X...X|X...X[|X...X]</b> -- 3 or 4 fields are a new task. The fields can appear in any order:<ul>"
	print "<li><b>assignee</b> -- The person assigned to this task</li>"
	print "<li><b>hours</b> -- The number of hours this task will take</li>"
	print "<li><b>status</b> -- The initial status of the task. This field is optional; it defaults to \"not started\"</li>"
	print "<li><b>name</b> -- The name of the task</li>"
	print "</ul></li>"
	print "</ul>"
	print CollapsibleBox('Help', help.done())

	print CollapsibleBox('Groups', "<ul>%s</ul>" % ''.join("<li>%s</li>" % ("<b>%s</b> (default)" if group == defaultGroup else "%s") % group.safe.name for group in sprint.getGroups()))

	print "<form method=\"post\" action=\"/tasks/new/many?group=%d\">" % defaultGroup.id
	print "<textarea id=\"many-body\" name=\"body\" class=\"defaultfocus\"></textarea>"

	print "<div id=\"preview\"></div>"
	print "<div id=\"new-task-many-buttons\">"
	print Button('Save All', id = 'save-button', type = 'button').positive()
	print Button('Cancel', id = 'cancel-button', type = 'button').negative()
	print "</div>"
	print "</form>"

@post('tasks/new/many')
def newTaskMany(handler, request, group, p_body, dryrun = False):
	request['wrappers'] = False
	requirePriv(handler, 'User')
	id = int(group)

	defaultGroup = Group.load(group)
	if not defaultGroup:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)
	sprint = defaultGroup.sprint

	group = defaultGroup
	groups = [group]
	newGroups = []
	tasks = {group: []}
	sep = '|'
	lines = map(lambda x: x.strip(" \r\n"), p_body.split('\n'))

	for line in lines:
		if line == '':
			group = defaultGroup
		elif len(line) == 1: # Separator
			sep = line[0]
		elif line[-1] == ':': # Group
			line = line[:-1]
			group = Group.load(sprintid = sprint.id, name = line)
			if not group:
				group = Group(sprint.id, line)
				newGroups.append(group)
				group.id = -len(newGroups)
			if not group in groups:
				groups.append(group)
				tasks[group] = []
		else:
			parts = line.split(sep)
			name, assigned, status, hours = None, None, None, None
			for case in switch(len(parts)):
				if case(3):
					status = 'not started'
					# Fall-through
				if case(4):
					for part in parts:
						part = part.strip()
						# Hours
						if not hours:
							try:
								hours = int(part)
								continue
							except ValueError: pass

						# Status
						if not status and part.lower() in statuses:
							status = part.lower()
							continue

						# Assigned
						if not assigned and part in map(lambda u: u.username, sprint.members):
							assigned = User.load(username = part)
							continue

						# Name
						if not name:
							name = part
							continue

						print "<i>Unable to parse (no field match on '%s'): %s</i><br>" % (stripTags(part), stripTags(line))
					break
				if case():
					print "<i>Unable to parse (field count mismatch): %s</i><br>" % stripTags(line)
					break
				break
			if all([name, assigned, status, hours]):
				tasks[group].append((name, assigned, status, hours))

	if dryrun:
		for group in groups:
			print "<br>"
			print "<b>%s%s</b><br>" % (group.safe.name, ' (NEW)' if group in newGroups else '')
			for name, assigned, status, hours in tasks[group]:
				print "%s (assigned to %s, %s, %d %s remain)<br>" % (stripTags(name), assigned, status, hours, 'hour' if hours == 1 else 'hours')
	else:
		for group in groups:
			# Changing a group's ID will change its hash, so this pulls from tasks before saving the group in case it's new
			groupTasks = tasks[group]
			if group in newGroups:
				group.id = 0
			group.save()
			for name, assigned, status, hours in groupTasks:
				Task(group.id, group.sprint.id, handler.session['user'].id, assigned.id, 0, name, status, hours).save()

		numGroups = len(newGroups)
		numTasks = sum(map(lambda g: len(g), tasks.values()))
		if numGroups > 0 and numGroups > 0:
			delay(handler, TintedBox("Added %d %s, %d %s" % (numGroups, 'group' if numGroups == 1 else 'groups', numTasks, 'task' if numTasks == 1 else 'tasks'), 'green'))
		elif numGroups > 0:
			delay(handler, TintedBox("Added %d %s" % (numGroups, 'group' if numGroups == 1 else 'groups'), 'green'))
		elif numTasks > 0:
			delay(handler, TintedBox("Added %d %s" % (numTasks, 'task' if numTasks == 1 else 'tasks'), 'green'))
		else:
			delay(handler, TintedBox("No changes", 'yellow'))
		request['code'] = 299

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
