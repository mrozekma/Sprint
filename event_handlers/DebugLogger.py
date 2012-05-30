import sys

from Event import EventHandler

class DebugLogger(EventHandler):
	def default(self, type, handler, *args):
		sys.__stdout__.write("DebugLogger: %s: %s\n" % (type, '\t'.join(map(str, args))))
