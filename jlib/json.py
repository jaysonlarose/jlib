
def encap(data):# {{{
	"""A function for shoehorning `set()` and `bytes()` objects into JSON.

	Call it like: print(json.dumps(jlib.json.encap(data), indent=2))

	See `jlib.json.decap()` for converting back.

	Note: This works by iterating through the input data and converting every
	set or bytes object it finds into a single-item dict... contents look like:
	set():
		{'$$setvalue$$': [list_of_set_values]}
	bytes():
		{'$$bytesvalue$$': binascii.hexlify(bytes_data).decode()}
	Therefore, if your source data happens to have any keys using the magic
	values '$$setvalue$$' or '$$bytesvalue$$', this shit will barf."""
	import binascii
	if type(data) is set:
		ret = {'$$setvalues$$': encap(list(data))}
		return ret
	elif type(data) is bytes:
		ret = {'$$bytesvalue$$': binascii.hexlify(data).decode()}
		return ret
	elif type(data) is dict:
		ret = {}
		for k, v in data.items():
			ret[k] = encap(v)
		return ret
	elif type(data) in [list, tuple]:
		ret = []
		for v in data:
			ret.append(encap(v))
		return ret
	else:
		return data
# }}}
def decap(data):# {{{
	"""This is `jlib.json.encap()`'s partner in crime.

	Call it like: jlib.json.decap(json.loads(json_data))"""
	import binascii
	if type(data) is dict and len(data) == 1 and '$$setvalues$$' in data:
		return set(list(data['$$setvalues$$']))
	elif type(data) is dict and len(data) == 1 and '$$bytesvalue$$' in data:
		return binascii.unhexlify(data['$$bytesvalue$$'])
	elif type(data) is dict:
		ret = {}
		for k, v in data.items():
			ret[k] = decap(v)
		return ret
	elif type(data) in [list, tuple]:
		ret = []
		for v in data:
			ret.append(decap(v))
		return ret
	else:
		return data
# }}}
