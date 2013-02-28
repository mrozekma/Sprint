from json import dumps as toJS, loads as fromJS
import re

class Index(object):
	def __init__(self, name, chartOrParent):
		self._name = name
		if isinstance(chartOrParent, Index):
			self._parent = chartOrParent
			self._chart = self._parent._chart
		else:
			self._parent = None
			self._chart = chartOrParent

	def get(self):
		path = []
		next = self
		while next:
			path.append(next)
			next = next._parent
		val = self._chart._m
		path.reverse()
		for node in path:
			val = val[node._name]
		return val

	def __getitem__(self, k):
		return Index(k, self)

	def __setitem__(self, k, v):
		self._chart.set(self, k, v)

	def __getattr__(self, k):
		try:
			return object.__getattr__(self, k)
		except AttributeError:
			return self[k]

	def __setattr__(self, k, v):
		if k[0] == '_':
			object.__setattr__(self, k, v)
		else:
			self[k] = v

	def __enter__(self): return self
	def __exit__(self, type, value, traceback): pass

	def __str__(self):
		return "%s > %s" % (self._parent, self._name) if self._parent else self._name

	def createKeys(self):
		m = self._parent.createKeys() if self._parent else self._chart._m
		try:
			m[self._name]
		except: # If it doesn't exist ("in" checks fail for types like lists)
			m[self._name] = {}
		return m[self._name]

class Chart(object):
	def __init__(self, placeholder = None):
		self._m = {}
		if placeholder:
			self.chart.renderTo = placeholder

	def __getitem__(self, k):
		return Index(k, self)

	def __setitem__(self, k, v):
		self._m[k] = v

	def __getattr__(self, k):
		try:
			return object.__getattr__(self, k)
		except AttributeError:
			return self[k]

	def __setattr__(self, k, v):
		if k[0] == '_':
			object.__setattr__(self, k, v)
		else:
			self[k] = v

	def __enter__(self): return self
	def __exit__(self, type, value, traceback): pass

	def set(self, index, k, v):
		m = index.createKeys()
		if isinstance(v, dict):
			m[k].update(v)
		else:
			m[k] = v

	@staticmethod
	def include():
		print "<script type=\"text/javascript\" src=\"/static/highcharts/js/highcharts.js\"></script>"
		print "<script type=\"text/javascript\" src=\"/static/highcharts/highstock/js/highstock.js\"></script>"

	def js(self):
		print "<script type=\"text/javascript\">"
		print "$(document).ready(function() {",
		print "new Highcharts.Chart(",
		print re.sub('"(?:\\\\n)*function\(\) {(.*)}(?:\\\\n)*"', lambda match: fromJS(match.group(0)), toJS(self._m, sort_keys = True, indent = 4)),
		print ");",
		print "});"
		print "</script>"

	def placeholder(self):
		print "<div id=\"%s\"></div>" % self._m['chart']['renderTo']
