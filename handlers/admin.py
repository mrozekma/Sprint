from __future__ import with_statement
import re
import tokenize
from token import *
import random
from pprint import pformat
from json import loads as fromJS, dumps as toJS
from cgi import escape

from rorn.Box import ErrorBox, SuccessBox
from rorn.Session import sessions, delay, undelay
from rorn.ResponseWriter import ResponseWriter
from rorn.code import highlightCode

from Privilege import admin
from User import User
from Button import Button
from utils import *

@get('admin')
def adminIndex(handler, request):
	handler.title('Admin')
	admin(handler)

	# print "<a href=\"/admin/db/reset\">Reset database</a><br>"

	print "<div class=\"user-list-entry\"><a href=\"/admin/resetpw\"><img class=\"admin-icon\" src=\"/static/images/admin-reset-password.png\"></a><br>Reset password</div>"
	print "<div class=\"user-list-entry\"><a href=\"/admin/test\"><img class=\"admin-icon\" src=\"/static/images/admin-test-pages.png\"></a><br>Test pages</div>"
	print "<div class=\"user-list-entry\"><a href=\"/admin/impersonate-user\"><img class=\"admin-icon\" src=\"/static/images/admin-impersonate.png\"></a><br>Impersonate user</div>"
	print "<div class=\"user-list-entry\"><a href=\"/admin/sessions\"><img class=\"admin-icon\" src=\"/static/images/admin-sessions.png\"></a><br>Sessions</div>"
	print "<div class=\"user-list-entry\"><a href=\"/admin/shell\"><img class=\"admin-icon\" src=\"/static/images/admin-shell.png\"></a><br>Shell</div>"

# @get('admin/db/reset')
# def resetDB(handler, request):
	# handler.title('Reset database')

@get('admin/test')
def adminTest(handler, request):
	handler.title('Test pages')
	admin(handler)

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

@get('admin/resetpw')
def adminResetPassword(handler, request):
	handler.title('Reset password')
	admin(handler)

	users = User.loadAll(orderby = 'username')
	for user in users:
		print "<form method=\"post\" action=\"/admin/resetpw/%s\">" % user.safe.username
		print "<div class=\"user-list-entry\"><input type=\"image\" src=\"%s\"><br>%s</div>" % (user.getAvatar(64), user.safe.username)
		print "</form>"

@post('admin/resetpw/(?P<username>[^/]+)')
def adminResetPasswordUser(handler, request, username, p_x = None, p_y = None):
	handler.title('Reset password')
	admin(handler)

	user = User.load(username = username)
	if not user:
		ErrorBox.die('User', "No user named <b>%s</b>" % stripTags(username))

	random.seed()
	hadPreviousKey = (user.resetkey != None)
	user.resetkey = "%x" % random.randint(268435456, 4294967295)
	user.save()

	print "Reset key for %s: <a href=\"/resetpw/%s?key=%s\">%s</a><br>" % (user, user.safe.username, user.resetkey, user.resetkey)
	if hadPreviousKey:
		print "<b>Warning</b>: This invalides the previous reset key for this user<br>"

@get('admin/impersonate-user')
def impersonateUser(handler, request):
	handler.title('Impersonate User')
	admin(handler)

	users = User.loadAll(orderby = 'username')
	for user in users:
		print "<form method=\"post\" action=\"/admin/impersonate-user/%s\">" % user.safe.username
		print "<div class=\"user-list-entry\"><input type=\"image\" src=\"%s\"><br>%s</div>" % (user.getAvatar(64), user.safe.username)
		print "</form>"

@post('admin/impersonate-user/(?P<username>[^/]+)')
def adminImpersonateUserPost(handler, request, username, p_x = None, p_y = None):
	handler.title('Reset password')
	admin(handler)

	user = User.load(username = username)
	if not user:
		ErrorBox.die('User', "No user named <b>%s</b>" % stripTags(username))

	handler.session['user'] = user
	redirect('/')

@get('admin/sessions')
def adminSessions(handler, request):
	handler.title('Sessions')
	admin(handler)

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
	admin(handler)
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

shells = {}

@get('admin/shell')
def adminShell(handler, request):
	handler.title('Shell')
	admin(handler)
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
		return escape(str(v))

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
	print toJS({'code': highlightCode(p_code), 'stdout': stdout, 'stderr': stderr, 'vars': [(k, pformat(v), makeStr(v)) for (k, v) in shells[handler.session.key].items() if k != '__builtins__']})
