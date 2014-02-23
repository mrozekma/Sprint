from __future__ import with_statement
import re
import tokenize
from token import *
import random
from pprint import pformat
from json import loads as fromJS, dumps as toJS
from cgi import escape
from datetime import datetime, time
import sys
from threading import enumerate as threads
from time import sleep
import traceback

from rorn.Box import ErrorBox, WarningBox, SuccessBox, CollapsibleBox
from rorn.Lock import locks, counters
from rorn.ResponseWriter import ResponseWriter
from rorn.Session import Session, delay, undelay
from rorn.code import highlightCode

from HTTPServer import server
from Privilege import requirePriv, privs as privList, defaults as privDefaults
from Project import Project
from Sprint import Sprint
from User import User, USERNAME_PATTERN
from Button import Button
from Table import LRTable
from Cron import Cron
from LoadValues import getLoadtime, setDevMode, brick
from Log import LogEntry, log
from Settings import settings
from Event import Event
from event_handlers.ErrorCounter import errorCounter
from relativeDates import timesince
from utils import *

pages = []
def admin(url, name, icon, **kw):
	def wrap(f):
		pages.append({'url': url, 'name': name, 'icon': icon})
		kw['statics'] = ['admin'] + ensureList(kw['statics'] if 'statics' in kw else [])
		return get(url, **kw)(f)
	return wrap

@get('admin', statics = 'admin')
def adminIndex(handler):
	handler.title('Admin')
	requirePriv(handler, 'Admin')

	for page in pages:
		print "<div class=\"admin-list-entry\"><a href=\"%(url)s\"><img class=\"admin-icon\" src=\"/static/images/admin-%(icon)s.png\"></a><br>%(name)s</div>" % page

@admin('admin/info', 'Information', 'info')
def adminInfo(handler):
	handler.title('Information')
	requirePriv(handler, 'Admin')

	print "<div class=\"info\">"

	print "<h3>Uptime</h3>"
	loadTime = getLoadtime()
	print "Started %s<br>" % loadTime
	print "Up for %s<br>" % timesince(loadTime)
	print "Total requests: %d<br>" % server().getTotalRequests()
	print "<form method=\"post\" action=\"/admin/restart\">"
	print Button('Restart', type = 'submit').negative()
	print "</form>"

	print "<h3>Threads</h3>"
	print "<table border=\"1\" cellspacing=\"0\" cellpadding=\"4\">"
	print "<tr><th>ID</th><th class=\"main\">Name</th><th>Alive</th><th>Daemon</th></tr>"
	for thread in sorted(threads(), key = lambda thread: thread.name):
		print "<tr><td>%s</td><td>%s</td><td class=\"%s\">&nbsp;</td><td class=\"%s\">&nbsp;</td></tr>" % ('None' if thread.ident is None else "%x" % abs(thread.ident), thread.name, 'yes' if thread.isAlive() else 'no', 'yes' if thread.daemon else 'no')
	print "</table>"

	print "<h3>Locks</h3>"
	print "<table border=\"1\" cellspacing=\"0\" cellpadding=\"4\">"
	print "<tr><th class=\"main\">Name</th><th>Available</th><th>Reentrant</th></tr>"
	for (name, lock) in sorted(locks.iteritems()):
		print "<tr><td>"
		print name
		avail = lock.avail()
		if not avail:
			print "<br>"
			writer = ResponseWriter()
			try:
				owner, tb = lock.owner, lock.tb
				name = ("%x" % abs(owner)) if owner else 'None'
				#TODO Is there no O(1) way to do this?
				for thread in threads():
					if thread.ident == owner:
						name = "%s (%x)" % (thread.name, abs(owner))
						break
				print "Owned by: <b>%s</b><br><br>" % name
				if tb:
					print "Acquisition traceback:<br>"
					print formatTrace(tb)
					print "<br>"
				print "Current traceback:<br>"
				print formatTrace(traceback.extract_stack(sys._current_frames()[owner]))
			except Exception, e:
				writer.clear()
				print "<i>(Unable to retrieve stack trace)</i>"
			print CollapsibleBox('Ownership', writer.done())
		print "</td><td class=\"%s\">&nbsp;</td><td class=\"%s\">&nbsp;</td></tr>" % ('yes' if avail else 'no', 'yes' if lock.reentrant() else 'no')
	print "</table>"

	print "<h3>Counters</h3>"
	print "<table border=\"1\" cellspacing=\"0\" cellpadding=\"4\">"
	print "<tr><th class=\"main\">Name</th><th>Count</th></tr>"
	for (name, counter) in sorted(counters.iteritems()):
		print "<tr><td>%s</td><td>%d</td></tr>" % (name, counter.count)
	print "</table>"

	print "</div><br><br>"

