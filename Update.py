# This is the first module loaded by main, and the first thing we do is check dependencies, before anything else has a chance to try importing them
def depcheck():
	failures = []
	def fail(msg):
		failures.append(msg)

	def imp(name, desc):
		try:
			return __import__(name)
		except ImportError:
			fail("Missing dependency: %s" % desc)

	# Python
	import sys
	pyver = sys.version_info
	if pyver.major > 2:
		fail("Python 3 is not backwards compatible. Sprint requires Python 2.7+")
	if pyver.minor < 7:
		fail("Sprint requires Python 2.7+ (you are running %d.%d.%d)" % (pyver.major, pyver.minor, pyver.micro))

	# Libraries
	imp('fuzzywuzzy', 'FuzzyWuzzy - https://github.com/seatgeek/fuzzywuzzy') # This is currently bundled, so it shouldn't ever fail. Might pull it out at some point
	imp('PIL', 'Python Imaging Library (PIL) - http://www.pythonware.com/products/pil/')
	imp('SilverCity', 'SilverCity - https://pypi.python.org/pypi/SilverCity')
	imp('rorn', 'Rorn') # Also bundled
	imp('stasis', 'Stasis - https://github.com/mrozekma/Stasis')

	if failures:
		print "Unresolved environment problems:"
		print
		for failure in failures:
			print "  * %s" % failure
		exit(1)
depcheck()

import sys
import tarfile
import termios
import tty
from os import mkdir, rename
from os.path import exists, isfile, isdir, splitext
from getpass import getpass
from socket import gethostname
from shutil import copy, rmtree
from time import sleep
import sqlite3

from ChangeLog import ChangeRecord, changelog
from LoadValues import dbFilename
from User import User
from Privilege import adminDefaults
from Options import option
from Settings import settings, PORT
from utils import *

from stasis.DiskMap import DiskMap
from stasis.Singleton import get as db, set as setDB
from stasis.StasisError import StasisError

LAST_SQLITE_VERSION = 19
LAST_SQLITE_REVISION = '38e224f66d34dd2077a6cf8597c8c299334cd059' # This is the revision that created DB 19; technically many after it would also work
HOW_TO_RUN = "You can run %s normally now and browse to http://%s:%d/" % (sys.argv[0], gethostname(), PORT)

updates = [None] * LAST_SQLITE_VERSION # Spacers for all the old sqlite versions, and the first stasis version that's created by check()
def update(f):
	updates.append(f)
	return f

def check():
	if option('mode') == 'init':
		init()
		exit(0)

	if isfile('db'):
		conn = sqlite3.connect(dbFilename)
		cur = conn.cursor()
		try:
			row = cur.execute("SELECT value FROM settings WHERE name = 'dbVersion'")
		except sqlite3.DatabaseError, e:
			if 'not a database' in e.message:
				print "There is a file named 'db', but it doesn't appear to be a sprint database"
			else:
				print "There was a problem attempting to open the database: %s" % e.message
			exit(1)
		if option('mode') != 'update':
			print "The database is in an old format. Run %s --update to update it" % sys.argv[0]
			exit(1)
		version = int(row.fetchone()[0])
		if version < LAST_SQLITE_VERSION:
			print "Sprint has changed backend formats, but your database is so old it can't be converted by this version. You need to:"
			print
			print "  * Rollback to revision %s" % LAST_SQLITE_REVISION
			print "  * Run %s --update to update to the latest sqlite database" % sys.argv[0]
			print "  * Switch back to the latest Sprint revision"
			print "  * Run %s --update again to switch from sqlite to stasis" % sys.argv[0]
		else:
			print "Sprint has changed backend formats, so your entire existing database needs to be converted. This is an automated procedure; your old database will be renamed 'db-old.sqlite'. The logs folder will also be converted to a stasis database with a single 'log' table; the existing logs folder will be renamed logs-old."
			print
			print "Run database conversion? [\033[1;32mYes\033[0m/\033[1;31mNo\033[0m] ",
			fd = sys.stdin.fileno()
			reg = termios.tcgetattr(fd)
			try:
				tty.setraw(fd)
				ch = sys.stdin.read(1)
			finally:
				termios.tcsetattr(fd, termios.TCSADRAIN, reg)
			sys.stdout.write("%s\n" % ch)
			print
			if ch not in ('y', 'Y', '\r', '\n'):
				print "Canceled"
				exit(0)
			print "Conversion will start in 3 seconds; depending on the database size you may see quite a lot of text go by"
			sleep(3)
			import sqlite_to_stasis
			print
			if isdir('logs'):
				rename('logs', 'logs-old')
			mkdir('logs')
			print "Database conversion complete. Ready to apply updates"

	if not isdir('db'):
		print "No database found. If you've never run this tool before, run %s --init to configure it" % sys.argv[0]
		exit(1)

	# There's no DB connection yet, so we set a temporary uncached one
	# The real cached version is set later in main
	setDB(DiskMap(dbFilename))

	if option('mode') == 'update':
		if int(settings.dbVersion) < len(updates):
			runUpdates()
			print "Updated to database version %d. %s" % (len(updates), HOW_TO_RUN)
			exit(0)
		elif int(settings.dbVersion) == len(updates):
			print "Unable to update -- already at database version %d" % len(updates)
			exit(1)
	if int(settings.dbVersion) < len(updates):
		print "The database is %s behind. Run %s --update to update it" % (pluralize(len(updates) - int(settings.dbVersion), 'version', 'versions'), sys.argv[0])
		exit(1)
	elif int(settings.dbVersion) > len(updates):
		print "The database is %s ahead; downgrading is not supported" % pluralize(int(settings.dbVersion) - DB_VERSION, 'version', 'versions')
		exit(1)

