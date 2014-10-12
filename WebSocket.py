try:
	from tornado.websocket import WebSocketHandler
	import tornado.ioloop
	tornadoAvailable = True
except ImportError:
	class WebSocketHandler(object): pass
	tornadoAvailable = False

from json import loads as fromJS, dumps as toJS
from threading import Thread

from Log import console
import Settings
from utils import *

PORT = Settings.PORT + 1

handlers = []
channels = {}

class WebSocket:
	@staticmethod
	def available():
		return tornadoAvailable

	@staticmethod
	def start():
		if WebSocket.available():
			WSThread().start()

	@staticmethod
	def broadcast(data):
		for handler in handlers:
			handler.write_message(toJS(data))

	@staticmethod
	def sendChannel(channel, data):
		if not 'channel' in data:
			data['channel'] = channel
		for handler in channels.get(channel, []):
			handler.write_message(toJS(data))

class WSThread(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.name = 'websocket'
		self.daemon = True

	def run(self):
		app = tornado.web.Application([('/', WSHandler)])
		app.listen(PORT, '0.0.0.0')
		tornado.ioloop.IOLoop.instance().start()

class WSHandler(WebSocketHandler):
	def __init__(self, *args, **kw):
		super(WSHandler, self).__init__(*args, **kw)
		self.channels = set()

	def open(self):
		handlers.append(self)
		console('websocket', "Opened")

	def on_message(self, message):
		console('websocket', "Message received: %s" % message)
		try:
			data = fromJS(message)
		except:
			return

		if 'subscribe' in data and isinstance(data['subscribe'], list):
			addChannels = (set(data['subscribe']) - self.channels)
			self.channels |= addChannels
			for channel in addChannels:
				if channel not in channels:
					channels[channel] = set()
				channels[channel].add(self)

		if 'unsubscribe' in data and isinstance(data['unsubscribe'], list):
			rmChannels = (self.channels & set(data['unsubscribe']))
			self.channels -= rmChannels
			for channel in rmChannels:
				channels[channel].remove(self)
				if len(channels[channel]) == 0:
					del channels[channel]

	def on_close(self):
		for channel in self.channels:
			channels[channel].remove(self)
			if len(channels[channel]) == 0:
				del channels[channel]
		handlers.remove(self)
		console('websocket', "Closed")

verbs = {
	'status': "Status set",
	'name': "Renamed",
	'goal': "Goal set",
	'assigned': "Reassigned",
	'hours': "Hours updated",
}

from Event import EventHandler, addEventHandler
class ShareTaskChanges(EventHandler):
	def newTask(self, handler, task):
		WebSocket.sendChannel("backlog#%d" % task.sprint.id, {'type': 'new'}); #TODO

	def taskUpdate(self, handler, task, field, value):
		if field == 'assigned': # Convert set of Users to list of usernames
			value = [user.username for user in value]
		elif field == 'goal': # Convert Goal to goal ID
			value = value.id if value else 0
		description = ("%s by %s" % (verbs[field], task.creator)) if field in verbs else None
		WebSocket.sendChannel("backlog#%d" % task.sprint.id, {'type': 'update', 'id': task.id, 'revision': task.revision, 'field': field, 'value': value, 'description': description, 'creator': task.creator.username})
addEventHandler(ShareTaskChanges())
