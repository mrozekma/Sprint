from utils import *
from Project import Project
from Sprint import Sprint
from Task import statuses, statusMenu
from User import User
from handlers.sprints import tabs as sprintTabs

from rorn.ResponseWriter import ResponseWriter
from stasis.ActiveRecord import ActiveRecord, link

class Prefs(ActiveRecord):
	user = link(User, 'id')

	def __init__(self, id, defaultSprintTab, defaultTasksTab, backlogStyles, messages):
		ActiveRecord.__init__(self)
		self.id = id # Same as the parent user's ID
		self.defaultSprintTab = defaultSprintTab
		self.defaultTasksTab = defaultTasksTab
		self.backlogStyles = backlogStyles
		self.messages = messages

	def getLogString(self):
		writer = ResponseWriter()
		print "default sprint tab: %s" % self.defaultSprintTab
		print "default tasks tab: %s" % self.defaultTasksTab
		print "backlog styles:"
		for k, v in self.backlogStyles.iteritems():
			print "  %s: %s" % (k, v)
		print "messages:"
		for k, v in self.messages.iteritems():
			print "  %s: %s" % (k, v)
		return writer.done()

	@classmethod
	def table(cls):
		return 'prefs'

	@staticmethod
	def getDefaults(user):
		return Prefs(user.id, 'backlog', 'single', {name: 'show' for block in statusMenu for name in block}, {'sprintMembership': False, 'taskAssigned': False, 'noteMention': True, 'noteRelated': True, 'priv': True})