@post('admin/restart', statics = ['admin', 'admin-restart'])
def adminRestart(handler, now = False):
	handler.title('Restart')
	requirePriv(handler, 'Admin')

	if now:
		# This is a POST, so we've already blocked other requests and it's safe to restart
		Event.restart(handler)
		brick("Restart triggered by %s" % handler.session['user'].username) # This string is checked for in main
		server().stop()
	else:
		print "<img src=\"/static/images/loading.gif\">&nbsp;Restarting..."

@admin('admin/settings', 'Settings', 'settings')
def adminSettings(handler):
	handler.title('Settings')
	requirePriv(handler, 'Admin')
	undelay(handler)

	print "<style type=\"text/css\">"
	print "table.list td.right > * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "table.list tr td:first-of-type {font-weight: bold;}"
	print "</style>"

	def quot(str): return str.replace('"', '&quot;')

	print "<h3>Mutable settings</h3>"
	print "<form method=\"post\" action=\"/admin/settings\">"
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">E-mail domain:</td><td class=\"right\"><input type=\"text\" name=\"emailDomain\" value=\"%s\"></td></tr>" % quot(settings.emailDomain)
	print "<tr><td class=\"left\">System message:</td><td class=\"right\"><input type=\"text\" name=\"systemMessage\" value=\"%s\"></td></tr>" % quot(settings.systemMessage or '')
	print "<tr><td class=\"left\">Bugzilla URL:</td><td class=\"right\"><input type=\"text\" name=\"bugzillaURL\" value=\"%s\"></td></tr>" % quot(settings.bugzillaURL or '')
	print "<tr><td class=\"left\">Redis host:</td><td class=\"right\"><input type=\"text\" name=\"redis\" value=\"%s\"></td></tr>" % quot(settings.redis or '')
	print "<tr><td class=\"left\">Kerberos realm:</td><td class=\"right\"><input type=\"text\" name=\"kerberosRealm\" value=\"%s\"></td></tr>" % quot(settings.kerberosRealm or '')
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'submit').positive()
	print Button('Cancel', type = 'button', url = '/admin').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"
	print "<br>"

	print "<h3>Immutable settings</h3>"
	print "<table class=\"list\">"
	print "<tr><td>Database version:</td><td>%s</td></tr>" % settings.dbVersion
	print "</table>"

@post('admin/settings')
def adminSettingsPost(handler, p_emailDomain, p_systemMessage, p_bugzillaURL, p_redis, p_kerberosRealm):
	handler.title('Settings')
	requirePriv(handler, 'Admin')

	settings.emailDomain = p_emailDomain

	if p_systemMessage == '':
		if settings.systemMessage:
			del settings['systemMessage']
	else:
		settings.systemMessage = p_systemMessage

	if p_bugzillaURL != '' and p_bugzillaURL[-1] == '/':
		p_bugzillaURL = p_bugzillaURL[:-1]
	settings.bugzillaURL = p_bugzillaURL

	if p_redis == '':
		if settings.redis:
			del settings['redis']
	else:
		if ':' in p_redis:
			try:
				host, port = p_redis.split(':', 1)
				port = int(port)
			except ValueError:
				ErrorBox.die("Invalid setting", "Malformed redis host")
		else:
			host = p_redis
			port = 6379

		settings.redis = "%s:%d" % (host, port)

	if p_kerberosRealm == '':
		if settings.kerberosRealm:
			del settings['kerberosRealm']
	else:
		settings.kerberosRealm = p_kerberosRealm

	delay(handler, SuccessBox("Updated settings", close = True))
	Event.adminSettings(handler, settings)
	redirect('/admin/settings')

