import re
from json import dumps as toJS

from Event import EventHandler
from User import User
from Log import console

try:
	from redis import StrictRedis
except ImportError:
	StrictRedis = None

class EventPublisher(EventHandler):
	def __init__(self, host, port):
		if StrictRedis:
			self.conn = StrictRedis(host = host, port = port)
			self.conn.pubsub()
		else:
			console('events', 'Unable to load redis python module; event publishing disabled')
			self.conn = None

	def publish(self, handler, sprint, type, **extraArgs):
		data = {'type': type, 'user': handler.session['user'].username}
		data.update(extraArgs)

		channel = EventPublisher.formatChannelName(sprint.project.name)
		try:
			self.conn.publish(channel, toJS(data))
		except Exception:
			pass

	@staticmethod
	def formatChannelName(projectName):
		return re.sub('\W+', '_', projectName.lower())

	# EventHandler interface

	def newSprint(self, handler, sprint):
		self.publish(handler, sprint, 'newSprint', name = sprint.name)

	def sprintInfoUpdate(self, handler, sprint, changes):
		import sys
		if changes['end']:
			self.publish(handler, sprint, 'sprintExtend', end = changes['end'].strftime('%A, %B %d'))
		if changes['addMembers']:
			self.publish(handler, sprint, 'addMembers', usernames = [user.username for user in changes['addMembers']])

	def sprintAvailUpdate(self, handler, sprint):
		self.publish(handler, sprint, 'sprintAvailUpdate')

	def newTask(self, handler, task):
		self.publish(handler, task.sprint, 'newTask', name = task.name, assigned = task.assigned.username, hours = task.hours)

	def taskUpdate(self, handler, task, field, value):
		if isinstance(value, User):
			value = value.username
		self.publish(handler, task.sprint, 'taskUpdate', id = task.id, name = task.name, field = field, value = value)

	def newNote(self, handler, note):
		self.publish(handler, note.task.sprint, 'newNote', taskName = note.task.name)
