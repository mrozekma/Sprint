from __future__ import with_statement
import re
import tokenize
from token import *
import random

from rorn.Box import ErrorBox, SuccessBox

from Privilege import admin
from User import User
from Table import LRTable
from Button import Button
from utils import *

@get('admin')
def adminIndex(handler, request):
	handler.title('Admin')
	admin(handler)

	# print "<a href=\"/admin/db/reset\">Reset database</a><br>"
	print "<a href=\"/admin/resetpw\">Reset password</a><br>"
	print "<a href=\"/admin/test\">Test pages</a><br>"

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

# This isn't an admin page, it just seemed convenient to group it here for now
@get('resetpw/(?P<username>[^/]+)')
def resetPassword(handler, request, username, key):
	handler.title('Reset password')

	user = User.load(username = username)
	if not user:
		ErrorBox.die('User', "No user named <b>%s</b>" % stripTags(username))

	print "<style type=\"text/css\">"
	print "input {"
	print "    position: relative;"
	print "    top: -2px;"
	print "}"
	print "</style>"

	if user.resetkey and user.resetkey == key:
		print "<form method=\"post\" action=\"/resetpw/%s?key=%s\">" % (user.safe.username, key)
		tbl = LRTable()
		tbl['New password:'] = '<input type=\"password\" name=\"newPassword\" class=\"defaultfocus\">'
		tbl['Confirm:'] = '<input type=\"password\" name=\"newPassword2\">'
		tbl[''] = Button('Change Password', type = 'submit').positive()
		print tbl
		print "</form>"

	print user

@post('resetpw/(?P<username>[^/]+)')
def resetPasswordPost(handler, request, username, key, p_newPassword, p_newPassword2):
	handler.title('Reset password')

	user = User.load(username = username)
	if not user:
		ErrorBox.die('User', "No user named <b>%s</b>" % stripTags(username))

	if not user.resetkey or user.resetkey != key:
		ErrorBox.die('Key', "Incorrect reset key")

	if p_newPassword != p_newPassword2:
		ErrorBox.die('Password', "New password mismatch")

	user.password = User.crypt(user.username, p_newPassword)
	user.resetkey = None
	user.save()

	print SuccessBox('Password changed', "Your password has been reset; you can <a href=\"/login\">login</a> now")
