from LoadValues import isDevMode
from User import User
from utils import stripTags

from rorn.ResponseWriter import ResponseWriter
from stasis.ActiveRecord import ActiveRecord

class Project(ActiveRecord):
	# Test projects have negative IDs
	def __init__(self, name, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.name = name

	def getSprints(self):
		from Sprint import Sprint
		return Sprint.loadAll(projectid = self.id)

	def getMembers(self):
		members = []
		for sprint in self.getSprints():
			members += sprint.members
		return set(members)

	def __str__(self):
		return "<img src=\"/static/images/project.png\" class=\"project\"><a href=\"/projects/?id=%d\">%s</a>" % (self.id, self.safe.name)

	@classmethod
	def loadAll(cls, **attrs):
		return filter(lambda project: project.id > 0, super(Project, cls).loadAll(**attrs))

	@classmethod
	def loadAllTest(cls, **attrs):
		return filter(lambda project: project.id < 0, super(Project, cls).loadAll(**attrs))

	@staticmethod
	def getAllSorted(user = None, firstProject = None):
		# Ordering:
		#   * firstProject (if not None)
		#   * Active projects this user is in
		#     - Projects with a planning sprint
		#     - Projects with a review sprint
		#     - Projects with any active sprint
		#   * Other active projects
		#   * Inactive projects
		#   * Test projects

		def sortKey(project):
			if project == firstProject:
				return 0
			sprints = project.getSprints()
			activeSprints = filter(lambda sprint: sprint.isPlanning() or sprint.isActive(), sprints)
			activeMembers = set()
			for sprint in activeSprints:
				activeMembers |= sprint.members
			if user and user in activeMembers:
				if filter(lambda sprint: sprint.isPlanning(), activeSprints):
					return 1
				elif filter(lambda sprint: sprint.isReview(), activeSprints):
					return 2
				return 3
			if activeSprints:
				return 4
			return 5

		projects = Project.loadAll(orderby = 'name') # First, just alphabetize
		projects = sorted(projects, key = sortKey) # Then use sortKey
		if isDevMode() and user and user.hasPrivilege('Dev'):
			projects += Project.loadAllTest()

		return projects
