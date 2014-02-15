from utils import *
from Sprint import Sprint

from stasis.ActiveRecord import ActiveRecord, link

COLORS = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']

class Goal(ActiveRecord):
	sprint = link(Sprint, 'sprintid')

	def __init__(self, sprintid, name, color, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.sprintid = sprintid
		self.name = name
		self.color = color

	def getHTMLColor(self):
		return HTML_COLORS[self.color]

	@staticmethod
	def newSet(sprint):
		goals = [Goal(sprint.id, '', clr) for clr in COLORS]
		map(lambda goal: goal.save(), goals)
		return goals

	def __str__(self):
		return self.safe.name
