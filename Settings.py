from utils import *
from stasis.Singleton import get as db

PORT = 8081

class Settings:
	def keys(self):
		return db()['settings'].keys()

	def items(self):
		return db()['settings'].all().items()

	def __iter__(self):
		return self.keys().__iter__

	def __len__(self):
		return len(self.keys())

	def __contains__(self, item):
		return item in db()['settings']

	def __getattr__(self, name):
		return self[name] if name in self else None

	def __setattr__(self, name, value):
		self[name] = value

	def __getitem__(self, name):
		return db()['settings'][name]

	def __setitem__(self, name, value):
		db()['settings'][name] = value

	def __delitem__(self, name):
		del db()['settings'][name]

	def __str__(self):
		return "\n".join("%s: %s" % i for i in self.items())

settings = Settings()
