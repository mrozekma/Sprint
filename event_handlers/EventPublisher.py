from redis import StrictRedis
import re

from Event import EventHandler
from User import User

def formatChannelName(projectName):
	return re.sub('\W+', '_', projectName.lower())

class EventPublisher(EventHandler):
	def __init__(self, host, port):
		self.conn = StrictRedis(host = host, port = port)
		self.conn.pubsub()

	def publish(self, sprint, message):
		channel = formatChannelName(sprint.project.name)
		try:
			self.conn.publish(channel, message)
		except Exception:
			pass

	# EventHandler interface

	def newSprint(self, handler, sprint):
		self.publish(sprint, "%s created a new sprint: %s" % (handler.session['user'].username, sprint.name))

	def sprintInfoUpdate(self, handler, sprint, changes):
		import sys
		if changes['end']:
			self.publish(sprint, "%s extended the sprint; it now ends %s" % (handler.session['user'].username, changes['end'].strftime('%A, %B %d')))
		if changes['addMembers']:
			if len(changes['addMembers']) == 1:
				self.publish(sprint, "%s added %s to the sprint" % (handler.session['user'].username, changes['addMembers'][0].username))
			elif len(changes['addMembers']) == 2:
				self.publish(sprint, "%s added %s and %s to the sprint" % (handler.session['user'].username, changes['addMembers'][0].username, changes['addMembers'][1].username))
			else:
				self.publish(sprint, "%s added %sand %s to the sprint" % (handler.session['user'].username, ''.join(user.username + ', ' for user in changes['addMembers'][:-1]), changes['addMembers'][-1].username))

	def sprintAvailUpdate(self, handler, sprint):
		self.publish(sprint, "%s updated sprint member availability" % handler.session['user'].username)

	def newTask(self, handler, task):
		self.publish(task.sprint, "%s created a new task: %s (assigned to %s, %d %s)" % (handler.session['user'].username, task.name, task.assigned.username, task.hours, 'hour' if task.hours == 1 else 'hours'))

	def taskUpdate(self, handler, task, field, value):
		textValue = value
		if isinstance(textValue, User):
			textValue = textValue.username
		#TODO Pull info from the History class
		self.publish(task.sprint, "%s updated a task: %s" % (handler.session['user'].username, task.name))

	def newNote(self, handler, note):
		self.publish(note.task.sprint, "%s created a new note on: %s" % (handler.session['user'].username, note.task.name))
