from utils import *

import sys
import os
from datetime import datetime

loadTime = datetime.now()
devMode = ('--dev' in sys.argv) # Also checked in wrappers
brickMessage = False

def getRevisionInfo():
	# These are recomputed each time because revisionRelative changes
	revisionHash, revisionDate, revisionRelative = os.popen('git log -n 1 --format=format:"%H %ct %cr"').read().split(' ', 2)
	revisionDate = tsToDate(int(revisionDate)).strftime('%d %b %Y %H:%M:%S')
	return revisionHash, revisionDate, revisionRelative

def getLoadtime():
	return loadTime

def isDevMode(handler = None):
	return devMode and ((handler.session['user'] and handler.session['user'].hasPrivilege('Dev')) if handler else True)

def setDevMode(dev):
	global devMode
	devMode = dev

def brick(msg):
	global brickMessage
	brickMessage = msg or True
	sys.__stdout__.write("BRICK: %s\n" % brickMessage)

def bricked():
	return brickMessage
