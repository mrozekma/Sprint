from utils import *

TYPES = [
	'pageHandle',
	'login', 'passwordReset', 'tfa', 'prefs',
	'newSprint', 'sprintInfoUpdate', 'sprintAvailUpdate',
	'newGroup', 'renameGroup', 'deleteGroup',
	'newTask', 'taskUpdate',
	'newNote', 'deleteNote',
	'admin', 'adminSettings', 'genResetKey', 'impersonate', 'newUser', 'grantPrivilege', 'revokePrivilege', 'newProject', 'repl', 'mockTime', 'cron'
]

handlers = []

class Event:
	"""
	Event will have a static method attached for each event type
	Calling Event.someEventType(...) will call Foo.someEventType(...)
	for each EventHandler subclass Foo in handlers
	"""

	@staticmethod
	def event(type, *args):
		if type not in TYPES:
			raise KeyError("Unknown event type: %s" % type)
		for handler in handlers:
			method = getattr(handler, type, None)
			if method:
				method(*args)
			else:
				method = getattr(handler, 'default', None)
				if method:
					method(type, *args)

class EventHandler: pass

def addEventHandler(handler):
	if not issubclass(handler.__class__, EventHandler):
		raise TypeError("handler should be an EventHandler")
	handlers.append(handler)

# Add a helper method to Event for each type that just calls event()
# The _ function is just to make a closure over name
def _(name):
	setattr(Event, name, staticmethod(lambda *args: Event.event(name, *args)))
map(_, TYPES)

"""
class EventHandlerTemplate(EventHandler):
	def pageHandle(self, handler, fn):
	def login(self, handler, user, success, text = None):
	def passwordReset(self, handler, user):
	def tfa(self, handler, user):
	def prefs(self, handler):
	def newSprint(self, handler, sprint):
	def sprintInfoUpdate(self, handler, sprint, changes):
	def sprintAvailUpdate(self, handler, sprint):
	def newGroup(self, handler, group):
	def renameGroup(self, handler, group, oldName):
	def deleteGroup(self, handler, group):
	def newTask(self, handler, task):
	def taskUpdate(self, handler, task, field, value):
	def newNote(self, handler, note):
	def deleteNote(self, handler, note):
	def adminSettings(self, handler, settings):
	def genResetKey(self, handler, user):
	def impersonate(self, handler, user):
	def newUser(self, handler, user):
	def newProject(self, handler, project):
	def grantPrivilege(self, handler, user, priv, isNewUser):
	def revokePrivilege(self, handler, user, priv):
	def repl(self, handler, code):
	def mockTime(self, handler, effectiveTime, delta):
	def cron(self, handler):
"""
