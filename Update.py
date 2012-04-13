import sys
from os import listdir, remove
from os.path import isdir, splitext
from getpass import getpass
from socket import gethostname

from DB import DB, DBError, db, filename as dbFilename
from User import User
from Privilege import Privilege
from Settings import settings, PORT

def check():
	if '--init' in sys.argv:
		init()

	try:
		db()
	except DBError, e:
		print e
		print "If you've never run this tool before, run %s --init to configure it" % sys.argv[0]
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

	if not isdir('db-templates'):
		die("Unable to find db-templates directory")

	templates = []
	for script in listdir('db-templates'):
		index, ext = splitext(script)
		if ext != '.sql':
			die("Unexpected template file: %s" % script)
		try:
			templates.append(int(index, 0))
		except ValueError:
			die("Unexpected template file: %s" % script)
	templates.sort()

	print "The database starts with a root user you can use to manage the installation"
	username = raw_input('Username: ')
	if username == '':
		exit(1)
	password = getpass('Password: ')
	if password == '':
		exit(1)
	print

	print "Creating database"
	open(dbFilename, 'w').close()
	try:
		for index in templates:
			map(db().update, open("db-templates/%d.sql" % index).readlines())
	except Exception, e:
		remove(dbFilename)
		die("Unable to apply template %d: %s" % (index, e))

	try:
		settings.dbVersion = index
	except Exception, e:
		remove(dbFilename)
		die("Unable to set database version: %s" % e)

	print "Creating admin user"
	try:
		user = User(username, password)
		user.save()

		for priv in Privilege.loadAll():
			db().update("INSERT INTO grants(userid, privid) VALUES(?, ?)", user.id, priv.id)
	except Exception, e:
		remove(dbFilename)
		die("Unable to create admin user: %s" % e)

	print "Done. You can run %s normally now and browse to http://%s:%d/" % (sys.argv[0], gethostname(), PORT)
	exit(0)
