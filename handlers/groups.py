from __future__ import with_statement
from itertools import groupby

from rorn.Box import ErrorBox, InfoBox
from rorn.Session import delay

from Privilege import requirePriv
from Group import Group
from User import User
from Goal import Goal
from Button import Button
from Chart import Chart
from SprintCharts import GroupGoalsChart
from Event import Event
from utils import *

@get('groups/new')
def newGroup(handler, after):
	handler.title('New Group')
	requirePriv(handler, 'User')
	afterID = int(after)

	afterGroup = Group.load(afterID)
	if not afterGroup:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % afterID)

	print "<style type=\"text/css\">"
	print "table.list td.right > * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "</style>"
	print "<script type=\"text/javascript\">"
	print "next_url = '/sprints/%d';" % afterGroup.sprint.id
	print "</script>"
	print "<script src=\"/static/groups.js\" type=\"text/javascript\"></script>"

	print InfoBox('', id = 'post-status')

	print "<form method=\"post\" action=\"/groups/new\">"
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">Sprint:</td><td class=\"right\"><select id=\"selectSprint\" disabled><option>%s</option></select></td></tr>" % afterGroup.sprint
	print "<tr><td class=\"left\">Predecessor:</td><td class=\"right\">"
	print "<select id=\"select-group\" name=\"group\" size=\"5\">"
	for sGroup in afterGroup.sprint.getGroups('name'):
		print "<option value=\"%d\"%s>%s</option>" % (sGroup.id, ' selected' if sGroup == afterGroup else '', sGroup.safe.name)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">Name:</td><td class=\"right\"><input type=\"text\" name=\"name\" class=\"defaultfocus\"></td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'button').positive()
	print Button('Cancel', id = 'cancel-button', type = 'button').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

@post('groups/new')
def newGroupPost(handler, p_group, p_name):
	def die(msg):
		print msg
		done()

	handler.title('New Group')
	requirePriv(handler, 'User')
	handler.wrappers = False

	predid = to_int(p_group, 'group', die)
	pred = Group.load(predid)
	if not pred:
		die("No group with ID <b>%d</b>" % predid)
	elif p_name.strip() == '':
		die("Group must have a non-empty name")

	group = Group(pred.sprint.id, p_name, pred.seq + 1)
	group.save()

	handler.responseCode = 299
	delay(handler, """
<script type=\"text/javascript\">
$(document).ready(function() {
	$('#group%d').effect('highlight', {}, 3000);
});
</script>""" % group.id)
	print "/sprints/%d#group%d" % (group.sprint.id, group.id)
	Event.newGroup(handler, group)

@get('groups/(?P<id>[0-9]+)')
def editGroup(handler, id):
	requirePriv(handler, 'User')
	handler.title('Manage Group')

	id = int(id)
	group = Group.load(id)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)
	tasks = group.getTasks()

	chart = GroupGoalsChart(group)
	Chart.include()
	chart.js()

	print "<style type=\"text/css\">"
	print "table.list td.left {position: relative; top: 4px;}"
	print "table.list td.right *, button {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "</style>"

	print "<h2>Edit Group</h2>"
	print "<form method=\"post\" action=\"/groups/%d/rename\">" % id
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">Name:</td><td class=\"right\"><input type=\"text\" name=\"name\" value=\"%s\">" % (group.safe.name)
	print "<tr><td class=\"left\">Predecessor:</td><td class=\"right\">"

	#TODO Waiting on group moving
	print "<select name=\"predecessor\" disabled>"
	print "<option>%s</option>" % ('None' if group.seq == 1 else Group.load(sprintid = group.sprintid, seq = group.seq-1).safe.name)
	print "</select>"

	print "</td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', type = 'submit').positive()
	print Button('Cancel', "/sprints/%d#group%d" % (group.sprintid, id), type = 'button').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

	print "<h2>Assign Goal</h2>"
	print "This is a quick way to set all the tasks in the group to the same sprint goal. The current breakdown is:"
	chart.placeholder()

	# The default is whichever goal currently has the most occurrences
	defaultGoal = max((sum(task.goal == goal or False for task in tasks), goal) for goal in group.sprint.getGoals() + [None])[1]

	print "<form method=\"post\" action=\"/groups/%d/goal\">" % id
	for goal in group.sprint.getGoals():
		if goal.name:
			print "<input type=\"radio\" id=\"goal%d\" name=\"goal\" value=\"%d\"%s>&nbsp;<label for=\"goal%d\"><img class=\"bumpdown\" src=\"/static/images/tag-%s.png\">&nbsp;%s</label><br>" % (goal.id, goal.id, ' checked' if goal == defaultGoal else '', goal.id, goal.color, goal.name)
	print "<input type=\"radio\" id=\"goal0\" name=\"goal\" value=\"0\"%s>&nbsp;<label for=\"goal0\"><img class=\"bumpdown\" src=\"/static/images/tag-none.png\">&nbsp;Other</label><br><br>" % ('' if defaultGoal else ' checked')
	print Button('Assign', type = 'submit').positive()
	print "</form>"

	print "<h2>Delete Group</h2>"
	if len(group.sprint.getGroups()) == 1:
		print "You can't delete the last group in a sprint"
	elif not group.deletable:
		print "This group is undeletable"
	else:
		print "<form method=\"post\" action=\"/groups/%d/delete\">" % id
		if len(tasks):
			print "This group has %d %s. Move %s to the <select name=\"newGroup\">" % (len(tasks), 'task' if len(tasks) == 1 else 'tasks', 'it' if len(tasks) == 1 else 'them')
			for thisGroup in group.sprint.getGroups('name'):
				if group == thisGroup: continue
				print "<option value=\"%d\">%s</option>" % (thisGroup.id, thisGroup.safe.name)
			print "<option value=\"0\">None (delete)</option>"
			print "</select> group<br><br>"
		print Button('Delete', type = 'submit')
		print "</form>"

