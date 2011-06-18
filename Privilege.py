from DB import ActiveRecord
from Box import LoginBox, ErrorBox
from utils import *

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

# print map(str, User.loadAll())
# print User.load(1)
# print User.load(100)

# usr = User.load(1)
# usr.username = 'foobar'
# usr.save()

# usr = User('newuser', 'password')
# usr.save()
