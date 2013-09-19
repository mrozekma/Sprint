from __future__ import with_statement
from json import dumps as toJS

from rorn.Session import delay, undelay
from rorn.Box import ErrorBox, CollapsibleBox, InfoBox, SuccessBox, WarningBox
from rorn.ResponseWriter import ResponseWriter

from Privilege import requirePriv
from Project import Project
from Sprint import Sprint
from Task import Task, statuses, statusMenu
from Group import Group
from Goal import Goal
from User import User
from Button import Button
from Tabs import Tabs
from History import showHistory
from Chart import Chart
from SprintCharts import TaskChart
from ProgressBar import ProgressBar
from Availability import Availability
from Note import Note
from relativeDates import timesince
from Event import Event
from Markdown import Markdown
from utils import *

from handlers.sprints import tabs as sprintTabs

@get('tasks/(?P<ids>[0-9]+(?:,[0-9]+)*)', statics = 'tasks')
def task(handler, request, ids):
	requirePriv(handler, 'User')
	Chart.include()

	Markdown.head('.note .text .body pre code')
	print "<script src=\"/static/jquery.typing-0.2.0.min.js\" type=\"text/javascript\"></script>"
	undelay(handler)

	tasks = {}
	if isinstance(ids, int): # Single ID
		tasks[ids] = Task.load(ids)
		ids = [ids]

		def header(task, text, level):
			if level == 1:
				handler.title(text)
			else:
				print "<h%d>%s</h%d>" % (level, text, level)
	else: # Many IDs
		ids = map(int, uniq(ids.split(',')))
		tasks = dict((id, Task.load(id)) for id in ids)
		handler.title("Task Information")

		if not all(tasks.values()):
			ids = [str(id) for (id, task) in tasks.iteritems() if not task]
			ErrorBox.die("No %s with %s %s" % ('task' if len(ids) == 1 else 'tasks', 'ID' if len(ids) == 1 else 'IDs', ', '.join(ids)))

		if len(set(task.sprint for task in tasks.values())) == 1: # All in the same sprint
			print "<small>(<a href=\"/sprints/%d?search=highlight:%s\">Show in backlog view</a>)</small><br><br>" % (tasks.values()[0].sprint.id, ','.join(map(str, ids)))

		for id in ids:
			print "<a href=\"#task%d\">%s</a><br>" % (id, tasks[id].safe.name)

		def header(task, text, level):
			if level == 1:
				print "<hr>"
				print "<a name=\"task%d\"></a>" % task.id
				print "<a href=\"#task%d\"><h2>%s</h2></a>" % (task.id, text)
			else:
				print "<h%d>%s</h%d>" % (level+1, text, level+1)

	for id in ids:
		task = tasks[id]
		if not task:
			ErrorBox.die('Tasks', "No task with ID <b>%d</b>" % id)
		revs = task.getRevisions()
		startRev = task.getStartRevision()

		header(task, task.safe.name, 1)

		header(task, 'Info', 2)
		print "Part of <a href=\"/sprints/%d\">%s</a>, <a href=\"/sprints/%d#group%d\">%s</a>" % (task.sprintid, task.sprint, task.sprintid, task.groupid, task.group),
		if task.goal:
			print "to meet the goal&nbsp;&nbsp;<img class=\"bumpdown\" src=\"/static/images/tag-%s.png\">&nbsp;<a href=\"/sprints/%d?search=goal:%s\">%s</a>" % (task.goal.color, task.sprintid, task.goal.color, task.goal.safe.name),
		print "<br>"
		print "Assigned to %s<br>" % ', '.join(map(str, task.assigned))
		print "Last changed %s ago<br><br>" % timesince(tsToDate(task.timestamp))
		hours, total, lbl = task.hours, startRev.hours, "<b>%s</b>" % statuses[task.status].text
		if task.deleted:
			if task.sprint.canEdit(handler.session['user']):
				print "<form method=\"post\" action=\"/sprints/%d\">" % task.sprint.id
				print "<input type=\"hidden\" name=\"id\" value=\"%d\">" % task.id
				print "<input type=\"hidden\" name=\"rev_id\" value=\"%d\">" % task.revision
				print "<input type=\"hidden\" name=\"field\" value=\"deleted\">"
				print "<input type=\"hidden\" name=\"value\"value=\"0\">"
				print "Deleted (%s)" % Button('undelete', id = 'undelete').mini().positive()
				print "</form>"
			else:
				print "Deleted"
			print "<br>"
		elif task.status == 'complete':
			print ProgressBar(lbl, total-hours, total, zeroDivZero = True, style = 'progress-current-green')
		elif task.status in ('blocked', 'canceled', 'deferred', 'split'):
			hours = filter(lambda rev: rev.hours > 0, revs)
			hours = hours[-1].hours if len(hours) > 0 else 0
			print ProgressBar(lbl, total-hours, total, zeroDivZero = True, style = 'progress-current-red')
		else:
			print ProgressBar(lbl, total-hours, total, zeroDivZero = True)

		header(task, 'Notes', 2)
		for note in task.getNotes():
			print "<div id=\"note%d\" class=\"note\">" % note.id
			print "<form method=\"post\" action=\"/tasks/%d/notes/%d/modify\">" % (id, note.id)
			print "<div class=\"avatar\"><img src=\"%s\"></div>" % note.user.getAvatar()
			print "<div class=\"text\">"
			print "<div class=\"title\"><a class=\"timestamp\" href=\"#note%d\">%s</a> by <span class=\"author\">%s</span>" % (note.id, tsToDate(note.timestamp).replace(microsecond = 0), note.user.safe.username)
			if note.user == handler.session['user']:
				print "<button name=\"action\" value=\"delete\" class=\"fancy mini danger\">delete</button>"
			print "</div>"
			print "<div class=\"body markdown\">%s</div>" % note.render()
			print "</div>"
			print "</form>"
			print "</div>"

		print "<div class=\"note new-note\">"
		print "<form method=\"post\" action=\"/tasks/%d/notes/new\">" % id
		print "<div class=\"avatar\"><div><img src=\"%s\"></div></div>" % handler.session['user'].getAvatar()
		print "<div class=\"text\">"
		print "<div class=\"title\">"
		print "<b>New note</b>"
		print "<a target=\"_blank\" href=\"/help/markdown\" class=\"fancy mini\">help</a>"
		print "</div>"
		print "<div class=\"body\"><textarea name=\"body\" class=\"large\"></textarea></div>"
		print Button('Post').post().positive()
		print "<hr>"
		print "<div class=\"body markdown\"><div id=\"preview\"></div></div>"
		print "</div>"
		print "</form>"
		print "</div>"

		print "<button class=\"btn start-new-note\">Add Note</button>"
		print "<div class=\"clear\"></div>"

		header(task, 'History', 2)
		chart = TaskChart("chart%d" % id, task)
		chart.js()

		chart.placeholder()
		showHistory(task, False)
		print "<br>"

