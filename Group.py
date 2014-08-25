from utils import *
from Sprint import Sprint

from stasis.Singleton import get as db
from stasis.ActiveRecord import ActiveRecord, link

class Group(ActiveRecord):
	sprint = link(Sprint, 'sprintid')

	def __init__(self, sprintid, name, seq = None, deletable = True, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.sprintid = sprintid
		self.name = name
		self.seq = seq if seq else maxOr(group.seq for group in self.sprint.getGroups()) + 1
		self.deletable = to_bool(deletable)

	def getTasks(self):
		return filter(lambda t: t.group and t.group == self, self.sprint.getTasks())

	def save(self):
		if not self.id:
			# Shift everything after this sequence
			for id, group in db()['groups'].iteritems():
				if group['sprintid'] == self.sprintid and group['seq'] >= self.seq:
					with db()['groups'].change(id) as data:
						data['seq'] += 1
		return ActiveRecord.save(self)

	def move(self, newSeq):
		# Remove group from the list
		for id, group in db()['groups'].iteritems():
			if group['sprintid'] == self.sprintid and group['seq'] > self.seq:
				with db()['groups'].change(id) as data:
					data['seq'] -= 1

		# Insert it at the new spot
		if newSeq:
			self.seq = newSeq
			for id, group in db()['groups'].iteritems():
				if group['sprintid'] == self.sprintid and group['seq'] >= self.seq:
					with db()['groups'].change(id) as data:
						data['seq'] += 1

		self.save()

	def delete(self):
		self.move(None)
		return ActiveRecord.delete(self)

	def __str__(self):
		return self.safe.name
