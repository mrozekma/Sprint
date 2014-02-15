from inspect import getmembers

from Settings import settings
from utils import md5

from stasis.ActiveRecord import ActiveRecord

USERNAME_PATTERN = '[a-zA-Z0-9]+'
AVATAR_TYPES = ['png', 'gif', 'jpeg']
AVATAR_MAX_SIZE = 5 * 1024 * 1024 # bytes

class User(ActiveRecord):
	def __init__(self, username, password, hotpKey = '', lastseen = 0, resetkey = 0, avatar = None, privileges = set(), id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.username = username
		self.password = password
		self.hotpKey = hotpKey
		self.lastseen = lastseen
		self.resetkey = resetkey
		self.avatar = avatar
		self.privileges = privileges

		if not id:
			self.password = User.crypt(self.username, self.password)

	def save(self):
		#DEBUG #NO
		if not isinstance(self.privileges, (set, frozenset)):
			raise RuntimeError("Broken type (%s)" % type(self.privileges).__name__)
		newUser = (self.id is None)
		ActiveRecord.save(self)
		if newUser:
			from Prefs import Prefs
			Prefs.getDefaults(self).save()

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
		self.__init__(**{field: vals[field] for field in fields})

	def hasPrivilege(self, name):
		return name in self.privileges

	def getPrefs(self):
		from Prefs import Prefs
		return Prefs.load(self.id)

	def getEmail(self):
		return "%s@%s" % (self.username, settings.emailDomain)

	def getAvatar(self, size = 64):
		if self.hasLocalAvatar():
			return "/users/%s/avatar?size=%d" % (self.username, size)
		else:
			email = md5(self.getEmail().strip().lower())
			return "http://www.gravatar.com/avatar/%s?s=%d&d=wavatar&r=pg" % (email, size)

	def hasLocalAvatar(self):
		return self.avatar is not None

	@staticmethod
	def getBlankAvatar(size = 64):
		return "http://www.gravatar.com/avatar/%s?s=%d&d=mm" % ('0' * 64, size)

	@staticmethod
	def crypt(username, password):
		return md5("%s\t%s" % (username, password))
