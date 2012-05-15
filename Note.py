from markdown import Markdown

from DB import ActiveRecord
from Task import Task
from User import User
from utils import *

md = Markdown(output_format = 'html4', safe_mode = 'escape', lazy_ol = False, extensions = ['nl2br', 'fenced_code']) # 'codehilite'

class Note(ActiveRecord):
	task = ActiveRecord.idObjLink(Task, 'taskid')
	user = ActiveRecord.idObjLink(User, 'userid')

	def __init__(self, taskid, userid, body, timestamp = None, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.taskid = taskid
		self.userid = userid
		self.body = body
		self.timestamp = timestamp or dateToTs(getNow())

	def render(self):
		return md.convert(self.body)
