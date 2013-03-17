from __future__ import with_statement
import re
import tokenize
from token import *
import random
from pprint import pformat
from json import loads as fromJS, dumps as toJS
from cgi import escape
from datetime import datetime, time
from threading import enumerate as threads

from rorn.Box import ErrorBox, SuccessBox
from rorn.Session import sessions, delay, undelay
from rorn.ResponseWriter import ResponseWriter
from rorn.code import highlightCode

from DB import db, DiskQueue
from Privilege import Privilege, admin as requireAdmin, defaults as privDefaults
from Project import Project
from User import User
from Button import Button
from Table import LRTable
from Cron import Cron
from LoadValues import getLoadtime, setDevMode
from Log import LogEntry, log
from Settings import settings
from Event import Event
from Lock import locks
from relativeDates import timesince
from utils import *

pages = []
def admin(url, name, icon):
	def wrap(f):
		pages.append({'url': url, 'name': name, 'icon': icon})
		return get(url)(f)
	return wrap

@get('admin')
def adminIndex(handler, request):
	handler.title('Admin')
	requireAdmin(handler)

	for page in pages:
		print "<div class=\"admin-list-entry\"><a href=\"%(url)s\"><img class=\"admin-icon\" src=\"/static/images/admin-%(icon)s.png\"></a><br>%(name)s</div>" % page

@admin('admin/info', 'Information', 'info')
def adminInfo(handler, request):
	handler.title('Information')
	requireAdmin(handler)

	print """
<style type="text/css">
table {
    border-color: #000;
    border-collapse: collapse
}
table tr th {
    background-color: #ccc;
}

table tr td.center {
    text-align: center;
}
</style>
"""

	print "<h3>Uptime</h3>"
	loadTime = getLoadtime()
	print "Started %s<br>" % loadTime
	print "Up for %s<br>" % timesince(loadTime)

	print "<h3>Database</h3>"
	print "Writing to memory; mirroring to disk every %d seconds / %d writes<br>" % (DiskQueue.PERIOD, DiskQueue.SIZE)
	print "Current queue size: %d<br>" % db().diskQueue.size
	print "Last sync: %s (%s ago)<br>" % (db().diskQueue.lastFlush, pluralize(int((datetime.now() - db().diskQueue.lastFlush).total_seconds()), 'second', 'seconds'))
	print "Disk writes: %d<br>" % db().counts['flush']
	print "Total requests: %d" % db().counts['total']

	print "<h3>Threads</h3>"
	print "<table border=\"1\" cellspacing=\"0\" cellpadding=\"4\">"
	print "<tr><th>ID</th><th>Name</th><th>Alive</th><th>Daemon</th></tr>"
	for thread in threads():
		print "<tr><td>%s</td><td>%s</td><td class=\"center\"><img src=\"/static/images/%s.png\"></td><td class=\"center\"><img src=\"/static/images/%s.png\"></td></tr>" % (thread.ident, thread.name, 'tick' if thread.isAlive() else 'cross', 'tick' if thread.daemon else 'cross')
	print "</table>"

	print "<h3>Locks</h3>"
	print "<table border=\"1\" cellspacing=\"0\" cellpadding=\"4\">"
	print "<tr><th>Name</th><th>Available</th><th>Reentrant</th></tr>"
	for (name, lock) in locks.iteritems():
		print "<tr><td>%s</td><td class=\"center\"><img src=\"/static/images/%s.png\"></td><td class=\"center\"><img src=\"/static/images/%s.png\"></td></tr>" % (name, 'tick' if lock.avail() else 'cross', 'tick' if lock.reentrant() else 'cross')
	print "</table>"

@admin('admin/test', 'Test pages', 'test-pages')
def adminTest(handler, request):
	handler.title('Test pages')
	requireAdmin(handler)

	with open('handlers/test.py') as f:
		found = 0
		for token, tokString, tokStart, tokEnd, line in tokenize.generate_tokens(f.readline):
			if token == OP and tokString == '@':
				found = 1
			elif token == NEWLINE:
				found = 0
			elif token == NAME and tokString == 'get' and found == 1:
				found = 2
			elif token == STRING and found == 2:
				tokString = tokString.replace("'", "")
				print "<a href=\"/%s\">%s</a><br>" % (tokString, stripTags(tokString))
				found = 0

