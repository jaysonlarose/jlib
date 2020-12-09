import random
class SeededStream:
	def __init__(self, seedval):
		self.seedval = seedval
		self._random = random.Random()
		self.closed = False
		self.reset()
	def reset(self):
		self._random.seed(self.seedval)
	def seekable(self):
		return False
	def read(self, size=1024):
		if self.closed:
			raise ValueError("read of closed file")
		data = bytes([ self._random.getrandbits(8) for x in range(size) ])
		return data
	def close():
		self.closed = True
