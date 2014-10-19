import git
import os
from os.path import basename
import re
from traceback import extract_stack
from utils import *

from User import User

from stasis.ActiveRecord import ActiveRecord, link

class ChangeLog:
	id = 1
	def __init__(self, message, urls = None):
		filename, line, _, _ = extract_stack(limit = 2)[0]
		if basename(filename) != 'ChangeLog.py':
			print filename
			raise RuntimeError('Unexpected ChangeLog construction')
		self.id = ChangeLog.id
		ChangeLog.id += 1
		self.hash = None
		self.line = line
		self.message = message
		self.urls = urls

	def onURL(self, url):
		if self.urls is None:
			return True
		for pattern in self.urls:
			if re.match("^%s$" % pattern, url):
				return True
		return False

	# We don't know exactly when this change went live on a given install, so rather than use
	# the commit timestamp we use the time it was first seen, and call it "recent" if it's
	# within two weeks of that first view
	def isRecent(self):
		records = ChangeRecord.loadAll(changeid = self.id)
		if records == []:
			return True
		first = tsToDate(min(record.timestamp for record in records))
		return (getNow() - first) < timedelta(weeks = 2)

class ChangeRecord(ActiveRecord):
	user = link(User, 'userid')

	def __init__(self, changeid, userid, timestamp = None, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.changeid = changeid
		self.userid = userid
		self.timestamp = timestamp if timestamp else dateToTs(getNow())

	@classmethod
	def table(cls):
		return 'changelog_views'

changelog = [
	ChangeLog("From now on, useful but hard to discover recent updates will be displayed on the relevant page the first time you visit it"),
	ChangeLog("The assignee username is now optional -- new tasks will default to being self-assigned", ['/tasks/new/many']),
	ChangeLog("You can upload your list of new tasks as a text file using the form above the textarea", ['/tasks/new/many']),
	ChangeLog("Deferred tasks now retain their hours, but aren't counted in the metrics", ['/sprints/[0-9]+']),
	ChangeLog("The default tab when adding a new task is now <a href=\"/prefs#default-tasks-tab\">customizable</a>", ['/tasks/new/.*']),
	ChangeLog("Importing tasks was rewritten to be less terrible. The interface is now similar to the backlog view"),
]

def getChanges(handler, url, markSeen = True):
	if not handler.session['user']:
		return
	seen = [change.changeid for change in ChangeRecord.loadAll(userid = handler.session['user'].id)]
	for change in changelog:
		if change.onURL(url) and change.id not in seen:
			if markSeen:
				ChangeRecord(change.id, handler.session['user'].id).save()
			if change.isRecent():
				yield change

blame = git.Repo().git.blame('--line-porcelain', '-L', "%d,%d" % (min(change.line for change in changelog), max(change.line for change in changelog)), 'ChangeLog.py')
for hash, startLine, endLine in re.findall("([0-9a-fA-F]{40}) ([0-9]+) ([0-9]+)(?: [0-9]+)?", blame):
	for change in changelog:
		if int(startLine) <= change.line <= int(endLine):
			change.hash = hash
			change.line = None