@admin('admin/users', 'Users', 'users')
def adminUsers(handler):
	handler.title('User Management')
	requirePriv(handler, 'Admin')

	print "<style type=\"text/css\">"
	print "table.list td.right > * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "</style>"
	undelay(handler)

	print "<h3>New User</h3>"
	print "<form method=\"post\" action=\"/admin/users\">"
	print "<input type=\"hidden\" name=\"action\" value=\"new\">"
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">Username:</td><td class=\"right\"><input type=\"text\" name=\"username\"></td></tr>"
	print "<tr><td class=\"left\">Privileges:</td><td class=\"right\"><div>"
	for name, desc in privList.iteritems():
		print "<input type=\"checkbox\" name=\"privileges[]\" id=\"priv_%s\" value=\"%s\"%s><label for=\"priv_%s\">%s &mdash; %s</label><br>" % (name, name, ' checked' if name in privDefaults else '', name, name, desc)
	print "</div></td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'submit').positive()
	print Button('Cancel', type = 'button', url = '/admin').negative()
	print "</td></tr>"
	print "</table>"
	print "</form><br>"

	print "<h3>Current Users</h3>"
	users = User.loadAll(orderby = 'username')
	print "<div class=\"user-list\">"
	for user in users:
		print "<div class=\"user-list-entry\"><a href=\"/users/%s\"><img src=\"%s\"></a><br>%s</div>" % (user.username, user.getAvatar(64), user.safe.username)
	print "</div>"
	print "<div class=\"clear\"></div>"

@post('admin/users')
def adminUsersPost(handler, p_action, p_username, p_privileges = []):
	handler.title('User Management')
	requirePriv(handler, 'Admin')

	for case in switch(p_action):
		if case('resetpw'):
			handler.title('Reset password')
			user = User.load(username = p_username)
			if not user:
				ErrorBox.die('Reset Password', "No user named <b>%s</b>" % stripTags(p_username))

			random.seed()
			hadPreviousKey = (user.resetkey != None and user.resetkey != '0')
			user.resetkey = "%x" % random.randint(0x10000000, 0xffffffff)
			user.save()
			Event.genResetKey(handler, user)

			print "Reset key for %s: <a href=\"/resetpw/%s?key=%s\">%s</a><br>" % (user, user.safe.username, user.resetkey, user.resetkey)
			if hadPreviousKey:
				print "<b>Warning</b>: This invalides the previous reset key for this user<br>"
			break
		if case('impersonate'):
			user = User.load(username = p_username)
			if not user:
				ErrorBox.die('Impersonate User', "No user named <b>%s</b>" % stripTags(p_username))

			if not 'impersonator' in handler.session:
				handler.session['impersonator'] = handler.session['user']
				handler.session.remember('impersonator')
			Event.impersonate(handler, user)
			handler.session['user'] = user
			redirect('/')
			break
		if case('sessions'):
			redirect("/admin/sessions?username=%s" % p_username)
			break
		if case('privileges'):
			redirect("/admin/privileges?username=%s" % p_username)
			break
		if case('new'):
			if User.load(username = p_username):
				ErrorBox.die('Add User', "There is already a user named <b>%s</b>" % stripTags(p_username))
			if not re.match("^%s$" % USERNAME_PATTERN, p_username):
				ErrorBox.die('Add User', "Username <b>%s</b> is illegal" % stripTags(p_username))
			if not all(name in privList for name in p_privileges):
				ErrorBox.die('Add User', "Unrecognized privilege name")

			user = User(p_username, '', privileges = set(p_privileges))
			Event.newUser(handler, user)
			for priv in p_privileges:
				Event.grantPrivilege(handler, user, priv, True)
			user.save()

			delay(handler, SuccessBox("Added user <b>%s</b>" % stripTags(p_username), close = True))
			redirect("/users/%s" % user.username)
			break

@admin('admin/projects', 'Projects', 'projects', statics = 'admin-projects')
def adminProjects(handler):
	handler.title('Project Management')
	requirePriv(handler, 'Admin')

	print "<style type=\"text/css\">"
	print "table.list td.right > * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "</style>"

	undelay(handler)

	print "<h3>New Project</h3>"
	print "<form method=\"post\" action=\"/admin/projects\">"
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">Name:</td><td class=\"right\"><input type=\"text\" name=\"name\"></td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'submit').positive()
	print Button('Cancel', type = 'button', url = '/admin').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

	print "<h3>Current Projects</h3>"
	for project in Project.getAllSorted(handler.session['user']):
		print "<a href=\"/admin/projects/%d\">%s</a><br>" % (project.id, project.safe.name)

@post('admin/projects')
def adminProjectsPost(handler, p_name):
	handler.title('Project Management')
	requirePriv(handler, 'Admin')

	if Project.load(name = p_name):
		ErrorBox.die('Add Project', "There is already a project named <b>%s</b>" % stripTags(p_name))

	project = Project(p_name)
	project.save()
	delay(handler, SuccessBox("Added project <b>%s</b>" % stripTags(p_name), close = True))
	Event.newProject(handler, project)
	redirect('/')

