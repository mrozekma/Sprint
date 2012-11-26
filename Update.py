import sys
from os import remove
from os.path import isdir, splitext
from getpass import getpass
from socket import gethostname
from shutil import copy

from DB import DB, DBError, db, filename as dbFilename
from User import User
from Privilege import Privilege
from Options import option
from Settings import settings, PORT
from utils import *

def check():
	if option('mode') == 'init':
		init()
		exit(0)

	try:
		db()
	except DBError, e:
		print e
		print "If you've never run this tool before, run %s --init to configure it" % sys.argv[0]
		exit(1)

	dbVersion = DB.getTemplates()[-1]
	if option('mode') == 'update':
		if int(settings.dbVersion) < dbVersion:
			update()
			exit(0)
		elif int(settings.dbVersion) == dbVersion:
			print "Unable to update -- already at database version %d" % dbVersion
			exit(1)
	if int(settings.dbVersion) < dbVersion:
		print "The database is %s behind. Run %s --update to update it" % (pluralize(dbVersion - int(settings.dbVersion), 'version', 'versions'), sys.argv[0])
		exit(1)
	elif int(settings.dbVersion) > dbVersion:
		print "The database is %s ahead; downgrading is not supported" % pluralize(int(settings.dbVersion) - dbVersion, 'version', 'versions')
		exit(1)

def init():
	def die(msg):
		print msg
		exit(1)

	try:
		db()
		die("The database %s already exists. If you really want to reconfigure, remove it first" % dbFilename)
	except DBError:
		pass

	try:
		templates = DB.getTemplates()
	except DBError, e:
		die(str(e))

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
	open(dbFilename, 'w').close()
	index = applyTemplates(templates, lambda: remove(dbFilename))

	try:
		settings.dbVersion = index
		settings.emailDomain = email
		settings.gitURL = 'https://github.com/mrozekma/sprint/commit/%(hash)s'
	except Exception, e:
		remove(dbFilename)
		die("Unable to set default settings: %s" % e)

	print "Creating admin user"
	try:
		user = User(username, password)
		user.save()

		for priv in Privilege.loadAll():
			db().update("INSERT INTO grants(userid, privid) VALUES(?, ?)", user.id, priv.id)
	except Exception, e:
		remove(dbFilename)
		die("Unable to create admin user: %s" % e)

	db().diskQueue.flush()
	print "Done. You can run %s normally now and browse to http://%s:%d/" % (sys.argv[0], gethostname(), PORT)

def update():
	templates = DB.getTemplates()
	dbVersion = templates[-1]
	if int(settings.dbVersion) >= dbVersion:
		print "Unable to update version %d to %d" % (int(settings.dbVersion), dbVersion)
		exit(1)

	backupFilename = "%s-preupgrade%s" % splitext(dbFilename)
	copy(dbFilename, backupFilename)
	print "Backed up database to %s" % backupFilename

	newTemplates = templates[templates.index(int(settings.dbVersion))+1:]
	applyTemplates(newTemplates, lambda: copy(backupFilename, dbFilename))
	settings.dbVersion = dbVersion
	db().diskQueue.flush()
	print "Updated to database version %d. You can run %s normally now and browse to http://%s:%d/" % (dbVersion, sys.argv[0], gethostname(), PORT)

def applyTemplates(templates, failFn):
	try:
		for index in templates:
			map(db().update, open("db-templates/%d.sql" % index).readlines())
		return index
	except Exception, e:
		print "Unable to apply template %d: %s" % (index, e)
		failFn()
		exit(1)
