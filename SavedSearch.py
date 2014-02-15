from User import User
from utils import *

from stasis.ActiveRecord import ActiveRecord, link

class SavedSearch(ActiveRecord):
	user = link(User, 'userid')
	followers = link(User, 'followerids')

	def __init__(self, userid, name, query, public, followerids = set(), id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.userid = userid
		self.name = name
		self.query = query
		self.public = public
		self.followerids = followerids

	#DEBUG #NO
	def save(self):
		if not isinstance(self.followerids, (set, frozenset)):
			raise RuntimeError("Broken type (%s)" % type(self.followerids).__name__)
		if not isinstance(self.followers, (set, frozenset)):
			raise RuntimeError("Broken type (%s)" % type(self.followers).__name__)
		return ActiveRecord.save(self)

	@staticmethod
	def table():
		return 'searches'

	def follow(self, user):
		self.followers |= set(user)

	def unfollow(self, user = None):
		if user:
			self.followers -= set(user)
		else:
			self.followers = set()
