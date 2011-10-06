from ResponseWriter import ResponseWriter
from utils import *

class Box:
	def __init__(self, title, text = None, id = None, clr = 'black'):
		if text:
			self.title = title
			self.text = text
		else:
			self.title = None
			self.text = title
		self.id = id
		self.clr = clr

	def __str__(self):
		writer = ResponseWriter()
		print "<div",
		if self.id:
			print "id=\"%s\"" % self.id,
		print "class=\"box %s rounded\">" % self.clr
		if self.title:
			print "<div class=\"title\">%s</div>" % self.title
		print "<span class=\"boxBody\">"
		print self.text
		print "</span>"
		print "</div>"
		return writer.done()

class AlertBox:
	def __init__(self, title, text = None, id = None):
		if text:
			self.title = title
			self.text = text
		else:
			self.title = None
			self.text = title
		self.id = id

	def getClasses(self):
		return ['alert-message']

	def __str__(self):
		writer = ResponseWriter()
		print "<div",
		if self.id:
			print "id=\"%s\"" % self.id,
		print "class=\"%s\">" % ' '.join(self.getClasses())
		print "<a class=\"close\" href=\"#\">x</a>"
		print "<span>"
		if self.title:
			print "<strong>%s</strong>: " % self.title
		print self.text
		print "</span>"
		print "</div>"
		return writer.done()

class InfoBox(AlertBox):
	def __init__(self, *args, **kargs):
		AlertBox.__init__(self, *args, **kargs)

	def getClasses(self):
		return AlertBox.getClasses(self) + ['info']

class SuccessBox(AlertBox):
	def __init__(self, *args, **kargs):
		AlertBox.__init__(self, *args, **kargs)

	def getClasses(self):
		return AlertBox.getClasses(self) + ['success']

class WarningBox(AlertBox):
	def __init__(self, *args, **kargs):
		AlertBox.__init__(self, *args, **kargs)

	def getClasses(self):
		return AlertBox.getClasses(self) + ['warning']

class ErrorBox(AlertBox):
	def __init__(self, *args, **kargs):
		AlertBox.__init__(self, *args, **kargs)

	def getClasses(self):
		return AlertBox.getClasses(self) + ['error']

	@staticmethod
	def die(*args):
		print ErrorBox(*args)
		done()

##########################

class LoginBox:
	def __str__(self):
		writer = ResponseWriter()
		print "<div class=\"box blue rounded login\">"
		print "<div class=\"title\">Login</div>"
		print "<span class=\"boxBody\">"
		print "<form method=\"post\" action=\"/login\">"
		print "<table style=\"margin-left: 30px;\">"
		print "<tr><td class=\"left\">Username:</td><td class=\"right\"><input type=\"text\" class=\"defaultfocus\" name=\"username\" class=\"username\"></td></tr>"
		print "<tr><td class=\"left\">Password:</td><td class=\"right\"><input type=\"password\" name=\"password\" class=\"password\"></td></tr>"
		print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\"><button type=\"submit\">Login</button></td></tr>"
		print "</table>"
		print "</form>"
		print "</span>"
		print "</div>"
		return writer.done()

class CollapsibleBox:
	def __init__(self, title, text, expanded = False, id = None):
		self.title = title
		self.text = text
		self.expanded = expanded
		self.id = id

	def __str__(self):
		writer = ResponseWriter()
		print "<div",
		if self.id:
			print "id=\"%s\"" % self.id,
		print "class=\"box rounded collapsible",
		if self.expanded:
			print "expanded",
		print "\">"
		if self.title:
			print "<div class=\"title\">%s</div>" % self.title
		print "<span class=\"boxBody\">"
		print self.text
		print "</span>"
		print "</div>"
		return writer.done()
