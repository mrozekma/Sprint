from BaseHTTPServer import HTTPServer
from HTTPHandler import HTTPHandler
from Cron import Cron

PORT = 8081

server = HTTPServer(('', PORT), HTTPHandler)
Cron.start()
try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
