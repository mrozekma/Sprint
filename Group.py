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

	def save(self):
		if not self.id:
			# Shift everything after this sequence
			db().update("UPDATE groups SET seq = seq + 1 WHERE sprintid = ? AND seq >= ?", self.sprintid, self.seq)
		return ActiveRecord.save(self)

	def move(self, newSeq):
		# Remove group from the list
		db().update("UPDATE groups SET seq = seq - 1 WHERE sprintid = ? AND seq > ?", self.sprintid, self.seq)

		# Insert it at the new spot
		if newSeq:
			self.seq = newSeq
			db().update("UPDATE groups SET seq = seq + 1 WHERE sprintid = ? AND seq > ?", self.sprintid, self.seq)

	def delete(self):
		self.move(None)
		return ActiveRecord.delete(self)

	def __str__(self):
		return self.safe.name
