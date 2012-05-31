from utils import *
from DB import ActiveRecord, db
from Project import Project
from Sprint import Sprint
from Task import statuses, statusMenu
from User import User
from handlers.sprints import tabs as sprintTabs

class Prefs(ActiveRecord):
	user = ActiveRecord.idObjLink(User, 'userid')

	def __init__(self, userid, defaultSprintTab, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.userid = userid
		self.defaultSprintTab = defaultSprintTab

		self.backlogStyles = {}
		for row in db().select("SELECT status, style FROM prefs_backlog_styles WHERE userid = ?", self.userid):
			self.backlogStyles[row['status']] = row['style']

		self.messages = {}
		for row in db().select("SELECT type, enabled FROM prefs_messages WHERE userid = ?", self.userid):
			self.messages[row['type']] = not not row['enabled']

	def getLogString(self):
		return "default sprint tab: %s\nbacklog styles: %s" % (self.defaultSprintTab, ', '.join("%s: %s" % (k, v) for k, v in self.backlogStyles.iteritems()))

	@staticmethod
	def create(user, defaultSprintTab, backlogStyles, messages):
		rtn = Prefs(user.id, defaultSprintTab)
		rtn.backlogStyles = backlogStyles
		rtn.messages = messages
		return rtn

	def save(self):
		for status, style in self.backlogStyles.iteritems():
			if self.id:
				db().update("UPDATE prefs_backlog_styles SET style = ? WHERE userid = ? AND status = ?", style, self.userid, status)
			else:
				db().update("INSERT INTO prefs_backlog_styles(userid, status, style) VALUES(?, ?, ?)", self.userid, status, style)

		for type, enabled in self.messages.iteritems():
			if self.id:
				db().update("UPDATE prefs_messages SET enabled = ? WHERE userid = ? AND type = ?", enabled, self.userid, type)
			else:
				db().update("INSERT INTO prefs_messages(userid, type, enabled) VALUES(?, ?, ?)", self.userid, type, enabled)

		ActiveRecord.save(self)

	@classmethod
	def table(cls):
		return 'Prefs'

	@staticmethod
	def getDefaults(user):
		return Prefs.create(user, 'backlog', dict((name, 'show') for block in statusMenu for name in block), {'sprintMembership': False, 'taskAssigned': False, 'note': True, 'priv': True})
messageTypes = [('sprintMembership', "Added to a sprint"), ('taskAssigned', "Assigned a task"), ('note', "Mentioned in a note"), ('priv', "Granted a privilege")]
