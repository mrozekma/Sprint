from BaseHTTPServer import HTTPServer
from HTTPHandler import HTTPHandler
import socket

from Cron import Cron
from Settings import PORT
from Update import check
from Event import addEventHandler
from event_handlers import *

check()

try:
	server = HTTPServer(('', PORT), HTTPHandler)
except socket.error, (errno, msg):
	print "Unable to open port %d: %s" % (PORT, msg)
	exit(1)

Cron.start()

# addEventHandler(DebugLogger.DebugLogger())
addEventHandler(DBLogger.DBLogger())

try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
