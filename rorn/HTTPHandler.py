from BaseHTTPServer import BaseHTTPRequestHandler
from inspect import getargspec
import re
import cgi
import sys
from sqlite3 import OperationalError
import traceback

from Session import Session, timestamp
from Box import ErrorBox
from code import showCode, highlightCode
from ResponseWriter import ResponseWriter
from utils import *

handlers = {'get': {}, 'post': {}}

@globalize
def get(index):
	def wrap(f):
		handlers['get'][index] = f
		return f
	return wrap

@globalize
def post(index):
	def wrap(f):
		handlers['post'][index] = f
		return f
	return wrap

def log(str, target = sys.stdout):
	print >> target, str

class HTTPHandler(BaseHTTPRequestHandler):
	def __init__(self, request, address, server):
		self.replacements = {}
		# self.leftMenu = LeftMenu()
		BaseHTTPRequestHandler.__init__(self, request, address, server)

	def buildResponse(self, method, data):
		log("Building response")
		self.contentType = 'text/html'

		path = self.path
		query = {}
		log("Original path: %s" % path)

		writer = ResponseWriter()

		request = {'path': [], 'wrappers': True, 'code': 200}
		try: # raise DoneRendering; starts here to catch self.error calls
			self.title(None)

			# Pull out get variables
			if '?' in path:
				path, queryStr = path.split('?', 1)
				parts = queryStr.split('&')
				query = dict(map(lambda x: x.split('=') if '=' in x else (x, True), parts))
				if len(parts) != len(query):
					self.error("Invalid request", "Query key collision")

			# Validate query keys (can't start with p_ to avoid collisions with post variables)
			for key in query:
				if key[:2] == 'p_':
					self.error("Invalid request", "Illegal query key: %s" % key)

			# Add p_ prefix to post variables
			if data:
				query.update(dict([('p_' + k, v) for (k, v) in data.iteritems()]))

			# Convert foo[bar] keys to maps (epic nesting!)
			oldQuery = query
			query = {}
			for key in oldQuery:
				match = re.match('(.*)\\[(.*)\\]', key)
				if match:
					name, realKey = match.groups()
					if re.match('\\d+', realKey):
						realKey = int(realKey)
					if name in query:
						if not isinstance(query[name], dict):
							self.error("Invalid request", "Name/map collision on query key: %s" % key)
					else:
						query[name] = {}
					query[name][realKey] = oldQuery[key]
				elif key in query:
					self.error("Invalid request", "Duplicate key in request: %s" % key)
				else:
					query[key] = oldQuery[key]

			log("Stripped path: %s" % path)

			assert path[0] == '/'
			path = path[1:]
			if len(path) and path[-1] == '/': path = path[:-1]
			path = path.split('/')

			# Try increasingly generic paths (e.g. if the path is /foo/bar/baz, try /foo/bar/baz, then /foo/bar, then /foo)
			log("Checking path fragments from %d to 0" % len(path))
			for i in range(len(path), 0, -1):
				slashPath = '/'.join(path[:i])
				log("Trying %s" % slashPath)
				try:
					if slashPath in handlers[method]:
						fn = handlers[method][slashPath]
					elif path[:i] != '':
						continue
					else:
						self.error("Invalid request", "No empty action handler")

					path = path[i-1:]
					break
				except AttributeError:
					pass
			else: # No path matched
				self.error("Invalid request", "Unknown action <b>%s</b>" % path[0])

			given = query.keys()
			expected, _, _, defaults = getargspec(fn)
			defaults = defaults or []

			givenS, expectedS = set(given), set(expected)
			log("expected = %s, defaults = %s" % (expected, defaults))
			requiredS = set(expected[:-len(defaults)] if defaults else expected)
			log("requiredS = %s" % requiredS)

			expectedS -= set(['self', 'handler', 'request'])
			requiredS -= set(['self', 'handler', 'request'])

			over = givenS - expectedS
			log("givenS (%s) - expectedS (%s) = %s" % (givenS, expectedS, over))
			if len(over):
				self.error("Invalid request", "Unexpected request argument%s: %s" % ('s' if len(over) > 1 else '', ', '.join(over)))

			under = requiredS - givenS
			log("requiredS (%s) - givenS (%s) = %s" % (requiredS, givenS, under))
			if len(under):
				self.error("Invalid request", "Missing expected request argument%s: %s" % ('s' if len(under) > 1 else '', ', '.join(under)))

			path = path[1:]
			request['path'] = path
			self.replace('{{path}}', '/'.join(path))

			fn(handler = self, request = request, **query)
		except DoneRendering: pass
		except OperationalError, e:
			writer.clear()
			self.title('Database Error')
			self.error('Database Error', e.message, False)
		except Redirect: raise
		except:
			writer.clear()
			self.title('Unhandled Error')

			writer2 = ResponseWriter()
			lpad = len(basePath()) + 1
			print "<br>"
			print "<div class=\"code_default light\" style=\"padding: 4px\">"
			for filename, line, fn, stmt in traceback.extract_tb(sys.exc_info()[2]):
				print "<div class=\"code_header\">%s:%s(%d)</div>" % (filename[lpad:], fn, line)
				print "<div style=\"padding: 0px 0px 10px 20px\">"
				print highlightCode(stmt)
				print "</div>"
			print "</div>"
			# traceback.print_tb(sys.exc_info()[2], None, writer2)
			ex = writer2.done()

			self.error('Unhandled Error', "<b>%s</b><br>%s" % (sys.exc_info()[1], ex), False)
			showCode(filename, line, 5)

		self.response = writer.done()

		if request['wrappers']:
			self.wrapContent(request)

		# self.leftMenu.clear()

		for (fromStr, toStr, count) in self.replacements.values():
			print "%s -> %s" % (fromStr, toStr)
			self.response = self.response.replace(fromStr, toStr, count)

		return request

	def replace(self, fromStr, toStr, count = -1):
		self.replacements[fromStr] = (fromStr, toStr, count)

	def title(self, title):
		self.replace('$title$', "%s - Sprint" % title if title else "Sprint", 1)
		self.replace('$bodytitle$', title if title else "Sprint", 1)

	def sendHead(self, code = 200, additionalHeaders = {}):
		headers = {
			'Content-type': self.contentType,
			'Content-Length': str(len(self.response)),
			'Last-Modified': self.date_time_string(),
			'Set-Cookie': 'session=%s; expires=%s; path=/' % (self.session.key, timestamp())
			}

		headers.update(additionalHeaders)

		self.send_response(code)
		for name, value in headers.iteritems():
			self.send_header(name, value)
		self.end_headers()

	def do_HEAD(self, method = 'get', data = None):
		self.session = Session.load(Session.determineKey(self))
		self.hackify() #TODO Remove

		try:
			request = self.buildResponse(method, data)
			self.sendHead(request['code'])
		except Redirect as r:
			self.response = ''
			self.sendHead(302, {'Location': r.target})

	def do_GET(self):
		self.do_HEAD('get')
		self.wfile.write(self.response)

	def do_POST(self):
		form = cgi.FieldStorage(fp = self.rfile, headers = self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}, keep_blank_values = True)
		data = {}
		for k in form:
			if k[-2:] == '[]':
				data[k[:-2]] = form.getlist(k)
			elif type(form[k]) is list:
				self.session = Session.load(Session.determineKey(self))
				self.hackify() #TODO Remove
				self.contentType = 'text/html'
				self.response = "Multiple values for POST key: %s" % k
				self.sendHead(200)
				self.wfile.write(self.response)
				return
			else:
				print form[k]
				data[k] = form[k].value
		# data = dict([(k, map(lambda v: v.value, form[k]) if type(form[k]) is list else form[k].value) for k in form])
		# print "DEBUG: %s" % self.rfile
		self.do_HEAD('post', data)
		self.wfile.write(self.response)

	def error(self, title, text, isDone = True):
		print ErrorBox(title, text)
		if isDone:
			done()
