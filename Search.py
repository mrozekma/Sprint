import re
import shlex

from fuzzywuzzy.fuzz import partial_ratio

from User import User
from Task import Task, statuses
from Goal import Goal

from utils import *

min_match = 80

class Filter(object):
	def __init__(self, search, value):
		self.search = search
		self.value = value

	@classmethod
	def getKey(cls):
		return cls.__name__.lower()

	def included(self, task):
		return True

	def filter(self, tasks):
		return [task for task in tasks if self.included(task)]

	def description(self):
		return None

	@classmethod
	def get(cls, search, terms):
		key = cls.getKey()
		for i in range(len(terms)):
			term = terms[i]
			if term[:len(key)+1] == key + ':':
				terms.pop(i)
				return cls(search, term[len(key)+1:])
		return None

# These are handled specially in the sprints handler, so they doesn't need any implementations
class Assigned(Filter):
	def __init__(self, search, value):
		self.users = filter(None, (User.load(username = username) for username in value.split(',')))
class Status(Filter):
	def __init__(self, search ,value):
		value = value.replace('-', ' ').replace('_', ' ')
		self.statuses = [statuses[status] for status in value.split(',') if status in statuses]
class Highlight(Filter):
	def __init__(self, search, value):
		self.tasks = filter(None, (Task.load(int(id)) for id in value.split(',')))

class Hours(Filter):
	def __init__(self, search, value):
		try:
			if len(value) > 2 and value[0:2] == '<=':
				self.min, self.max = None, int(value[2:])
			elif len(value) > 2 and value[0:2] == '>=':
				self.min, self.max = int(value[2:]), None
			elif value[0] == '<':
				self.min, self.max = None, int(value[1:]) - 1
			elif value[0] == '>':
				self.min, self.max = int(value[1:]) + 1, None
			elif value[0] == '-':
				self.min, self.max = None, int(value[1:])
			elif value[-1] == '-':
				self.min, self.max = int(value[:-1]), None
			elif '-' in value:
				self.min, self.max = map(int, value.split('-', 1))
			else:
				self.min = self.max = int(value)
		except (ValueError, IndexError):
			self.min = self.max = None

	def included(self, task):
		# Check if the filter spec was broken; include all tasks if so
		if self.min == self.max == None:
			return True

		# Check the actual hours
		min = task.hours if self.min is None else self.min
		max = task.hours if self.max is None else self.max
		return min <= task.hours <= max

	def description(self):
		if self.min == None and self.max == None:
			return None
		elif self.min == None:
			return "with at most %s remaining" % pluralize(self.max, 'hour', 'hours')
		elif self.max == None:
			return "with at least %s remaining" % pluralize(self.min, 'hour', 'hours')
		elif self.min == self.max:
			return "with %s remaining" % pluralize(self.min, 'hour', 'hours')
		else:
			return "with %d-%d hours remaining" % (self.min, self.max)

class GoalFilter(Filter):
	def __init__(self, search, value):
		values = value.split(',')
		self.goals = filter(lambda goal: goal and goal.name != '', (Goal.load(sprintid = search.sprint.id, color = clr) for clr in values))
		if 'none' in values:
			self.goals.append(None)
		if self.goals == []:
			self.goals = None

	@classmethod
	def getKey(cls):
		return 'goal'

	def included(self, task):
		return self.goals == None or task.goal in self.goals

	def description(self):
		return None if self.goals == None else "with goals %s" % ', '.join(goal.name if goal else '(none)' for goal in self.goals)


class TimeRange(Filter):
	def __init__(self, search, value, taskHandler):
		self.taskHandler = taskHandler
		try:
			if '-' in value:
				min, max = value.split('-', 1)
				self.min = datetime.strptime(min, '%Y%m%d')
				self.max = getNow() if max == '' else datetime.strptime(max, '%Y%m%d')
			else:
				self.min = self.max = datetime.strptime(value, '%Y%m%d')
			self.max = self.max.replace(hour = 23, minute = 59, second = 59)
		except ValueError:
			self.min = self.max = None

	def included(self, task):
		if self.min == None or self.max == None:
			return True
		for test in self.taskHandler(task):
			if self.min <= tsToDate(test.timestamp) <= self.max:
				return True
		return False

	def description(self):
		if self.min == None or self.max == None:
			return None
		elif self.min.date() == self.max.date():
			return "%s %s" % (self.__class__.__name__.lower(), self.min.strftime('%Y-%m-%d'))
		else:
			return "%s between %s and %s" % (self.__class__.__name__.lower(), self.min.strftime('%Y-%m-%d'), self.max.strftime('%Y-%m-%d'))

class Created(TimeRange):
	def __init__(self, search, value):
		TimeRange.__init__(self, search, value, lambda task: [task.getRevision(1)])

class Modified(TimeRange):
	def __init__(self, search, value):
		TimeRange.__init__(self, search, value, lambda task: task.getRevisions())

filters = Filter.__subclasses__()
filters += [cls for sublist in filters for cls in sublist.__subclasses__()]

class Search:
	def __init__(self, sprint, str):
		self.fullStr = str or ''
		self.sprint = sprint

		terms = shlex.split(self.fullStr)
		self.filters = (filt.get(self, terms) for filt in filters)
		self.filters = dict((filt.getKey(), filt) for filt in self.filters if filt != None)
		self.str = ' '.join(terms)

	def hasBaseString(self): return self.getBaseString() != ''
	def getBaseString(self): return self.str

	def hasFullString(self): return self.getFullString() != ''
	def getFullString(self): return self.fullStr

	def get(self, key): return self.filters[key]
	def getAll(self): return self.filters.values()
	def has(self, key): return key in self.filters

	@staticmethod
	def minMatchPercent(): return min_match

	def filter(self, tasks):
		for filt in self.filters.values():
			tasks = filt.filter(tasks)
		if self.hasBaseString():
			tasks = filter(lambda task: partial_ratio(task.name.lower(), self.getBaseString().lower()) >= Search.minMatchPercent(), tasks)
		return tasks
