import re

from fuzzywuzzy.fuzz import partial_ratio

from User import User
from Task import Task

from utils import *

keys = {
	'assigned': lambda s: filter(None, (User.load(username = username) for username in s.split(','))),
	'highlight': lambda s: filter(None, (Task.load(int(id)) for id in s.split(',') if id != ''))
}
min_match = 80

keyPattern = re.compile("(%s):([^ ]+)" % '|'.join(keys.keys()))

class Search:
	def __init__(self, str):
		self.fullStr = str or ''
		self.str = []
		self.keys = {}

		if str:
			for part in str.split(' '):
				match = keyPattern.match(part)
				if match:
					key, value = match.groups()
					self.keys[key] = keys[key](value)
				else:
					self.str.append(part)

		self.str = ' '.join(self.str)

	def hasBaseString(self): return self.getBaseString() != ''
	def getBaseString(self): return self.str

	def hasFullString(self): return self.getFullString() != ''
	def getFullString(self): return self.fullStr

	def get(self, key): return self.keys[key] if self.has(key) else self.getDefault(key)
	def getDefault(self, key): return keys[key]('')
	def has(self, key): return key in self.keys

	def minMatchPercent(self): return min_match

	def included(self, task):
		return partial_ratio(task.name.lower(), self.getBaseString().lower()) >= self.minMatchPercent()

	def filter(self, tasks):
		return __builtins__['filter'](lambda task: self.included(task), tasks)
