from BaseHTTPServer import HTTPServer
from HTTPHandler import HTTPHandler
import socket

from Cron import Cron
from Settings import PORT
from Update import check

check()

try:
	server = HTTPServer(('', PORT), HTTPHandler)
except socket.error, (errno, msg):
	print "Unable to open port %d: %s" % (PORT, msg)
	exit(1)

Cron.start()

try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
