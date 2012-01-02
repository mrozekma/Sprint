from rorn.Box import LoginBox, ErrorBox, WarningBox

from DB import ActiveRecord
from LoadValues import isDevMode
from utils import *

# Privileges to give to new users
defaults = ['User', 'Write']

class Privilege(ActiveRecord):
	def __init__(self, name, description, arguments, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.name = name
		self.description = description
		self.arguments = arguments

	def argument(i):
		return self.arguments.split(',')[i]

	def __str__(self):
		return self.name

def requirePriv(handler, priv):
	if isinstance(priv, Privilege):
		priv = priv.name

	if not handler.session['user']:
		print LoginBox()
		done()

	if not handler.session['user'].hasPrivilege(priv):
		print ErrorBox('Forbidden', "You need the <b>%s</b> privilege" % priv)
		done()

def admin(handler):
	requirePriv(handler, 'Dev')
	handler.replace('$headerbg$', '#AA0000', 1)

def dev(handler):
	if isDevMode(handler):
		print WarningBox('Under development', close = True)
	else:
		print WarningBox('This feature is still under development and is disabled')
		done()

# print map(str, User.loadAll())
# print User.load(1)
# print User.load(100)

# usr = User.load(1)
# usr.username = 'foobar'
# usr.save()

# usr = User('newuser', 'password')
# usr.save()