tabs = Tabs()
tabs['single'] = '/tasks/new/single?group=%d'
tabs['many'] = '/tasks/new/many?group=%d'
tabs['import'] = '/tasks/new/import?group=%d'

@get('tasks/new')
def newTaskGeneric(handler, request, group, assigned = None):
	url = '/tasks/new/single'
	url += "?group=%s" % group
	if assigned:
		url += "&assigned=%s" % assigned
	redirect(url)

@get('tasks/new/single', statics = 'tasks-new')
def newTaskSingle(handler, request, group, assigned = ''):
	handler.title("New Task")
	requirePriv(handler, 'User')
	id = int(group)
	assigned = assigned.split(' ')

	print tabs.format(id).where('single')

	group = Group.load(group)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)

	sprint = group.sprint
	if not (sprint.isActive() or sprint.isPlanning()):
		ErrorBox.die("Sprint closed", "Unable to modify inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		ErrorBox.die("Permission denied", "You don't have permission to modify this sprint")

	# name, assigned, hours, status, sprint, group

	print "<script type=\"text/javascript\">"
	print "next_url = '/sprints/%d#group%d';" % (group.sprint.id, group.id)
	print "</script>"

	print InfoBox('', id = 'post-status', close = True)

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
	print "<select id=\"select-assigned\" name=\"assigned[]\" data-placeholder=\"Choose assignees (or leave blank to self-assign)\" size=\"10\" multiple>"
	for user in sorted(group.sprint.members):
		print "<option value=\"%d\"%s>%s</option>" % (user.id, ' selected' if user.username in assigned else '', user.safe.username)
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
def newTaskPost(handler, request, p_group, p_name, p_goal, p_status, p_hours, p_assigned = []):
	def die(msg):
		print msg
		done()

	requirePriv(handler, 'User')
	request['wrappers'] = False

	groupid = to_int(p_group, 'group', die)
	group = Group.load(groupid)
	if not group:
		die("No group with ID <b>%d</b>" % groupid)

	sprint = group.sprint
	if not (sprint.isActive() or sprint.isPlanning()):
		die("Unable to modify inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		die("You don't have permission to modify this sprint")

	if p_name.strip() == '':
		die("Task must have a non-empty name")

	assignedids = map(lambda i: to_int(i, 'assigned', die), p_assigned)
	assigned = [User.load(assignedid) for assignedid in assignedids]
	if assigned == []:
		assigned = [handler.session['user']]
	if not all(assigned):
		die("Invalid assignee")

	goalid = to_int(p_goal, 'goal', die)
	if goalid != 0:
		goal = Goal.load(goalid)
		if not goal:
			die("No goal with ID <b>%d</b>" % goalid)
		if goal.sprint != group.sprint:
			die("Goal does not belong to the correct sprint")

	hours = to_int(p_hours, 'hours', die)

	task = Task(groupid, group.sprintid, handler.session['user'].id, goalid, p_name, p_status, hours)
	task.assigned += assigned
	task.save()

	request['code'] = 299
	delay(handler, """
<script type=\"text/javascript\">
$(document).ready(function() {
	$('#task%d').effect('highlight', {}, 3000);
});
</script>""" % task.id)
	delay(handler, SuccessBox("Added task <b>%s</b>" % task.safe.name, close = 3, fixed = True))
	Event.newTask(handler, task)

@get('tasks/new/many', statics = 'tasks-new')
def newTaskMany(handler, request, group):
	handler.title("New Tasks")
	requirePriv(handler, 'User')
	id = int(group)

	defaultGroup = Group.load(group)
	if not defaultGroup:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)
	sprint = defaultGroup.sprint

	print "<script src=\"/static/jquery.typing-0.2.0.min.js\" type=\"text/javascript\"></script>"
	print "<script type=\"text/javascript\">"
	print "next_url = '/sprints/%d';" % sprint.id
	print "</script>"

	print tabs.format(id).where('many')

	if not (sprint.isActive() or sprint.isPlanning()):
		ErrorBox.die("Sprint Closed", "Unable to modify inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		ErrorBox.die("Permission Denied", "You don't have permission to modify this sprint")

	help = ResponseWriter()
	print "Each line needs to match the following syntax. Unparseable lines generate an error message in the preview and must be resolved before saving"
	print "<ul>"
	print "<li><b>X</b> &mdash; A single character changes the field separator to that character. The default field separator is |, so that's used in the examples here</li>"
	print "<li><b>X...X:</b> &mdash; A line ending in a colon is a group name. All tasks after that line will be added to that group. If no group of that name exists, it will be created (the preview will label that group as \"(NEW)\"). A blank line switches back to the default group, which is the group you clicked the new task button on, %s" % defaultGroup.safe.name
	print "<li><b>X...X|X...X|X...X[|X...X]</b> &mdash; 3 or 4 fields are a new task. The fields can appear in any order:<ul>"
	print "<li><b>assignee</b> &mdash; The person assigned to this task. If multiple people, separate usernames with spaces</li>"
	print "<li><b>hours</b> &mdash; The number of hours this task will take</li>"
	print "<li><b>status</b> &mdash; The initial status of the task. This field is optional; it defaults to \"not started\"</li>"
	print "<li><b>name</b> &mdash; The name of the task</li>"
	print "</ul></li>"
	print "<li><b>#...</b> &mdash; A line starting with a hash character is a comment, and is ignored. You can only comment out entire lines; a hash within a line does not start a comment at that point</li>"
	print "</ul>"
	print CollapsibleBox('Help', help.done())

	print CollapsibleBox('Groups', "<ul>%s</ul>" % ''.join("<li>%s</li>" % ("<b>%s</b> (default)" if group == defaultGroup else "%s") % group.safe.name for group in sprint.getGroups()))

	print "<form method=\"post\" action=\"/tasks/new/many?group=%d\">" % defaultGroup.id
	print "<textarea id=\"many-body\" name=\"body\" class=\"defaultfocus\"></textarea>"

	print "<div id=\"preview\"></div>"
	print InfoBox('Loading...', id = 'post-status', close = True)
	print "<div id=\"new-task-many-buttons\">"
	print Button('Save All', id = 'save-button', type = 'button').positive()
	print Button('Cancel', id = 'cancel-button', type = 'button').negative()
	print "</div>"
	print "</form>"

@post('tasks/new/many')
def newTaskMany(handler, request, group, p_body, dryrun = False):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False
	requirePriv(handler, 'User')
	id = int(group)

	defaultGroup = Group.load(group)
	if not defaultGroup:
		die("No group with ID <b>%d</b>" % id)

	sprint = defaultGroup.sprint
	if not (sprint.isActive() or sprint.isPlanning()):
		die("Unable to modify inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		die("You don't have permission to modify this sprint")

	group = defaultGroup
	groups = [group]
	newGroups = []
	tasks = {group: []}
	sep = '|'
	lines = map(lambda x: x.strip(" \r\n"), p_body.split('\n'))
	errors = False

	for line in lines:
		if line == '':
			group = defaultGroup
		elif line[0] == '#': # Comment
			continue
		elif len(line) == 1: # Separator
			sep = line[0]
		elif line[-1] == ':': # Group
			line = line[:-1]
			group = Group.load(sprintid = sprint.id, name = line)
			if not group: # Check if new group already defined
				for newGroup in newGroups:
					if newGroup.name == line:
						group = newGroup
						break
			if not group: # Make new group
				group = Group(sprint.id, line)
				newGroups.append(group)
				group.id = -len(newGroups)
			if not group in groups: # First time this group has been used in the script
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
						if hours is None:
							try:
								hours = int(part)
								continue
							except ValueError: pass

						# Status
						if status is None and part.lower() in statuses:
							status = part.lower()
							continue

						# Assigned
						if assigned is None and set(part.split(' ')) <= set(u.username for u in sprint.members):
							assigned = [User.load(username = username) for username in part.split(' ')]
							continue

						# Name
						if name is None:
							name = part
							continue

						errors = True
						if dryrun:
							print "<i>Unable to parse (no field match on '%s'): %s</i><br>" % (stripTags(part), stripTags(line))
					if name == '':
						name = None
						errors = True
						if dryrun:
							print "<i>Unable to parse (empty name): %s</i><br>" % stripTags(line)
					break
				if case():
					errors = True
					if dryrun:
						print "<i>Unable to parse (field count mismatch): %s</i><br>" % stripTags(line)
					break
				break

			if not any(v is None for v in (name, assigned, status, hours)):
				tasks[group].append((name, assigned, status, hours))

	if dryrun:
		request['log'] = False
		for group in groups:
			print "<br>"
			print "<b>%s%s</b><br>" % (group.safe.name, ' (NEW)' if group in newGroups else '')
			for name, assigned, status, hours in tasks[group]:
				print "%s (assigned to %s, %s, %d %s)<br>" % (stripTags(name), ' '.join(map(str, assigned)), status, hours, 'hour remains' if hours == 1 else 'hours remain')
	elif errors:
		die('There are unparseable lines in the task script. See the preview for more information')
	else:
		for group in groups:
			# Changing a group's ID will change its hash, so this pulls from tasks before saving the group in case it's new
			groupTasks = tasks[group]
			if group in newGroups:
				group.id = 0
			group.save()
			for name, assigned, status, hours in groupTasks:
				task = Task(group.id, group.sprint.id, handler.session['user'].id, 0, name, status, hours)
				task.assigned += assigned
				task.save()
				Event.newTask(handler, task)

		numGroups = len(newGroups)
		numTasks = sum(map(lambda g: len(g), tasks.values()))
		if numGroups > 0 and numGroups > 0:
			delay(handler, SuccessBox("Added %d %s, %d %s" % (numGroups, 'group' if numGroups == 1 else 'groups', numTasks, 'task' if numTasks == 1 else 'tasks'), close = 3, fixed = True))
		elif numGroups > 0:
			delay(handler, SuccessBox("Added %d %s" % (numGroups, 'group' if numGroups == 1 else 'groups'), close = 3, fixed = True))
		elif numTasks > 0:
			delay(handler, SuccessBox("Added %d %s" % (numTasks, 'task' if numTasks == 1 else 'tasks'), close = 3, fixed = True))
		else:
			delay(handler, WarningBox("No changes", close = 3, fixed = True))
		request['code'] = 299

@get('tasks/new/import')
def newTaskImport(handler, request, group, source = None):
	handler.title("New Tasks")
	requirePriv(handler, 'User')
	id = int(group)
	print "<script src=\"/static/tasks-import.js\" type=\"text/javascript\"></script>"

	print tabs.format(id).where('import')

	group = Group.load(group)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)

	sprint = group.sprint
	if not (sprint.isActive() or sprint.isPlanning()):
		ErrorBox.die("Sprint Closed", "Unable to modify inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		ErrorBox.die("Permission Denied", "You don't have permission to modify this sprint")

	sprints = sprint.project.getSprints()
	sprintIdx = sprints.index(sprint)
	prevSprint = sprints[sprintIdx - 1] if sprintIdx > 0 else None

	if not source:
		print "Select a sprint to import from:<br><br>"
		print "<form method=\"get\" action=\"/tasks/new/import\">"
		print "<input type=\"hidden\" name=\"group\" value=\"%d\">" % group.id
		print "<select name=\"source\" id=\"import-source\">"
		for projectIter in Project.getAllSorted(handler.session['user'], sprint.project):
			print "<optgroup label=\"%s\">" % projectIter.safe.name
			for sprintIter in projectIter.getSprints():
				print "<option value=\"%d\"%s>%s</option>" % (sprintIter.id, ' selected' if sprintIter == prevSprint else '', sprintIter.safe.name)
			print "</optgroup>"
		print "</select>"
		print "<br><br>"
		print Button('Next').positive().post()
		print "</form>"
	else:
		id = int(source)
		source = Sprint.load(id)
		if not source:
			ErrorBox.die('Invalid Sprint', "No sprint with ID <b>%d</b>" % id)
		print "<b>Source sprint</b>: <a href=\"/sprints/%d\">%s</a><br>" % (source.id, source.name)
		print "<b>Target sprint</b>: <a href=\"/sprints/%d\">%s</a><br><br>" % (sprint.id, sprint.name)
		print "All incomplete tasks are listed here, with their current values from the source sprint. You can change any of the fields before importing. Unassigned tasks will be assigned to the scrummaster<br><br>"

		groups = source.getGroups()
		names = [g.name for g in groups]
		groups += [g for g in sprint.getGroups() if g.name not in names]
		existingNames = [g.name for g in sprint.getGroups()]

		print "<form method=\"post\" action=\"/tasks/new/import?group=%d&source=%d\">" % (group.id, source.id)
		print "<input type=\"hidden\" name=\"included\" value=\"\">"
		print "<table class=\"task-import\" border=0>"
		print "<tr><th><input type=\"checkbox\" id=\"include_all\"></th><th>Task</th><th>Group</th><th>Assigned</th><th>Hours</th></tr>"
		for task in source.getTasks():
			if not task.shouldImport():
				continue
			print "<tr>"
			print "<td><input type=\"checkbox\" data-id=\"%d\"></td>" % task.id
			print "<td class=\"name\"><input type=\"text\" name=\"name[%d]\" value=\"%s\"></td>" % (task.id, task.name.replace('"', '&quot;'))
			print "<td class=\"group\"><select name=\"group[%d]\">" % task.id
			for g in groups:
				print "<option value=\"%d\"%s>%s</option>" % (g.id, ' selected' if g == task.group else '', g.name + ('' if g.name in existingNames else ' (NEW)'))
			print "</select></td>"
			print "<td class=\"assigned\"><select name=\"assigned[%d][]\" data-placeholder=\"Previously %s\" multiple>" % (task.id, ' '.join(user.username for user in task.assigned))
			assigned = filter(lambda user: user in sprint.members, task.assigned)
			for member in sprint.members:
				print "<option value=\"%s\"%s>%s</option>" % (member.id, ' selected' if member in assigned else '', member.username)
			print "</select></td>"
			print "<td class=\"hours\"><input type=\"text\" name=\"hours[%d]\" value=\"%d\"></td>" % (task.id, task.hours)
			print "</tr>"
		print "</table>"
		print Button('Import').positive().post()
		print "</form><br><br>"

@post('tasks/new/import')
def newTaskImportPost(handler, request, group, source, p_group, p_name, p_hours, p_assigned, p_included = ''):
	handler.title("Import Tasks")
	requirePriv(handler, 'User')

	id = int(group)
	group = Group.load(group)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)

	sprint = group.sprint
	if not (sprint.isActive() or sprint.isPlanning()):
		ErrorBox.die("Sprint Closed", "Unable to modify inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		ErrorBox.die("Permission Denied", "You don't have permission to modify this sprint")

	id = int(source)
	source = Sprint.load(id)
	if not source:
		ErrorBox.die('Invalid Sprint', "No sprint with ID <b>%d</b>" % id)

	ids = p_included.split(',') if p_included != '' else []
	if not all(map(lambda id: id in p_group and id in p_name and id in p_hours, ids)):
		ErrorBox.die('Malformed Request', 'Incomplete form data')

	groups, numGroups = {}, 0
	for id in ids:
		groupID, name, hours = int(p_group[id]), p_name[id], int(p_hours[id])
		if not groupID in groups:
			groups[groupID] = Group.load(groupID)
			if not groups[groupID]:
				ErrorBox.die('Malformed Request', "Invalid group ID %d" % groupID)
			if groups[groupID].sprint != sprint:
				search = Group.loadAll(sprintid = sprint.id, name = groups[groupID].name) # Try to find a group with the same name
				if len(search) > 0:
					groups[groupID] = search[0]
				else: # Duplicate the group
					numGroups += 1
					groups[groupID] = Group(sprint.id, groups[groupID].name)
					groups[groupID].save()
		group = groups[groupID]

		assigned = [User.load(int(assignedID)) for assignedID in p_assigned[id]] if id in p_assigned else [sprint.owner]
		if not all(assigned):
			ErrorBox.die('Malformed Request', "Invalid user ID(s): %s" % ', '.join(map(stripTags, assignedID)))

		task = Task(group.id, group.sprint.id, handler.session['user'].id, 0, name, 'not started', hours)
		task.assigned += assigned
		task.save()
		Event.newTask(handler, task)

	numTasks = len(ids)
	if numGroups > 0 and numGroups > 0:
		delay(handler, SuccessBox("Added %d %s, %d %s" % (numGroups, 'group' if numGroups == 1 else 'groups', numTasks, 'task' if numTasks == 1 else 'tasks'), close = 3, fixed = True))
	elif numGroups > 0:
		delay(handler, SuccessBox("Added %d %s" % (numGroups, 'group' if numGroups == 1 else 'groups'), close = 3, fixed = True))
	elif numTasks > 0:
		delay(handler, SuccessBox("Added %d %s" % (numTasks, 'task' if numTasks == 1 else 'tasks'), close = 3, fixed = True))
	else:
		delay(handler, WarningBox("No changes", close = 3, fixed = True))
	redirect("/sprints/%d" % sprint.id)

@get('tasks/distribute', statics = 'tasks-distribute')
def distribute(handler, request, sprint):
	handler.title('Distribute Tasks')
	sprintid = int(sprint)
	sprint = Sprint.load(sprintid)
	if not sprint:
		ErrorBox.die('Invalid Sprint', "No sprint with ID <b>%d</b>" % id)

	handler.title(sprint.safe.name)
	print sprintTabs(sprint, 'distribute')
	requirePriv(handler, 'Write')
	if not (sprint.isActive() or sprint.isPlanning()):
		ErrorBox.die("Sprint Closed", "Unable to modify inactive sprint")
	if not sprint.canEdit(handler.session['user']):
		ErrorBox.die("Permission Denied", "You don't have permission to modify this sprint")

	print "<script type=\"text/javascript\" src=\"/static/highcharts/js/highcharts.js\"></script>"
	print "<script type=\"text/javascript\" src=\"/static/highcharts/js/highcharts-more.js\"></script>"
	print "<script type=\"text/javascript\">"
	print "var sprintid = %d;" % sprint.id
	print "</script>"

	print InfoBox('Loading...', id = 'post-status', close = True)

	print "<div id=\"distribution-range\">"
	print "Acceptable commitment: <span></span>"
	print "</div>"
	print "<div id=\"distribution-range-slider\"></div>"
	print "<div class=\"clear\"></div>"

	print "<div id=\"distribution-chart\"></div>"

	for col in ('left', 'right'):
		print "<div class=\"distribution %s\">" % col
		for user in sorted(sprint.members):
			print "<img class=\"user-gravatar\" src=\"%s\" userid=\"%d\" title=\"%s\">" % (user.getAvatar(64), user.id, user.safe.username)
		if col == 'right':
			print "<img class=\"user-gravatar\" src=\"/static/images/revision-deferred.svg\" userid=\"deferred\" title=\"Deferred tasks\">"
		print "<br><br>"

		print "<div class=\"selected\">"
		print "<img style=\"visibility: hidden\" class=\"user-gravatar\" src=\"%s\">" % User.getBlankAvatar(64)
		print "<div class=\"info\">"
		print "<div class=\"username\"></div>"
		print "<div class=\"hours\"></div>"
		print "<div class=\"task-progress-total\"><div class=\"progress-current\" style=\"visibility: hidden;\"></div></div>"
		print "</div>"
		print "</div>"
		print "<div class=\"clear\"></div>"
		print "<div class=\"tasks\"></div>"
		print "</div>"

	print "<div class=\"clear\"></div><br><br>"

@post('tasks/distribute/update')
def distributeUpdate(handler, request, p_sprint, p_targetUser = None, p_task = None):
	def die(msg):
		print toJS({'error': msg})
		done()

	handler.title("Distribute Tasks")
	requirePriv(handler, 'Write')
	request['wrappers'] = False
	request['contentType'] = 'application/json'

	sprintid = int(p_sprint)
	sprint = Sprint.load(sprintid)
	if not sprint:
		die("No sprint with ID %d" % sprintid)
	if not sprint.canEdit(handler.session['user']):
		die("Unable to edit sprint")

	# Make changes
	if p_targetUser != None and p_task != None:
		task = Task.load(int(p_task))
		if not task:
			die("Invalid task ID")

		if p_targetUser == 'deferred':
			task.status = 'deferred'
			task.hours = 0
			if task.creator == handler.session['user'] and (dateToTs(getNow()) - task.timestamp) < 5*60:
				task.save()
			else:
				task.saveRevision(handler.session['user'])
			Event.taskUpdate(handler, task, 'status', task.status)
		else:
			userid = to_int(p_targetUser, 'targetUser', die)
			user = User.load(userid)
			if not user:
				die("No user with ID %d" % userid)

			task.assigned = [user]
			if task.creator == handler.session['user'] and (dateToTs(getNow()) - task.timestamp) < 5*60:
				task.save()
			else:
				task.saveRevision(handler.session['user'])
			Event.taskUpdate(handler, task, 'assigned', task.assigned)

	def makeTaskMap(task):
		return {
			'id': task.id,
			'groupid': task.group.id,
			'hours': task.hours,
			'name': task.name,
			'important': task.hours > 8,
			'team': len(task.assigned) > 1
		}

	# Return current info
	tasks = filter(lambda task: task.stillOpen(), sprint.getTasks())
	avail = Availability(sprint)

	deferredTasks = filter(lambda task: task.status == 'deferred', sprint.getTasks())
	m = {
		'deferred': {
			'username': 'Deferred tasks',
			'groups': [{
				'id': group.id,
				'name': group.name
			} for group in sorted((group for group in set(task.group for task in deferredTasks)), key = lambda group: group.seq)],
			'tasks': [makeTaskMap(task) for task in deferredTasks]
		}
	}

	for user in sprint.members:
		userTasks = filter(lambda task: user in task.assigned, tasks)
		m[user.id] = {
			'username': user.username,
			'hours': sum(task.hours for task in userTasks),
			'availability': avail.getAllForward(getNow().date(), user),
			'groups': [{
				'id': group.id,
				'name': group.name
			} for group in sorted((group for group in set(task.group for task in userTasks)), key = lambda group: group.seq)],
			'tasks': [makeTaskMap(task) for task in userTasks]
		}

	print toJS(m)

@post('tasks/(?P<taskid>[0-9]+)/notes/new')
def newNotePost(handler, request, taskid, p_body, dryrun = False):
	handler.title('New Note')
	if dryrun:
		request['wrappers'] = False
	requirePriv(handler, 'User')

	taskid = int(taskid)
	task = Task.load(taskid)
	if not task:
		ErrorBox.die('Invalid Task', "No task with ID <b>%d</b>" % taskid)

	note = Note(task.id, handler.session['user'].id, p_body)

	if dryrun:
		print note.render()
	else:
		if p_body == '':
			ErrorBox.die('Empty Body', "No note provided")
		note.save()
		Event.newNote(handler, note)
		redirect("/tasks/%d#note%d" % (task.id, note.id))

@post('tasks/(?P<taskid>[0-9]+)/notes/(?P<id>[0-9]+)/modify')
def newNoteModify(handler, request, taskid, id, p_action):
	handler.title('New Note')
	requirePriv(handler, 'User')

	if p_action != 'delete':
		ErrorBox.die('Invalid Action', "Unrecognized action <b>%s</b>" % p_action)

	taskid = int(taskid)
	task = Task.load(taskid)
	if not task:
		ErrorBox.die('Invalid Task', "No task with ID <b>%d</b>" % taskid)

	id = int(id)
	note = Note.load(id)
	if not note:
		ErrorBox.die('Invalid Note', "No note with ID <b>%d</b>" % noteid)
	elif note.task != task: # Doesn't really matter, but shouldn't happen
		ErrorBox.die('Task mismatch', "Note/task mismatch")
	elif note.user != handler.session['user']:
		ErrorBox.die('Permission denied', "Notes can only be deleted by their creators")

	note.delete()
	delay(handler, SuccessBox("Deleted note", close = 3))
	Event.deleteNote(handler, note)
	redirect("/tasks/%d" % task.id)

@get('tasks/mine')
def tasksMine(handler, request):
	handler.title("My tasks")
	requirePriv(handler, 'User')
	redirect("/users/%s/tasks" % handler.session['user'].username)

@get('tasks/(?P<ids>[0-9]+(?:,[0-9]+)*)/edit', statics = 'tasks-edit')
def taskEdit(handler, request, ids):
	handler.title("Edit tasks")
	requirePriv(handler, 'Write')

	ids = map(int, uniq(ids.split(',')))
	tasks = dict((id, Task.load(id)) for id in ids)
	if not all(tasks.values()):
		ids = [str(id) for (id, task) in tasks.iteritems() if not task]
		ErrorBox.die("No %s with %s %s" % ('task' if len(ids) == 1 else 'tasks', 'ID' if len(ids) == 1 else 'IDs', ', '.join(ids)))
	tasks = [tasks[id] for id in ids]
	if len(set(task.sprint for task in tasks)) > 1:
		ErrorBox.die("All tasks must be in the same sprint")
	sprint = tasks[0].sprint
	if not sprint.isActive():
		ErrorBox.die("You can't mass-edit tasks from an inactive sprint")
	elif not sprint.canEdit(handler.session['user']):
		ErrorBox.die("You don't have permission to modify this sprint")

	print "<h3>New values</h3>"
	print "<form method=\"post\" action=\"/tasks/%s/edit\">" % ','.join(map(str, ids))
	print "<table id=\"task-edit-values\" class=\"list\">"
	print "<tr><td class=\"left\">Assigned:</td><td class=\"right\">"
	print "<select id=\"select-assigned\" name=\"assigned[]\" data-placeholder=\"(unchanged)\" multiple>"
	for user in sorted(sprint.members):
		print "<option value=\"%d\">%s</option>" % (user.id, user.safe.username)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">Hours:</td><td class=\"right\"><input type=\"text\" name=\"hours\" class=\"hours\"></td></tr>"
	print "<tr><td class=\"left\">Status:</td><td class=\"right\"><select name=\"status\">"
	print "<option value=\"\">(unchanged)</option>"
	for statusSet in statusMenu:
		for name in statusSet:
			print "<option value=\"%s\">%s</option>" % (name, statuses[name].text)
	print "</select></td></tr>"
	print "<tr><td class=\"left\">Sprint Goal:</td><td class=\"right\"><select name=\"goal\">"
	print "<option value=\"\">(unchanged)</option>"
	print "<option value=\"0\">None</option>"
	for goal in sprint.getGoals():
		print "<option value=\"%d\">%s</option>" % (goal.id, goal.safe.name)
	print "</select></td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', type = 'submit').positive()
	print Button('Cancel', url = "/sprints/%d" % sprint.id, type = 'button').negative()
	print "</td></tr>"
	print "</table>"
	print "<br>"

	print "<h3>Current values</h3>"
	print "<table border=0 cellspacing=0 cellpadding=2 class=\"task-edit\">"
	for task in tasks:
		print "<tr><td class=\"task-name\" colspan=\"4\"><input type=\"checkbox\" id=\"task%d\" name=\"include[%d]\" checked=\"true\">&nbsp;<label for=\"task%d\">%s</label></td></tr>" % (task.id, task.id, task.id, task.safe.name)
		print "<tr class=\"task-fields\">"
		print "<td class=\"task-assigned\">%s</td>" % ', '.join(map(str, task.assigned))
		print "<td class=\"task-hours\"><img src=\"/static/images/time-icon.png\">&nbsp;%d %s</td>" % (task.hours, 'hour' if task.hours == 1 else 'hours')
		print "<td class=\"task-status\"><img class=\"status\" src=\"%s\">&nbsp;%s</td>" % (task.stat.icon, task.stat.text)
		print "<td class=\"task-goal\"><img class=\"goal\" src=\"/static/images/tag-%s.png\">&nbsp;%s</td>" % ((task.goal.color, task.goal.safe.name) if task.goal else ('none', 'None'))
		print "</tr>"
	print "</table>"
	print "</form>"

@post('tasks/(?P<ids>[0-9]+(?:,[0-9]+)*)/edit')
def taskEditPost(handler, request, ids, p_hours, p_status, p_goal, p_assigned = [], p_include = {}):
	handler.title("Edit tasks")
	requirePriv(handler, 'Write')

	allIDs = map(int, uniq(ids.split(',')))
	ids = map(lambda i: to_int(i, 'include', ErrorBox.die), p_include.keys())
	if not set(ids) <= set(allIDs):
		ErrorBox.die("Included tasks don't match query arguments")

	tasks = dict((id, Task.load(id)) for id in ids)
	if not all(tasks.values()):
		ids = [str(id) for (id, task) in tasks.iteritems() if not task]
		ErrorBox.die("No %s with %s %s" % ('task' if len(ids) == 1 else 'tasks', 'ID' if len(ids) == 1 else 'IDs', ', '.join(ids)))
	tasks = [tasks[id] for id in ids]
	if len(set(task.sprint for task in tasks)) > 1:
		ErrorBox.die("All tasks must be in the same sprint")
	sprint = (tasks[0] if len(tasks) > 0 else Task.load(allIDs[0])).sprint
	if not sprint.canEdit(handler.session['user']):
		ErrorBox.die("You don't have permission to modify this sprint")

	assignedids = map(lambda i: to_int(i, 'assigned', ErrorBox.die), p_assigned)

	changes = {
		'assigned': False if assignedids == [] else [User.load(assignedid) for assignedid in assignedids],
		'hours': False if p_hours == '' else int(p_hours),
		'status': False if p_status == '' else p_status,
		'goal': False if p_goal == '' else Goal.load(int(p_goal))
	}

	if changes['assigned'] and not all(changes['assigned']):
		ErrorBox.die("Invalid assignee")
	if changes['assigned'] and not set(changes['assigned']).issubset(sprint.members):
		ErrorBox.die("Unable to assign tasks to non-sprint members")
	if changes['goal'] and changes['goal'].sprint != sprint:
		ErrorBox.die("Unable to set goal to a goal outside the sprint")

	changed = set()
	for task in tasks:
		for field, value in changes.iteritems():
			if value is not False and getattr(task, field) != value:
				setattr(task, field, value)
				changed.add(task)
				Event.taskUpdate(handler, task, field, value)

	if len(changed) == 0:
		delay(handler, WarningBox("No changes necessary", close = 3, fixed = True))
	else:
		for task in changed:
			task.saveRevision(handler.session['user'])
		delay(handler, SuccessBox("Updated %d %s" % (len(changed), 'task' if len(changed) == 1 else 'tasks')))
	redirect("/sprints/%d" % sprint.id)
