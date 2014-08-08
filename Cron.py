import re
from threading import Thread
from time import sleep
from os.path import isdir, exists
from datetime import datetime
from shutil import copy

from rorn.ResponseWriter import ResponseWriter
from rorn.Session import Session

from stasis.DiskMap import DiskMap
from stasis.Singleton import get as db

from HTTPServer import server
from User import User
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
		pattern = re.compile(period.replace('#', '\d'))
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

			sleep(30)

class CronJob:
	def __init__(self, name, period, fn):
		self.name = name
		self.period = period
		self.fn = fn
		self.laststart = None
		self.lastrun = None
		self.log = None

	def tick(self):
		# Don't run jobs more than once/minute
		if self.laststart and (getNow() - self.laststart) < timedelta(minutes = 1):
			return

		if self.period.match(str(getNow().replace(microsecond = 0))):
			self.laststart = getNow()
			self.run()

	def run(self):
		writer = ResponseWriter()
		lock = server().block_requests()
		try:
			self.fn()
			self.log = writer.done()
		except Exception, e:
			writer.done()
			self.log = "<div style=\"font-weight: bold; color: #f00\">%s</div>" % stripTags(str(e))
		finally:
			self.lastrun = getNow()
			lock.release()

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
	ids = Session.getIDs()
	print "Processing %s<br><br>" % pluralize(len(ids), 'session', 'sessions')
	toDelete = []
	now = getNow()
	for key in ids:
		session = Session.load(key)
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
		Session.destroy(key)
	print "done"

@job('Old reset keys', DAILY)
def oldResetKeys():
	if 'reset-keys' not in db()['cron']:
		db()['cron']['reset-keys'] = {}

	with db()['cron'].change('reset-keys') as data:
		for user in User.loadAll():
			if user.resetkey:
				if user.id in data:
					if user.resetkey == data[user.id]:
						user.resetkey = None
						user.save()
						del data[user.id]
						print "<b>%s</b>: Key expired<br>" % user.safe.username
					else:
						data[user.id] = user.resetkey
						print "<b>%s</b>: New key marked<br>" % user.safe.username
				else:
					data[user.id] = user.resetkey
					print "<b>%s</b>: New key marked<br>" % user.safe.username
			else:
				if user.id in data:
					del data[user.id]
					print "<b>%s</b>: Key consumed; removed old mark<br>" % user.safe.username

@job('Backup', DAILY)
def backup():
	if not isdir('backups'):
		print "No backups directory exists; aborting"
		return

	filename = datetime.now().strftime('backups/%Y%m%d-%H%M%S.tar.gz')
	if exists(filename):
		print "Backup file <code>%s</code> already exists; aborting" % filename
		return

	db().archive(filename)
	print "Backup to <code>%s</code> successful" % filename

@job('Log Archive', MONTHLY)
def logArchive():
	if not isdir('logs'):
		print "No logs directory exists; aborting"
		return

	logDB = DiskMap('logs')
	logDB['log'].merge(db()['log'])
	print "Archived %s; %d total" % (pluralize(len(db()['log']), 'log entry', 'log entries'), len(logDB['log']))
	db()['log'].truncate(resetID = False)
