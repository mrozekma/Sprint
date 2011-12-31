from __future__ import division

from rorn.Box import SuccessBox, ErrorBox, InfoBox
from rorn.ResponseWriter import ResponseWriter

from Prefs import Prefs
from Privilege import requirePriv
from Task import statuses, statusMenu
from Table import LRTable
from Button import Button
from resetpw import printResetForm
from sprints import tabs as sprintTabs
from utils import *

@get('prefs')
def prefs(handler, request):
	handler.title('Preferences')
	requirePriv(handler, 'User')

	prefs = handler.session['user'].getPrefs()
	print "<script src=\"/static/prefs.js\" type=\"text/javascript\"></script>"
	print InfoBox('', id = 'post-status', close = True)
	print "<form method=\"post\" action=\"/prefs\">"

	print InfoBox("Note", "Your password and avatar are controlled from <a href=\"/users/%s\">your profile</a>" % handler.session['user'].username)

	print "<h3>Default Sprint Tab</h3>"
	print "<select name=\"default_tab\">"
	for tab in sprintTabs:
		print "<option value=\"%s\"%s>%s</option>" % (tab['name'], ' selected' if tab['name'] == prefs.defaultSprintTab else '', tab['displayName'])
	print "</select>"

	print "<h3>Backlog Style</h3>"
	select = ResponseWriter()
	print "<select name=\"backlog_style[%s]\">"
	print "<option value=\"show\">Show</option>"
	print "<option value=\"dim\">Dim</option>"
	print "<option value=\"hide\">Hide</option>"
	print "</select>"
	select = select.done()

	tbl = LRTable()
	for statusBlock in statusMenu:
		for name in statusBlock:
			val = prefs.backlogStyles[name]
			tbl[statuses[name].text] = (select % name).replace("<option value=\"%s\">" % val, "<option value=\"%s\" selected>" % val)
	print tbl

	print "<br>"
	print Button('Save', id = 'save-button', type = 'button').positive()
	print "</form>"

@post('prefs')
def prefsPost(handler, request, p_default_tab, p_backlog_style):
	def die(msg):
		print msg
		done()

	request['wrappers'] = False

	if not handler.session['user']:
		die("You must be logged in to modify preferences")
	if not p_default_tab in sprintTabs:
		die("Unrecognized default tab <b>%s</b>" % stripTags(p_default_tab))
	if set(p_backlog_style.keys()) != set(name for block in statusMenu for name in block):
		die("Backlog style key mismatch")

	prefs = handler.session['user'].getPrefs()
	prefs.defaultSprintTab = p_default_tab
	prefs.backlogStyles = p_backlog_style
	prefs.save()

	request['code'] = 299
	print "Saved changes"
