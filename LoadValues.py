from Log import console
from Options import option
from relativeDates import timesince
from utils import *

import git
import sys
import os
from datetime import datetime

dbFilename = 'db'
gitURL = 'https://github.com/mrozekma/sprint/commit/%(hash)s'
loadTime = datetime.now()
devMode = None # Also checked in wrappers
brickMessage = False

repo = git.Repo()

def getRevisionInfo():
	# These are recomputed each time because revisionRelative changes
	revisionHash = repo.head.object.hexsha
	revisionDate = tsToDate(repo.head.object.committed_date)
	return revisionHash, revisionDate.strftime('%d %b %Y %H:%M:%S'), timesince(revisionDate) + ' ago'

def getLoadtime():
	return loadTime

def isDevMode(handler = None):
	if devMode is None:
		setDevMode(option('dev'))
	return devMode and ((handler is None) or (handler.session['user'] and handler.session['user'].hasPrivilege('Dev')))

def setDevMode(dev):
	global devMode
	devMode = dev

def brick(msg):
	global brickMessage
	brickMessage = msg or True
	console('brick', "Bricked: %s", brickMessage)

def bricked():
	return brickMessage
