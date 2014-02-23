from rorn.Box import LoginBox, ErrorBox, WarningBox

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
