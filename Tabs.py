import traceback
import sys

from rorn.HTTPHandler import handlers
from rorn.ResponseWriter import ResponseWriter

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
			print "<ul class=\"tabs\">"
			for tab in self.tabs:
				print "<li%s><a href=\"%s\">%s</a></li>" % (' class="active"' if tab['name'] == self.currentTab else '', (tab['path'] % fmt) if fmt else tab['path'], tab['displayName'])
			print "</ul>"
			# print "<div class=\"clear\"></div>"
			return w.done()
		except:
			w.done()
			raise
