from Event import EventHandler

class ErrorCounter(EventHandler):
	def __init__(self):
		self.count = 0

	def getCount(self):
		return self.count

	def reset(self):
		self.count = 0

	# EventHandler.error
	def error(self, handler, description):
		self.count += 1

errorCounter = ErrorCounter()
