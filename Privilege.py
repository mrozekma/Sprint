from rorn.Box import ErrorBox, WarningBox
from rorn.ResponseWriter import ResponseWriter

from LoadValues import isDevMode
from utils import *

from stasis.ActiveRecord import ActiveRecord

privs = {
	'User': 'Privilege all registered users have',
	'Admin': 'Allows access to administration features',
	'Write': 'Allows modifications to sprints',
	'Dev': 'Show debugging information',
}

# Privileges to give to new users
defaults = ['User', 'Write']
adminDefaults = ['User', 'Admin', 'Write']

class LoginBox:
	def __init__(self, redir = None):
		self.redir = redir

	def __str__(self):
		writer = ResponseWriter()
		print "<div class=\"box blue rounded login\">"
		print "<div class=\"title\">Login</div>"
		print "<span class=\"boxBody\">"
		print "<form method=\"post\" action=\"/login\">"
		print "<input type=\"hidden\" name=\"redir\" value=\"%s\">" % (self.redir or '/{{path}}?{{get-args}}')
		print "<table style=\"margin-left: 30px;\" class=\"list\">"
		print "<tr><td class=\"left\">Username:</td><td class=\"right\"><input type=\"text\" name=\"username\" class=\"username defaultfocus\"></td></tr>"
		print "<tr><td class=\"left\">Password:</td><td class=\"right\"><input type=\"password\" name=\"password\" class=\"password\">&nbsp;<a class=\"resetpw\" href=\"/resetpw/:mail\">(Forgot password)</a></td></tr>"
		print "<tr><td class=\"left\">Verification Code:</td><td class=\"right\"><input type=\"text\" name=\"verification\" class=\"code\" maxlength=\"6\" size=\"6\"><br><small>(This is only necessary if you've enabled two-factor authentication)</small></td></tr>"
		print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\"><button type=\"submit\">Login</button></td></tr>"
		print "</table>"
		print "</form>"
		print "</span>"
		print "</div>"
		return writer.done()

def requirePriv(handler, priv):
	if not handler.session['user']:
		print LoginBox()
		done()

	if not handler.session['user'].hasPrivilege(priv):
		print ErrorBox('Forbidden', "You need the <b>%s</b> privilege" % priv)
		done()

def dev(handler):
	if isDevMode(handler):
		print WarningBox('Under development', close = True)
	else:
		print WarningBox('This feature is still under development and is disabled')
		done()
