from BaseHTTPServer import HTTPServer
from HTTPHandler import HTTPHandler

PORT = 8081

server = HTTPServer(('', PORT), HTTPHandler)
try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
