from utils import *

import os
from datetime import datetime
from socket import gethostname

loadTime = datetime.now()
devBuild = (gethostname() != 'barium')

def getRevisionInfo():
	# These are recomputed each time because revisionRelative changes
	revisionHash, revisionDate, revisionRelative = os.popen('git log -n 1 --format=format:"%H %ct %cr"').read().split(' ', 2)
	revisionDate = tsToDate(int(revisionDate)).strftime('%d %b %Y %H:%M:%S')
	return revisionHash, revisionDate, revisionRelative

def getLoadtime():
	return loadTime

def isDevBuild():
	return devBuild
