def unparse(scheme='', netloc='', path='', params='', query='', fragment=''):
	"""
	Just a simple frontend for `urllib.parse.urlunparse` that uses
	keyword arguments instead of positional arguments, because having
	to look up the order and fields involved each time aggravates me.
	"""
	import urllib.parse
	kwargs = dict(scheme=scheme, netloc=netloc, path=path, params=params, query=query, fragment=fragment)
	return urllib.parse.urlunparse([ kwargs[x] for x in urllib.parse.ParseResult._fields ])
