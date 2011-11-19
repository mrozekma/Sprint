from threading import Thread
from time import sleep
from os.path import isdir, exists
from datetime import datetime
from shutil import copy

from rorn.ResponseWriter import ResponseWriter
from rorn.Session import sessions

from utils import *

cronjobs = []
def job(name):
	def wrap(f):
		cronjobs.append(CronJob(name, f))
		return f
	return wrap

class CronThread(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.daemon = True
		self.running = False

	def run(self):
		self.running = True
		while self.running:
			if getNow().hour == 0:
				Cron.runAll()

			sleep(60*60)

class CronJob:
	def __init__(self, name, fn):
		self.name = name
		self.fn = fn
		self.lastrun = None
		self.log = None

	def run(self):
		writer = ResponseWriter()
		self.fn()
		self.log = writer.done()
		self.lastrun = getNow()

	def __str__(self):
		return self.name

thread = None
class Cron:
	@staticmethod
	def getJobs():
		return cronjobs

	@staticmethod
	def runAll():
		map(lambda job: job.run(), Cron.getJobs())

	@staticmethod
	def start():
		global thread
		thread = CronThread()
		thread.start()

	def stop():
		thread.running = False

@job('Old sessions')
def oldSessions():
	print "Processing %s<br><br>" % pluralize(len(sessions), 'session', 'sessions')
	toDelete = []
	now = getNow()
	for key, session in sessions.iteritems():
		age = (now - session['timestamp']) if session['timestamp'] else None

		if session['user']:
			if not age or age.days >= 7: # Logged-in sessions dead for a week
				toDelete.append(key)
				print "<div style=\"color: #a00;\"><b>%s</b>: queued for deletion (owned by %s, age: %s)</div>" % (key, session['user'], age or '&#8734;')
			else:
				print "<div style=\"color: #0a0;\"><b>%s</b>: retained (owned by %s, age: %s)</div>" % (key, session['user'], age)
		else:
			if not age or age.days >= 1: # Anonymous sessions dead for a day
				toDelete.append(key)
				print "<div style=\"color: #a00;\"><b>%s</b>: queued for deletion (anonymous %s, age: %s)</div>" % (key, session['address'] or 'unknown', age or '&#8734;')
			else:
				print "<div style=\"color: #0a0;\"><b>%s</b>: retained (anonymous %s, age: %s)</div>" % (key, session['address'] or 'unknown', age)

	print "<br>Deleting %s... " % pluralize(len(toDelete), 'session', 'sessions'),
	for key in toDelete:
		del sessions[key]
	print "done"

@job('Backup')
def backup():
	if not isdir('backups'):
		print "No backups directory exists; aborting"
		return

	filename = datetime.now().strftime('backups/%Y%m%d-%H%M%S.db')
	if exists(filename):
		print "Backup file %s already exists; aborting" % filename
		return

	copy('db', filename)
	if not exists(filename):
		print "Unable to write backup file %s" % filename
		return

	print "Backup to %s successful" % filename