def init():
	def die(msg):
		print msg
		exit(1)

	if exists(dbFilename):
		die("The database %s already exists. If you really want to reconfigure, remove it first" % dbFilename)

	print "The database starts with a root user you can use to manage the installation"
	username = raw_input('Username: ')
	if username == '':
		exit(1)
	password = getpass('Password: ')
	if password == '':
		exit(1)
	print

	print "All users are assumed to share a common e-mail domain. This is currently used for gravatars and sending password reset e-mails"
	email = raw_input('E-mail domain: ')
	if email == '':
		exit(1)
	print

	print "Creating database"
	setDB(DiskMap(dbFilename, create = True))

	try:
		settings.dbVersion = LAST_SQLITE_VERSION
		settings.emailDomain = email
		settings.autolink = ([], [], [])
	except Exception, e:
		rmtree(dbFilename)
		die("Unable to set default settings: %s" % e)

	try:
		runUpdates(False)
	except:
		rmtree(dbFilename)
		raise

	print "Creating admin user"
	try:
		user = User(username, password, privileges = set(adminDefaults))
		user.save()
	except Exception, e:
		rmtree(dbFilename)
		die("Unable to create admin user: %s" % e)

	# Mark all changelog entries read
	try:
		for change in changelog:
			ChangeRecord(change.id, user.id).save()
	except Exception, e:
		rmtree(dbFilename)
		die("Unable to mark changelog entries: %s" % e)

	print "Creating backup and log directories"
	if not isdir('backups'):
		mkdir('backups')
	if not isdir('logs'):
		mkdir('logs')

	print "Done. %s" % HOW_TO_RUN

def runUpdates(output = True):
	backupFilename = "%s-preupgrade.tar.gz" % dbFilename
	if output:
		print "Backing up database to %s" % backupFilename
	db().archive(backupFilename)

	if output:
		print "Updating"
	toApply = updates[settings.dbVersion:]
	try:
		for f in toApply:
			if f.__doc__:
				print "  v%d: %s" % (settings.dbVersion + 1, f.__doc__)
			f()
			settings.dbVersion += 1
	except:
		if output:
			print "Unable to update to version %d. Restoring database from backup" % (settings.dbVersion + 1)
		rmtree(dbFilename)
		f = tarfile.open(backupFilename, 'r:gz')
		f.extractall()
		f.close()
		if output:
			print "Update rolled back. Error follows:"
			print
		raise

@update
def v20():
	pass # Version 20 is the conversion to stasis, which is done in check()

@update
def v21():
	"""Move all existing Dev grants to Admin"""
	table = db()['users']
	for id in table:
		with table.change(id) as data:
			if 'Dev' in data['privileges']:
				data['privileges'].remove('Dev')
				data['privileges'].add('Admin')

@update
def v22():
	"""Add the defaultTasksTab preference"""
	table = db()['prefs']
	for id in table:
		with table.change(id) as data:
			data['defaultTasksTab'] = 'single'

@update
def v23():
	"""Convert bugzillaURL to autolinkPatterns"""
	table = db()['settings']
	table['autolink'] = ([], [], [])
	if 'bugzillaURL' in table:
		with table.change('autolink') as data:
			icons, patterns, urls = data
			icons.append('bugzilla')
			patterns.append('(?:bug |bz)(?P<id>[0-9]+)')
			urls.append("%s/show_bug.cgi?id=$id" % table['bugzillaURL'])
		del table['bugzillaURL']

@update
def v24():
	"""Fix tasks 'deleted' field type"""
	table = db()['tasks']
	for id in table:
		with table.change(id) as data:
			for rev in range(len(data)):
				if data[rev]['deleted'] in [0, '0']:
					data[rev]['deleted'] = False
				elif data[rev]['deleted'] in [1, '1']:
					data[rev]['deleted'] = True
				else:
					raise RuntimeError("Unexpected deleted value for task #%d, revision %d: %s" % (id, rev + 1, data['deleted']))

@update
def v25():
	"""Add 'flags' field to sprints"""
	table = db()['sprints']
	for id in table:
		with table.change(id) as data:
			data['flags'] = set()
