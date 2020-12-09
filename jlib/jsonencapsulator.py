import wrapt, types

class JsonLineEncapsulator(wrapt.ObjectProxy):
	def __init__(self, wrapped):# {{{
		super(JsonLineEncapsulator, self).__init__(wrapped)
		self.linebuffer = None
# }}}
	def line(self, *args, **kwargs):# {{{
		if 'printfile' not in kwargs or ('printfile' in kwargs and kwargs['printfile']):
			if self.linebuffer is None:
				retval = self.__wrapped__.line("[")
			else:
				retval = self.__wrapped__.line("  {},".format(self.linebuffer))
			self.linebuffer = args[0]
			return retval
		self.__wrapped__.line(*args, **kwargs)
# }}}
	def close(self, *args, **kwargs):# {{{
		if self.linebuffer is not None:
			self.__wrapped__.line("  {}".format(self.linebuffer))
		self.__wrapped__.line("]")
		self.__wrapped__.close(*args, **kwargs)
# }}}

class JsonWriteEncapsulator(wrapt.ObjectProxy):
	def __init__(self, wrapped):# {{{
		super(JsonWriteEncapsulator, self).__init__(wrapped)
		self.linebuffer = None
# }}}
	def __getattribute__(self, name):
		if name == 'getvalue':
			getattr(object.__getattribute__(self, '__wrapped__'), 'getvalue')
			return object.__getattribute__(self, 'getvalue')
		return object.__getattribute__(self, name)
	def getvalue(self):
		if self.linebuffer is not None:
			return self.__wrapped__.getvalue() + "  {}".format(self.linebuffer) + "]\n"
		else:
			return self.__wrapped__.getvalue()
	def write(self, *args, **kwargs):# {{{
		if self.linebuffer is None:
			self.__wrapped__.write("[\n")
			self.linebuffer = ''
		elif self.linebuffer.endswith("\n"):
			self.__wrapped__.write("  {},\n".format(self.linebuffer[:-1]))
			self.linebuffer = ''
		self.linebuffer += args[0]
# }}}
	def close(self, *args, **kwargs):# {{{
		if self.linebuffer is not None:
			self.__wrapped__.write("  {}]\n".format(self.linebuffer))
		self.linebuffer = None
		self.__wrapped__.close(*args, **kwargs)
# }}}
	def __del__(self):
		if self.linebuffer is not None:
			self.__wrapped__.write("  {}]\n".format(self.linebuffer))
		self.linebuffer = None

class JsonEncapsulator:# {{{
	def __new__(cls, wrapped):# {{{
		if hasattr(wrapped, 'line'):
			return JsonLineEncapsulator(wrapped)
		if hasattr(wrapped, 'write'):
			return JsonWriteEncapsulator(wrapped)
# }}}
