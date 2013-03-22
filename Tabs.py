import traceback
import sys

from rorn.HTTPHandler import handlers
from rorn.ResponseWriter import ResponseWriter

from collections import OrderedDict

class Tab:
	def __init__(self, base, name, path = None, displayName = None, num = None):
		self.base = base
		self.name = name
		self.displayName = displayName
		self.path = path
		self.num = num

	def getDisplayName(self):
		return self.displayName or self.name.capitalize()

	def getPath(self, fmt = None):
		if self.path is None:
			return '#'
		elif fmt is None:
			return self.path
		else:
			return self.path % fmt

	def out(self, fmt, isActive):
		print "<li%s><a href=\"%s\">" % (' class="active"' if isActive else '', self.getPath(fmt))
		print self.getDisplayName()
		if self.num is not None:
			print "<div class=\"num\">%d</div>" % self.num
		print "</a></li>"

	def outGroup(self, fmt, activeTab, members):
		cls = ['dropdown']
		if activeTab is not None and activeTab.base == self.name:
			cls.append('active')
		print "<li class=\"%s\"><a class=\"dropdown-toggle\" data-toggle=\"dropdown\" href=\"#\">" % ' '.join(cls)
		print self.getDisplayName()
		num = self.num
		if num is None:
			subNums = sum(tab.num or 0 for tab in members.values())
			if subNums > 0:
				num = subNums
		if num is not None:
			print "<div class=\"num\">%d</div>" % num
		print "<b class=\"caret\"></b>"
		print "</a>"
		print "<ul class=\"dropdown-menu\">"
		for tab in members.values():
			tab.out(fmt, activeTab == tab)
		print "</ul>"
		print "</li>"

def parseName(name):
	if isinstance(name, tuple):
		return name
	else:
		return '', name

class Tabs():
	def __init__(self):
		self.tabs = {'': OrderedDict()}

	def __getitem__(self, name):
		base, name = parseName(name)
		return self.tabs[base][name]

	def __setitem__(self, name, path):
		self.add(name, path = path)

	def __contains__(self, name):
		base, name = parseName(name)
		return base in self.tabs and name in self.tabs[base]

	def __iter__(self):
		for k in self.keys():
			yield k

	def group(self, name):
		return self.tabs[name] if name in self.tabs else None

	def add(self, name, path = None, displayName = None, num = None):
		base, name = parseName(name)
		if base not in self.tabs:
			self.add(('', base))
			self.tabs[base] = OrderedDict()
		if name:
			self.tabs[base][name] = Tab(base, name, path, displayName, num)

	def keys(self):
		return self.tabs.keys()

	def values(self):
		return self.tabs.values()

	def format(self, key, value = None):
		return TabsView(self).format(key, value)

	def where(self, name, path = None, displayName = None):
		return TabsView(self).where(name, path, displayName)

	def __str__(self):
		return str(TabsView(self))

class TabsView:
	def __init__(self, tabs):
		self.tabs = tabs
		self.fmt = None
		self.whr = None

	def __getitem__(self, name): return self.tabs[name]
	def __setitem__(self, name, path): self.tabs[name] = path
	def __contains__(self, name): return name in self.tabs
	def add(self, name, path = None, displayName = None, num = None): self.tabs.add(name, path, displayName, num)
	def keys(self): return self.tabs.keys()
	def values(self): return self.tabs.values()

	def format(self, key, value = None):
		self.fmt = key if value is None else {key: value}
		return self

	def where(self, name, path = None, displayName = None, num = None):
		base, name = parseName(name)
		if (base, name) in self.tabs:
			self.whr = self.tabs[base, name]
		else:
			self.whr = Tab(base, name, path, displayName, num)
		return self

	def __str__(self):
		w = ResponseWriter()
		try:
			print "<ul class=\"nav nav-tabs\">"
			for tab in self.tabs.group('').values():
				if self.tabs.group(tab.name):
					tab.outGroup(self.fmt, self.whr, self.tabs.group(tab.name))
				else:
					tab.out(self.fmt, self.whr == tab)
			# The current tab isn't in the list
			if self.whr is not None and (self.whr.base, self.whr.name) not in self.tabs:
				self.whr.out(self.fmt, True)
			print "</ul>"
			print "<div class=\"clear\"></div>"
			return w.done()
		except:
			w.done()
			raise
