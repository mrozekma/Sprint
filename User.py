from inspect import getmembers

from DB import ActiveRecord, db
from Privilege import Privilege
from utils import md5

class User(ActiveRecord):
	def __init__(self, username, password, lastseen = 0, resetkey = 0, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.username = username
		self.password = password
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
		clazz = 'user'

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
		return Privilege.load(id = self.id)

	def hasPrivilege(self, name):
		if not self.id:
			return False
		return db().matches("SELECT g.* FROM grants AS g, privileges AS p WHERE g.userid=? AND g.privid=p.id AND p.name=?", self.id, name)

	def getAvatar(self, size = 64):
		email = "%s@microsemi-wl.com" % self.username
		email = md5(email.strip().lower())
		return "http://www.gravatar.com/avatar/%s?s=%d&d=wavatar&r=pg" % (email, size)

	@staticmethod
	def crypt(username, password):
		return md5("%s\t%s" % (username, password))

# print map(str, User.loadAll())
# print User.load(1)
# print User.load(100)

# usr = User.load(1)
# usr.username = 'foobar'
# usr.save()

# usr = User('newuser', 'password')
# usr.save()