@get('admin/projects/(?P<id>[0-9]+)', statics = ['admin', 'admin-projects'])
def adminProjectsManage(handler, id):
	handler.title('Manage Project')
	requirePriv(handler, 'Admin')
	project = Project.load(int(id))
	if not project:
		ErrorBox.die('Invalid Project', "No project with ID <b>%d</b>" % int(id))
	undelay(handler)

	otherProjects = sorted((p for p in Project.loadAll() if p != project), key = lambda p: p.name)

	print "<a name=\"sprints\"></a>"
	print "<h3>Sprints</h3>"
	sprints = project.getSprints()
	if len(sprints) > 0:
		print "<form method=\"post\" action=\"/admin/projects/%d/move-sprints\">" % project.id
		for sprint in sprints:
			print "<input type=\"checkbox\" name=\"sprintid[]\" value=\"%d\">&nbsp;<a href=\"/sprints/%d\">%s</a><br>" % (sprint.id, sprint.id, sprint)
		print "<br>"
		print "Move to project: <select name=\"newproject\">"
		for p in otherProjects:
			print "<option value=\"%d\">%s</option>" % (p.id, p.safe.name)
		print "</select>"
		print Button('Move', type = 'submit').positive()
		print "</form>"
	else:
		print "No sprints"

	print "<a name=\"rename\"></a>"
	print "<h3>Rename</h3>"
	print "<form method=\"post\" action=\"/admin/projects/%d/edit\">" % project.id
	print "Name: <input type=\"text\" name=\"name\" value=\"%s\">" % project.safe.name
	print Button('Rename', type = 'submit').positive()
	print "</form>"

	print "<a name=\"delete\"></a>"
	print "<h3>Delete</h3>"
	print "<form method=\"post\" action=\"/admin/projects/%d/delete\">" % project.id
	if len(project.getSprints()) > 0:
		if len(otherProjects) > 0:
			print "Delete <b>%s</b> and move all sprints to <select name=\"newproject\">" % project.safe.name
			for p in otherProjects:
				print "<option value=\"%d\">%s</option>" % (p.id, p.safe.name)
			print "</select>"
			print Button('Delete', type = 'submit').negative()
		else:
			print "Unable to remove the only project if it has sprints"
	else:
		print Button("Delete %s" % project.safe.name, type = 'submit').negative()
	print "</form><br>"

@post('admin/projects/(?P<id>[0-9]+)/move-sprints')
def adminProjectsMoveSprintsPost(handler, id, p_newproject, p_sprintid = None):
	handler.title('Move Sprints')
	requirePriv(handler, 'Admin')
	project = Project.load(int(id))
	if not project:
		ErrorBox.die('Invalid Project', "No project with ID <b>%d</b>" % int(id))

	p_newproject = to_int(p_newproject, 'newproject', ErrorBox.die)
	target = Project.load(p_newproject)

	if not p_sprintid:
		delay(handler, WarningBox("No sprints to move", close = True))
		redirect("/admin/projects/%d" % project.id)

	sprintids = [to_int(id, 'sprintid', ErrorBox.die) for id in p_sprintid]
	sprints = [Sprint.load(id) for id in sprintids]
	if not all(sprints):
		ErrorBox.die("Invalid sprint ID(s)")

	for sprint in sprints:
		sprint.project = target
		sprint.save()

	delay(handler, SuccessBox("%s moved" % pluralize(len(sprints), 'sprint', 'sprints'), close = True))
	redirect("/admin/projects/%d" % project.id)

@post('admin/projects/(?P<id>[0-9]+)/edit')
def adminProjectsEditPost(handler, id, p_name):
	handler.title('Edit Project')
	requirePriv(handler, 'Admin')
	project = Project.load(int(id))
	if not project:
		ErrorBox.die('Invalid Project', "No project with ID <b>%d</b>" % int(id))
	project.name = p_name
	project.save()
	delay(handler, SuccessBox("Saved project changes", close = True))
	redirect("/admin/projects/%d" % project.id)

