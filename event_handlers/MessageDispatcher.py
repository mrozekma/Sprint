import re

from Event import EventHandler
from User import User
from Message import Message

types = {
	'sprintMembership': ("Added to a sprint", "You were added to %s"),
	'taskAssigned': ("Assigned a task", "You were assigned the task %s"),
	'note': ("Mentioned in a note", "You were mentioned in a note on %s"),
	'priv': ("Granted a privilege", "You were granted the %s privilege: %s"),
}

class MessageDispatcher(EventHandler):
	def sendMessage(self, handler, target, type, *args):
		# Right now logged out users can't trigger messages, but just in case
		if not handler.session['user']:
			return

		# Don't notify if the user caused the event -- they're probably aware
		if handler.session['user'] == target:
			return

		# Also don't notify if the user isn't subscribed to this event type
		if not target.getPrefs().messages[type]:
			return

		title, body = types[type]
		Message(target.id, handler.session['user'].id, title, body % args).save()

	# EventHandler methods

	def newSprint(self, handler, sprint):
		for member in sprint.members:
			self.sendMessage(handler, member, 'sprintMembership', sprint.link(member))

	def sprintInfoUpdate(self, handler, sprint, changes):
		for member in changes['addMembers']:
			self.sendMessage(handler, member, 'sprintMembership', sprint.link(member))

	def newTask(self, handler, task):
		self.sendMessage(handler, task.assigned, 'taskAssigned', task.link())

	def taskUpdate(self, handler, task, field, value):
		if field == 'assigned':
			self.sendMessage(handler, task.assigned, 'taskAssigned', task.link())

	def newNote(self, handler, note):
		for username in re.findall("<a href=\"/users/([a-z0-9]+)\">", note.render()):
			user = User.load(username = username)
			if user: # Should never be false
				self.sendMessage(handler, user, 'note', "<a href=\"/tasks/%d#note%d\">%s</a>" % (note.task.id, note.id, note.task.safe.name))

	def grantPrivilege(self, handler, user, priv):
		self.sendMessage(handler, user, 'priv', priv.name, priv.description)
