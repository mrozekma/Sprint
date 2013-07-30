import re
from sqlite3 import connect
from threading import Thread
from time import sleep
from os.path import isdir, exists
from datetime import datetime
from shutil import copy

from rorn.ResponseWriter import ResponseWriter
from rorn.Session import sessions

from DB import db
from Lock import getLock
from utils import *

# Regular expression that matches 'YYYY-MM-DD HH:MM:SS', where # is a digit
# The cron thread only checks once/minute, so times can't be more precise than that and the SS field should always be ## to avoid missing some cycles
MINUTELY = '####-##-## ##:##:##'
HOURLY = '####-##-## ##:00:##'
DAILY = '####-##-## 00:00:##'
MONTHLY = '####-##-01 00:00:##'

cronjobs = []
def job(name, period):
	def wrap(f):
		pattern = re.compile(period.replace('#', '\d+'))
		cronjobs.append(CronJob(name, pattern, f))
		return f
	return wrap

class CronThread(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.name = 'cron'
		self.daemon = True
		self.running = False

	def run(self):
		self.running = True
		while self.running:
			for job in cronjobs:
				job.tick()

			sleep(60)

class CronJob:
	def __init__(self, name, period, fn):
		self.name = name
		self.period = period
		self.fn = fn
		self.lastrun = None
		self.log = None

	def tick(self):
		if self.period.match(str(getNow().replace(microsecond = 0))):
			self.run()

	def run(self):
		writer = ResponseWriter()
		try:
			with getLock('global'):
				self.fn()
			self.log = writer.done()
		except Exception, e:
			writer.done()
			self.log = "<div style=\"font-weight: bold; color: #f00\">%s</div>" % stripTags(str(e))
		self.lastrun = getNow()

	def __str__(self):
		return self.name

thread = None
class Cron:
	@staticmethod
	def getJobs():
		return cronjobs

	@staticmethod
	def start():
		global thread
		thread = CronThread()
		thread.start()

	def stop():
		thread.running = False

@job('Old sessions', DAILY)
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

@job('Backup', DAILY)
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

@job('Log Archive', MONTHLY)
def logArchive():
	if not isdir('logs'):
		print "No logs directory exists; aborting"
		return

	filename = datetime.now().strftime('logs/%Y%m%d-%H%M%S.log')
	if exists(filename):
		print "Log file %s already exists; aborting" % filename
		return

	cursor = db().cursor()
	cursor.execute("ATTACH DATABASE '%s' AS archive" % filename)
	cursor.execute("SELECT sql FROM main.sqlite_master WHERE type = 'table' AND name = 'log'")
	sql = cursor.fetchone()[0]
	if not sql.startswith('CREATE TABLE log'):
		print "Unexpected SQL: %s" % sql
		return
	cursor.execute(sql.replace('CREATE TABLE log', 'CREATE TABLE archive.log'))
	cursor.execute("INSERT INTO archive.log SELECT * FROM log")
	cursor.execute("SELECT COUNT(*) FROM archive.log")
	numRows = cursor.fetchone()[0]
	cursor.execute("DETACH DATABASE archive")

	db().update("DELETE FROM log")
	db().update("VACUUM")
	print "Archived %s to %s" % (pluralize(numRows, 'log entry', 'log entries'), filename)
