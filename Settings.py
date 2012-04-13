from utils import *
from DB import ActiveRecord, db

PORT = 8081

class Setting(ActiveRecord):
	def __init__(self, name, value, id = None):
		ActiveRecord.__init__(self)
		self.id = id
		self.name = name
		self.value = value

class Settings:
	def _get(self, name):
		rtn = Setting.load(name = name)
		if rtn:
			return rtn
		raise IndexError("Unrecognized setting name: %s" % name)

	def items(self):
		return [(setting.name, setting.value) for setting in Setting.loadAll()]

	def keys(self):
		return [name for name, value in self.items()]

	def __iter__(self):
		return self.keys().__iter__

	def __len__(self):
		return len(self.items())

	def __contains__(self, item):
		return item in self.keys()

	def __getattr__(self, name):
		return self[name]

	def __setattr__(self, name, value):
		self[name] = value

	def __getitem__(self, name):
		return self._get(name).value

	def __setitem__(self, name, value):
		try:
			item = self._get(name)
			item.value = value
		except IndexError:
			item = Setting(name, value)
		item.save()

	def __delitem__(self, name):
		self._get(name).delete()

settings = Settings()
