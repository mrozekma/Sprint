from ResponseWriter import ResponseWriter
from utils import *

# colorSchemes = {
	# 'black':  {'solid': '#000',    'contrast': '#FFF', 'tint': '#F2DEE8', 'border': '#630'},
	# 'red':    {'solid': '#F00',    'contrast': '#000', 'tint': '#FCC',    'border': '#C00'},
	# 'yellow': {'solid': '#FF0',    'contrast': '#000', 'tint': '#FFC',    'border': '#FC0'},
	# 'green':  {'solid': '#0F0',    'contrast': '#000', 'tint': '#CFC',    'border': '#090'},
	# 'blue':   {'solid': '#0152A1', 'contrast': '#FFF', 'tint': '#DEE',    'border': '#00C'},
	# }

class Box:
	def __init__(self, title, text, scheme = 'black', id = None, tinted = False, rounded = True):
		self.title = title
		self.text = text
		self.scheme = scheme
		self.id = id
		self.tinted = tinted
		self.rounded = rounded

	def extraClasses(self):
		return []

	def __str__(self):
		w = ResponseWriter()

		classes = []
		classes.append('tint' if self.tinted else 'box')
		if self.rounded:
			classes.append('rounded')
		if self.scheme:
			classes.append(self.scheme)
		classes += self.extraClasses()

		print "<div",
		if self.id:
			print "id=\"%s\"" % self.id,
		print "class=\"%s\">" % ' '.join(classes)
		if self.title:
			print "<div class=\"title\">%s</div>" % self.title
		print "<span class=\"boxBody\">%s</span>" % self.text
		print "</div>"

		return w.done()

class TintedBox(Box):
	def __init__(self, text, scheme = 'black', id = None, centered = True):
		Box.__init__(self, None, text, id = id, scheme = scheme, tinted = True)
		self.centered = centered

	def extraClasses(self):
		return ['center'] if self.centered else []

##########################

class ErrorBox(Box):
	def __init__(self, title, text):
		Box.__init__(self, title, text, scheme = 'red')

	def extraClasses(self):
		return ['error']

	@staticmethod
	def die(*args):
		print ErrorBox(*args)
		done()

class WarningBox(Box):
	def __init__(self, title, text):
		Box.__init__(self, title, text, scheme = 'yellow')

	def extraClasses(self):
		return ['warning']

class SuccessBox(Box):
	def __init__(self, title, text):
		Box.__init__(self, title, text, scheme = 'green')

	def extraClasses(self):
		return ['success']

##########################

class LoginBox(Box):
	def __init__(self):
		Box.__init__(self, 'Login', self.text(), scheme = 'blue')

	def extraClasses(self):
		return ['login']

	def text(self):
		writer = ResponseWriter()

		print "<form method=\"post\" action=\"/login\">"
		print "<table style=\"margin-left: 30px;\">"
		print "<tr><td class=\"left\">Username:</td><td class=\"right\"><input type=\"text\" id=\"defaultfocus\" name=\"username\" class=\"username\"></td></tr>"
		print "<tr><td class=\"left\">Password:</td><td class=\"right\"><input type=\"password\" name=\"password\" class=\"password\"></td></tr>"
		print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\"><button type=\"submit\">Login</button></td></tr>"
		print "</table>"
		print "</form>"

		return writer.done()

class CollapsibleBox(Box):
	def __init__(self, title, text, expanded = False, id = None):
		Box.__init__(self, title, text, scheme = '', id = id)
		self.expanded = expanded

	def extraClasses(self):
		return ['collapsible'] + (['expanded'] if self.expanded else [])