@post('groups/(?P<id>[0-9]+)/rename')
def renameGroupPost(handler, id, p_name):
	def die(msg):
		print msg
		done()

	handler.title('Manage Group')
	requirePriv(handler, 'User')

	group = Group.load(id)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)
	elif p_name.strip() == '':
		ErrorBox.die('Invalid Name', "Group must have a non-empty name")

	oldName = group.name
	group.name = p_name
	group.save()
	Event.renameGroup(handler, group, oldName)
	redirect("/sprints/%d#group%d" % (group.sprintid, group.id))

@post('groups/(?P<id>[0-9]+)/goal')
def assignGroupGoalPost(handler, id, p_goal):
	def die(msg):
		print msg
		done()

	handler.title('Manage Group')
	requirePriv(handler, 'User')
	handler.wrappers = False

	group = Group.load(id)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)

	if p_goal == '0':
		goal = None
	else:
		goal = Goal.load(int(p_goal))
		if not goal:
			ErrorBox.die('Invalid Goal', "No goal with ID <b>%d</b>" % int(p_goal))
		elif not goal.sprint == group.sprint:
			ErrorBox.die('Invalid Goal', "Selected goal is not part of the correct sprint")

	for task in group.getTasks():
		if task.goal != goal:
			task.goal = goal

			if task.creator == handler.session['user'] and (dateToTs(getNow()) - task.timestamp) < 5*60:
				task.save()
			else:
				task.saveRevision(handler.session['user'])

			#TODO Event
			# NO

	redirect("/sprints/%d#group%d" % (group.sprintid, group.id))

@post('groups/(?P<id>[0-9]+)/delete')
def deleteGroupPost(handler, id, p_newGroup = None):
	def die(msg):
		print msg
		done()

	handler.title('Manage Group')
	requirePriv(handler, 'User')
	handler.wrappers = False

	id = int(id)
	group = Group.load(id)
	if not group:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % id)
	if not group.deletable:
		ErrorBox.die('Invalid Group', "Group is not deletable")
	if len(group.sprint.getGroups()) == 1:
		ErrorBox.die('Invalid Group', "Cannot delete the last group in a sprint")

	tasks = group.getTasks()
	newGroup = None
	if p_newGroup == '0': # Delete tasks
		for task in tasks:
			task.deleted = True
			task.revise()
	elif p_newGroup: # Move tasks
		newGroup = Group.load(p_newGroup)
		if not newGroup:
			ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % int(p_newGroup))

		# Move all the tasks to the end of the new group
		pred = newGroup.getTasks()
		pred = pred[-1] if pred else None
		for task in tasks:
			task.move(pred, newGroup)
			pred = task
	elif len(tasks):
		ErrorBox.die('Invalid Request', "Missing new group request argument")

	sprintid = group.sprintid
	group.delete()
	Event.deleteGroup(handler, group)
	redirect("/sprints/%d%s" % (sprintid, "#group%d" % newGroup.id if newGroup else ''))
