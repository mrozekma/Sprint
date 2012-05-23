from Log import log
from utils import *

TYPES = [
	'pageHandle',
	'login', 'passwordReset', 'prefs',
	'newSprint', 'sprintInfoUpdate', 'sprintAvailUpdate',
	'newGroup', 'renameGroup', 'deleteGroup',
	'newTask', 'taskUpdate',
	'newNote', 'deleteNote',
	'admin', 'adminSettings', 'genResetKey', 'impersonate', 'newUser', 'grantPrivilege', 'revokePrivilege', 'newProject', 'shell', 'mockTime', 'cron'
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

class DebugLogger(EventHandler):
	def default(self, type, handler, *args):
		sys.__stdout__.write("DebugLogger: %s: %s\n" % (type, '\t'.join(map(str, args))))
# addEventHandler(DebugLogger())

class DBLogger(EventHandler):
	def pageHandle(self, handler, fn):
		# Logged in HTTPHandler
		pass

	def login(self, handler, user, success, text = None):
		log(handler, 'user.login', "Login %s for user %s%s" % ('succeeded' if success else 'failed', user.username if user else '(none)', (": %s" % text) if text else ''))

	def passwordReset(self, handler, user):
		log(handler, 'user.password.reset', "%s password reset" % user)

	def prefs(self, handler):
		log(handler, 'user.prefs', handler.session['user'].getPrefs().getLogString())

	def newSprint(self, handler, sprint):
		lines = [
			sprint.link(None),
			"project: %s" % sprint.project,
			"name: %s" % sprint.safe.name,
			"owner: %s" % sprint.owner,
			"active: %s - %s" % (tsToDate(sprint.start), tsToDate(sprint.end)),
			"members: %s" % ', '.join(map(str, sprint.members))
		]

		log(handler, 'sprint.new', "\n".join(lines))

	def sprintInfoUpdate(self, handler, sprint, changes):
		lines = [sprint.link(None)]
		for k, v in changes.iteritems():
			if v:
				if isinstance(v, list):
					v = ', '.join(map(str, v))
				lines.append("%s: %s" % (k, stripTags(str(v))))

		log(handler, 'sprint.info.update', "\n".join(lines))

	def sprintAvailUpdate(self, handler, sprint):
		log(handler, 'sprint.availability.update', sprint.link(None))

	def newGroup(self, handler, group):
		lines = [
			group.safe.name,
			"sprint: %s" % group.sprint.link(None),
			"seq: %d" % group.seq,
			"deletable: %s" % group.deletable
		]

		log(handler, 'group.new', "\n".join(lines))

	def renameGroup(self, handler, group, oldName):
		log(handler, 'group.rename', "%s\nold name: %s\nsprint: %s" % (group.safe.name, stripTags(oldName), group.sprint.link(None)))

	def deleteGroup(self, handler, group):
		log(handler, 'group.delete', "%s\nsprint: %s" % (group.safe.name, group.sprint.link(None)))

	def newTask(self, handler, task):
		lines = [
			task.name,
			"sprint: %s" % task.sprint.link(None),
			"group: %s" % task.group.safe.name,
			"creator: %s" % task.creator,
			"assigned: %s" % task.assigned,
			"status: %s" % task.getStatus().text,
			"hours: %d" % task.hours,
			"seq: %d" % task.seq
		]

		log(handler, 'task.new', "\n".join(lines))

	def taskUpdate(self, handler, task, field, value):
		log(handler, 'task.update', "Task %d\n%s: %s" % (task.id, field, stripTags(str(value))))

	def newNote(self, handler, note):
		lines = [
			"task: <a href=\"/tasks/%d\">%s</a>" % (note.task.id, note.task.safe.name),
			"user: %s" % note.user,
			"body: %s" % note.safe.body
		]

		log(handler, 'note.new', "\n".join(lines))

	def deleteNote(self, handler, note):
		log(handler, 'note.delete', "%d\ntask: <a href=\"/tasks/%d\">%s</a>" % (note.id, note.task.id, note.task.safe.name))

	def adminSettings(self, handler, settings):
		log(handler, 'admin.settings', str(settings))

	def genResetKey(self, handler, user):
		log(handler, 'admin.user.resetkey.generate', "Generated reset key for %s" % user)

	def impersonate(self, handler, user):
		if user:
			log(handler, 'admin.user.impersonate', "Impersonating %s" % user)
		else:
			log(handler, 'admin.user.impersonate', "Stopped impersonating")

	def newUser(self, handler, user):
		log(handler, 'admin.user.new', str(user))

	def newProject(self, handler, project):
		log(handler, 'admin.project.new', project.name)

	def grantPrivilege(self, handler, user, priv):
		log(handler, 'admin.user.privilege.grant', "Granted %s to %s" % (priv, user))

	def revokePrivilege(self, handler, user, priv):
		log(handler, 'admin.user.privilege.revoke', "Revoked %s from %s" % (priv, user))

	def shell(self, handler, code):
		log(handler, 'admin.shell', code)

	def mockTime(self, handler, effectiveTime, delta):
		log(handler, 'admin.mocktime', "%s (%s)" % (effectiveTime, delta))

	def cron(self, handler):
		log(handler, 'admin.cron.run', "")
addEventHandler(DBLogger())
