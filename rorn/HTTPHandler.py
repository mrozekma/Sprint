from BaseHTTPServer import BaseHTTPRequestHandler
from inspect import getargspec
from collections import defaultdict
import re
import cgi
import sys
from urllib import unquote
from sqlite3 import OperationalError
import traceback

from Session import Session, timestamp
from Box import Box, ErrorBox
from code import showCode
from ResponseWriter import ResponseWriter
from FrameworkException import FrameworkException
from utils import *

handlers = {'get': {}, 'post': {}}

@globalize
def get(index, **kw):
	def wrap(f):
		kw['fn'] = f
		handlers['get'][re.compile("^%s$" % index)] = kw
		return f
	return wrap

@globalize
def post(index, **kw):
	def wrap(f):
		kw['fn'] = f
		handlers['post'][re.compile("^%s$" % index)] = kw
		return f
	return wrap

class HTTPHandler(BaseHTTPRequestHandler, object):
	def __init__(self, request, address, server):
		self.session = None
		self.replacements = {}
		self.title(None)
		self.contentType = 'text/html'
		self.forceDownload = False
		self.responseCode = 200
		BaseHTTPRequestHandler.__init__(self, request, address, server)

	def buildResponse(self, method, postData):
		self.handler = None
		self.method = method
		writer = ResponseWriter()

		try: # raise DoneRendering; starts here to catch self.error calls
			path = self.path
			query = {}
			queryStr = None

			# Add GET params to query
			if '?' in path:
				path, queryStr = path.split('?', 1)
				if queryStr != '':
					query = self.parseQueryString(queryStr)

			# Check GET params for a p_ prefix collision
			for key in query:
				if key[:2] == 'p_':
					self.error("Invalid request", "Illegal query key: %s" % key)

			# Add POST params to query with a p_ prefix
			query.update(dict([('p_' + k, v) for (k, v) in postData.iteritems()]))

			assert path[0] == '/'
			path = path[1:]
			if len(path) and path[-1] == '/': path = path[:-1]
			path = unquote(path)
			for pattern in handlers[method]:
				match = pattern.match(path)
				if match:
					self.handler = handlers[method][pattern]
					for k, v in match.groupdict().items():
						if k in query:
							self.error("Invalid request", "Duplicate key in request: %s" % k)
						query[k] = v
					break

			if not self.handler:
				self.error("Invalid request", "Unknown %s action <b>%s</b>" % (method.upper(), path if path != '' else "No empty action handler"))

			given = query.keys()
			expected, _, _, defaults = getargspec(self.handler['fn'])
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

			self.path = '/' + path
			self.replace('{{path}}', path)
			self.replace('{{get-args}}', queryStr or '')

			self.invokeHandler(self.handler, query)
		except DoneRendering: pass
		except OperationalError, e:
			writer.clear()
			self.title('Database Error')
			self.error('Database Error', e.message, False)
		except Redirect: raise
		except:
			writer.start()
			self.unhandledError()

		self.response = writer.done()
		self.requestDone()
		# self.leftMenu.clear()

		for (fromStr, toStr, count) in self.replacements.values():
			self.response = self.response.replace(fromStr, toStr, count)

	def parseQueryString(self, query):
		# Adapted from urlparse.parse_qsl
		items = []
		for arg in query.split('&'):
			if not arg: continue
			parts = arg.split('=', 1)
			items.append([unquote(part.replace('+', ' ')) for part in parts])
		return self.parseQueryItems(items)

	def parseQueryItems(self, items):
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

	def sendHead(self, additionalHeaders = {}, includeCookie = True):
		headers = {
			'Content-type': self.contentType,
			'Content-Length': str(len(self.response)),
			'Last-Modified': self.date_time_string(),
		}
		if self.session:
			headers['Set-Cookie'] = 'session=%s; expires=%s; path=/' % (self.session.key, timestamp())
		if self.forceDownload:
			headers['Content-disposition'] = "attachment; filename=%s" % self.forceDownload

		headers.update(additionalHeaders)

		self.send_response(self.responseCode)
		for name, value in headers.iteritems():
			self.send_header(name, value)
		self.end_headers()

	def handle_one_request(self):
		try:
			BaseHTTPRequestHandler.handle_one_request(self)
		except:
			self.response = str(FrameworkException(sys.exc_info()))
			self.sendHead(includeCookie = False)
			self.wfile.write(self.response)
			raise

	def do_HEAD(self, method = 'get', postData = {}):
		self.session = Session.load(Session.determineKey(self))
		self.processingRequest()

		try:
			self.buildResponse(method, postData)
			self.sendHead()
		except Redirect as r:
			self.responseCode = 302
			self.response = ''
			self.sendHead(additionalHeaders = {'Location': r.target})

	def do_GET(self):
		self.do_HEAD('get')
		self.wfile.write(self.response)

	def do_POST(self):
		form = cgi.FieldStorage(fp = self.rfile, headers = self.headers, environ = {'REQUEST_METHOD': 'POST'}, keep_blank_values = True)
		data = {}
		try:
			items = []
			for k in form:
				if type(form[k]) is list:
					items += [(k, v.value) for v in form[k]]
				else:
					items.append((k, form[k].value))
			data = self.parseQueryItems(items)
		except DoneRendering: pass
		except TypeError: pass # Happens with empty forms
		self.do_HEAD('post', data)
		self.wfile.write(self.response)

	def error(self, title, text, isDone = True):
		print ErrorBox(title, text)
		if isDone:
			done()

	def title(self, title): pass

	def processingRequest(self): pass

	def invokeHandler(self, handler, query):
		handler['fn'](handler = self, **query)

	def requestDone(self): pass

	def unhandledError(self):
		self.title('Unhandled Error')
		print Box('Unhandled Error', formatException(), clr = 'red')
		filename, line, fn, stmt = traceback.extract_tb(sys.exc_info()[2])[-1]
		showCode(filename, line, 5)
