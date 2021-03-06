from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
import re
import smtplib
import sys
import time
from threading import Thread
from time import mktime, sleep

from rorn.utils import *

DATE_FMT = '%d %b %Y'
UTC_OFFSET = (time.timezone / -3600) + time.daylight
HTML_COLORS = {'red': '#f00', 'orange': '#ffa500', 'yellow': '#ff0', 'green': '#0f0', 'blue': '#00f', 'purple': '#f0f', 'status': '#33b5e5'}

def tsToDate(timestamp): return datetime.fromtimestamp(timestamp)
def dateToTs(d): return mktime(d.timetuple())
def tsStripHours(timestamp): return dateToTs(tsToDate(timestamp).date())
def utcToLocal(timestamp): return timestamp + (UTC_OFFSET * 3600)
def localToUTC(timestamp): return timestamp - (UTC_OFFSET * 3600)
def tsStart(timestamp): return dateToTs(tsToDate(timestamp).replace(hour = 0, minute = 0, second = 0))
def tsEnd(timestamp): return dateToTs(tsToDate(timestamp).replace(hour = 23, minute = 59, second = 59))
def formatDate(d): return d.strftime(DATE_FMT)

def threadYield():
	sleep(0)

class RunBG(Thread):
	def __init__(self, fn):
		Thread.__init__(self)
		self.fn = fn

	def run(self):
		self.fn()

def bg(fn):
	RunBG(fn).start()

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
		return Weekday.nextWeekday(getNow())

	@staticmethod
	def nextWeekday(day):
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

def to_int(val, name, error_handler):
	if isinstance(val, list):
		try:
			return [int(subval) for subval in val]
		except ValueError:
			error_handler("Expected %s element to be an integer; was `%s'" % (stripTags(name), stripTags(subval)))
	elif isinstance(val, set):
		try:
			return set(int(subval) for subval in val)
		except ValueError:
			error_handler("Expected %s element to be an integer; was `%s'" % (stripTags(name), stripTags(subval)))
	else:
		try:
			return int(val)
		except ValueError:
			error_handler("Expected %s to be an integer; was `%s'" % (stripTags(name), stripTags(val)))

def to_bool(val):
	return val in [True, 'true', 1]

def minOr(vals, default = 0):
	try:
		return min(vals)
	except ValueError:
		return default

def maxOr(vals, default = 0):
	try:
		return max(vals)
	except ValueError:
		return default

def uniq(l):
	rtn = []
	for n in l:
		if not n in rtn:
			rtn.append(n)
	return rtn

def ensureList(l):
	return l if isinstance(l, list) else [l]

nowDelta = timedelta()
def getNow():
	return datetime.now() + nowDelta
def getNowDelta():
	return nowDelta
def setNowDelta(delta):
	global nowDelta
	nowDelta = delta

def partition(pred, iter):
	good, bad = [], []
	for item in iter:
		(good if pred(item) else bad).append(item)
	return good, bad

def sendmail(to, subject, body):
	from Settings import settings
	if not settings.smtpServer:
		raise RuntimeError("No SMTP server configured")
	msg = MIMEText(body)
	msg['Subject'] = subject
	msg['From'] = settings.smtpFrom
	msg['To'] = to
	smtp = smtplib.SMTP(settings.smtpServer)
	smtp.sendmail(settings.smtpFrom, to, msg.as_string())
	smtp.quit()

