import traceback
import sys
from HTTPHandler import handlers
from ResponseWriter import ResponseWriter

class Tabs:
	def __init__(self):
		self.tabs = []
		self.currentTab = None

	def __setitem__(self, name, value):
		if isinstance(value, tuple):
			displayName, path = value
		else:
			displayName = name.capitalize()
			path = value
		self.tabs.append({'name': name, 'displayName': displayName, 'path': path})

	def __lshift__(self, name):
		self.currentTab = name
		return self

	def __str__(self): return self % None
	def __mod__(self, fmt):
		w = ResponseWriter()
		try:
			print "<div class=\"tabs\">"
			for tab in self.tabs:
				print "<a href=\"%s\"%s>%s</a>" % ((tab['path'] % fmt) if fmt else tab['path'], ' class="current"' if tab['name'] == self.currentTab else '', tab['displayName'])
			print "</div>"
			return w.done()
		except:
			w.done()
			raise
