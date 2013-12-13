from BaseHTTPServer import HTTPServer as ParentServer
from datetime import datetime
from threading import Thread

requests = 0

# This is basically SocketServer.ThreadingMixIn, but it also handles naming the threads
class HTTPServer(ParentServer, object):
	def process_request_thread(self, request, client_address):
		try:
			self.finish_request(request, client_address)
		except:
			self.handle_error(request, client_address)
		finally:
			self.shutdown_request(request)

	def process_request(self, request, client_address):
		host, port = client_address
		now = datetime.now()
		t = Thread(name = "request <%s> @%s" % (host, now), target = self.process_request_thread, args = (request, client_address))
		t.daemon = True
		t.start()
