from Task import Task
from User import User
from Markdown import Markdown
from utils import *

from stasis.ActiveRecord import ActiveRecord, link

class Note(ActiveRecord):
	task = link(Task, 'taskid')
	user = link(User, 'userid')

	def __init__(self, taskid, userid, body, timestamp = None, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.taskid = taskid
		self.userid = userid
		self.body = body
		self.timestamp = timestamp or dateToTs(getNow())

	def render(self):
		return Markdown.render(self.body)
