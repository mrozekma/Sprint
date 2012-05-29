from BaseHTTPServer import BaseHTTPRequestHandler
from inspect import getargspec
from collections import defaultdict
import re
import cgi
import sys
import urllib
from sqlite3 import OperationalError
import traceback

from Session import Session, timestamp
from Box import Box, ErrorBox
from code import showCode, highlightCode
from ResponseWriter import ResponseWriter
from FrameworkException import FrameworkException
from utils import *

handlers = {'get': {}, 'post': {}}

@globalize
def get(index):
	def wrap(f):
		handlers['get'][re.compile("^%s$" % index)] = f
		return f
	return wrap

@globalize
def post(index):
	def wrap(f):
		handlers['post'][re.compile("^%s$" % index)] = f
		return f
	return wrap

class HTTPHandler(BaseHTTPRequestHandler):
	def __init__(self, request, address, server):
		self.session = None
		self.replacements = {}
		# self.leftMenu = LeftMenu()
		BaseHTTPRequestHandler.__init__(self, request, address, server)

	def buildResponse(self, method, postData):
		writer = ResponseWriter()
		request = self.makeRequest()
		request['method'] = method

		try: # raise DoneRendering; starts here to catch self.error calls
			path = self.path
			query = {}

			# Add GET params to query
			if '?' in path:
				path, queryStr = path.split('?', 1)
				queryStr = urllib.unquote(queryStr)
				query = self.parseQueryString([item.split('=', 1) for item in queryStr.split('&')])

			# Check GET params for a p_ prefix collision
			for key in query:
				if key[:2] == 'p_':
					self.error("Invalid request", "Illegal query key: %s" % key)

			# Add POST params to query with a p_ prefix
			query.update(dict([('p_' + k, v) for (k, v) in postData.iteritems()]))

			self.title(None)
			assert path[0] == '/'
			path = path[1:]
			if len(path) and path[-1] == '/': path = path[:-1]
			fn = None
			for pattern in handlers[method]:
				match = pattern.match(path)
				if match:
					fn = handlers[method][pattern]
					for k, v in match.groupdict().items():
						if k in query:
							self.error("Invalid request", "Duplicate key in request: %s" % k)
						query[k] = v
					break

			if not fn:
				self.error("Invalid request", "Unknown %s action <b>%s</b>" % (method.upper(), path if path != '' else "No empty action handler"))

			given = query.keys()
			expected, _, _, defaults = getargspec(fn)
			defaults = defaults or []

			givenS, expectedS = set(given), set(expected)
			requiredS = set(expected[:-len(defaults)] if defaults else expected)

			expectedS -= set(['self', 'handler', 'request'])
			requiredS -= set(['self', 'handler', 'request'])

			over = givenS - expectedS
			if len(over):
				self.error("Invalid request", "Unexpected request argument%s: %s" % ('s' if len(over) > 1 else '', ', '.join(over)))

			under = requiredS - givenS
			if len(under):
				self.error("Invalid request", "Missing expected request argument%s: %s" % ('s' if len(under) > 1 else '', ', '.join(under)))

			request['path'] = '/' + path
			self.replace('{{path}}', path)

			self.invokeHandler(fn, request, query)
		except DoneRendering: pass
		except OperationalError, e:
			writer.clear()
			self.title('Database Error')
			self.error('Database Error', e.message, False)
		except Redirect: raise
		except:
			writer.start()
			self.title('Unhandled Error')

			writer2 = ResponseWriter()
			base = basePath()
			lpad = len(base) + 1
			print "<br>"
			print "<div class=\"code_default light\" style=\"padding: 4px\">"
			for filename, line, fn, stmt in traceback.extract_tb(sys.exc_info()[2]):
				print "<div class=\"code_header\">%s:%s(%d)</div>" % (filename[lpad:] if filename.startswith(base) else "<i>%s</i>" % filename.split('/')[-1], fn, line)
				print "<div style=\"padding: 0px 0px 10px 20px\">"
				print highlightCode(stmt)
				print "</div>"
			print "</div>"
			# traceback.print_tb(sys.exc_info()[2], None, writer2)
			ex = writer2.done()

			print Box('Unhandled Error', "<b>%s: %s</b><br>%s" % (sys.exc_info()[0].__name__, sys.exc_info()[1], ex), clr = 'red')
			showCode(filename, line, 5)

		self.response = writer.done()
		self.requestDone(request)
		# self.leftMenu.clear()

		for (fromStr, toStr, count) in self.replacements.values():
			self.response = self.response.replace(fromStr, toStr, count)

		return request

	def parseQueryString(self, items):
		query = {}
		for i in items:
			k, v = (i[0], True) if len(i) == 1 else i

			match = re.match(('([^[]*)(\\[.*\\])'), k)
			if match:
				key, subKeys = match.groups()
				subKeys = re.findall('\\[([^\\]]*)\\]', subKeys)

				if key in query:
					if not isinstance(query[key], list if subKeys == [''] else dict):
						self.error("Invalid request", "Type conflict on query key %s" % key)
				else:
					query[key] = [] if subKeys == [''] else {}

				base = query[key]
				for thisSubKey in subKeys[:-2]:
					if thisSubKey in base:
						if not isinstance(base[thisSubKey], dict):
							self.error("Invalid request", "Type conflict on query key %s, subkey %s" % (key, thisSubKey))
					else:
						base[thisSubKey] = {}
					base = base[thisSubKey]

				type = list if subKeys[-1] == '' else dict
				if len(subKeys) >= 2:
					if subKeys[-2] in base:
						if not isinstance(base[subKeys[-2]], type):
							self.error("Invalid request", "Type conflict on query key %s, subkey %s" % (key, subKeys[-2]))
					else:
						base[subKeys[-2]] = type()
					base = base[subKeys[-2]]

				if type == list:
					base.append(v)
				else:
					if subKeys[-1] in base:
						self.error("Invalid request", "Collision on query key %s, subkey %s" % (key, subKeys[-1]))
					base[subKeys[-1]] = v
			else:
				if k in query:
					self.error("Invalid request", "Collision on query key %s" % k)
				query[k] = v

		return query

	def replace(self, fromStr, toStr, count = -1):
		self.replacements[fromStr] = (fromStr, toStr, count)

	def title(self, title):
		self.replace('$title$', "%s - Sprint" % title if title else "Sprint", 1)
		self.replace('$bodytitle$', title if title else "Sprint", 1)

	def sendHead(self, code, contentType = 'application/octet-stream', forceDownload = False, additionalHeaders = {}, includeCookie = True):
		headers = {
			'Content-type': contentType,
			'Content-Length': str(len(self.response)),
			'Last-Modified': self.date_time_string(),
		}
		if self.session:
			headers['Set-Cookie'] = 'session=%s; expires=%s; path=/' % (self.session.key, timestamp())
		if forceDownload:
			headers['Content-disposition'] = "attachment; filename=%s" % forceDownload

		headers.update(additionalHeaders)

		self.send_response(code)
		for name, value in headers.iteritems():
			self.send_header(name, value)
		self.end_headers()

	def handle_one_request(self):
		try:
			BaseHTTPRequestHandler.handle_one_request(self)
		except:
			self.response = str(FrameworkException(sys.exc_info()))
			self.sendHead(200, 'text/html', False)
			self.wfile.write(self.response)
			raise

	def do_HEAD(self, method = 'get', postData = {}):
		self.session = Session.load(Session.determineKey(self))
		self.processingRequest()

		try:
			request = self.buildResponse(method, postData)
			self.sendHead(request['code'], request['contentType'], request['forceDownload'])
		except Redirect as r:
			self.response = ''
			self.sendHead(302, additionalHeaders = {'Location': r.target})

	def do_GET(self):
		self.do_HEAD('get')
		self.wfile.write(self.response)

	def do_POST(self):
		form = cgi.FieldStorage(fp = self.rfile, headers = self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}, keep_blank_values = True)
		data = {}
		try:
			items = []
			for k in form:
				if type(form[k]) is list:
					items += [(k, v.value) for v in form[k]]
				else:
					items.append((k, form[k].value))
			data = self.parseQueryString(items)
		except TypeError: pass # Happens with empty forms
		self.do_HEAD('post', data)
		self.wfile.write(self.response)

	def error(self, title, text, isDone = True):
		print ErrorBox(title, text)
		if isDone:
			done()

	def processingRequest(self): pass

	def makeRequest(self):
		return {
			'path': [],
			'contentType': 'text/html',
			'forceDownload': False,
			'code': 200
		}

	def invokeHandler(self, fn, request, query):
		fn(handler = self, request = request, **query)

	def requestDone(self, request): pass
