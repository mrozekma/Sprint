from User import User
from Markdown import Markdown
from utils import *

from stasis.ActiveRecord import ActiveRecord, link

class Message(ActiveRecord):
	user = link(User, 'userid')
	sender = link(User, 'senderid')

	def __init__(self, userid, senderid, title, body, language = 'html', timestamp = None, read = False, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.userid = userid
		self.senderid = senderid
		self.title = title
		self.body = body
		self.language = language
		self.timestamp = timestamp or dateToTs(getNow())
		self.read = read

	def render(self):
		for case in switch(self.language):
			if case('markdown'):
				return Markdown.render(self.body)
			elif case('html'):
				return self.body
			else: # Shouldn't happen
				return self.body
