# This should always be the first import
import Update

from datetime import datetime
import errno
import os
from os.path import abspath, dirname
from resource import getrlimit, RLIMIT_NOFILE, RLIM_INFINITY
import signal
import socket
import sys
from threading import currentThread

os.chdir(dirname(abspath(__file__)))

# We give stasis a single lock for all DiskMaps, but there will only be one DiskMap
from rorn.Lock import getLock, setStackRecording
from stasis.Lock import setMutexProvider
setMutexProvider(lambda: getLock('#stasis'))

from Options import option, parse as parseOptions
parseOptions()
Update.check()
if option('lock-tracking'):
	setStackRecording(True)

from stasis.Singleton import set as setDB
from stasis.DiskMap import DiskMap
from LoadValues import dbFilename
def cacheLog(table):
	sys.__stdout__.write("[%s] [%s] %s\n" % (datetime.now().replace(microsecond = 0), 'stasis', "Backfilling table: %s" % table))
setDB(DiskMap(dbFilename, cache = True, nocache = ['log', 'sessions'], cacheNotifyFn = cacheLog))

from LoadValues import bricked
from Log import console
from Cron import Cron
from HTTPServer import server as getServer, ServerError
from Settings import PORT, settings
from Event import addEventHandler
from event_handlers import *

from rorn.Session import setSerializer
from SessionSerializer import SessionSerializer
setSerializer(SessionSerializer())

currentThread().name = 'main'

try:
	server = getServer()
except ServerError, e:
	console('server', e.message)
	exit(1)

Cron.start()

# addEventHandler(DebugLogger.DebugLogger())
addEventHandler(DBLogger.DBLogger())
addEventHandler(ErrorCounter.errorCounter)
addEventHandler(MessageDispatcher.MessageDispatcher())
if settings.redis:
	host, port = settings.redis.split(':', 1)
	port = int(port)
	addEventHandler(EventPublisher.EventPublisher(host, port))

# When python is started in the background it ignores SIGINT instead of throwing a KeyboardInterrupt
def signal_die(signum, frame):
	signals = dict((getattr(signal, name), name) for name in dir(signal) if name.startswith('SIG') and '_' not in name)
	raise SystemExit("Caught %s; exiting" % signals.get(signum, "signal %d" % signum))
signal.signal(signal.SIGINT, signal.default_int_handler)
signal.signal(signal.SIGTERM, signal_die)

# Daemonize
if option('daemon'):
	logFile = datetime.now().strftime('log-%Y%m%d-%H%M%S.log')
	console('main', "Switching to daemon mode. Output logged to %s" % logFile)

	# Double-fork
	if os.fork() != 0:
		os._exit(0)
	os.setsid()
	if os.fork() != 0:
		os._exit(0)

	# Point the standard file descriptors at a log file
	log = os.open(logFile, os.O_CREAT | os.O_RDWR)
	os.dup2(log, 0)
	os.dup2(log, 1)
	os.dup2(log, 2)

# Writing the pidfile
pidFile = option('pidfile')
if pidFile:
	with open(pidFile, 'w') as f:
		f.write("%d\n" % os.getpid())

restart = False

try:
	console('rorn', 'Listening for connections')
	try:
		server.serve_forever()
	except socket.error, e:
		if e.errno == errno.EBADF and (bricked() or '').startswith('Restart'):
			restart = True
		else:
			raise
except KeyboardInterrupt:
	sys.__stdout__.write("\n\n")
	console('main', 'Exiting at user request')
except (Exception, SystemExit), e:
	sys.__stdout__.write("\n\n")
	console('main', '%s', e)

console('main', 'Closing server sockets')
server.server_close()

if pidFile:
	os.remove(pidFile)

if restart:
	console('main', 'Restarting')
	os.execl(sys.executable, sys.executable, *sys.argv)
else:
	console('main', 'Done')
