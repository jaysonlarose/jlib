import io, struct, os, enum, gzip, bz2, lzma

class Condenser:
	readlen = 0
	def __init__(self):
		pass
	def skip(self, fobj):
		fobj.seek(self.readlen, os.SEEK_CUR)

class StrCondenser(Condenser):
	def __init__(self, packing, encoding='utf-8'):
		super(self.__class__, self).__init__()
		self.current_readlen = None
		self.packing = packing
		self.encoding = encoding
	@property
	def readlen(self):
		if self.current_readlen is None:
			subread_data = self._fobj.read(struct.calcsize(self.packing))
			if len(subread_data) == 0:
				raise StopIteration
			else:
				self.current_readlen = struct.unpack(self.packing, subread_data)[0]
			
		return self.current_readlen
	def encode(self, fobj, data):
		encoded = data.encode(self.encoding)
		fobj.write(struct.pack(self.packing, len(encoded)))
		fobj.write(encoded)
	def decode(self, fobj):
		# Sort of a hack, we're defining self._fobj here, because
		# A) the readlen property needs to read from the file object in
		#    order to know how much data the *next* read will take
		# B) I didn't want to make the file object required at instantiation,
		#    because that'd lock the condenser into that one instance
		# C) As long as you're not doing wacky threading/multiprocessing,
		#    decode is always called before the readlen property is accessed.
		self._fobj = fobj
		encoded = fobj.read(self.readlen)
		self.current_readlen = None
		return encoded.decode(self.encoding)

class FixedSizeStrCondenser(Condenser):
	def __init__(self, size, encoding='ascii'):
		super(self.__class__, self).__init__()
		self.size = size
		self.encoding = encoding
	@property
	def readlen(self):
		return self.size
	def encode(self, fobj, data):
		unpadded = data.encode(self.encoding)
		encoded = unpadded + (b'\x00' * (self.readlen - len(unpadded)))
		fobj.write(encoded)
	def decode(self, fobj):
		read_data = fobj.read(self.readlen)
		if len(read_data) == 0:
			raise StopIteration
		return read_data.decode(self.encoding)

class FixedSizeBlobCondenser(Condenser):
	def __init__(self, size):
		super(self.__class__, self).__init__()
		self.size = size
	@property
	def readlen(self):
		return self.size
	def encode(self, fobj, data):
		unpadded = data
		encoded = unpadded + (b'\x00' * (self.readlen - len(unpadded)))
		fobj.write(encoded)
	def decode(self, fobj):
		read_data = fobj.read(self.readlen)
		if len(read_data) == 0:
			raise StopIteration
		return read_data

class IntCondenser(Condenser):
	def __init__(self, packing):
		self.packing = packing
	@property
	def readlen(self):
		return struct.calcsize(self.packing)
	def encode(self, fobj, data):
		fobj.write(struct.pack(self.packing, data))
	def decode(self, fobj):
		read_data = fobj.read(self.readlen)
		if len(read_data) == 0:
			raise StopIteration
		return struct.unpack(self.packing, read_data)[0]

class Mode(enum.Enum):
	READ  = 0
	WRITE = 1
	CLEAR = 2
	REWIND = 3

class Condensed:
	def __init__(self, *condensers, fobj=io.BytesIO()):
		self.condensers = condensers
		self.fobj = fobj
		self._fobj = fobj
		self.mode = None
		self._qty = 0
	def _switch_mode(self, newmode):
		if self.mode != newmode:
			if newmode == Mode.READ:
				self.fobj.seek(0)
			elif newmode == Mode.WRITE:
				self.fobj.seek(0, os.SEEK_END)
			elif newmode == Mode.CLEAR:
				self.fobj.seek(0)
				self.fobj.truncate()
				self._qty = 0
			elif newmode == Mode.REWIND:
				self.fobj.seek(0)
		self.mode = newmode
	def append(self, data):
		self._switch_mode(Mode.WRITE)
		for c, d in zip(self.condensers, data):
			c.encode(self.fobj, d)
		self._qty += 1
	def read(self):
		self._switch_mode(Mode.READ)
		return [ c.decode(self.fobj) for c in self.condensers ]
	def clear(self):
		self._switch_mode(Mode.CLEAR)
	def finish(self):
		self._switch_mode(Mode.READ)
	def rewind(self):
		self._switch_mode(Mode.REWIND)
	def __iter__(self):
		self._switch_mode(Mode.REWIND)
		return self
	def __next__(self):
		return self.read()
	def __len__(self):
		return self._qty
	def dump(self, dst_fobj):
		self.rewind()
		while True:
			buf = self._fobj.read(65536)
			if len(buf) > 0:
				dst_fobj.write(buf)
			else:
				break
		self.rewind()
	def load(self, src_fobj):
		self.rewind()
		while True:
			buf = src_fobj.read(65536)
			if len(buf) > 0:
				self._fobj.write(buf)
			else:
				break
		self.rewind()
		self._qty = sum([ 1 for x in self ])

class GenericCompressedCondensed(Condensed):
	def __init__(self, *args, **kwargs):
		super(GenericCompressedCondensed, self).__init__(*args, **kwargs)
		self.fobj = None
	def _switch_mode(self, newmode):
		if self.mode != newmode:
			if self.fobj is not None:
				self.fobj.close()
			if newmode == Mode.READ:
				self._fobj.seek(0)
				self.fobj = self._init_compressor(fileobj=self._fobj, mode="rb")
			elif newmode == Mode.WRITE:
				self._fobj.seek(0, os.SEEK_END)
				self.fobj = self._init_compressor(fileobj=self._fobj, mode="ab")
			elif newmode == Mode.CLEAR:
				self._fobj.seek(0)
				self._fobj.truncate()
			elif newmode == Mode.REWIND:
				self._fobj.seek(0)
				self.fobj = self._init_compressor(fileobj=self._fobj, mode="rb")
		self.mode = newmode

class GzipCondensed(GenericCompressedCondensed):
	def _init_compressor(self, fileobj, mode):
		return gzip.GzipFile(fileobj=fileobj, mode=mode)

class Bzip2Condensed(GenericCompressedCondensed):
	def _init_compressor(self, fileobj, mode):
		return bz2.BZ2File(filename=fileobj, mode=mode)

class XZCondensed(GenericCompressedCondensed):
	def _init_compressor(self, fileobj, mode):
		return lzma.LZMAFile(filename=fileobj, mode=mode)

#class GzipCondensed(Condensed):
#	def __init__(self, *args, **kwargs):
#		super(self.__class__, self).__init__(*args, **kwargs)
#		self.fobj = None
#	def _switch_mode(self, newmode):
#		if self.mode != newmode:
#			if self.fobj is not None:
#				self.fobj.close()
#			if newmode == Mode.READ:
#				self._fobj.seek(0)
#				self.fobj = gzip.GzipFile(fileobj=self._fobj, mode="rb")
#			elif newmode == Mode.WRITE:
#				self._fobj.seek(0, os.SEEK_END)
#				self.fobj = gzip.GzipFile(fileobj=self._fobj, mode="ab")
#			elif newmode == Mode.CLEAR:
#				self._fobj.seek(0)
#				self._fobj.truncate()
#			elif newmode == Mode.REWIND:
#				self._fobj.seek(0)
#				self.fobj = gzip.GzipFile(fileobj=self._fobj, mode="rb")
#		self.mode = newmode

