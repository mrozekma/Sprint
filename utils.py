import re
import hashlib
from datetime import datetime, date, timedelta
from time import mktime

DATE_FMT = '%d %b %Y'

# http://smitbones.blogspot.com/2008/01/python-strip-html-tags-function.html
def stripTags(value):
    # "Return the given HTML with all tags stripped."
    # return re.sub(r'<[^>]*?>', '', value)
	return value.replace("<", "&lt;")

class DoneRendering(Exception): pass
def done():
	raise DoneRendering()

class Redirect(Exception):
	def __init__(self, target):
		self.target = target
def redirect(target):
	raise Redirect(target)

def md5(str):
	return hashlib.md5(str).hexdigest()

def ucfirst(str):
	if len(str) == 0:
		return str
	elif len(str) == 1:
		return str.upper()
	else:
		return str[0].upper() + str[1:]

def pluralize(num, singular, plural):
	return "%d %s" % (num, singular if num == 1 else plural)

def globalize(f):
	__builtins__[f.func_name] = f
	return f

def tsToDate(timestamp): return datetime.fromtimestamp(timestamp)
def dateToTs(d): return mktime(d.timetuple())
def tsStart(timestamp): return dateToTs(tsToDate(timestamp).replace(hour = 0, minute = 0, second = 0))
def tsEnd(timestamp): return dateToTs(tsToDate(timestamp).replace(hour = 23, minute = 59, second = 59))
def formatDate(d): return d.strftime(DATE_FMT)

import sys
def andmap(f, l):
	for i in l:
		if not f(i):
			return False
	return True

def ormap(f, l):
	for i in l:
		if f(i):
			return True
	return False

# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/410692
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration
    
    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False

class Weekday:
	@staticmethod
	def isWeekDay(day):
		return day.weekday() < 5

	@staticmethod
	def today():
		day = datetime.now()
		while not Weekday.isWeekDay(day):
			day += timedelta(1)
		return day

	@staticmethod
	def shift(n, day = None):
		if not day: day = Weekday.today()
		if n == 0: return day
		one = timedelta(1 if n > 0 else -1)
		n = abs(n)

		for _ in range(n):
			day += one
			while not Weekday.isWeekDay(day):
				day += one

		return day
