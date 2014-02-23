import re

from Event import EventHandler
from Note import Note
from User import User
from Message import Message
from Privilege import privs as privList

types = {
	'sprintMembership': ("Added to a sprint", "You were added to %s"),
	'taskAssigned': ("Assigned a task", "You were assigned the task %s"),
	'noteMention': ("Mentioned in a note", "You were mentioned in a note on %s"),
	'noteRelated': ("Note created", "A user posted a note on %s, %s"),
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
		for user in task.assigned:
			self.sendMessage(handler, user, 'taskAssigned', task.link())

	def taskUpdate(self, handler, task, field, value):
		if field == 'assigned':
			for user in task.assigned:
				self.sendMessage(handler, user, 'taskAssigned', task.link())

	def newNote(self, handler, note):
		usersContacted = []
		for username in re.findall("<a href=\"/users/([a-z0-9]+)\">", note.render()):
			user = User.load(username = username)
			if user and (user not in usersContacted):
				usersContacted.append(user)
				self.sendMessage(handler, user, 'noteMention', "<a href=\"/tasks/%d#note%d\">%s</a>" % (note.task.id, note.id, note.task.safe.name))

		for user in note.task.assigned:
			if user not in usersContacted:
				usersContacted.append(user)
				self.sendMessage(handler, user, 'noteRelated', "<a href=\"/tasks/%d#note%d\">%s</a>" % (note.task.id, note.id, note.task.safe.name), "a task assigned to you")

		for note in Note.loadAll(taskid = note.task.id):
			if note.user not in usersContacted:
				usersContacted.append(note.user)
				self.sendMessage(handler, note.user, 'noteRelated', "<a href=\"/tasks/%d#note%d\">%s</a>" % (note.task.id, note.id, note.task.safe.name), "a task you've also commented on")

	def grantPrivilege(self, handler, user, priv, isNewUser):
		if not isNewUser:
			self.sendMessage(handler, user, 'priv', priv, privList[priv])
