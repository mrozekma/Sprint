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
import termios
import tty
from os import mkdir, rename
from os.path import exists, isfile, isdir, splitext
from getpass import getpass
from socket import gethostname
from shutil import copy, rmtree
from time import sleep
import sqlite3

from LoadValues import dbFilename
from User import User
from Privilege import adminDefaults
from Options import option
from Settings import settings, PORT
from utils import *

from stasis.DiskMap import DiskMap
from stasis.Singleton import set as setDB
from stasis.StasisError import StasisError

LAST_SQLITE_VERSION = 19
LAST_SQLITE_REVISION = '38e224f66d34dd2077a6cf8597c8c299334cd059' # This is the revision that created DB 19; technically many after it would also work
DB_VERSION = 20 # Temporary until stasis updating is implemented

HOW_TO_RUN = "You can run %s normally now and browse to http://%s:%d/" % (sys.argv[0], gethostname(), PORT)

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
			print "Database conversion complete. %s" % HOW_TO_RUN
			exit(0)

	if not isdir('db'):
		print "No database found. If you've never run this tool before, run %s --init to configure it" % sys.argv[0]
		exit(1)

	# There's no DB connection yet, so we set a temporary uncached one
	# The real cached version is set later in main
	setDB(DiskMap(dbFilename))

	if option('mode') == 'update':
		if int(settings.dbVersion) < DB_VERSION:
			update()
			exit(0)
		elif int(settings.dbVersion) == DB_VERSION:
			print "Unable to update -- already at database version %d" % DB_VERSION
			exit(1)
	if int(settings.dbVersion) < DB_VERSION:
		print "The database is %s behind. Run %s --update to update it" % (pluralize(DB_VERSION - int(settings.dbVersion), 'version', 'versions'), sys.argv[0])
		exit(1)
	elif int(settings.dbVersion) > DB_VERSION:
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

	print "All users are assumed to share a common e-mail domain. This is currently only used for gravatars, but might be used to send e-mails later"
	email = raw_input('E-mail domain: ')
	if email == '':
		exit(1)
	print

	print "Creating database"
	setDB(DiskMap(dbFilename, create = True))

	try:
		settings.dbVersion = DB_VERSION
		settings.emailDomain = email
	except Exception, e:
		rmtree(dbFilename)
		die("Unable to set default settings: %s" % e)

	print "Creating admin user"
	try:
		user = User(username, password, privileges = set(adminDefaults))
		user.save()
	except Exception, e:
		rmtree(dbFilename)
		die("Unable to create admin user: %s" % e)

	print "Creating backup and log directories"
	if not isdir('backups'):
		mkdir('backups')
	if not isdir('logs'):
		mkdir('logs')

	print "Done. %s" % HOW_TO_RUN

def update():
	pass # Unimplemented until the first update
	# print "Updated to database version %d. You can run %s normally now and browse to http://%s:%d/" % (dbVersion, sys.argv[0], gethostname(), PORT)
