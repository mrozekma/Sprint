from utils import *
from DB import ActiveRecord, db
from Sprint import Sprint

COLORS = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']

class Goal(ActiveRecord):
	sprint = ActiveRecord.idObjLink(Sprint, 'sprintid')

	def __init__(self, sprintid, name, color, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.sprintid = sprintid
		self.name = name
		self.color = color

	@staticmethod
	def newSet(sprint):
		goals = [Goal(sprint.id, '', clr) for clr in COLORS]
		map(lambda goal: goal.save(), goals)
		return goals

	def __str__(self):
		return self.safe.name