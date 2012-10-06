import sys
from BaseHTTPServer import HTTPServer
from HTTPHandler import HTTPHandler
import socket
from threading import currentThread
import signal

from Log import console
from DB import db
from Cron import Cron
from Options import option, parse as parseOptions
from Settings import PORT, settings
from Update import check
from Event import addEventHandler
from event_handlers import *

currentThread().name = 'main'

parseOptions()
check()

try:
	server = HTTPServer(('', PORT), HTTPHandler)
except socket.error, (errno, msg):
	print "Unable to open port %d: %s" % (PORT, msg)
	exit(1)

Cron.start()

# addEventHandler(DebugLogger.DebugLogger())
addEventHandler(DBLogger.DBLogger())
addEventHandler(MessageDispatcher.MessageDispatcher())
if settings.redis:
	host, port = settings.redis.split(':', 1)
	port = int(port)
	addEventHandler(EventPublisher.EventPublisher(host, port))

# When python is started in the background it ignores SIGINT instead of throwing a KeyboardInterrupt
signal.signal(signal.SIGINT, signal.default_int_handler)

try:
	server.serve_forever()
except KeyboardInterrupt:
	sys.__stdout__.write("\n\n")
	console('main', 'Exiting at user request')
except Exception, e:
	sys.__stdout__.write("\n\n")
	console('main', '%s', e)

console('main', 'Closing server sockets')
server.server_close()

console('main', 'Flushing database')
db().diskQueue.flush()

console('main', 'Done')
