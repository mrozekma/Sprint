import traceback
import sys
from HTTPHandler import handlers
from ResponseWriter import ResponseWriter

class Tabs:
	def __init__(self, defaultTab = None):
		self.tabs = []
		self.argsStore = {}
		self.defaultTab = defaultTab

	def tab(self, path, label, args = []):
		def wrap(f):
			handlers['get'][path] = f # Modifying handlers from here is kind of hackish
			self.tabs.append({'path': path, 'label': label, 'func': f.func_name, 'args': args})
			return f
		return wrap

	def args(self, **kw):
		self.argsStore = kw

	def __str__(self):
		def getCurrentTab():
			# -1: getCurrentTab
			# -2: __str__
			# -3: @tab
			_, _, fn, _ = traceback.extract_stack()[-3]
			for tab in self.tabs:
				if tab['func'] == fn:
					return tab['label']
			return self.defaultTab if self.defaultTab else self.tabs[0]['func']

		w = ResponseWriter()
		try:
			currentTab = getCurrentTab()
			print "<div class=\"tabs\">"
			for tab in self.tabs:
				url = "/%s" % tab['path']
				if len(tab['args']):
					sep = '?'
					for arg in tab['args']:
						if arg in self.argsStore:
							url += "%s%s=%s" % (sep, arg, self.argsStore[arg])
							sep = '&'
				print "<a href=\"%s\"%s>%s</a>" % (url, ' class="current"' if tab['label'] == currentTab else '', tab['label'])
			print "</div>"
			return w.done()
		except:
			w.done()
			raise
