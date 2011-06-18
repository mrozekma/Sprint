from DB import ActiveRecord, db
from Privilege import Privilege
from utils import md5

class User(ActiveRecord):
	def __init__(self, username, password, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.username = username
		self.password = password

		if not id:
			self.password = md5(self.password)

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
			s += "<a %shref=\"/users/?username=%s\">%s</a>" % ("id=\"%s\" " % id if id else '', self.username, self.username)
		else:
			s += "<span %sclass=\"username\" username=\"%s\">%s</span>" % ("id=\"%s\" " % id if id else '', self.username, self.username)

		return s
	def __str__(self):
		return self.str()

	def __cmp__(self, other):
		return cmp(self.username, other.username)

	def getPrivileges(self):
		return Privilege.load(id = self.id)

	def hasPrivilege(self, name):
		if not self.id:
			return False
		return db().matches("SELECT g.* FROM grants AS g, privileges AS p WHERE g.userid=? AND g.privid=p.id AND p.name=?", self.id, name)

	def getAvatar(self):
		email = "%s@arxandefense.com" % self.username
		email = md5(email.strip().lower())
		return "http://www.gravatar.com/avatar/%s?s=64&d=wavatar" % email

# print map(str, User.loadAll())
# print User.load(1)
# print User.load(100)

# usr = User.load(1)
# usr.username = 'foobar'
# usr.save()

# usr = User('newuser', 'password')
# usr.save()