@post('admin/projects/(?P<id>[0-9]+)/delete')
def adminProjectsDeletePost(handler, id, p_newproject = None):
	handler.title('Delete Project')
	requirePriv(handler, 'Admin')
	project = Project.load(int(id))
	if not project:
		ErrorBox.die('Invalid Project', "No project with ID <b>%d</b>" % int(id))

	sprints = project.getSprints()
	if len(sprints) > 0:
		if p_newproject is None:
			ErrorBox.die('Missing Parameter', "No new project specified")
		p_newproject = to_int(p_newproject, 'newproject', ErrorBox.die)
		target = Project.load(p_newproject)
		if not target:
			ErrorBox.die('Invalid Project', "No target project with ID <b>%d</b>" % p_newproject)
		for sprint in sprints:
			sprint.project = target
			sprint.save()

	project.delete()
	delay(handler, SuccessBox("Project deleted", close = True))
	redirect("/admin/projects")

@admin('admin/sessions', 'Sessions', 'sessions')
def adminSessions(handler, username = None):
	handler.title("Sessions for %s" % stripTags(username) if username else "Sessions")
	requirePriv(handler, 'Admin')

	undelay(handler)

	def cmpSessionTimes(s1, s2):
		if 'timestamp' in s1 and 'timestamp' in s2:
			return cmp(s1['timestamp'], s2['timestamp'])
		elif 'timestamp' in s1:
			return 1
		elif 'timestamp' in s2:
			return -1
		else:
			return 0

	print "<table border=0 cellspacing=4>"
	print "<tr><th>Key</th><th>User</th><th>Last address</th><th>Last seen</th><th>&nbsp;</th></tr>"
	sessions = {sessionID: Session.load(sessionID) for sessionID in Session.getIDs()}
	for key, session in sorted(sessions.iteritems(), lambda (k1, s1), (k2, s2): cmpSessionTimes(s1, s2), reverse = True):
		if username and (('user' not in session) or session['user'].username != username):
			continue
		print "<tr>"
		print "<td>%s</td>" % key
		print "<td>%s</td>" % (session['user'] if 'user' in session else 'None')
		print "<td>%s</td>" % (session['address'] if 'address' in session else 'None')
		print "<td>%s</td>" % (session['timestamp'] if 'timestamp' in session else 'Never')
		print "<td>"
		print "<form method=\"post\" action=\"/admin/sessions\">"
		print "<input type=\"hidden\" name=\"key\" value=\"%s\">" % key
		print "<button type=\"submit\" class=\"fancy\" name=\"action\" value=\"reassign\">reassign</button>"
		print "<button type=\"submit\" class=\"fancy\" name=\"action\" value=\"destroy\">destroy</button>"
		print "</form>"
		print "</td>"
		print "</tr>"
	print "</table>"

@post('admin/sessions')
def adminSessionsPost(handler, p_key, p_action, p_value = None):
	handler.title('Sessions')
	requirePriv(handler, 'Admin')
	print "<script src=\"/static/admin-sessions.js\" type=\"text/javascript\"></script>"

	if not p_key in Session.getIDs():
		ErrorBox.die("Retrieve session", "No session exists with key <b>%s</b>" % stripTags(p_key))
	session = Session.load(p_key)

	for case in switch(p_action):
		if case('reassign'):
			handler.title('Reassign Session')
			if p_value:
				user = User.load(int(p_value))
				if not user:
					ErrorBox.die("Load user", "No user exists with ID <b>%s</b>" % stripTags(p_value))
				session['user'] = user
				redirect('/admin/sessions')
			else:
				print "<form method=\"post\" action=\"/admin/sessions\">"
				print "<input type=\"hidden\" name=\"action\" value=\"reassign\">"
				print "<input type=\"hidden\" name=\"key\" value=\"%s\">" % p_key
				print "<select id=\"selectUser\" name=\"value\">"
				for user in sorted(User.loadAll()):
					print "<option value=\"%d\">%s</option>" % (user.id, user.safe.username)
				print "</select><br>"
				print Button('Reassign', type = 'submit').positive()
				print Button('Cancel', id = 'cancel-button', type = 'button', url = '/admin/sessions').negative()
				print "</form>"
				break
		if case('destroy'):
			Session.destroy(p_key)
			redirect('/admin/sessions')
			break
		break