def lipsum():
	return """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pharetra ornare tortor, a ornare nibh aliquam et. Cras ultricies rutrum magna et elementum. Aliquam at sapien ante, sit amet fermentum nisi. Maecenas in arcu ante. Etiam ac ligula sed est elementum rhoncus vitae et urna. Vestibulum tempus enim quis nisi rutrum venenatis. Vivamus dapibus aliquet erat, pellentesque dapibus leo placerat lacinia. Suspendisse potenti. Etiam nisl felis, aliquam in molestie id, dapibus feugiat dolor. Duis sagittis auctor fringilla. Curabitur tellus neque, vehicula a imperdiet ut, ullamcorper in nunc. Aliquam tincidunt ornare fringilla. Suspendisse potenti. Vestibulum quis turpis dignissim lectus ullamcorper viverra.<br><br>

Mauris eu orci a lacus interdum commodo. Cras faucibus, mauris in malesuada rutrum, ante ante fermentum enim, eu tempor augue sapien in elit. Sed eu ligula lacus. Donec iaculis semper auctor. Nam ut turpis at orci vehicula scelerisque. Nam euismod accumsan eros, tempor tincidunt tortor luctus sit amet. Cras ac metus nibh, a congue urna. Pellentesque tempus lorem a magna condimentum fermentum. Quisque ac elit non nunc tincidunt pretium id convallis tortor. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. In tincidunt est in velit egestas pellentesque sollicitudin sed massa. Morbi vulputate, mi vitae tempor posuere, metus nunc sodales odio, ut cursus velit nisi eu lorem. Maecenas scelerisque sodales mi, at ultricies risus tristique eget. Phasellus faucibus leo ac tortor ullamcorper cursus. Vivamus ligula turpis, varius et mattis volutpat, hendrerit sit amet ante. Fusce et sapien id elit iaculis pellentesque. Fusce odio nibh, ultrices et facilisis at, tempor vel dolor. Donec sed justo sed diam blandit rhoncus.<br><br>

Sed ullamcorper orci eget erat posuere non malesuada mi iaculis. Maecenas dictum metus vel diam pellentesque rhoncus. Ut tempus dictum augue, id sollicitudin ligula facilisis rhoncus. Maecenas suscipit nunc sed felis pharetra id commodo metus bibendum. Curabitur diam nulla, cursus ut fringilla a, lobortis eget orci. Quisque adipiscing dui ornare elit pulvinar luctus. Vivamus justo turpis, vehicula sed tincidunt aliquam, tincidunt at nunc. Maecenas vitae ante nunc. Aenean sed nulla ac turpis vestibulum luctus quis nec ante. Maecenas a erat eu quam convallis pellentesque eu vel mi. Suspendisse potenti. Nam sollicitudin lectus vitae velit blandit accumsan. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. In faucibus bibendum semper. Etiam tellus elit, egestas et ullamcorper vitae, dignissim in lectus.<br><br>

Nunc bibendum fermentum ipsum, ut sodales mi lacinia sit amet. Sed ipsum magna, sollicitudin euismod elementum a, egestas in nulla. Vestibulum non pharetra justo. Donec euismod mauris quis justo commodo quis porta sapien bibendum. Vestibulum velit enim, aliquet dapibus porttitor eu, suscipit ac eros. Duis lobortis metus vitae est iaculis molestie. Proin augue leo, consectetur ac lobortis accumsan, molestie et nisi. Aliquam erat volutpat. Fusce pharetra, metus non mollis condimentum, elit mauris consectetur turpis, ut tincidunt sem dui vel quam. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Pellentesque suscipit, nulla at pharetra mattis, eros arcu ullamcorper nulla, eu ornare dui lacus vitae tortor. Proin egestas, purus et vestibulum tempor, dui justo egestas lectus, nec eleifend sapien metus non sapien. Etiam sed vehicula ligula. Donec sollicitudin blandit erat nec posuere. Fusce ac elit urna, commodo ullamcorper justo. Quisque tellus leo, sollicitudin nec elementum in, convallis non lectus. Phasellus varius dolor vitae metus tristique ac mattis urna interdum.<br><br>

Nulla ut leo id ante facilisis ullamcorper. Fusce eleifend, felis sed elementum sollicitudin, tortor metus hendrerit lectus, sed hendrerit massa orci at purus. Vestibulum at est libero, et bibendum velit. Ut ac tortor nec justo accumsan porta. Maecenas ut facilisis orci. Proin in fringilla est. Sed a feugiat massa. Curabitur nec aliquam purus. Aliquam erat volutpat. Vivamus urna mi, imperdiet vitae egestas eget, ornare eget dui. Vestibulum eget odio in metus pulvinar tempus in non felis. Morbi sollicitudin, arcu non imperdiet bibendum, mauris libero condimentum nunc, ut fringilla velit sapien eu magna."""
