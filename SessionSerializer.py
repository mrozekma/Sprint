from rorn.Session import Session
from stasis.Singleton import get as db

class SessionSerializer:
	def __init__(self):
		self.cache = {}

	def get(self, sessionID):
		if sessionID not in self.cache:
			if sessionID not in db()['sessions']:
				db()['sessions'][sessionID] = Session(sessionID)
			self.cache[sessionID] = db()['sessions'][sessionID]
		return self.cache[sessionID]

	def save(self, sessionID):
		db()['sessions'][sessionID] = self.cache[sessionID]

	def getIDs(self):
		return db()['sessions'].keys()

	def destroy(self, sessionID):
		if sessionID in self.cache:
			del self.cache[sessionID]
		del db()['sessions'][sessionID]