@admin('admin/privileges', 'Privileges', 'privileges')
def adminPrivileges(handler, username = None):
	handler.title("Privileges")
	requirePriv(handler, 'Admin')
	undelay(handler)

	users = User.loadAll(orderby = 'username')
	counts = {name: len(filter(lambda user: name in user.privileges, users)) for name in privList}

	if username:
		print "<style type=\"text/css\">"
		print "table.granttable tr[username=%s] {" % username
		print "    background-color: #faa;"
		print "}"
		print "</style>"

	print "<h3>List</h3>"
	print "<table border=\"0\" cellspacing=\"4\">"
	print "<tr><th>Name</th><th>Grants</th><th>Description</th></tr>"
	for name, desc in privList.iteritems():
		print "<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (name, counts[name] if name in counts else 0, desc)
	print "</table>"

	print "<h3>Grants</h3>"
	print "<form method=\"post\" action=\"/admin/privileges\">"
	print "<table border=\"0\" cellspacing=\"0\" cellpadding=\"2\" class=\"granttable\">"
	print "<tr><td>&nbsp;</td>%s</tr>" % ''.join("<td>%s</td>" % name for name in privList)
	for user in users:
		print "<tr username=\"%s\">" % user.username
		print "<td>%s</td>" % user.username
		for name in privList:
			print "<td><input type=\"checkbox\" name=\"grant[%s][%s]\"%s></td>" % (user.username, name, ' checked' if user.hasPrivilege(name) else '')
		print "</tr>"
	print "<tr><td>&nbsp;</td><td colspan=\"3\">%s</td></tr>" % Button('Save', type = 'submit').positive()
	print "</table>"
	print "</form>"

@post('admin/privileges')
def adminPrivilegesPost(handler, p_grant):
	handler.title("Privileges")
	requirePriv(handler, 'Admin')
	p_grant = {name: privs.keys() for name, privs in p_grant.iteritems()}

	privNames = set()
	for privs in p_grant.values():
		privNames |= set(privs)
	if not privNames <= set(privList.keys()):
		ErrorBox.die("Update privileges", "Unrecognized privilege name")

	for user in User.loadAll():
		for priv in privList:
			privs = p_grant.get(user.username, [])
			has = user.hasPrivilege(priv)
			if has and priv not in privs:
				print "Revoking %s from %s<br>" % (priv, user.username)
				user.privileges.remove(priv)
				Event.revokePrivilege(handler, user, priv)
			elif not has and priv in privs:
				print "Granting %s to %s<br>" % (priv, user.username)
				user.privileges.add(priv)
				Event.grantPrivilege(handler, user, priv, False)
		user.save()
	print "Done"

@admin('admin/repl', 'REPL', 'repl')
def adminRepl(handler):
	handler.title('Python REPL')
	requirePriv(handler, 'Admin')
	print "<script src=\"/static/admin-repl.js\" type=\"text/javascript\"></script>"

	handler.session['admin-repl'] = {'handler': handler}

	print "<div id=\"variables\" class=\"repl-box\"><span class=\"title\">Variables</span>"
	print "<div class=\"box-wrapper\">"
	for col in ['Name', 'Value', 'Rendered']:
		print "<div class=\"elem header\">%s</div>" % col
	print "</div></div>"
	print "<div id=\"console\" class=\"repl-box\"><span class=\"title\">Console</span><pre class=\"box-wrapper code_default light\"></pre></div>"
	print "<input type=\"text\" id=\"input\" class=\"defaultfocus\">"

@post('admin/repl')
def adminReplPost(handler, p_code):
	def makeStr(v):
		if isinstance(v, list):
			return "<ul>%s</ul>" % ''.join("<li>%s</li>" % item for item in v)
		return str(v)

	handler.wrappers = False

	p_code = re.sub('^!([A-Za-z]+)$', 'from \\1 import \\1', p_code)
	match = re.match('!([A-Za-z ]+)$', p_code)
	if match:
		parts = match.group(1).split(' ')
		res = []
		for part in parts:
			w = ResponseWriter()
			adminReplPost(handler, "!%s" % part)
			res.append(fromJS(w.done()))
		print toJS(res)
		done()

	if 'admin-repl' not in handler.session:
		print toJS({'code': highlightCode(p_code), 'stdout': '', 'stderr': ['Session Expired', 'REPL session no longer exists'], 'vars': {}})
		done()

	writer = ResponseWriter()
	try:
		Event.repl(handler, p_code)
		exec compile(p_code, '<admin repl>', 'single') in handler.session['admin-repl']
		stderr = ''
	except:
		stderr = map(str, [sys.exc_info()[0].__name__, sys.exc_info()[1]])
	stdout = writer.done()

	vars = sorted([(k, pformat(v), makeStr(v)) for (k, v) in handler.session['admin-repl'].items() if k != '__builtins__'], lambda (k1, v1, vs1), (k2, v2, vs2): cmp(k1, k2))
	print toJS({'code': highlightCode(p_code), 'stdout': stdout, 'stderr': stderr, 'vars': vars})

