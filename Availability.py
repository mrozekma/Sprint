from utils import *
from DB import ActiveRecord, db
from User import User
from Project import Project
from Sprint import Sprint

class Availability:
	def __init__(self, sprint):
		self.sprint = sprint

	def get(self, user, timestamp):
		rows = db().select("SELECT hours FROM availability WHERE sprintid = ? AND userid = ? AND timestamp = ?", self.sprint.id, user.id, dateToTs(timestamp))
		rows = [x for x in rows]
		return int(rows[0]['hours']) if len(rows) > 0 else 0

	def set(self, user, timestamp, hours):
		db().update("INSERT OR REPLACE INTO availability(sprintid, userid, timestamp, hours) VALUES(?, ?, ?, ?)", self.sprint.id, user.id, dateToTs(timestamp), hours)

	def getAllForward(self, timestamp):
		rows = db().select("SELECT SUM(hours) FROM availability WHERE sprintid = ? AND timestamp >= ?", self.sprint.id, dateToTs(timestamp))
		rows = [x for x in rows]
		return int(rows[0]['SUM(hours)'])
