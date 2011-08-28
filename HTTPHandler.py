from datetime import datetime

from rorn.HTTPHandler import HTTPHandler as ParentHandler
from rorn.ResponseWriter import ResponseWriter

from wrappers import header, footer
from User import User
from utils import *

class HTTPHandler(ParentHandler):
	def __init__(self, request, address, server):
		ParentHandler.__init__(self, request, address, server)

	def log_message(self, format, *args):
		user = self.session['user'].username if self.session['user'] else self.address_string()
		log("[%s] %s(%s) %s" % (self.log_date_time_string(), self.session['user'].username if self.session['user'] else 'logged out', self.address_string(), format % args))

	def wrapContent(self, request):
		writer = ResponseWriter()
		header(self, request['path'])
		print self.response
		footer(self, request['path'])
		self.response = writer.done()

	def processingRequest(self):
		self.session['user'] = User.load(username = 'mmrozek') #TODO Remove

		#HACK
		if self.path.startswith('/static/'): return

		if self.session['user']:
			self.session['user'].lastseen = dateToTs(datetime.now())
			self.session['user'].save()

# Handlers
# import index
from handlers import *
from static import static