@admin('admin/settings', 'Settings', 'settings')
def adminSettings(handler, request):
	handler.title('Settings')
	requireAdmin(handler)
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
def adminSettingsPost(handler, request, p_emailDomain, p_systemMessage, p_bugzillaURL, p_redis, p_kerberosRealm):
	handler.title('Settings')
	requireAdmin(handler)

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
def adminUsers(handler, request):
	handler.title('User Management')
	requireAdmin(handler)

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
	for priv in Privilege.loadAll():
		print "<input type=\"checkbox\" name=\"privileges[]\" id=\"priv%d\" value=\"%s\"%s><label for=\"priv%d\">%s &mdash; %s</label><br>" % (priv.id, priv.name, ' checked' if priv.name in privDefaults else '', priv.id, priv.name, priv.description)
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
def adminUsersPost(handler, request, p_action, p_username, p_privileges = []):
	handler.title('User Management')
	requireAdmin(handler)

	for case in switch(p_action):
		if case('resetpw'):
			handler.title('Reset password')
			user = User.load(username = p_username)
			if not user:
				ErrorBox.die('Reset Password', "No user named <b>%s</b>" % stripTags(p_username))

			random.seed()
			hadPreviousKey = (user.resetkey != None and user.resetkey != '0')
			user.resetkey = "%x" % random.randint(268435456, 4294967295)
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
			privileges = [Privilege.load(name = name) for name in p_privileges]
			if not all(privileges):
				ErrorBox.die('Add User', "Unrecognized privilege name")

			user = User(p_username, '')
			user.save()
			Event.newUser(handler, user)
			for priv in privileges:
				db().update("INSERT INTO grants(userid, privid) VALUES(?, ?)", user.id, priv.id)
				Event.grantPrivilege(handler, user, priv, True)

			delay(handler, SuccessBox("Added user <b>%s</b>" % stripTags(p_username), close = True))
			redirect("/users/%s" % user.username)
			break

@admin('admin/projects', 'Projects', 'projects')
def adminProjects(handler, request):
	handler.title('Project Management')
	requireAdmin(handler)

	print "<style type=\"text/css\">"
	print "table.list td.right > * {width: 400px;}"
	print "table.list td.right button {width: 200px;}" # Half of the above value
	print "</style>"
	print "<script src=\"/static/admin-projects.js\" type=\"text/javascript\"></script>"

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

@post('admin/projects')
def adminProjectsPost(handler, request, p_name):
	handler.title('Project Management')
	requireAdmin(handler)

	if Project.load(name = p_name):
		ErrorBox.die('Add Project', "There is already a project named <b>%s</b>" % stripTags(p_name))

	project = Project(p_name)
	project.save()
	delay(handler, SuccessBox("Added project <b>%s</b>" % stripTags(p_name), close = True))
	Event.newProject(handler, project)
	redirect('/')

@admin('admin/sessions', 'Sessions', 'sessions')
def adminSessions(handler, request, username = None):
	handler.title("Sessions for %s" % stripTags(username) if username else "Sessions")
	requireAdmin(handler)

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
def adminSessionsPost(handler, request, p_key, p_action, p_value = None):
	handler.title('Sessions')
	requireAdmin(handler)
	print "<script src=\"/static/admin-sessions.js\" type=\"text/javascript\"></script>"

	if not p_key in sessions:
		ErrorBox.die("Retrieve session", "No session exists with key <b>%s</b>" % stripTags(p_key))

	for case in switch(p_action):
		if case('reassign'):
			handler.title('Reassign Session')
			if p_value:
				user = User.load(int(p_value))
				if not user:
					ErrorBox.die("Load user", "No user exists with ID <b>%s</b>" % stripTags(p_value))
				sessions[p_key]['user'] = user
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
			del sessions[p_key]
			redirect('/admin/sessions')
			break
		break

@admin('admin/privileges', 'Privileges', 'privileges')
def adminPrivileges(handler, request, username = None):
	handler.title("Privileges")
	requireAdmin(handler)
	undelay(handler)

	users = User.loadAll(orderby = 'username')
	privs = Privilege.loadAll()
	counts = dict((row['privid'], row['count']) for row in db().select("SELECT privid, COUNT(*) AS count FROM grants GROUP BY privid"))

	if username:
		print "<style type=\"text/css\">"
		print "table.granttable tr[username=%s] {" % username
		print "    background-color: #faa;"
		print "}"
		print "</style>"

	print "<h3>List</h3>"
	print "<table border=\"0\" cellspacing=\"4\">"
	print "<tr><th>Name</th><th>Grants</th><th>Description</th></tr>"
	for priv in privs:
		print "<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (priv.name, counts[priv.id] if priv.id in counts else 0, priv.description)
	print "</table>"

	print "<h3>Grants</h3>"
	print "<form method=\"post\" action=\"/admin/privileges\">"
	print "<table border=\"0\" cellspacing=\"0\" cellpadding=\"2\" class=\"granttable\">"
	print "<tr><td>&nbsp;</td>%s</tr>" % ''.join("<td>%s</td>" % priv.name for priv in privs)
	for user in users:
		print "<tr username=\"%s\">" % user.username
		print "<td>%s</td>" % user.username
		for priv in privs:
			print "<td><input type=\"checkbox\" name=\"grant[%s][%s]\"%s></td>" % (user.username, priv.name, ' checked' if user.hasPrivilege(priv.name) else '')
		print "</tr>"
	print "<tr><td>&nbsp;</td><td colspan=\"3\">%s</td></tr>" % Button('Save', type = 'submit').positive()
	print "</table>"
	print "</form>"

