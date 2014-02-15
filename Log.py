from __future__ import division
import traceback
import datetime
from math import ceil

from User import User
from utils import *

from stasis.Singleton import get as db
from stasis.ActiveRecord import ActiveRecord, link

class LogEntry(ActiveRecord):
	user = link(User, 'userid')

	def __init__(self, type, text, userid = None, ip = None, timestamp = None, location = 0, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.userid = userid
		self.ip = ip
		self.type = type
		self.text = text

		if timestamp:
			self.timestamp = timestamp
		else:
			now = datetime.now() # Use real time, not mocked time through getNow()
			self.timestamp = dateToTs(now) + now.microsecond / 1000000

		if isinstance(location, int):
			filename, line, fn, code = traceback.extract_stack()[-2-location]
			if filename.startswith(basePath()):
				filename = filename[len(basePath())+1:]
			self.location = "%s(%s:%d)" % (fn, filename, line)
		else:
			self.location = location

	@classmethod
	def table(cls):
		return 'log'

	@classmethod
	def getTypes(cls):
		return set(entry['type'] for entry in db()['log'].values())

def log(handler, type, fmt, *args):
	str = fmt
	if args:
		str %= args
	LogEntry(type, str, handler.session['user'].id if handler.session['user'] else None, handler.client_address[0]).save()

def console(source, fmt, *args):
	str = fmt
	if args:
		str %= args
	sys.__stdout__.write("[%s] [%s] %s\n" % (datetime.now().replace(microsecond = 0), source, str))
