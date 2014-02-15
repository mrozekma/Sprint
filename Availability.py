from utils import *
from User import User
from Project import Project
from Sprint import Sprint

from stasis.Singleton import get as db

class Availability:
	def __init__(self, sprint):
		self.sprint = sprint

	def get(self, user, timestamp):
		table = db()['availability']
		if self.sprint.id in table:
			data = table[self.sprint.id]
			if user.id in data:
				ts = dateToTs(timestamp)
				if ts in data[user.id]:
					return data[user.id][ts]
		return 0

	def getAll(self, timestamp):
		rtn = 0
		ts = dateToTs(timestamp)
		table = db()['availability']
		if self.sprint.id in table:
			for data in table[self.sprint.id].values():
				if ts in data:
					rtn += data[ts]
		return rtn

	def set(self, user, timestamp, hours):
		table = db()['availability']
		if self.sprint.id not in table:
			table[self.sprint.id] = {}
		with table.change(self.sprint.id) as data:
			if user.id not in data:
				data[user.id] = {}
			data[user.id][dateToTs(timestamp)] = hours

	def delete(self, user):
		table = db()['availability']
		if self.sprint.id in table:
			if user.id in table[self.sprint.id]:
				with table.change(self.sprint.id) as data:
					del data[user.id]

	def getAllForward(self, timestamp, user = None):
		rtn = 0
		ts = dateToTs(timestamp)
		table = db()['availability']
		if self.sprint.id in table:
			for userid, data in table[self.sprint.id].iteritems():
				if user is not None and user.id != userid:
					continue
				for thisstamp, hours in data.iteritems():
					if thisstamp >= ts:
						rtn += hours
		return rtn

	def trim(self):
		table = db()['availability']
		if self.sprint.id in table:
			with table.change(self.sprint.id) as data:
				for userid, hourmap in data.iteritems():
					data[userid] = {timestamp: hours for timestamp, hours in hourmap.iteritems() if self.sprint.start <= timestamp <= self.sprint.end}
