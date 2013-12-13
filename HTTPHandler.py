from datetime import datetime
from os.path import isfile

from wrappers import header, footer
from DB import db
from User import User
from Event import Event
from HTTPServer import server
from Log import LogEntry, console
from LoadValues import bricked
from utils import *

from rorn.HTTPHandler import HTTPHandler as ParentHandler
from rorn.Lock import getLock
from rorn.ResponseWriter import ResponseWriter

class HTTPHandler(ParentHandler):
	def __init__(self, request, address, server):
		ParentHandler.__init__(self, request, address, server)

	def log_message(self, fmt, *args):
		user = self.session['user'].username if self.session and self.session['user'] else self.address_string()
		console('rorn', "%s(%s) %s", user or 'logged out', self.address_string(), fmt % args)

	def do_POST(self):
		lock = server().block_requests(expected = 1)
		try:
			ParentHandler.do_POST(self)
		finally:
			lock.release()

	def makeRequest(self):
		return dict(ParentHandler.makeRequest(self).items() + {
			'wrappers': True,
			'log': True
		}.items())

	def invokeHandler(self, handler, request, query):
		if request['log']:
			filename = handler['fn'].func_code.co_filename
			if filename.startswith(basePath()):
				filename = filename[len(basePath())+1:]
			request['log'] = LogEntry('rorn.handle', "%s %s" % (request['method'].upper(), request['path']), userid = self.session['user'].id if self.session['user'] else None, ip = self.client_address[0], location = "%s(%s:%d)" % (handler['fn'].func_code.co_name, filename, handler['fn'].func_code.co_firstlineno))
			Event.pageHandle(self, handler['fn'])

		return super(HTTPHandler, self).invokeHandler(handler, request, query)

	def requestDone(self, request):
		if isinstance(request['log'], LogEntry):
			request['log'].save()

		if request['wrappers']:
			types = ['less', 'css', 'js']
			includes = {type: [] for type in types}
			if 'handler' in request and 'statics' in request['handler']:
				for key in ensureList(request['handler']['statics']):
					for type in types:
						if isfile("static/%s.%s" % (key, type)):
							includes[type].append("/static/%s.%s" % (key, type))

			writer = ResponseWriter()
			header(self, request['path'], includes)
			print self.response
			footer(self, request['path'])
			self.response = writer.done()

	def processingRequest(self):
		if bricked():
			raise Exception(bricked())

		db().resetCount()

		#HACK
		if self.path.startswith('/static/'): return

		self.session['address'] = self.address_string()
		self.session['timestamp'] = getNow()
		self.session.remember('address', 'timestamp')

		if self.session['user']:
			self.session['user'] = User.load(self.session['user'].id) # Make sure the user isn't out of date
			self.session['user'].lastseen = dateToTs(getNow())
			self.session['user'].save()

	def title(self, title):
		self.replace('$title$', "%s - Sprint" % title if title else "Sprint", 1)
		self.replace('$bodytitle$', title if title else "Sprint", 1)

# Handlers
# import index
from handlers import *
from static import static
