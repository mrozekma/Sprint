import random
from socket import gethostname

from rorn.Box import ErrorBox, SuccessBox

from User import User
from Table import LRTable
from Button import Button
from Privilege import requirePriv
from Event import Event
from Settings import settings, PORT
from utils import *

def printResetForm(handler, user, key = None):
	print "<form method=\"post\" action=\"/resetpw/%s?key=%s\">" % (user.safe.username, key or '')
	tbl = LRTable()
	tbl['New password:'] = '<input type=\"password\" name=\"newPassword\" class=\"defaultfocus\">'
	tbl['Confirm:'] = '<input type=\"password\" name=\"newPassword2\">'
	tbl[''] = Button('Change Password', type = 'submit').positive()
	print tbl
	print "</form>"

@get('resetpw')
def resetPassword(handler):
	handler.title('Reset password')
	requirePriv(handler, 'User')
	redirect("/resetpw/%s" % handler.session['user'].username)

@get('resetpw/(?P<username>[^:/]+)')
def resetUserPassword(handler, username, key = None):
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
		printResetForm(handler, user, user.resetkey)
	else:
		ErrorBox.die('Reset Password', 'Invalid reset key')

@post('resetpw/(?P<username>[^:/]+)')
def resetUserPasswordPost(handler, username, key, p_newPassword, p_newPassword2):
	handler.title('Reset password')

	user = User.load(username = username)
	if not user:
		ErrorBox.die('User', "No user named <b>%s</b>" % stripTags(username))

	if user != handler.session['user'] and (not user.resetkey or user.resetkey != key):
		ErrorBox.die('Key', "Incorrect reset key")

	if p_newPassword != p_newPassword2:
		ErrorBox.die('Password', "New password mismatch")

	user.password = User.crypt(user.username, p_newPassword)
	user.hotpKey = ''
	user.resetkey = None
	user.save()

	print SuccessBox('Password changed', "Your password has been reset; you can <a href=\"/login\">login</a> now")
	Event.passwordReset(handler, user)

@get('resetpw/:mail', statics = 'reset-mail')
def sendResetEmail(handler):
	handler.title('Reset password')
	if handler.session['user']:
		redirect('/resetpw')
	if not settings.smtpServer:
		ErrorBox.die("Sprint is not configured for sending e-mail. You will need to contact an administrator to reset your password")

	print "A reset link will be send to your e-mail address. You can also contact an administrator to reset your password.<br><br>"
	print "<form method=\"post\" action=\"/resetpw/:mail\">"
	print "Username: <select name=\"username\">"
	for user in User.loadAll(orderby = 'username'):
		print "<option value=\"%s\">%s</option>" % (user.safe.username, user.safe.username)
	print "</select><br>"
	print Button('Send e-mail', type = 'submit').positive()

@post('resetpw/:mail')
def sendResetEmailPost(handler, p_username):
	handler.title('Reset password')
	user = User.load(username = p_username)
	if not user:
		ErrorBox.die("Invalid User", "No user named <b>%s</b>" % stripTags(p_username))

	user.resetkey = "%x" % random.randint(0x10000000, 0xffffffff)
	try:
		sendmail(user.getEmail(), "Sprint - Password Reset", "Someone (hopefully you) requested a Sprint password reset. You can follow this link to reset your password: http://%s:%d/resetpw/%s?key=%s. If you didn't request this or no longer need it, it will expire in a day or two." % (gethostname(), PORT, user.safe.username, user.resetkey))
	except Exception:
		Event.error(handler, "<div style=\"white-space: normal\">%s</div>" % formatException())
		ErrorBox.die("Reset failed", "Unable to send password reset e-mail")

	user.save()
	print SuccessBox("A password reset e-mail has been sent")
