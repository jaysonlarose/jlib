#!/usr/bin/env python3

def strtobool(string):
	"""
	Interprets a string value into an appropriate bool. Case-insensitive versions of "y", "yes", "true", and "1" evaluate to True. Case-insensitive versions of "n", "no", "false", and "0" evaluate to False. Anything else raises ValueError.

	Jays Note: the module `distutils.util.strtobool` does the same thing,
	even down to raising ValueError.
	"""
	true_values = ['y', 'yes', 'true', '1']
	false_values = ['n', 'no', 'false', '0']
	string = string.lower().strip()
	if string in true_values:
		return True
	if string in false_values:
		return False
	raise ValueError

def drwxrwxrwx(st_mode):
	"""
	Given a value provided from `os.lstat().st_mode` or `os.stat().st_mode`,
	this function will return a "drwxrwxrwx" permissions legend like the
	one from the `ls` command. It should even show things like device files
	and setuid permissions bits properly, too!
	"""
	import stat

	ret = []
	imode = stat.S_IMODE(st_mode)
	ret.append('b' if stat.S_ISBLK(st_mode) else 'c' if stat.S_ISCHR(st_mode) else 'l' if stat.S_ISLNK(st_mode) else 'p' if stat.S_ISFIFO(st_mode) else 's' if stat.S_ISSOCK(st_mode) else 'd' if stat.S_ISDIR(st_mode) else '-' if stat.S_ISREG(st_mode) else '?')
	ret.append('r' if imode & 0o0400 else '-')
	ret.append('w' if imode & 0o0200 else '-')
	ret.append('s' if imode & 0o4100 else 'S' if imode & 0o4000 else 'x' if imode & 0o0100 else '-')
	ret.append('r' if imode & 0o0040 else '-')
	ret.append('w' if imode & 0o0020 else '-')
	ret.append('s' if imode & 0o2010 else 'S' if imode & 0o2000 else 'x' if imode & 0o0010 else '-')
	ret.append('r' if imode & 0o0004 else '-')
	ret.append('w' if imode & 0o0002 else '-')
	ret.append('t' if imode & 0o1001 else 'T' if imode & 0o1000 else 'x' if imode & 0o0001 else '-')
	return ''.join(ret)

class PasswdEntry:
	"""
	Pythonic representation of an /etc/passwd entry.

	Notable attributes:
	  * user
	  * password
	  * uid
	  * gid
	  * gecos
	  * shell
	"""
	field_defs = [
		('user',     lambda x: x),
		('password', lambda x: x),
		('uid',      lambda x: int(x)),
		('gid',      lambda x: int(x)),
		('gecos',    lambda x: GecosEntry(x)),
		('home',     lambda x: x),
		('shell',    lambda x: x),
	]
	id_field = 'uid'
	name_field = 'user'
	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)
	def to_string(self):
		return ':'.join([ str(getattr(self, x)) for x in [ x[0] for x in self.field_defs ] ])
	def __repr__(self):
		return "<PasswdEntry {}>".format(repr(self.to_string()))

class GroupMembers(list):
	def __init__(self, data):
		self.extend([ x for x in data.split(',') if len(x) > 0 ])
	def __str__(self):
		return(','.join(self))

class GroupEntry:
	field_defs = [
		('name',  lambda x: x),
		('password', lambda x: x),
		('gid',      lambda x: int(x)),
		('members',  lambda x: GroupMembers(x)),
	]
	id_field = 'gid'
	name_field = 'name'
	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)
	def to_string(self):
		return ':'.join([ str(getattr(self, x)) for x in [ x[0] for x in self.field_defs ] ])
	def __repr__(self):
		return "<GroupEntry {}>".format(repr(self.to_string()))

class GecosEntry:
	fields = ['name', 'room', 'workphone', 'homephone', 'other']
	def __init__(self, data):
		field_data = data.split(',', 5)
		for x in self.fields:
			setattr(self, x, '')
		for i, val in enumerate(field_data):
			setattr(self, self.fields[i], val)
	def to_string(self):
		return ','.join([ getattr(self, x) for x in self.fields ])
	def __repr__(self):
		return "<GecosEntry {}>".format(repr(self.to_string()))
	def __str__(self):
		return self.to_string()

class PwdEntryCache:
	def __init__(self, entries):
		self.entries = entries
		self.id_lut = dict([ (getattr(x, x.id_field), x) for x in self.entries ])
		self.name_lut = dict([ (getattr(x, x.name_field), x) for x in self.entries ])
	def get_name(self, entry_id):
		entry = self.id_lut[entry_id]
		return getattr(entry, entry.name_field)
	def get_id(self, entry_name):
		entry = self.name_lut[entry_name]
		return getattr(entry, entry.id_field)

def passwd(line):
	"""
	Parses a line from an /etc/passwd file.
	Data is returned in the form of a PasswdEntry object.
	"""
	if isinstance(line, bytes):
		line = line.decode()
	if line.endswith("\n"):
		line = line[:-1]
		if line.endswith("\r"):
			line = line[:-1]
	return PasswdEntry(**dict([ (x[0][0], x[0][1](x[1])) for x in zip(PasswdEntry.field_defs, line.split(':')) ]))

def group(line):
	if isinstance(line, bytes):
		line = line.decode()
	if line.endswith("\n"):
		line = line[:-1]
		if line.endswith("\r"):
			line = line[:-1]
	return GroupEntry(**dict([ (x[0][0], x[0][1](x[1])) for x in zip(GroupEntry.field_defs, line.split(':')) ]))

