from datetime import datetime

from rorn.HTTPHandler import HTTPHandler as ParentHandler
from rorn.ResponseWriter import ResponseWriter

from wrappers import header, footer
from User import User
from Log import LogEntry
from utils import *

class HTTPHandler(ParentHandler):
	def __init__(self, request, address, server):
		ParentHandler.__init__(self, request, address, server)

	def log_message(self, format, *args):
		user = self.session['user'].username if self.session and self.session['user'] else self.address_string()
		sys.__stdout__.write("[%s] %s(%s) %s\n" % (self.log_date_time_string(), user or 'logged out', self.address_string(), format % args))

	def makeRequest(self):
		return dict(ParentHandler.makeRequest(self).items() + {
			'wrappers': True,
			'log': True
		}.items())

	def invokeHandler(self, fn, request, query):
		if request['log']:
			filename = fn.func_code.co_filename
			if filename.startswith(basePath()):
				filename = filename[len(basePath())+1:]
			request['log'] = LogEntry('handle', "%s %s" % (request['method'].upper(), request['path']), userid = self.session['user'].id if self.session['user'] else None, ip = self.client_address[0], location = "%s(%s:%d)" % (fn.func_code.co_name, filename, fn.func_code.co_firstlineno))

		fn(handler = self, request = request, **query)

	def requestDone(self, request):
		if request['log']:
			request['log'].save()

		if request['wrappers']:
			writer = ResponseWriter()
			header(self, request['path'])
			print self.response
			footer(self, request['path'])
			self.response = writer.done()

	def processingRequest(self):
		self.replace('$headerbg$', '#0152A1', 1)

		#HACK
		if self.path.startswith('/static/'): return

		self.session['address'] = self.address_string()
		self.session['timestamp'] = getNow()

		if self.session['user']:
			self.session['user'] = User.load(self.session['user'].id) # Make sure the user isn't out of date
			self.session['user'].lastseen = dateToTs(getNow())
			self.session['user'].save()

# Handlers
# import index
from handlers import *
from static import static
