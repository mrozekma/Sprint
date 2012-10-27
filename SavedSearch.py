from DB import ActiveRecord, db
from User import User
from utils import *

class SavedSearch(ActiveRecord):
	user = ActiveRecord.idObjLink(User, 'userid')

	def __init__(self, userid, name, query, public, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.userid = userid
		self.name = name
		self.query = query
		self.public = public

	@staticmethod
	def table():
		return 'searches'

	def following(self, user):
		if not user or not user.id or not self.id:
			return False
		return db().matches("SELECT u.* FROM search_uses AS u, searches AS s WHERE u.searchid = s.id AND u.searchid = ? AND u.userid = ?", self.id, user.id)

	def follow(self, user):
		db().update("INSERT INTO search_uses(searchid, userid) VALUES(?, ?)", self.id, user.id)

	def unfollow(self, user = None):
		if user:
			db().update("DELETE FROM search_uses WHERE searchid = ? AND userid = ?", self.id, user.id)
		else:
			db().update("DELETE FROM search_uses WHERE searchid = ?", self.id)
