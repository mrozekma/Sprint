import sys
from threading import _Semaphore as Semaphore, _RLock as RLock
from uuid import uuid1 as uuid

locks = {}

class SingleLock(Semaphore):
	def avail(self):
		return self._Semaphore__value

	def reentrant(self):
		return False

	# def acquire(self):
		# sys.__stdout__.write("locking (single)\n")
		# super(SingleLock, self).acquire()
		# sys.__stdout__.write("locked (single)\n")

	# def release(self):
		# sys.__stdout__.write("unlocking (single)\n")
		# super(SingleLock, self).release()

	# def __enter__(self): return self.acquire()
	# def __exit__(self, *x): return self.release()

class ReentLock(RLock):
	def avail(self):
		return self._RLock__count == 0

	def reentrant(self):
		return True

	# def acquire(self):
		# sys.__stdout__.write("locking (reent)\n")
		# super(ReentLock, self).acquire()
		# sys.__stdout__.write("locked (reent)\n")

	# def release(self):
		# sys.__stdout__.write("unlocking (reent%s)\n" % ('' if self._RLock__count == 1 else ' -- still held'))
		# super(ReentLock, self).release()

	# def __enter__(self): return self.acquire()
	# def __exit__(self, *x): return self.release()

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
