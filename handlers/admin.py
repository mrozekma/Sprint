from __future__ import with_statement
import re
import tokenize
from token import *
import random
from pprint import pformat
from json import loads as fromJS, dumps as toJS
from cgi import escape
from datetime import time

from rorn.Box import ErrorBox, SuccessBox
from rorn.Session import sessions, delay, undelay
from rorn.ResponseWriter import ResponseWriter
from rorn.code import highlightCode

from DB import db
from Privilege import Privilege, admin as requireAdmin, defaults as privDefaults
from Project import Project
from User import User
from Button import Button
from Table import LRTable
from Cron import Cron
from LoadValues import getLoadtime, setDevMode
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

@admin('admin/stats', 'Statistics', 'stats')
def adminStats(handler, request):
	handler.title('Statistics')
	requireAdmin(handler)

	print "<h3>Uptime</h3>"
	loadTime = getLoadtime()
	print "Started %s<br>" % loadTime
	print "Up for %s<br>" % timesince(loadTime)

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

			print "Reset key for %s: <a href=\"/resetpw/%s?key=%s\">%s</a><br>" % (user, user.safe.username, user.resetkey, user.resetkey)
			if hadPreviousKey:
				print "<b>Warning</b>: This invalides the previous reset key for this user<br>"
			break
		if case('impersonate'):
			user = User.load(username = p_username)
			if not user:
				ErrorBox.die('Impersonate User', "No user named <b>%s</b>" % stripTags(p_username))

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
			for priv in privileges:
				db().update("INSERT INTO grants(userid, privid) VALUES(?, ?)", user.id, priv.id)

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
	print "<tr><td class=\"left\">Scrummaster:</td><td class=\"right\">"
	print "<select name=\"owner\">"
	for user in User.loadAll(orderby = 'username'):
		print "<option value=\"%s\"%s>%s</option>" % (user.username, ' selected' if user == handler.session['user'] else '', user.username)
	print "</select>"
	print "</td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'submit').positive()
	print Button('Cancel', type = 'button', url = '/admin').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

@post('admin/projects')
def adminProjectsPost(handler, request, p_owner, p_name):
	handler.title('Project Management')
	requireAdmin(handler)

	owner = User.load(username = p_owner)
	if not owner:
		ErrorBox.die('Add Project', "No user named <b>%s</b>" % stripTags(p_owner))
	if Project.load(name = p_name):
		ErrorBox.die('Add Project', "There is already a project named <b>%s</b>" % stripTags(p_name))

	Project(owner.id, p_name).save()
	delay(handler, SuccessBox("Added project <b>%s</b>" % stripTags(p_name), close = True))
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
				print Button('Cancel', id = 'cancel-button', type = 'button').negative()
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
		print "<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (priv.name, counts[priv.id], priv.description)
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
			elif not has and name in privs:
				print "Granting %s to %s<br>" % (name, username)
				db().update("INSERT INTO grants(userid, privid) VALUES(?, ?)", user.id, priv.id)
	print "Done"

shells = {}

@admin('admin/shell', 'Shell', 'shell')
def adminShell(handler, request):
	handler.title('Shell')
	requireAdmin(handler)
	print "<script src=\"/static/admin-shell.js\" type=\"text/javascript\"></script>"

	shells[handler.session.key] = {'handler': handler}

	# print "<table border=1 cellspacing=0 cellpadding=4>"
	# print "<thead><tr><th>Name</th><th>Value</th><th>String</th></tr></thead>"
	# print "<tbody></tbody>"
	# print "</table>"

	print "<div id=\"variables\" class=\"shell-box\"><span class=\"title\">Variables</span>"
	print "<div class=\"box-wrapper\">"
	for col in ['Name', 'Value', 'Rendered']:
		print "<div class=\"elem header\">%s</div>" % col
	print "</div></div>"
	print "<div id=\"console\" class=\"shell-box\"><span class=\"title\">Console</span><pre class=\"box-wrapper code_default light\"></pre></div>"
	print "<input type=\"text\" id=\"input\" class=\"defaultfocus\">"

@post('admin/shell')
def adminShellPost(handler, request, p_code):
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
			adminShellPost(handler, request, "!%s" % part)
			res.append(fromJS(w.done()))
		print toJS(res)
		done()

	if handler.session.key not in shells:
		print toJS({'code': highlightCode(p_code), 'stdout': '', 'stderr': ['Session Expired', 'Shell session no longer exists'], 'vars': {}})
		done()

	writer = ResponseWriter()
	try:
		exec compile(p_code, '<admin shell>', 'single') in shells[handler.session.key]
		stderr = ''
	except:
		stderr = map(str, [sys.exc_info()[0].__name__, sys.exc_info()[1]])
	stdout = writer.done()

	# 'vars': pformat(dict(filter(lambda (k, v): k != '__builtins__', shells[handler.session.key].items())), width = 80)}
	vars = sorted([(k, pformat(v), makeStr(v)) for (k, v) in shells[handler.session.key].items() if k != '__builtins__'], lambda (k1, v1, vs1), (k2, v2, vs2): cmp(k1, k2))
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
		print effective
		print effective - datetime.now()
		setNowDelta(effective - datetime.now())
	except ValueError, e:
		die(e.message)

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
	redirect('/admin/cron')

@post('admin/build')
def adminModeMode(handler, request, p_mode):
	if p_mode == 'development':
		setDevMode(True)
	elif p_mode == 'production':
		setDevMode(False)
