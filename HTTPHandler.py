from rorn.HTTPHandler import HTTPHandler as ParentHandler
from rorn.ResponseWriter import ResponseWriter

from wrappers import header, footer
from User import User

class HTTPHandler(ParentHandler):
	def __init__(self, request, address, server):
		ParentHandler.__init__(self, request, address, server)

	def wrapContent(self, request):
		writer = ResponseWriter()
		header(self, request['path'])
		print self.response
		footer(self, request['path'])
		self.response = writer.done()

	def hackify(self):
		self.session['user'] = User.load(username = 'mmrozek')

# Handlers
# import index
from handlers import *
from static import static
