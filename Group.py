from utils import *
from DB import ActiveRecord, db
from Sprint import Sprint
# from inspect import getmembers

class Group(ActiveRecord):
	sprint = ActiveRecord.idObjLink(Sprint, 'sprintid')

	def __init__(self, sprintid, name, seq = None, deletable = True, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.sprintid = sprintid
		self.name = name
		self.seq = seq if seq else maxOr(group.seq for group in self.sprint.getGroups())+1
		self.deletable = to_bool(deletable)

	def getTasks(self):
		return filter(lambda t: t.group and t.group == self, self.sprint.getTasks())

	def __str__(self):
		return self.safe.name
