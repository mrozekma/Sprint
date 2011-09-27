import sys

class ResponseWriter:
	def __init__(self, autoStart = True, prefixSigil = True):
		self.prefixSigil = prefixSigil
		self.old = None
		if autoStart:
			self.start()

	def write(self, data):
		if data[:1] == '|' and self.prefixSigil:
			print >>self.old, data[1:]
		else:
			self.data += data

	def clear(self):
		self.data = ''

	def start(self):
		self.old = sys.stdout
		sys.stdout = self
		self.clear()

	def done(self):
		sys.stdout = self.old
		return self.data
