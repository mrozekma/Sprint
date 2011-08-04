from __future__ import with_statement
from utils import *
from Privilege import requirePriv
from Group import Group
from User import User
from Box import TintedBox, ErrorBox
from Table import LRTable
from Button import Button
from Session import delay

@get('groups/new')
def newGroup(handler, request, after):
	requirePriv(handler, 'User')
	handler.title("New Group")
	afterID = int(after)

	afterGroup = Group.load(afterID)
	if not afterGroup:
		ErrorBox.die('Invalid Group', "No group with ID <b>%d</b>" % afterID)

	print "<style type=\"text/css\">"
	print "#post-status {display: none}"
	print "table.list td.left {position: relative; top: 4px;}"
	print "table.list td.right * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "</style>"
	print "<script src=\"/static/groups.js\" type=\"text/javascript\"></script>"

	print TintedBox('', scheme = 'blue', id = 'post-status')

	print "<form method=\"post\" action=\"/groups/new\">"
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">Sprint:</td><td class=\"right\"><select id=\"selectSprint\" disabled><option>%s</option></select></td></tr>" % afterGroup.sprint
	print "<tr><td class=\"left\">Predecessor:</td><td class=\"right\">"
	print "<select id=\"select-group\" name=\"group\" size=\"5\">"
	for sGroup in afterGroup.sprint.getGroups('name'):
		print "<option value=\"%d\"%s>%s</option>" % (sGroup.id, ' selected' if sGroup == afterGroup else '', sGroup.safe.name)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">Name:</td><td class=\"right\"><input type=\"text\" name=\"name\" id=\"defaultfocus\"></td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'button').positive()
	print Button('Cancel', id = 'cancel-button', type = 'button').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

@post('groups/new')
def newGroupkPost(handler, request, p_group, p_name):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False

	predid = to_int(p_group, 'group', die)
	pred = Group.load(predid)
	if not pred:
		die("No group with ID <b>%d</b>" % predid)

	# def __init__(self, sprintid, name, seq = None, deletable = True, id = None):
	group = Group(pred.sprint.id, p_name, pred.seq)
	group.save()

	request['code'] = 299
	delay(handler, """
<script type=\"text/javascript\">
$(document).ready(function() {
	$('#group%d').effect('highlight', {}, 3000);
});
</script>""" % group.id)
	print "/sprints/%d" % group.sprint.id

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
