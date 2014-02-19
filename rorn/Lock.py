import functools
import sys
from thread import get_ident
from threading import _Semaphore as Semaphore, _RLock as RLock
from uuid import uuid1 as uuid

from utils import *

locks = {}
counters = {}
recordOwnerStack = False

def synchronized(lockName):
	def wrap(f):
		@functools.wraps(f)
		def wrap2(*args, **kw):
			with getLock(lockName):
				return f(*args, **kw)
		return wrap2
	return wrap

class SingleLock(Semaphore):
	def __init__(self):
		super(SingleLock, self).__init__()
		self.owner = self.tb = None

	def avail(self):
		return self._Semaphore__value

	def reentrant(self):
		return False

	def acquire(self):
		# sys.__stdout__.write("locking (single)\n")
		super(SingleLock, self).acquire()
		self.owner = get_ident()
		if recordOwnerStack:
			self.tb = traceback.extract_stack()[:-1]
		# sys.__stdout__.write("locked (single)\n")

	def release(self):
		# sys.__stdout__.write("unlocking (single)\n")
		self.owner = self.tb = None
		super(SingleLock, self).release()

	def __enter__(self): return self.acquire()
	def __exit__(self, *x): return self.release()

class ReentLock(RLock):
	def __init__(self):
		super(ReentLock, self).__init__()
		self.owner = self.tb = None

	def avail(self):
		return self._RLock__count == 0

	def reentrant(self):
		return True

	def acquire(self):
		# sys.__stdout__.write("locking (reent)\n")
		super(ReentLock, self).acquire()
		self.owner = get_ident()
		if recordOwnerStack and self.tb is None:
			self.tb = traceback.extract_stack()[:-1]
		# sys.__stdout__.write("locked (reent)\n")

	def release(self):
		# sys.__stdout__.write("unlocking (reent%s)\n" % ('' if self._RLock__count == 1 else ' -- still held'))
		if self._RLock__count == 1:
			self.owner = self.tb = None
		super(ReentLock, self).release()

	def __enter__(self): return self.acquire()
	def __exit__(self, *x): return self.release()

# Starting the name with # makes it single instead of reentrant
def getLock(name = None):
	if not name:
		name = str(uuid())
		while name in locks:
			name = str(uuid())
	if not name in locks:
		locks[name] = SingleLock() if name[0] == '#' else ReentLock()
	return locks[name]

def lock(name):
	return getLock(name).acquire()

def unlock(name):
	return getLock(name).release()

def setStackRecording(flag):
	global recordOwnerStack
	recordOwnerStack = flag

class Counter:
	def __init__(self, start = 0):
		self.count = start

	@synchronized('counter')
	def inc(self):
		self.count += 1
		return self.count

	@synchronized('counter')
	def dec(self):
		self.count -= 1
		return self.count

	@synchronized('counter')
	def any(self):
		return self.count != 0

def getCounter(name = None, start = 0, unique = False):
	if name:
		base = name
		idx = 1
		while unique and name in counters:
			idx += 1
			name = "%s-%d" % (base, idx)
	else:
		name = str(uuid())
		while name in counters:
			name = str(uuid())

	if not name in counters:
		counters[name] = Counter(start)
	return counters[name]
