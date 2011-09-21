import random

from rorn.Box import ErrorBox, SuccessBox

from User import User
from Table import LRTable
from Button import Button
from Privilege import requirePriv
from utils import *

@get('resetpw')
def resetPassword(handler, request):
	handler.title('Reset password')
	requirePriv(handler, 'User')
	redirect("/resetpw/%s" % handler.session['user'].username)

@get('resetpw/(?P<username>[^/]+)')
def resetUserPassword(handler, request, username, key = None):
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

	if user == handler.session['user'] or (user.resetkey and user.resetkey == key):
		print "<form method=\"post\" action=\"/resetpw/%s?key=%s\">" % (user.safe.username, key if key else '')
		tbl = LRTable()
		tbl['New password:'] = '<input type=\"password\" name=\"newPassword\" class=\"defaultfocus\">'
		tbl['Confirm:'] = '<input type=\"password\" name=\"newPassword2\">'
		tbl[''] = Button('Change Password', type = 'submit').positive()
		print tbl
		print "</form>"
	else:
		ErrorBox.die('Reset Password', 'Invalid reset key')

@post('resetpw/(?P<username>[^/]+)')
def resetUserPasswordPost(handler, request, username, key, p_newPassword, p_newPassword2):
	handler.title('Reset password')

	user = User.load(username = username)
	if not user:
		ErrorBox.die('User', "No user named <b>%s</b>" % stripTags(username))

	if user != handler.session['user'] and (not user.resetkey or user.resetkey != key):
		ErrorBox.die('Key', "Incorrect reset key")

	if p_newPassword != p_newPassword2:
		ErrorBox.die('Password', "New password mismatch")

	user.password = User.crypt(user.username, p_newPassword)
	user.resetkey = None
	user.save()

	print SuccessBox('Password changed', "Your password has been reset; you can <a href=\"/login\">login</a> now")
