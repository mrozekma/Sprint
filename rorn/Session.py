from __future__ import with_statement
from Cookie import SimpleCookie
import time
import base64
import os
from utils import md5, ucfirst
from datetime import datetime, timedelta
import pickle

from Lock import synchronized

sessions = {}

class Session(object):
	def __init__(self, key):
		self.key = key
		self.map = {}
		self.persistent = set() # Only keys in this set are saved to disk

	@synchronized('session')
	def keys(self):
		return self.map.keys()

	@synchronized('session')
	def values(self):
		return self.map.values()

	@synchronized('session')
	def __getitem__(self, k):
		return self.map[k] if k in self.map else None

	@synchronized('session')
	def __setitem__(self, k, v):
		self.map[k] = v
		Session.saveAll()

	@synchronized('session')
	def __delitem__(self, k):
		del self.map[k]
		Session.saveAll()

	@synchronized('session')
	def remember(self, *keys):
		self.persistent.update(keys)

	@synchronized('session')
	def __contains__(self, k):
		return k in self.map

	@synchronized('session')
	def __iter__(self):
		return self.map.__iter__()

	@synchronized('session')
	def __getstate__(self):
		return (self.key, {k: v for (k, v) in self.map.iteritems() if k in self.persistent})

	@synchronized('session')
	def __setstate__(self, (key, map)):
		self.key = key
		self.map = map
		self.persistent = set(map.keys())

	@staticmethod
	@synchronized('session')
	def determineKey(handler):
		hdr = handler.headers.getheader('Cookie')
		if not hdr: return Session.generateKey()
		c = SimpleCookie()
		c.load(hdr)
		return c['session'].value if c.has_key('session') else Session.generateKey()

	@staticmethod
	@synchronized('session')
	def generateKey():
		key = md5(os.urandom(128) + str(time.time()))[:-3].replace('/', '$')
		if key in sessions:
			return None
		return key

	@staticmethod
	@synchronized('session')
	def load(key):
		if key not in sessions:
			sessions[key] = Session(key)
			Session.saveAll()
		return sessions[key]

	@staticmethod
	@synchronized('session')
	def loadAll():
		global sessions
		try:
			with open('session', 'r') as f:
				sessions = pickle.load(f)
		except Exception: pass

	@staticmethod
	@synchronized('session')
	def saveAll():
		with open('session', 'w') as f:
			pickle.dump(sessions, f)

def timestamp(days = 7):
	return (datetime.utcnow() + timedelta(days)).strftime("%a, %d-%b-%Y %H:%M:%S GMT")

def delay(handler, item):
	if 'delayed' not in handler.session:
		handler.session['delayed'] = []
	handler.session['delayed'].append(item)

def undelay(handler):
	if 'delayed' in handler.session:
		for item in handler.session['delayed']:
			print item
		del handler.session['delayed']

Session.loadAll()
