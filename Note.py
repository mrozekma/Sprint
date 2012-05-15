from markdown import Markdown, Extension

from DB import ActiveRecord
from Task import Task
from User import User
from utils import *

standardExtensions = ['nl2br', 'fenced_code', 'sane_lists'] # 'codehilite'

extensions = standardExtensions[:]
import markdown_extensions
for v in markdown_extensions.__dict__.values():
	try:
		if issubclass(v, Extension) and v != Extension:
			extensions.append(v())
	except TypeError:
		pass

md = Markdown(output_format = 'html4', safe_mode = 'escape', lazy_ol = False, extensions = extensions)

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
