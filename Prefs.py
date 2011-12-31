from utils import *
from DB import ActiveRecord, db
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

	@staticmethod
	def create(user, defaultSprintTab, backlogStyles):
		rtn = Prefs(user.id, defaultSprintTab)
		rtn.backlogStyles = backlogStyles
		return rtn

	def save(self):
		for (status, style) in self.backlogStyles.iteritems():
			if self.id:
				db().update("UPDATE prefs_backlog_styles SET style = ? WHERE userid = ? AND status = ?", style, self.userid, status)
			else:
				db().update("INSERT INTO prefs_backlog_styles(userid, status, style) VALUES(?, ?, ?)", self.userid, status, style)
		ActiveRecord.save(self)

	@classmethod
	def table(cls):
		return 'Prefs'

	@staticmethod
	def getDefaults(user):
		return Prefs.create(user, 'backlog', dict((name, 'show') for block in statusMenu for name in block))
