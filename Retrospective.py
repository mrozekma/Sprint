from collections import OrderedDict

from DB import ActiveRecord, db
from Project import Project
from Sprint import Sprint
from utils import *

DEFAULT_CATEGORIES = ['Product Management', 'Infrastructure', 'Teamwork', 'Release Planning', 'Scrum Process', 'Engineering Practices']

class Category(ActiveRecord):
	sprint = ActiveRecord.idObjLink(Sprint, 'sprintid')

	def __init__(self, sprintid, name, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.sprintid = sprintid
		self.name = name

	@staticmethod
	def table():
		return 'retrospective_categories'

class Entry(ActiveRecord):
	category = ActiveRecord.idObjLink(Category, 'catid')

	def __init__(self, catid, body, good, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.catid = catid
		self.body = body
		self.good = good

	@staticmethod
	def table():
		return 'retrospective_entries'

class Retrospective:
	@staticmethod
	def load(sprint):
		rtn = OrderedDict()
		for category in Category.loadAll(sprintid = sprint.id):
			rtn[category] = Entry.loadAll(catid = category.id)
		return rtn or None

	@staticmethod
	def init(sprint):
		for name in DEFAULT_CATEGORIES:
			Category(sprint.id, name).save()