@post('admin/privileges')
def adminPrivilegesPost(handler, request, p_grant):
	handler.title("Privileges")
	requireAdmin(handler)
	p_grant = dict((name, privs.keys()) for name, privs in p_grant.iteritems())

	allPrivs = dict((priv.name, priv) for priv in Privilege.loadAll())

	privNames = set()
	for privs in p_grant.values():
		privNames |= set(privs)
	if not all(map(lambda name: name in allPrivs, privNames)):
		ErrorBox.die("Update privileges", "Unrecognized privilege name")

	for username, privs in p_grant.iteritems():
		user = User.load(username = username)
		for name, priv in allPrivs.iteritems():
			has = user.hasPrivilege(name)
			if has and name not in privs:
				print "Revoking %s from %s<br>" % (name, username)
				db().update("DELETE FROM grants WHERE userid = ? AND privid = ?", user.id, priv.id)
				Event.revokePrivilege(handler, user, priv)
			elif not has and name in privs:
				print "Granting %s to %s<br>" % (name, username)
				db().update("INSERT INTO grants(userid, privid) VALUES(?, ?)", user.id, priv.id)
				Event.grantPrivilege(handler, user, priv, False)
	print "Done"

@admin('admin/repl', 'REPL', 'repl')
def adminRepl(handler, request):
	handler.title('Python REPL')
	requireAdmin(handler)
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
def adminReplPost(handler, request, p_code):
	def makeStr(v):
		if isinstance(v, list):
			return "<ul>%s</ul>" % ''.join("<li>%s</li>" % item for item in v)
		return str(v)

	request['wrappers'] = False

	p_code = re.sub('^!([A-Za-z]+)$', 'from \\1 import \\1', p_code)
	match = re.match('!([A-Za-z ]+)$', p_code)
	if match:
		parts = match.group(1).split(' ')
		res = []
		for part in parts:
			w = ResponseWriter()
			adminReplPost(handler, request, "!%s" % part)
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
def adminTime(handler, request):
	handler.title('Mock time')
	requireAdmin(handler)
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
def adminTimePost(handler, request, p_date, p_time):
	handler.title('Mock time')
	requireAdmin(handler)

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

	request['wrappers'] = False
	redirect('/admin/time')

@admin('admin/cron', 'Cron jobs', 'cron')
def adminCron(handler, request):
	handler.title('Cron jobs')
	requireAdmin(handler)

	print "<form method=\"post\" action=\"/admin/cron/run\">"
	print Button('Run now').info().post()
	print "</form>"

	for job in Cron.getJobs():
		print "<h2>%s</h2>" % job.name
		print "<b>Last run: %s</b><br>" % (job.lastrun.strftime('%d %b %Y %H:%M:%S') if job.lastrun else 'Never')

		print "<div class=\"cron-log\">%s</div>" % (job.log if job.log else '')
	print "<br><br>"

@post('admin/cron/run')
def adminCronPost(handler, request):
	handler.title('Run cron jobs')
	requireAdmin(handler)

	Cron.runAll()
	Event.cron(handler)
	redirect('/admin/cron')

@post('admin/build')
def adminBuildModePost(handler, request, p_mode):
	if p_mode == 'development':
		setDevMode(True)
	elif p_mode == 'production':
		setDevMode(False)

@post('admin/unimpersonate')
def adminUnimpersonatePost(handler, request):
	if 'impersonator' in handler.session:
		handler.session['user'] = handler.session['impersonator']
		del handler.session['impersonator']
		Event.impersonate(handler, None)

@admin('admin/log', 'Log', 'log')
def adminLog(handler, request, page = 1, users = None, types = None):
	PAGE_LEN = 100
	PAGINATION_BOXES = 12

	handler.title('Log')
	requireAdmin(handler)
	entries = LogEntry.loadAll(orderby = 'timestamp DESC')

	users = set(User.load(int(id)) for id in users) if users else (User.loadAll(orderby = 'username') + [None])
	# if not all(users):
		# ErrorBox.die("Unrecognized user ID(s)")

	types = [str(type) for type in types] if types else LogEntry.getTypes()

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
		print "<pre>%s</pre>" % entry.text
		print "</div>"
		print "</div>"
		print "<div class=\"clear\"></div>"
