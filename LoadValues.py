from Log import console
from Options import option
from utils import *

import sys
import os
from datetime import datetime

dbFilename = 'db'
gitURL = 'https://github.com/mrozekma/sprint/commit/%(hash)s'
loadTime = datetime.now()
devMode = None # Also checked in wrappers
brickMessage = False

def getRevisionInfo():
	# These are recomputed each time because revisionRelative changes
	revisionHash, revisionDate, revisionRelative = os.popen('git log -n 1 --format=format:"%H %ct %cr"').read().split(' ', 2)
	revisionDate = tsToDate(int(revisionDate)).strftime('%d %b %Y %H:%M:%S')
	return revisionHash, revisionDate, revisionRelative

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