@admin('admin/time', 'Mock time', 'time')
def adminTime(handler):
	handler.title('Mock time')
	requirePriv(handler, 'Admin')
	print "<link href=\"/static/jquery.ui.timepicker.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/jquery.ui.timepicker.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/admin-time.js\" type=\"text/javascript\"></script>"

	nowDelta = getNowDelta()
	real, effective = datetime.now(), getNow()
	days = nowDelta.days
	if nowDelta.seconds < 0:
		prefix = '-'
		times = tsToDate(0) + timedelta(hours = 24 - datetime.fromtimestamp(0).hour) - nowDelta
	else:
		prefix = ''
		times = tsToDate(0) + timedelta(hours = 24 - datetime.fromtimestamp(0).hour) + nowDelta

	tbl = LRTable()
	tbl['Real time:'] = str(real)
	tbl['Current delta:'] = "%d %s, %s%d:%02d" % (days, 'day' if days == 1 else 'days', prefix, times.hour, times.minute)
	tbl['Effective time:'] = str(effective)
	print tbl

	print "<br>"
	print "<form method=\"post\" action=\"/admin/time\">"
	print "<input type=\"text\" name=\"date\" class=\"date\" value=\"%s\">" % effective.strftime('%m/%d/%Y')
	print "<input type=\"text\" name=\"time\" class=\"time\" value=\"%s\">" % effective.strftime('%H:%M')
	print Button('Set', type = 'submit').positive()
	print "</form>"

@post('admin/time')
def adminTimePost(handler, p_date, p_time):
	handler.title('Mock time')
	requirePriv(handler, 'Admin')

	try:
		ts = re.match("^(\d{1,2})/(\d{1,2})/(\d{4})$", p_date)
		if not ts:
			raise ValueError("Malformed date: %s" % p_date)
		month, day, year = map(int, ts.groups())

		ts2 = re.match("^(\d{1,2}):(\d{1,2})$", p_time)
		if not ts2:
			raise ValueError("Malformed time: %s" % p_time)
		hour, minute = map(int, ts2.groups())

		effective = datetime(year, month, day, hour, minute, 0)
		delta = effective - datetime.now()
		setNowDelta(delta)
		Event.mockTime(handler, effective, delta)
	except ValueError, e:
		ErrorBox.die(e.message)

	handler.wrappers = False
	redirect('/admin/time')

@admin('admin/cron', 'Cron jobs', 'cron')
def adminCron(handler):
	handler.title('Cron jobs')
	requirePriv(handler, 'Admin')

	for job in Cron.getJobs():
		print "<form method=\"post\" action=\"/admin/cron/run\">"
		print "<input type=\"hidden\" name=\"name\" value=\"%s\">" % job.name
		print "<h2>%s</h2>" % job.name
		print "<b>Last run: %s</b>&nbsp;&nbsp;&nbsp;%s<br>" % (job.lastrun.strftime('%d %b %Y %H:%M:%S') if job.lastrun else 'Never', Button('run now').mini().post())

		print "<div class=\"cron-log\">%s</div>" % (job.log if job.log else '')
		print "</form>"
	print "<br><br>"

@post('admin/cron/run', statics = ['admin', 'admin-cron'])
def adminCronRun(handler, p_name):
	handler.title('Run cron job')
	requirePriv(handler, 'Admin')

	print "<script type=\"text/javascript\">"
	print "job_name = %s;" % toJS(p_name)
	print "</script>"

	print "<div id=\"output\"></div>"

@post('admin/cron/run-bg')
def adminCronRunBG(handler, p_name):
	handler.wrappers = False

	for job in Cron.getJobs():
		if job.name == p_name:
			bg(job.run)
			Event.cron(handler, p_name)
			handler.responseCode = 299
			print "Job started"
			return

	print "Unknown job: %s" % stripTags(p_name)

@post('admin/build')
def adminBuildModePost(handler, p_mode):
	if p_mode == 'development':
		setDevMode(True)
	elif p_mode == 'production':
		setDevMode(False)

@post('admin/unimpersonate')
def adminUnimpersonatePost(handler):
	if 'impersonator' in handler.session:
		handler.session['user'] = handler.session['impersonator']
		del handler.session['impersonator']
		Event.impersonate(handler, None)

