from inspect import getmembers

from DB import ActiveRecord, db
from Privilege import Privilege
from Settings import settings
from utils import md5

class User(ActiveRecord):
	def __init__(self, username, password, hotpKey = '', lastseen = 0, resetkey = 0, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.username = username
		self.password = password
		self.hotpKey = hotpKey
		self.lastseen = lastseen
		self.resetkey = resetkey

		if not id:
			self.password = User.crypt(self.username, self.password)

	def str(self, role = None, link = True, id = None):
		roles = {
			None: 'user-online',
			'member': 'member',
			'scrummaster': 'scrummaster'
		}

		image = roles[role if role in roles else None]

		s = "<img src=\"/static/images/%s.png\" class=\"user\">" % image

		if link:
			s += "<a %shref=\"/users/%s\">%s</a>" % ("id=\"%s\" " % id if id else '', self.username, self.username)
		else:
			s += "<span %sclass=\"username\" username=\"%s\">%s</span>" % ("id=\"%s\" " % id if id else '', self.username, self.username)

		return s

	def __str__(self):
		return self.str()

	def __cmp__(self, other):
		return cmp(self.username, other.username)

	def __getstate__(self):
		return self.id

	def __setstate__(self, state):
		other = User.load(state)
		fields = set(User.fields())
		vals = dict(getmembers(other))
		self.__init__(**dict([(field, vals[field]) for field in fields]))

	def getPrivileges(self):
		return Privilege.load(userid = self.id)

	def hasPrivilege(self, name):
		if not self.id:
			return False
		return db().matches("SELECT g.* FROM grants AS g, privileges AS p WHERE g.userid=? AND g.privid=p.id AND p.name=?", self.id, name)

	def getPrefs(self):
		from Prefs import Prefs
		return Prefs.load(userid = self.id) or Prefs.getDefaults(self)

	def getEmail(self):
		return "%s@%s" % (self.username, settings.emailDomain)

	def getAvatar(self, size = 64):
		email = md5(self.getEmail().strip().lower())
		return "http://www.gravatar.com/avatar/%s?s=%d&d=wavatar&r=pg" % (email, size)

	@staticmethod
	def getBlankAvatar(size = 64):
		return "http://www.gravatar.com/avatar/%s?s=%d&d=mm" % ('0' * 64, size)

	@staticmethod
	def crypt(username, password):
		return md5("%s\t%s" % (username, password))
