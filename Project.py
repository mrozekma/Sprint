from rorn.ResponseWriter import ResponseWriter

from DB import ActiveRecord, db
from User import User
from utils import stripTags

class Project(ActiveRecord):
	owner = ActiveRecord.idObjLink(User, 'ownerid')

	def __init__(self, ownerid, name, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.ownerid = ownerid
		self.name = name

	def getSprints(self):
		return Sprint.loadAll(projectid = self.id)

	def getMembers(self):
		members = []
		for sprint in self.getSprints():
			members += sprint.members
		return set(members)

	def __str__(self):
		return "<img src=\"/static/images/project.png\" class=\"project\"><a href=\"/projects/?id=%d\">%s</a>" % (self.id, self.safe.name)

from Sprint import Sprint
