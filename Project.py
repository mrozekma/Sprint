from rorn.ResponseWriter import ResponseWriter

from DB import ActiveRecord, db
from LoadValues import isDevMode
from User import User
from utils import stripTags

class Project(ActiveRecord):
	# Test projects have negative IDs
	def __init__(self, name, id = None):
		ActiveRecord.__init__(self)
		self.id = id
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

	@classmethod
	def loadAll(cls, orderby = None, **attrs):
		return filter(lambda project: project.id > 0, super(Project, cls).loadAll(orderby = orderby, **attrs))

	@classmethod
	def loadAllTest(cls, orderby = None, **attrs):
		return filter(lambda project: project.id < 0, super(Project, cls).loadAll(orderby = orderby, **attrs))

	@staticmethod
	def getAllSorted(user = None, firstProject = None):
		# Ordering:
		#   * firstProject (if not None)
		#   * Active projects this user is in
		#   * Other active projects
		#   * Inactive projects
		#   * Test projects

		def sortKey(project):
			if project == firstProject:
				return 0
			sprints = project.getSprints()
			activeSprints = filter(lambda sprint: sprint.isActive(), sprints)
			activeMembers = set(sum((sprint.members for sprint in activeSprints), []))
			if user and user in activeMembers:
				return 1
			if activeSprints:
				return 2
			return 3

		projects = Project.loadAll(orderby = 'name') # First, just alphabetize
		projects = sorted(projects, key = sortKey) # Then use sortKey
		if isDevMode() and user and user.hasPrivilege('Dev'):
			projects += Project.loadAllTest()

		return projects

from Sprint import Sprint
