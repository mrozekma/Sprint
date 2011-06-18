from utils import *
from DB import ActiveRecord, db
from Sprint import Sprint
# from inspect import getmembers

class Group(ActiveRecord):
	sprint = ActiveRecord.idObjLink(Sprint, 'sprintid')

	def __init__(self, sprintid, seq, name, id = None):
		self.id = id
		self.sprintid = sprintid
		self.seq = seq
		self.name = name

	def __str__(self):
		return self.safe.name