@admin('admin/log', 'Log', 'log', statics = 'admin-log')
def adminLog(handler, page = 1, users = None, types = None):
	PAGE_LEN = 100
	PAGINATION_BOXES = 12

	handler.title('Log')
	requirePriv(handler, 'Admin')
	LogEntry.cacheAll()
	entries = LogEntry.loadAll(orderby = '-timestamp')
	filtered = (users is not None) or (types is not None)

	users = set(User.load(int(id)) for id in users) if users else (User.loadAll(orderby = 'username') + [None])
	# if not all(users):
		# ErrorBox.die("Unrecognized user ID(s)")

	types = [str(type) for type in types] if types else LogEntry.getTypes()
	if 'error' in types:
		errorCounter.reset()

	if filtered:
		entries = filter(lambda entry: entry.user in users and entry.type in types, entries)
	page = int(page)
	pages = max(len(entries) / PAGE_LEN, 1)
	if page < 1: page = 1
	if page > pages: page = pages

	print "<form method=\"get\" action=\"/admin/log\">"
	print "<select name=\"users[]\" multiple size=\"10\">"
	for user in User.loadAll(orderby = 'username'):
		print "<option value=\"%d\"%s>%s</option>" % (user.id, ' selected' if user in users else '', user.safe.username)
	print "<option value=\"0\"%s>(anonymous)</option>" % (' selected' if None in users else '')
	print "</select>"
	print "<select name=\"types[]\" multiple size=\"10\">"
	for type in LogEntry.getTypes():
		print "<option value=\"%s\"%s>%s</option>" % (type, ' selected' if type in types else '', type)
	print "</select>"
	print "<br>"

	print Button('Update', type = 'submit')
	print "</form>"

	firstPage, lastPage = max(1, page - (PAGINATION_BOXES - 1)), min(pages, page + (PAGINATION_BOXES - 1))
	while lastPage - firstPage > ((PAGINATION_BOXES - 1) - sum([firstPage > 1, firstPage > 2, lastPage < pages, lastPage < pages - 1])):
		if abs(firstPage - page) >= abs(lastPage - page):
			firstPage += 1
		else:
			lastPage -= 1

	link = "/admin/log?page=%d" + ''.join("&users[]=%d" % (user.id if user else 0) for user in users) + ''.join("&types[]=%s" % type for type in types)

	print "<div class=\"pagination\">"
	print "<ul>"
	if page == 1:
		print "<li class=\"disabled\"><a href=\"#\">&laquo;</a></li>"
	else:
		print "<li><a href=\"%s\">&laquo;</a></li>" % (link % (page - 1))
	if firstPage > 1:
		print "<li><a href=\"%s\">1</a></li>" % (link % 1)
		if firstPage > 2:
			print "<li class=\"disabled\"><a href=\"#\">...</a></li>"
	for i in range(firstPage, lastPage + 1):
		print "<li%s><a href=\"%s\">%d</a></li>" % (' class="active"' if i == page else '', link % i, i)
	if lastPage < pages:
		if lastPage < pages - 1:
			print "<li class=\"disabled\"><a href=\"#\">...</a></li>"
		print "<li><a href=\"%s\">%d</a></li>" % (link % pages, pages)
	if page == pages:
		print "<li class=\"disabled\"><a href=\"#\">&raquo;</a></li>"
	else:
		print "<li><a href=\"%s\">&raquo;</a></li>" % (link % (page + 1))
	print "</ul>"
	print "</div>"
	print "<br>"

	for entry in entries[((page - 1) * PAGE_LEN):(page * PAGE_LEN)]:
		print "<div class=\"logentry\">"
		print "<div class=\"gravatar\">"
		print "<img class=\"gravatar\" src=\"%s\">" % (entry.user.getAvatar() if entry.user else User.getBlankAvatar())
		print "</div>"
		print "<div>"
		print "<b><span class=\"label logtype-%s\">%s</span> at %s</b><br>" % (entry.type.split('.')[0], entry.type, entry.location)
		print "%s by %s<br>" % (tsToDate(entry.timestamp), "%s (%s)" % (entry.user.username, entry.ip) if entry.user else entry.ip)
		print "<pre>%s</pre>" % (entry.text or '&nbsp;')
		print "</div>"
		print "</div>"
		print "<div class=\"clear\"></div>"
