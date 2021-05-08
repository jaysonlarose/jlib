# coding=utf-8
from __future__ import print_function, division
import sys
if sys.version_info.major >= 3:
	import queue as Queue
	StringTypes = [str]
else:
	import Queue
	from types import StringTypes
import os, atexit, collections, argparse, enum, string
from threading import Thread

__version__ = "1.0.13"

image_exts = set('.bmp .cur .dcx .eps .fli .fpx .gbr .gif .icns .ico .im .imt .iptc .jpe .jpeg .jpg .jp2 .mpo .msp .pbm .pcd .pcx .png .ppm .psd .svg .tga .tif .tiff .wal .xbm .xpm .vtx .webp'.split())
video_exts = set('.wmv .mpeg .mpg .asf .rm .rmvb .ram .flv .mov .mkv .m4v .webm .3g .3gpp .3gp .mp4 .avi .divx .vob'.split())
svg_exts = set(['.svg'])
compressed_exts = set('.gz .z .bz2 .xz'.split())
html_exts = set('.html .htm'.split())
ext_types = {
	'image': image_exts,
	'video': video_exts,
	'svg':   svg_exts,
	'html':  html_exts,
	'compressed': compressed_exts,
}

class JException(Exception):
	"""
	An exception mix-in with added convenience.

	You can use it in your own exceptions by subclassing it:

	class StatxError(jlib.JExcepption):
		pass
	
	and then calling it thusly:

	raise StatxError("[Errno {errno}] {strerror}: {path!r}", path=path, returncode=res, errno=errnum, errval=errno.errorcode[errnum], strerror=os.strerror(errnum))

	The exception will print out the text in the template argument, formatted via the additional named arguments. In addition, the following attributes will be available inside the exception:
	* message: the text of the message printed out as mentioned above.
	* kwargs: an OrderedDict containing each of the named arguments, in the order they were specified.
	* args: equivalent to list(kwargs.values())
	* fields: equivalent to list(kwargs.keys())

	Finally, each of the named arguments will be set as attributes of the exception.
	"""
	def __init__(self, template, **kwargs):
		self.kwargs = collections.OrderedDict(list(kwargs.items()))
		self.message = template.format(**kwargs)
		self.args = list(kwargs.values())
		self.fields = list(kwargs.keys())
		for k, v in self.kwargs.items():
			setattr(self, k, v)
		super().__init__(self.message)


# STRING STUFF{{{

def is_ascii(value):
	# TODO: some time in the indefinite future, áfter I've excised all of my
	# legacy code using this thing, rework it to operate natively on bytes
	# instead of converting bytes to str.
	"""Returns True or False depending on whether or not the supplied string consists entirely of ASCII characters (ie, values between 0x20-0x73, or (0x09, 0x0A, 0x0D))"""
	if isinstance(value, bytes):
		value = value.decode()
	return not bool(len(list(filter(lambda x: (x < 0x20 or x > 0x7e) and x not in (9, 10, 13), map(lambda x: ord(x), value)))))

def chomp(s):
	import re
	return re.sub(r'\s*$', '', s)

def lstripn(text, count, chars=None):
	"""
	Strip up to `count` leading characters of whitespace from a string.

	As with the builtin `str.lstrip()` method, if `chars` is specified,
	those characters will be stripped instead.
	"""
	if chars is None:
		import string
		chars = string.whitespace
	for i in range(count):
		if len(text) == 0:
			break
		if text[0] in chars:
			text = text[1:]
		else:
			break
	return text

def rstripn(text, count, chars=None):
	"""
	Strip up to `count` trailing characters of whitespace from a string.

	As with the builtin `str.lstrip()` method, if `chars` is specified,
	those characters will be stripped instead.
	"""
	if chars is None:
		import string
		chars = string.whitespace
	for i in range(count):
		if len(text) == 0:
			break
		if text[-1] in chars:
			text = text[:-1]
		else:
			break
	return text

def stripn(text, count, chars=None):
	"""
	Strip up to `count` leading and trailing characters of whitespace
	from a string.

	It doesn't really make much sense to use this function, but
	it was written for completeness' sake. In reality, it's just
	calling `lstripn()` followed by `rstripn()`.
	"""
	text = lstripn(text, count, chars=chars)
	text = rstripn(text, count, chars=chars)
	return text

def shellunescape(s):
	pos = 0
	idx = s.find('\\', pos)
	while idx > -1:
		if len(s) == idx + 1:
			break
		s = s[:idx] + s[idx + 1:]
		pos = idx + 2
		idx = s.find('\\', pos)
	return s

def ascii_to_regional(s):
	out = ""
	for c in s:
		if ord(c) >= ord("a") and ord(c) <= ord("z"):
			out += chr(ord(c) - ord("a") + 0x1F1E6)
		elif ord(c) >= ord("A") and ord(c) <= ord("Z"):
			out += chr(ord(c) - ord("A") + 0x1F1E6)
		else:
			out += c
	return out
# Routines for doing string justification stuff in environments where
# "double-width" characters are a thing.
def wcscenter(text, width, fillchar=' '):# {{{
	import wcwidth
	twidth = wcwidth.wcswidth(text)
	if twidth >= width:
		return text
	lhs_pad = round((width - twidth) / 2)
	rhs_pad = width - (lhs_pad + twidth)
	return (fillchar * lhs_pad) + text + (fillchar * rhs_pad)
# }}}
def wcsljust(text, width, fillchar=' '):# {{{
	import wcwidth
	twidth = wcwidth.wcswidth(text)
	if twidth >= width:
		return text
	pad = width - twidth
	return text + (fillchar * pad)
# }}}
def wcsrjust(text, width, fillchar=' '):# {{{
	import wcwidth
	twidth = wcwidth.wcswidth(text)
	if twidth >= width:
		return text
	pad = width - twidth
	return (fillchar * pad) + text
# }}}
# }}}

def ansiwcsrjust(text, width, fillchar=' '):
	import JaysTerm
	twidth = JaysTerm.textwidth(text)
	if twidth >= width:
		return text
	return (fillchar * pad) + text
# NUMBER STUFF{{{

def bytelen_to_humanreadable(val, binary=True, min_magnitude=0, max_magnitude=8, separator=''):# {{{
	"""
	Turns a number, like 1457664, into something a little more
	human-parsable, like "1.39MiB".

	keyword arguments

	binary (True):
		Use binary magnitude units (1 mebibyte = 1024 * 1024 bytes) if True.
		Use decimal magnitude units (1 megabyte = 1000 * 1000 bytes) if False.

	min_magnitude (0), max_magnitude (8):
		These arguments control the lower and upper bounds of unit magnitude.

		| Idx | Binary         | Decimal        |
		| --- | -------------- | -------------- |
		| 0   | byte (B)       | byte (B)       |
		| 1   | kibibyte (KiB) | kilobyte (kB)  |
		| 2   | mebibyte (MiB) | megabyte (MB)  |
		| 3   | gibibyte (GiB) | gigabyte (GB)  |
		| 4   | tebibyte (TiB) | terabyte (TB)  |
		| 5   | pebibyte (PiB) | petabyte (PB)  |
		| 6   | exibyte (EiB)  | exabyte (EB)   |
		| 7   | zebibyte (ZiB) | zettabyte (ZB) |
		| 8   | yobibyte (YiB) | yottabyte (YB) |

		Unless constrained, the smallest unit magnitude that returns a quantity
		greater than 1.0 will be used.
		
		So, for example, bytelen_to_humanreadable(max_magnitude=0) will return
		"9,0001B" instead of "8.79KiB".
	
	separator (''):
		This string is inserted betwen the numeric value and the unit magnitude.

	"""
	binary_suffixes =  ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
	decimal_suffixes = ['B',  'kB',  'MB',  'GB',  'TB',  'PB',  'EB',  'ZB',  'YB']
	if binary:
		magnitude_base = 1024
		suffixes = binary_suffixes
	else:
		magnitude_base = 1000
		suffixes = decimal_suffixes

	if max_magnitude > len(suffixes) - 1:
		max_magnitude = len(suffiexes) - 1

	if min_magnitude < 0 or min_magnitude > max_magnitude:
		raise ValueError
	suffixpos = 0

	newval = val
	while suffixpos < min_magnitude or (newval >= magnitude_base and suffixpos < max_magnitude):
		newval /= magnitude_base
		suffixpos += 1
	if suffixpos == 0:
		valfmt = "{}"
	else:
		valfmt = "{:.2f}"
	return valfmt.format(newval) + separator + suffixes[suffixpos]
# }}}

def resize_aspect(orig_width, orig_height, width=None, height=None, factor=None): # {{{
	if width is not None:
		factor = float(width) / float(orig_width)
		height = int(orig_height * factor)
	elif height is not None:
		factor = float(height) / float(orig_height)
		width = int(orig_width * factor)
	else:
		width = int(orig_width * factor)
		height = int(orig_height * factor)
	return width, height, factor
# }}}

# }}}

def calculate_size(obj, seen=None):
	"""
	Recursively finds size of objects.
	https://goshippo.com/blog/measure-real-size-any-python-object/
	"""
	size = sys.getsizeof(obj)
	if seen is None:
		seen = set()
	obj_id = id(obj)
	if obj_id in seen:
		return 0
	seen.add(obj_id)
	if isinstance(obj, dict):
		size += sum([calculate_size(v, seen) for v in obj.values()])
		size += sum([calculate_size(k, seen) for k in obj.keys()])
	elif hasattr(obj, '__dict__'):
		size += calculate_size(obj.__dict__, seen)
	elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
		size += sum([calculate_size(i, seen) for i in obj])
	return size

# ANSI AND COLORIZATION{{{

ansi_colors = {
	'normal':		'0',
	'bold':			'1',	'bright':		'1',	'hi':		   '1',
	'black':		'0;30',
	'dark gray':	'1;30', 'dark grey':	'1;30',
	'light gray':	'0;37', 'light grey':	'0;37',
	'bright gray':	'0;37', 'bright grey':	'0;37',
	'white':		'1;37',
	'blue':			'0;34', 'bright blue':	'1;34', 'light blue':  '1;34',
	'green':		'0;32', 'bright green': '1;32', 'light green': '1;32',
	'cyan':			'0;36', 'bright cyan':	'1;36', 'light cyan':  '1;36',
	'red':			'0;31', 'bright red':	'1;31', 'light red':   '1;31',
	'purple':		'0;35', 'bright purple':'1;35', 'light purple':'1;35',
	'yellow':		'0;33', 'bright yellow':'1;33', 'light yellow':'1;33',

}
ansi_codes = {
	'csi':	"\033[",
	'cuu':	"A",
	'cud':	"B",
	'cuf':	"C",
	'cub':	"D",
	'cnl':	"E",
	'cpl':	"F",
	'cha':	"G",
	'cup':	"H",
	'ed':	"J",
	'el':	"K",
	'su':	"S",
	'sd':	"T",
	'hvp':	"f",
	'sgr':	"m",
	'dsr':	"6n",
	'scp':	"s",
	'rcp':	"u",
	'dectcem_hide':	"?25l",
	'dectcem_show':	"?25h",
	'disable_line_wrap': "?7l",
	'enable_line_wrap':  "?7h",
}
ansi_code_equivalents = {
	'escape':			ansi_codes['csi'],
	'cursor_up':			ansi_codes['cuu'],
	'cursor_down':			ansi_codes['cud'],
	'cursor_forward':		ansi_codes['cuf'],
	'cursor_fwd':			ansi_codes['cuf'],
	'cursor_right':			ansi_codes['cuf'],
	'cursor_back':			ansi_codes['cub'],
	'cursor_left':			ansi_codes['cub'],
	'cursor_next_line':		ansi_codes['cnl'],
	'cursor_previous_line':		ansi_codes['cpl'],
	'cursor_horizontal_absolute':	ansi_codes['cha'],
	'cursor_colnum':		ansi_codes['cha'],
	'cursor_col':			ansi_codes['cha'],
	'cursor_position':		ansi_codes['cup'],
	'cursor_pos':			ansi_codes['cup'],
	'erase_screen_from_cursor':	'0' + ansi_codes['ed'],
	'erase_screen_to_cursor':	'1' + ansi_codes['ed'],
	'erase_screen':			'2' + ansi_codes['ed'],
	'erase_screen_and_scrollback':	'3' + ansi_codes['ed'],
	'erase_line_from_cursor':	'0' + ansi_codes['el'],
	'erase_line_to_cursor':		'1' + ansi_codes['el'],
	'erase_line':			'2' + ansi_codes['el'],
	'horizontal_vertical_position': ansi_codes['hvp'],
	'scroll_up':			ansi_codes['su'],
	'scroll_down':			ansi_codes['sd'],
	'select_graphic_rendition':	ansi_codes['sgr'],
	'color':			ansi_codes['sgr'],
	'device_status_report':		ansi_codes['dsr'],
	'status':			ansi_codes['dsr'],
	'save_cursor_position':		ansi_codes['scp'],
	'save_cursor':			ansi_codes['scp'],
	'savepos':			ansi_codes['scp'],
	'save':				ansi_codes['scp'],
	'get_cursor_position':		ansi_codes['scp'],
	'get_cursor':			ansi_codes['scp'],
	'getpos':			ansi_codes['scp'],
	'get':				ansi_codes['scp'],
	'restore_cursor_positon':	ansi_codes['rcp'],
	'restore_cursor':		ansi_codes['rcp'],
	'restorepos':			ansi_codes['rcp'],
	'restore':			ansi_codes['rcp'],
	'load_cursor_positon':		ansi_codes['rcp'],
	'load_cursor':			ansi_codes['rcp'],
	'loadpos':			ansi_codes['rcp'],
	'load':				ansi_codes['rcp'],
	'put_cursor_positon':		ansi_codes['rcp'],
	'put_cursor':			ansi_codes['rcp'],
	'putpos':			ansi_codes['rcp'],
	'put':				ansi_codes['rcp'],
}

def ansi_code(x):
	for y in (ansi_codes, ansi_code_equivalents):
		if x in y:
			return y[x]
	return ansi_codes[x] # to raise keyerror

def encapsulate_ansi(code, vals=[]):
	return(ansi_code('csi') + ';'.join(vals) + ansi_code(code))
	
# FUck these things, use fabulous instead.
	
def printc(color, text, fh=sys.stdout, force=False):
	if (fh == sys.stdout or fh == sys.stderr) and not tty_interactive and not force:
		print(text, file=fh)
	else:
		print(sprintc(color, text), file=fh)
 
def writec(color, text, fh=sys.stdout, force=False):
	if (fh == sys.stdout or fh == sys.stderr) and not tty_interactive and not force:
		fh.write(text)
	else:
		fh.write(sprintc(color, text))
 
def sprintc(color, text, force=False):
	if type(text) not in StringTypes:
		text = repr(text)
	if not tty_interactive and not force:
		return text
	return encapsulate_ansi('color', [ansi_colors[color]]) + text + encapsulate_ansi('color', [ansi_colors['normal']])

def sprintc_rgb(rgb, text, force=False):
	if not tty_interactive and not force:
		return text
	return encapsulate_ansi('color', ['38', '2', str(rgb[0]), str(rgb[1]), str(rgb[2])]) + text + encapsulate_ansi('color', [ansi_colors['normal']])

def switchColor(color, fh=sys.stdout, force=False):
	if (fh == sys.stdout or fh == sys.stderr) and not tty_interactive and not force:
		pass
	else:
		fh.write(encapsulate_ansi('color', [ansi_colors[color]]))


# Hint: Call me like:  globals().update(jlib.get_fabulous())
def get_fabulous(force=False, autostr=True):
	import types, functools
	fabulous = None
	if sys.stdout.isatty() or force:
		try:
			import fabulous.color
		except ImportError:
			pass
	ret = {}
	# This is how we derive our list of attrs to either merge in or
	# pretend-implement from fabulous.color:
	# print("\tfabulous_attrs = '{}'.split()".format(' '.join([ x for x in dir(fabulous.color) if not x.startswith('_') and x not in 'basestring OVERLINE section sys functools parse_color printy unicode utils xterm256 ColorString ColorString256 esc'.split() ])))
	fabulous_attrs = 'bg256 black black_bg blink blue blue_bg bold complement complement256 cyan cyan_bg fg256 flip grapefruit green green_bg h1 highlight256 highlight_black highlight_blue highlight_cyan highlight_green highlight_magenta highlight_red highlight_white highlight_yellow italic magenta magenta_bg plain red red_bg strike underline underline2 white white_bg yellow yellow_bg fgtrue bgtrue highlighttrue complementtrue'.split()
	if type(fabulous) is types.ModuleType:
		#def fg256(c, text):
		#	return fabulous.color.fg256(c, text).as_utf8.decode()
		#def bg256(c, text):
		#	return fabulous.color.bg256(c, text).as_utf8.decode()
		#ret['fg256'] = fg256
		#ret['bg256'] = bg256
		#for funcattr in 'bold underline underline2 blink italic'.split():
		#	baa = getattr(fabulous.color, funcattr)
		#	ret[funcattr] = lambda x: baa(x)

		# TODO: in future, try:
		#for funcattr in 'bold underline underline2 blink italic'.split():
		#	baa = getattr(fabulous.color, funcattr)
		#	ret[funcattr] = lambda x=x: baa(x)


		
		# OHH THIS PISSED ME OFF SO MUCH
		if autostr:
			def lambdas_arent_working_so_fuck_you_python(fuckyou, *soverymuch, **goddamnyou):
				return getattr(fabulous.color, fuckyou)(*soverymuch, **goddamnyou).as_utf8.decode()
		else:
			def lambdas_arent_working_so_fuck_you_python(fuckyou, *soverymuch, **goddamnyou):
				return getattr(fabulous.color, fuckyou)(*soverymuch, **goddamnyou)

		for attr in fabulous_attrs:
			if hasattr(fabulous.color, attr):
				ret[attr] = functools.partial(lambdas_arent_working_so_fuck_you_python, attr)
	else:
		#def fg256(c, text):
		#	return text
		#def bg256(c, text):
		#	return text
		#ret['fg256'] = fg256
		#ret['bg256'] = bg256
		#for funcattr in 'bold underline underline2 blink italic'.split():
		#	ret[funcattr] = lambda x: x
		
		# New strategy here. A little more "set parameters gently against the
		# hole they're supposed to fit through, apply sledgehammer until
		# parameters are on the other side"...
		for attr in fabulous_attrs:
			ret[attr] = lambda *x: x[-1]
	return ret

def parse_rgbtxt(fn='/usr/share/X11/rgb.txt'):
	"""
	Reads an X11 color definition file (aka `rgb.txt`) and returns
	a dict mapping color names to RGB tuples.
	"""
	ret = {}
	for i, line in enumerate(open(fn, "r").read().splitlines(), 1):
		try:
			if line.startswith('!'):
				continue
			frags = [ x.strip() for x in line.split(None, 3) ]
			rval, bval, gval = [ int(x) for x in frags[:3] ]
			colorname = frags[3]
			ret[colorname] = (rval, bval, gval)
		except:
			print("Fucked up parsing {} line {} ({})".format(fn, i, line), file=sys.stderr)
			raise
	return ret


# colormap_json {{{
colormap_json = """
{"medium violet red": [199, 21, 133], "pale goldenrod": [238, 232, 170], "yellow": [255, 255, 0], "grey61": [156, 156, 156], "grey60": [153, 153, 153], "grey63": [161, 161, 161], "grey62": [158, 158, 158], "grey65": [166, 166, 166], "AliceBlue": [240, 248, 255], "slate gray": [112, 128, 144], "grey66": [168, 168, 168], "LightCyan1": [224, 255, 255], "grey68": [173, 173, 173], "LightCyan3": [180, 205, 205], "LightCyan2": [209, 238, 238], "LightCyan4": [122, 139, 139], "gray32": [82, 82, 82], "gray33": [84, 84, 84], "DarkTurquoise": [0, 206, 209], "gray31": [79, 79, 79], "gray36": [92, 92, 92], "gray37": [94, 94, 94], "gray34": [87, 87, 87], "gray35": [89, 89, 89], "aquamarine4": [69, 139, 116], "gray38": [97, 97, 97], "gray39": [99, 99, 99], "aquamarine1": [127, 255, 212], "aquamarine3": [102, 205, 170], "aquamarine2": [118, 238, 198], "misty rose": [255, 228, 225], "CadetBlue3": [122, 197, 205], "CadetBlue2": [142, 229, 238], "CadetBlue1": [152, 245, 255], "VioletRed1": [255, 62, 150], "VioletRed2": [238, 58, 140], "HotPink4": [139, 58, 98], "VioletRed4": [139, 34, 82], "brown": [165, 42, 42], "DarkGoldenrod": [184, 134, 11], "gray8": [20, 20, 20], "SlateGrey": [112, 128, 144], "NavajoWhite2": [238, 207, 161], "gray2": [5, 5, 5], "cyan": [0, 255, 255], "gray0": [0, 0, 0], "gray1": [3, 3, 3], "gray6": [15, 15, 15], "gray7": [18, 18, 18], "gray4": [10, 10, 10], "gray5": [13, 13, 13], "MistyRose": [255, 228, 225], "gray98": [250, 250, 250], "DarkKhaki": [189, 183, 107], "gray99": [252, 252, 252], "grey11": [28, 28, 28], "coral4": [139, 62, 47], "grey12": [31, 31, 31], "grey64": [163, 163, 163], "PaleGreen1": [154, 255, 154], "PaleGreen3": [124, 205, 124], "PaleGreen2": [144, 238, 144], "PaleGreen4": [84, 139, 84], "grey14": [36, 36, 36], "lavender": [230, 230, 250], "chartreuse3": [102, 205, 0], "chartreuse2": [118, 238, 0], "dark slate blue": [72, 61, 139], "grey16": [41, 41, 41], "chartreuse4": [69, 139, 0], "RosyBrown": [188, 143, 143], "blue": [0, 0, 255], "NavajoWhite": [255, 222, 173], "LightSeaGreen": [32, 178, 170], "maroon3": [205, 41, 144], "dark khaki": [189, 183, 107], "maroon1": [255, 52, 179], "gold3": [205, 173, 0], "gold2": [238, 201, 0], "gold1": [255, 215, 0], "BlueViolet": [138, 43, 226], "LightSlateGrey": [119, 136, 153], "dim gray": [105, 105, 105], "gray30": [77, 77, 77], "medium purple": [147, 112, 219], "green1": [0, 255, 0], "SkyBlue": [135, 206, 235], "GhostWhite": [248, 248, 255], "midnight blue": [25, 25, 112], "LavenderBlush": [255, 240, 245], "SeaGreen": [46, 139, 87], "BlanchedAlmond": [255, 235, 205], "gray60": [153, 153, 153], "DarkOliveGreen": [85, 107, 47], "firebrick2": [238, 44, 44], "firebrick1": [255, 48, 48], "pale green": [152, 251, 152], "firebrick4": [139, 26, 26], "sienna": [160, 82, 45], "DarkOrchid4": [104, 34, 139], "dodger blue": [30, 144, 255], "gray55": [140, 140, 140], "LightSteelBlue": [176, 196, 222], "DarkViolet": [148, 0, 211], "blue4": [0, 0, 139], "CadetBlue4": [83, 134, 139], "peru": [205, 133, 63], "DarkMagenta": [139, 0, 139], "LightBlue2": [178, 223, 238], "LightBlue3": [154, 192, 205], "red1": [255, 0, 0], "LightBlue1": [191, 239, 255], "LightBlue4": [104, 131, 139], "red4": [139, 0, 0], "navy blue": [0, 0, 128], "MediumSpringGreen": [0, 250, 154], "chocolate": [210, 105, 30], "MediumTurquoise": [72, 209, 204], "DarkRed": [139, 0, 0], "HotPink3": [205, 96, 144], "HotPink2": [238, 106, 167], "HotPink1": [255, 110, 180], "SlateGray": [112, 128, 144], "grey18": [46, 46, 46], "grey19": [48, 48, 48], "DodgerBlue3": [24, 116, 205], "FloralWhite": [255, 250, 240], "moccasin": [255, 228, 181], "grey10": [26, 26, 26], "chocolate1": [255, 127, 36], "chocolate2": [238, 118, 33], "chocolate3": [205, 102, 29], "chocolate4": [139, 69, 19], "grey15": [38, 38, 38], "dark orchid": [153, 50, 204], "grey17": [43, 43, 43], "gray69": [176, 176, 176], "gray68": [173, 173, 173], "gray65": [166, 166, 166], "gray64": [163, 163, 163], "gray67": [171, 171, 171], "gray66": [168, 168, 168], "gray61": [156, 156, 156], "coral": [255, 127, 80], "gray63": [161, 161, 161], "gray62": [158, 158, 158], "LightGoldenrod": [238, 221, 130], "seashell2": [238, 229, 222], "seashell3": [205, 197, 191], "magenta": [255, 0, 255], "seashell1": [255, 245, 238], "tan": [210, 180, 140], "seashell4": [139, 134, 130], "DarkSeaGreen2": [180, 238, 180], "pink": [255, 192, 203], "medium aquamarine": [102, 205, 170], "LightSlateBlue": [132, 112, 255], "chartreuse1": [127, 255, 0], "dark turquoise": [0, 206, 209], "papaya whip": [255, 239, 213], "SteelBlue1": [99, 184, 255], "SteelBlue3": [79, 148, 205], "SteelBlue2": [92, 172, 238], "SteelBlue4": [54, 100, 139], "grey89": [227, 227, 227], "grey88": [224, 224, 224], "gray56": [143, 143, 143], "grey86": [219, 219, 219], "grey85": [217, 217, 217], "grey84": [214, 214, 214], "grey83": [212, 212, 212], "grey82": [209, 209, 209], "grey81": [207, 207, 207], "grey80": [204, 204, 204], "tomato": [255, 99, 71], "white smoke": [245, 245, 245], "khaki1": [255, 246, 143], "khaki2": [238, 230, 133], "khaki3": [205, 198, 115], "salmon1": [255, 140, 105], "salmon3": [205, 112, 84], "salmon2": [238, 130, 98], "salmon4": [139, 76, 57], "LightPink": [255, 182, 193], "gray9": [23, 23, 23], "green": [0, 255, 0], "brown2": [238, 59, 59], "brown3": [205, 51, 51], "brown1": [255, 64, 64], "brown4": [139, 35, 35], "cadet blue": [95, 158, 160], "orange4": [139, 90, 0], "old lace": [253, 245, 230], "orange3": [205, 133, 0], "orange2": [238, 154, 0], "gray3": [8, 8, 8], "medium spring green": [0, 250, 154], "yellow4": [139, 139, 0], "yellow3": [205, 205, 0], "yellow2": [238, 238, 0], "yellow1": [255, 255, 0], "PapayaWhip": [255, 239, 213], "light sky blue": [135, 206, 250], "MediumOrchid3": [180, 82, 205], "orange": [255, 165, 0], "MediumOrchid2": [209, 95, 238], "OliveDrab1": [192, 255, 62], "OliveDrab2": [179, 238, 58], "OliveDrab3": [154, 205, 50], "dark magenta": [139, 0, 139], "SkyBlue4": [74, 112, 139], "SkyBlue1": [135, 206, 255], "SkyBlue3": [108, 166, 205], "SkyBlue2": [126, 192, 238], "light slate gray": [119, 136, 153], "grey87": [222, 222, 222], "grey58": [148, 148, 148], "grey59": [150, 150, 150], "dark olive green": [85, 107, 47], "grey55": [140, 140, 140], "grey56": [143, 143, 143], "green yellow": [173, 255, 47], "grey50": [127, 127, 127], "orange red": [255, 69, 0], "grey52": [133, 133, 133], "grey53": [135, 135, 135], "cyan2": [0, 238, 238], "cyan3": [0, 205, 205], "gray23": [59, 59, 59], "goldenrod": [218, 165, 32], "gray25": [64, 64, 64], "CornflowerBlue": [100, 149, 237], "cyan4": [0, 139, 139], "gray26": [66, 66, 66], "gray29": [74, 74, 74], "LimeGreen": [50, 205, 50], "dark violet": [148, 0, 211], "DarkBlue": [0, 0, 139], "MediumSlateBlue": [123, 104, 238], "dark orange": [255, 140, 0], "steel blue": [70, 130, 180], "navy": [0, 0, 128], "grey67": [171, 171, 171], "SeaGreen3": [67, 205, 128], "firebrick3": [205, 38, 38], "gray94": [240, 240, 240], "gray95": [242, 242, 242], "gray96": [245, 245, 245], "gray97": [247, 247, 247], "gray90": [229, 229, 229], "gray91": [232, 232, 232], "gray92": [235, 235, 235], "gray93": [237, 237, 237], "MediumPurple": [147, 112, 219], "MidnightBlue": [25, 25, 112], "cornsilk": [255, 248, 220], "red": [255, 0, 0], "dark gray": [169, 169, 169], "royal blue": [65, 105, 225], "grey69": [176, 176, 176], "blue1": [0, 0, 255], "sky blue": [135, 206, 235], "blue3": [0, 0, 205], "blue2": [0, 0, 238], "gainsboro": [220, 220, 220], "DarkOrchid2": [178, 58, 238], "DarkOrchid3": [154, 50, 205], "lemon chiffon": [255, 250, 205], "cornflower blue": [100, 149, 237], "plum4": [139, 102, 139], "alice blue": [240, 248, 255], "rosy brown": [188, 143, 143], "grey70": [179, 179, 179], "DarkSeaGreen": [143, 188, 143], "grey71": [181, 181, 181], "slate grey": [112, 128, 144], "grey77": [196, 196, 196], "tomato4": [139, 54, 38], "tomato1": [255, 99, 71], "grey74": [189, 189, 189], "tomato3": [205, 79, 57], "tomato2": [238, 92, 66], "DarkSlateGray1": [151, 255, 255], "DarkSlateGray2": [141, 238, 238], "DarkSlateGray3": [121, 205, 205], "DarkSlateGray4": [82, 139, 139], "SteelBlue": [70, 130, 180], "deep pink": [255, 20, 147], "gray82": [209, 209, 209], "pink3": [205, 145, 158], "grey79": [201, 201, 201], "MediumVioletRed": [199, 21, 133], "burlywood": [222, 184, 135], "light slate grey": [119, 136, 153], "dark blue": [0, 0, 139], "white": [255, 255, 255], "khaki4": [139, 134, 78], "blanched almond": [255, 235, 205], "DodgerBlue": [30, 144, 255], "RoyalBlue4": [39, 64, 139], "RoyalBlue1": [72, 118, 255], "RoyalBlue3": [58, 95, 205], "RoyalBlue2": [67, 110, 238], "MistyRose1": [255, 228, 225], "MistyRose3": [205, 183, 181], "MistyRose2": [238, 213, 210], "MistyRose4": [139, 125, 123], "LightGray": [211, 211, 211], "LightYellow": [255, 255, 224], "DarkOrange": [255, 140, 0], "medium blue": [0, 0, 205], "forest green": [34, 139, 34], "gray73": [186, 186, 186], "grey41": [105, 105, 105], "gray70": [179, 179, 179], "light green": [144, 238, 144], "DarkGray": [169, 169, 169], "medium turquoise": [72, 209, 204], "turquoise3": [0, 197, 205], "turquoise2": [0, 229, 238], "turquoise1": [0, 245, 255], "burlywood2": [238, 197, 145], "saddle brown": [139, 69, 19], "turquoise4": [0, 134, 139], "lawn green": [124, 252, 0], "linen": [250, 240, 230], "grey47": [120, 120, 120], "snow": [255, 250, 250], "grey46": [117, 117, 117], "gray58": [148, 148, 148], "gray59": [150, 150, 150], "IndianRed4": [139, 58, 58], "purple4": [85, 26, 139], "gray52": [133, 133, 133], "grey44": [112, 112, 112], "purple1": [155, 48, 255], "LightSalmon": [255, 160, 122], "IndianRed2": [238, 99, 99], "IndianRed3": [205, 85, 85], "DarkOrchid1": [191, 62, 255], "thistle3": [205, 181, 205], "SpringGreen1": [0, 255, 127], "SpringGreen2": [0, 238, 118], "SpringGreen3": [0, 205, 102], "salmon": [250, 128, 114], "thistle4": [139, 123, 139], "LightPink2": [238, 162, 173], "LightPink3": [205, 140, 149], "LightPink1": [255, 174, 185], "antique white": [250, 235, 215], "LightPink4": [139, 95, 101], "MediumPurple1": [171, 130, 255], "MediumPurple2": [159, 121, 238], "MediumPurple3": [137, 104, 205], "MediumPurple4": [93, 71, 139], "DimGray": [105, 105, 105], "gray14": [36, 36, 36], "grey100": [255, 255, 255], "OrangeRed3": [205, 55, 0], "OrangeRed2": [238, 64, 0], "OrangeRed1": [255, 69, 0], "maroon4": [139, 28, 98], "gold": [255, 215, 0], "OrangeRed4": [139, 37, 0], "NavajoWhite4": [139, 121, 94], "NavajoWhite1": [255, 222, 173], "LawnGreen": [124, 252, 0], "NavajoWhite3": [205, 179, 139], "LightGoldenrod4": [139, 129, 76], "LightGoldenrod1": [255, 236, 139], "LightGoldenrod3": [205, 190, 112], "LightGoldenrod2": [238, 220, 130], "gray21": [54, 54, 54], "gray13": [33, 33, 33], "azure4": [131, 139, 139], "PaleGreen": [152, 251, 152], "green4": [0, 139, 0], "violet red": [208, 32, 144], "DarkGreen": [0, 100, 0], "green3": [0, 205, 0], "green2": [0, 238, 0], "MediumOrchid": [186, 85, 211], "navajo white": [255, 222, 173], "light steel blue": [176, 196, 222], "black": [0, 0, 0], "indian red": [205, 92, 92], "gray20": [51, 51, 51], "orchid4": [139, 71, 137], "DodgerBlue1": [30, 144, 255], "DodgerBlue2": [28, 134, 238], "PeachPuff": [255, 218, 185], "DodgerBlue4": [16, 78, 139], "orchid1": [255, 131, 250], "orchid2": [238, 122, 233], "orchid3": [205, 105, 201], "DarkSeaGreen4": [105, 139, 105], "DarkSeaGreen3": [155, 205, 155], "yellow green": [154, 205, 50], "DarkSeaGreen1": [193, 255, 193], "orange1": [255, 165, 0], "gold4": [139, 117, 0], "grey72": [184, 184, 184], "bisque4": [139, 125, 107], "MediumOrchid4": [122, 55, 139], "MintCream": [245, 255, 250], "MediumOrchid1": [224, 102, 255], "bisque1": [255, 228, 196], "bisque2": [238, 213, 183], "bisque3": [205, 183, 158], "gray": [190, 190, 190], "DeepSkyBlue": [0, 191, 255], "LightGrey": [211, 211, 211], "grey78": [199, 199, 199], "gray22": [56, 56, 56], "RosyBrown3": [205, 155, 155], "plum3": [205, 150, 205], "plum2": [238, 174, 238], "plum1": [255, 187, 255], "DarkSlateGrey": [47, 79, 79], "DarkOrchid": [153, 50, 204], "OliveDrab": [107, 142, 35], "gray83": [212, 212, 212], "grey": [190, 190, 190], "grey49": [125, 125, 125], "grey48": [122, 122, 122], "thistle": [216, 191, 216], "violet": [238, 130, 238], "grey43": [110, 110, 110], "grey42": [107, 107, 107], "LightSalmon4": [139, 87, 66], "grey40": [102, 102, 102], "LightSalmon2": [238, 149, 114], "LightSalmon3": [205, 129, 98], "grey45": [115, 115, 115], "LightSalmon1": [255, 160, 122], "honeydew": [240, 255, 240], "gray18": [46, 46, 46], "gray19": [48, 48, 48], "LightCyan": [224, 255, 255], "gray15": [38, 38, 38], "gray16": [41, 41, 41], "gray17": [43, 43, 43], "gray10": [26, 26, 26], "gray11": [28, 28, 28], "gray12": [31, 31, 31], "pale violet red": [219, 112, 147], "thistle2": [238, 210, 238], "grey93": [237, 237, 237], "light slate blue": [132, 112, 255], "PaleGoldenrod": [238, 232, 170], "DarkSlateGray": [47, 79, 79], "AntiqueWhite3": [205, 192, 176], "AntiqueWhite2": [238, 223, 204], "AntiqueWhite1": [255, 239, 219], "gray27": [69, 69, 69], "SlateBlue": [106, 90, 205], "AntiqueWhite4": [139, 131, 120], "RosyBrown4": [139, 105, 105], "DimGrey": [105, 105, 105], "VioletRed": [208, 32, 144], "WhiteSmoke": [245, 245, 245], "grey38": [97, 97, 97], "grey39": [99, 99, 99], "grey36": [92, 92, 92], "grey37": [94, 94, 94], "grey34": [87, 87, 87], "hot pink": [255, 105, 180], "grey32": [82, 82, 82], "grey33": [84, 84, 84], "grey30": [77, 77, 77], "grey31": [79, 79, 79], "NavyBlue": [0, 0, 128], "sienna4": [139, 71, 38], "gray81": [207, 207, 207], "gray80": [204, 204, 204], "sienna1": [255, 130, 71], "gray86": [219, 219, 219], "sienna3": [205, 104, 57], "sienna2": [238, 121, 66], "gray89": [227, 227, 227], "gray88": [224, 224, 224], "magenta2": [238, 0, 238], "magenta4": [139, 0, 139], "gray87": [222, 222, 222], "magenta3": [205, 0, 205], "IndianRed": [205, 92, 92], "SlateBlue2": [122, 103, 238], "magenta1": [255, 0, 255], "blue violet": [138, 43, 226], "LightBlue": [173, 216, 230], "grey75": [191, 191, 191], "PeachPuff4": [139, 119, 101], "seashell": [255, 245, 238], "SaddleBrown": [139, 69, 19], "PeachPuff1": [255, 218, 185], "PeachPuff2": [238, 203, 173], "PeachPuff3": [205, 175, 149], "dark goldenrod": [184, 134, 11], "gray100": [255, 255, 255], "aquamarine": [127, 255, 212], "LemonChiffon2": [238, 233, 191], "LemonChiffon1": [255, 250, 205], "tan4": [139, 90, 43], "tan3": [205, 133, 63], "tan2": [238, 154, 73], "tan1": [255, 165, 79], "LemonChiffon4": [139, 137, 112], "IndianRed1": [255, 106, 106], "red3": [205, 0, 0], "OliveDrab4": [105, 139, 34], "OldLace": [253, 245, 230], "LightSkyBlue": [135, 206, 250], "gray84": [214, 214, 214], "PowderBlue": [176, 224, 230], "RoyalBlue": [65, 105, 225], "LightSkyBlue4": [96, 123, 139], "VioletRed3": [205, 50, 120], "LightSkyBlue1": [176, 226, 255], "LightSkyBlue2": [164, 211, 238], "LightSkyBlue3": [141, 182, 205], "dark cyan": [0, 139, 139], "LightYellow1": [255, 255, 224], "LightYellow2": [238, 238, 209], "LightYellow3": [205, 205, 180], "LightYellow4": [139, 139, 122], "goldenrod4": [139, 105, 20], "grey35": [89, 89, 89], "goldenrod1": [255, 193, 37], "goldenrod2": [238, 180, 34], "goldenrod3": [205, 155, 29], "light goldenrod yellow": [250, 250, 210], "LemonChiffon": [255, 250, 205], "burlywood1": [255, 211, 155], "YellowGreen": [154, 205, 50], "LightCoral": [240, 128, 128], "burlywood3": [205, 170, 125], "ivory3": [205, 205, 193], "ivory2": [238, 238, 224], "ivory1": [255, 255, 240], "grey8": [20, 20, 20], "ivory4": [139, 139, 131], "mint cream": [245, 255, 250], "grey9": [23, 23, 23], "burlywood4": [139, 115, 85], "DarkSalmon": [233, 150, 122], "SlateGray1": [198, 226, 255], "SlateGray2": [185, 211, 238], "SlateGray3": [159, 182, 205], "SlateGray4": [108, 123, 139], "RosyBrown2": [238, 180, 180], "RosyBrown1": [255, 193, 193], "dark grey": [169, 169, 169], "dark salmon": [233, 150, 122], "gray85": [217, 217, 217], "medium orchid": [186, 85, 211], "LightGreen": [144, 238, 144], "LavenderBlush1": [255, 240, 245], "grey73": [186, 186, 186], "LavenderBlush3": [205, 193, 197], "LavenderBlush2": [238, 224, 229], "grey76": [194, 194, 194], "LavenderBlush4": [139, 131, 134], "deep sky blue": [0, 191, 255], "dark slate gray": [47, 79, 79], "pink1": [255, 181, 197], "OrangeRed": [255, 69, 0], "pink2": [238, 169, 184], "pink4": [139, 99, 108], "gray47": [120, 120, 120], "gray46": [117, 117, 117], "gray45": [115, 115, 115], "gray44": [112, 112, 112], "gray43": [110, 110, 110], "gray42": [107, 107, 107], "gray41": [105, 105, 105], "gray40": [102, 102, 102], "gray49": [125, 125, 125], "gray48": [122, 122, 122], "MediumAquamarine": [102, 205, 170], "light gray": [211, 211, 211], "powder blue": [176, 224, 230], "azure1": [240, 255, 255], "azure3": [193, 205, 205], "azure2": [224, 238, 238], "sea green": [46, 139, 87], "firebrick": [178, 34, 34], "grey54": [138, 138, 138], "DarkGrey": [169, 169, 169], "grey57": [145, 145, 145], "medium slate blue": [123, 104, 238], "light yellow": [255, 255, 224], "SlateBlue4": [71, 60, 139], "SlateBlue3": [105, 89, 205], "pale turquoise": [175, 238, 238], "SlateBlue1": [131, 111, 255], "grey51": [130, 130, 130], "chartreuse": [127, 255, 0], "dark sea green": [143, 188, 143], "DarkOliveGreen4": [110, 139, 61], "turquoise": [64, 224, 208], "DarkOliveGreen1": [202, 255, 112], "DarkOliveGreen3": [162, 205, 90], "DarkOliveGreen2": [188, 238, 104], "grey6": [15, 15, 15], "grey7": [18, 18, 18], "grey4": [10, 10, 10], "grey5": [13, 13, 13], "grey2": [5, 5, 5], "grey3": [8, 8, 8], "grey0": [0, 0, 0], "grey1": [3, 3, 3], "gray50": [127, 127, 127], "cyan1": [0, 255, 255], "gray51": [130, 130, 130], "gray24": [61, 61, 61], "gray53": [135, 135, 135], "HotPink": [255, 105, 180], "DarkGoldenrod4": [139, 101, 8], "gray54": [138, 138, 138], "DarkGoldenrod1": [255, 185, 15], "DarkGoldenrod2": [238, 173, 14], "DarkGoldenrod3": [205, 149, 12], "purple3": [125, 38, 205], "DeepPink": [255, 20, 147], "gray28": [71, 71, 71], "purple2": [145, 44, 238], "DarkCyan": [0, 139, 139], "peach puff": [255, 218, 185], "GreenYellow": [173, 255, 47], "DebianRed": [215, 7, 81], "DarkOrange4": [139, 69, 0], "DarkOrange1": [255, 127, 0], "DarkOrange3": [205, 102, 0], "orchid": [218, 112, 214], "purple": [160, 32, 240], "grey27": [69, 69, 69], "wheat4": [139, 126, 102], "wheat1": [255, 231, 186], "wheat3": [205, 186, 150], "wheat2": [238, 216, 174], "coral3": [205, 91, 69], "coral2": [238, 106, 80], "coral1": [255, 114, 86], "thistle1": [255, 225, 255], "PaleTurquoise": [175, 238, 238], "bisque": [255, 228, 196], "DeepPink3": [205, 16, 118], "DeepPink2": [238, 18, 137], "DeepPink1": [255, 20, 147], "khaki": [240, 230, 140], "wheat": [245, 222, 179], "MediumSeaGreen": [60, 179, 113], "DeepPink4": [139, 10, 80], "SpringGreen4": [0, 139, 69], "DarkSlateBlue": [72, 61, 139], "PaleVioletRed4": [139, 71, 93], "PaleVioletRed1": [255, 130, 171], "PaleVioletRed2": [238, 121, 159], "PaleVioletRed3": [205, 104, 137], "dark slate grey": [47, 79, 79], "AntiqueWhite": [250, 235, 215], "light salmon": [255, 160, 122], "PaleTurquoise4": [102, 139, 139], "PaleTurquoise3": [150, 205, 205], "PaleTurquoise2": [174, 238, 238], "PaleTurquoise1": [187, 255, 255], "light grey": [211, 211, 211], "plum": [221, 160, 221], "beige": [245, 245, 220], "SpringGreen": [0, 255, 127], "azure": [240, 255, 255], "honeydew1": [240, 255, 240], "honeydew2": [224, 238, 224], "honeydew3": [193, 205, 193], "honeydew4": [131, 139, 131], "gray57": [145, 145, 145], "snow4": [139, 137, 137], "snow2": [238, 233, 233], "snow3": [205, 201, 201], "snow1": [255, 250, 250], "SandyBrown": [244, 164, 96], "grey13": [33, 33, 33], "SeaGreen4": [46, 139, 87], "sandy brown": [244, 164, 96], "SeaGreen2": [78, 238, 148], "SeaGreen1": [84, 255, 159], "grey29": [74, 74, 74], "grey28": [71, 71, 71], "grey25": [64, 64, 64], "grey24": [61, 61, 61], "light pink": [255, 182, 193], "grey26": [66, 66, 66], "grey21": [54, 54, 54], "grey20": [51, 51, 51], "grey23": [59, 59, 59], "grey22": [56, 56, 56], "gray78": [199, 199, 199], "gray79": [201, 201, 201], "gray76": [194, 194, 194], "gray77": [196, 196, 196], "gray74": [189, 189, 189], "gray75": [191, 191, 191], "gray72": [184, 184, 184], "medium sea green": [60, 179, 113], "olive drab": [107, 142, 35], "gray71": [181, 181, 181], "ghost white": [248, 248, 255], "ivory": [255, 255, 240], "light coral": [240, 128, 128], "LemonChiffon3": [205, 201, 165], "DeepSkyBlue4": [0, 104, 139], "DeepSkyBlue3": [0, 154, 205], "DeepSkyBlue2": [0, 178, 238], "DeepSkyBlue1": [0, 191, 255], "cornsilk4": [139, 136, 120], "cornsilk2": [238, 232, 205], "cornsilk3": [205, 200, 177], "CadetBlue": [95, 158, 160], "cornsilk1": [255, 248, 220], "grey90": [229, 229, 229], "grey91": [232, 232, 232], "grey92": [235, 235, 235], "light cyan": [224, 255, 255], "grey94": [240, 240, 240], "floral white": [255, 250, 240], "grey96": [245, 245, 245], "grey97": [247, 247, 247], "grey98": [250, 250, 250], "grey99": [252, 252, 252], "LightSteelBlue1": [202, 225, 255], "LightSteelBlue2": [188, 210, 238], "LightSteelBlue3": [162, 181, 205], "LightSteelBlue4": [110, 123, 139], "red2": [238, 0, 0], "maroon": [176, 48, 96], "light sea green": [32, 178, 170], "spring green": [0, 255, 127], "light goldenrod": [238, 221, 130], "light blue": [173, 216, 230], "lime green": [50, 205, 50], "grey95": [242, 242, 242], "LightGoldenrodYellow": [250, 250, 210], "MediumBlue": [0, 0, 205], "LightSlateGray": [119, 136, 153], "lavender blush": [255, 240, 245], "DarkOrange2": [238, 118, 0], "PaleVioletRed": [219, 112, 147], "maroon2": [238, 48, 167], "dim grey": [105, 105, 105], "ForestGreen": [34, 139, 34], "dark red": [139, 0, 0], "slate blue": [106, 90, 205], "dark green": [0, 100, 0]}
"""
# }}}

def stripAnsi(s):
	# Shamelessly ripped from http://stackoverflow.com/questions/2186919/getting-correct-string-length-in-python-for-strings-with-ansi-color-codes
	import pyparsing
	_ppESC = pyparsing.Literal('\x1b')
	_ppinteger = pyparsing.Word(pyparsing.nums)
	_ppescapeSeq = pyparsing.Combine(_ppESC + '[' + pyparsing.Optional(pyparsing.delimitedList(_ppinteger, ';')) + pyparsing.oneOf(list(pyparsing.alphas)))
	return pyparsing.Suppress(_ppescapeSeq).transformString(s)

# }}}
# DATE AND TIME FUNCTIONS{{{

_TZLOOKUP = {}

def any_tz(name):# {{{
	import pytz, datetime
	global _TZLOOKUP
	if len(_TZLOOKUP) == 0:
		_TZLOOKUP = dict(zip(pytz.all_timezones, pytz.all_timezones) + map(lambda x: [datetime.datetime.now(pytz.timezone(x)).tzname(), x], pytz.all_timezones))
	return pytz.timezone(_TZLOOKUP[name])

def timedelta_to_DHMS(dur, weeks=True, precision=0):
	# doc{{{
	"""
	Given a timedelta object, outputs a string representing said duration.
	For example: 


	>>> print(jlib.timedelta_to_DHMS(datetime.timedelta(days=5, hours=2, minutes=25)))
	5d 02h 25m 00s

	>>> print(jlib.timedelta_to_DHMS(datetime.timedelta(days=5, hours=2, minutes=25, microseconds=123), precision=4))
	5d 02h 25m 00.0001s
	"""
	# }}}
	ts = abs(dur.total_seconds())
	micros = int(ts * int(1e6)) - (int(ts) * int(1e6))
	secs = int(ts)
	if weeks:
		wks=0
		if secs >= 604800:
			wks = secs / 604800
			secs = secs % 604800

	days = 0
	if secs >= 86400:
		days = secs / 86400
		secs = secs % 86400
	hours = 0
	if secs >= 3600:
		hours = secs / 3600
		secs = secs % 3600
	mins = 0
	if secs >= 60:
		mins = secs / 60
		secs = secs % 60

	strout = ''
	if dur.total_seconds() < 0:
		strout += '-'
	if weeks and wks > 0:
		strout += '%dw ' % wks
	if days > 0 or weeks and wks > 0:
		strout += '%dd ' % days
	strout += "%02dh %02dm %02d" % (hours, mins, secs)
	if precision > 0:
		if precision > 6:
			precision = 6
		strout += '.' + str(micros).rjust(6, '0')[:precision]
	strout += 's'
	return strout
# }}}
def DHMS_to_timedelta(dhms):# {{{
	# Lifted and adapted from https://gist.github.com/Ayehavgunne/ac6108fa8740c325892b
	import datetime
	dhms = dhms.lower()
	prev_num = []
	timedelta_kwargs = {}
	for character in dhms:
		if character.isalpha():
			if prev_num:
				num_str = ''.join(prev_num)
				if '.' in num_str:
					num = float(num_str)
				else:
					num = int(num_str)
				if character == 'w':
					key = 'weeks'
				elif character == 'd':
					key = 'days'
				elif character == 'h':
					key = 'hours'
				elif character == 'm':
					key = 'minutes'
				elif character == 's':
					key = 'seconds'
				else:
					raise ValueError("Unknown DHMS predicate: {}".format(character))
				timedelta_kwargs[key] = num
				prev_num = []
		elif character.isnumeric() or character == '.':
			prev_num.append(character)
	if prev_num:
		raise ValueError("Dangling quantity: {}".format(''.join(prev_num)))
	return datetime.timedelta(**timedelta_kwargs)
# }}}
def format_timestamp(dt, omit_tz=False, alt_tz=False, precision=6):# {{{
	# doc{{{
	"""\
	Takes a timezone-aware datetime object and makes it look like:

	2019-01-21 14:38:21.123456 PST

	Or, if you call it with omit_tz=True:

	2019-01-21 14:38:21.123456

	The precision parameter controls how many digits past the decimal point you
	get. 6 gives you all the microseconds, 0 avoids the decimal point altogether
	and you just get whole seconds.
	"""
	# }}}
	tz_format = "%Z"
	if alt_tz:
		tz_format = "%z"
	timestamp_txt = dt.strftime("%F %T")
	if precision > 0:
		timestamp_txt = "{}.{}".format(timestamp_txt, "{:06d}".format(dt.microsecond)[:precision])
	if not omit_tz and dt.tzinfo is not None:
		timestamp_txt = "{} {}".format(timestamp_txt, dt.strftime("%z"))
	return timestamp_txt
# }}}
def datetime_to_timestamp(dt):# {{{
	# doc{{{
	"""
	Turns a timezone-aware datetime object into a standard UTC-seconds-since-epoch timestamp.

	If the datetime object passed to this function has no timezone information, it is treated as UTC.
	"""
	# }}}
	from pytz.reference import LocalTimezone, UTC
	import time
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=UTC)
	tupe = dt.astimezone(LocalTimezone()).timetuple()
	ctime = time.mktime(tupe)
	if dt.microsecond > 0:
		ctime += (float(dt.microsecond) / int(1e6))
	return ctime
# }}}
def parse_decimal_timestamp(ts):# {{{
	# doc{{{
	"""
	Turns a fractional timestamp (1559053068.263864) provided as a string
	into a datetime object. This datetime object will be timezone-aware,
	set to your local timezone.
	
	NOTE: this function returns different results than vanilla
	datetime.datetime.fromtimestamp(), as this function performs no
	rounding:

	>>> import datetime, pytz.reference, jlib
	>>> ts = 1569306469.4397779
	>>> jlib.parse_decimal_timestamp(str(ts))
	datetime.datetime(2019, 9, 23, 23, 27, 49, 439777, tzinfo=<pytz.reference.LocalTimezone object at 0x7ff525c83208>)
	>>> datetime.datetime.fromtimestamp(ts, tz=pytz.reference.Local)
	datetime.datetime(2019, 9, 23, 23, 27, 49, 439778, tzinfo=<pytz.reference.LocalTimezone object at 0x7ff525c83208>)
	"""
	# }}}
	import pytz.reference, datetime
	frags = ts.split('.', 1)
	dt = datetime.datetime.fromtimestamp(int(frags[0]), tz=pytz.reference.Local)
	if len(frags) > 1:
		# Note the "[:6]" — sometimes we get floats with
		# greater-than-microsecond precision!
		dt = dt.replace(microsecond=int(frags[1][:6]))
	return dt
# }}}
def utcnow_tzaware():# {{{
	# doc{{{
	"""
	Convenience function, equivalent to 
	`datetime.datetime.utcnow().replace(tzinfo=pytz.reference.UTC)`
	"""
	# }}}
	import pytz.reference, datetime
	return datetime.datetime.utcnow().replace(tzinfo=pytz.reference.UTC)
# }}}
def now_tzaware():# {{{
	# doc{{{
	"""
	Convenience function, equivalent to 
	`datetime.datetime.now(tz=pytz.reference.Local)`
	"""
	# }}}
	import pytz.reference, datetime
	return datetime.datetime.now(tz=pytz.reference.Local)
# }}}
def timestamp_to_utcdatetime(ts):# {{{
	# doc{{{
	"""
	Like `datetime.datetime.utcfromtimestamp()`, except it returns a
	timezone-aware datetime object.
	"""
	# }}}
	import pytz.reference, datetime
	return datetime.datetime.utcfromtimestamp(ts).replace(tzinfo=pytz.reference.UTC)
# }}}
def timestamp_to_localdatetime(ts):# {{{
	# doc{{{
	"""
	Like `datetime.datetime.fromtimestamp()`, except it returns a
	timezone-aware datetime object.
	"""
	# }}}
	import pytz.reference, datetime
	return datetime.datetime.fromtimestamp(ts).replace(tzinfo=pytz.reference.Local)
# }}}
# }}}
# ARRAY MAKING AND BREAKING{{{

# Shamelessly culled from http://code.activestate.com/recipes/496784-split-string-into-n-size-pieces/
# Note that, slick as the implementation of this and splitlen_array are, they
# have a potentially fatal flaw in that they silently drop any remainder pieces
# that don't line up against the split length.
def splitlen(data, length):
	return [''.join(x) for x in list(zip(*[list(data[z::length]) for z in range(length)]))]

#def splitlen_array(data, length):
#	return [x for x in list(zip(*[list(data[z::length]) for z in range(length)]))]

# This is my own design, and is BETTAR
def splitlen_array(data, length):
	return [ data[x:x+length] for x in [ x * length for x in range(int(len(data) / length)) ] ]

# Here's another implementation, from 2021 jays:
#def splitlen_array(data, length):
#	return list(zip(*[ data[z::length] for z in range(length) ]))

def splitlen_array_remainder(data, length):
	import math
	return [ data[x:x+length] for x in [ x * length for x in range(math.ceil(len(data) / length)) ] ]

# Just tack on a ....
# "Just tack on" he says. This was more of a pain in the ass than I thought
# it would be.
# Just to be pedantically verbose about what's going on here, these next
# two functions are the versions that are able to handle the remainder
# that get left over when the size of the dataset doesn't divide evenly
# into the requested split size. In other words, if you split an array
# of 143,584 items into chunks of length 10,000, the regular splitlen
# functions will give you 14 chunks and exclude the last 3,584
# datapoints, whereas these *_remainder functions will give you
# 15 chunks: 14 of size 10,000, and 1 of size 3,584.
def splitlen_remainder(data, length):
	ret = splitlen(data, length)
	rem = list(data[int(len(data) / length) * length:])
	if len(rem) > 0:
		ret.append(''.join(rem))
	return ret

#def splitlen_array_remainder(data, length):
#	ret = splitlen_array(data, length)
#	rem = list(data[int(len(data) / length) * length:])
#	if len(rem) > 0:
#		ret += [rem]
#	return ret

def flatten(stuff):
	return [item for sublist in stuff for item in sublist]
# }}}
# SELECTPIPE{{{

class wat:
	def __init__(self, fd):
		self.fd = fd
	def read(self, size):
		return os.read(self.fd, size)
	def fileno(self):
		return self.fd

class SelectPipeSocketSource(Thread):
	def __init__(self, insock, outfh=None, bsize=8192):
		import io
		Thread.__init__(self)
		self.insock = insock
		self.outfh = outfh
		self.bsize = bsize
		if self.outfh is None:
			self.output_rend, self.output_wend = os.pipe()
			self.outfh = io.BufferedWriter(io.FileIO(self.output_wend, mode="w"))
			self.stdout = wat(self.output_rend)
	def run(self):
		import select
		keepGoing = True
		while keepGoing:
			ri = []
			wi = []
			xi = []
			if self.insock.fileno() == -1:
				try:
					print("SelectPipeSocketSource input socket went invalid, closing output")
					self.outfh.close()
				except IOError:
					pass
				break
			ri.append(self.insock)
			wi.append(self.outfh)
			try:
				ro, wo, xo = select.select(ri, wi, xi, 0.1)
			except ValueError:
				print("{} {} {}".format(repr(ro), repr(wo), repr(xo)))
				raise
			if self.insock in ro and self.outfh in wo:
				buf = self.insock.recv(self.bsize)
				if len(buf) > 0:
					try:
						self.outfh.write(buf)
					except IOError:
						keepGoing = False
						try:
							print("SelectPipeSocketSource closing input")
							self.insock.close()
						except IOError:
							pass
				else:
					keepGoing = False
					try:
						print("SelectPipeSocketSource closing input")
						self.insock.close()
					except IOError:
						pass
					try:
						print("SelectPipeSocketSource closing output")
						self.outfh.close()
					except IOError:
						pass
		print("SelectPipeSocketSource falling out")

class SelectPipeFileobjSink:
	def __init__(self, blocking=True):
		import io
		self.rfd, self.wfd = os.pipe()
		self.stdin = io.FileIO(self.wfd, mode="wb")
		self.stdout = io.FileIO(self.rfd, mode="rb")
		
class SelectPipe(Thread):
	def __init__(self, infh, outfh, infn=None, outfn=None, bsize=8192):
		Thread.__init__(self)
		self.infh = infh
		self.outfh = outfh
		self.infn = infn
		self.outfn = outfn
		self.bsize = bsize
	def run(self):
		import io, select
		if self.infh is None:
			#print("SelectPipe opening input %s" % self.infn)
			self.infh = open(self.infn, 'rb')
		if self.outfh is None:
			#print("SelectPipe opening output %s" % self.outfn)
			self.outfh = open(self.outfn, 'wb')
		while not self.infh.closed:
			ri = []
			wi = []
			xi = []

			# Workaround pt. 1: Don't add it to the list of
			# filehandles to check for readability if it's BytesIO.
			if not type(self.infh) is io.BytesIO:
				ri.append(self.infh)

			wi.append(self.outfh)
			ro, wo, xo = select.select(ri, wi, xi, 0.1)

			# Workaround pt. 2: Add it to the list of readable
			# filehandles if it's BytesIO.
			if type(self.infh) is io.BytesIO:
				ro.append(self.infh)

			if self.infh in ro and self.outfh in wo:
				buf = self.infh.read(self.bsize)
				if len(buf) > 0:
					try:
						self.outfh.write(buf)
						self.outfh.flush()
					except IOError:
						try:
							self.infh.close()
						except IOError:
							return
				else:
					#try:
					#	self.infh.close()
					#except IOError:
					#	pass
					try:
						self.infh.close()
					except IOError:
						pass
					try:
						self.outfh.close()
					except IOError:
						pass

class SelectPipeFitting(object):
	def __init__(self, func, textmode=False):
		import io
		self.func = func
		self.input_rend, self.input_wend = os.pipe()
		self.output_rend, self.output_wend = os.pipe()
		self.stdin = io.FileIO(self.input_wend, mode="w")
		self.stdout = io.FileIO(self.output_rend, mode="r")
		if textmode:
			rfio = io.FileIO(self.input_rend, mode="r")
			rfbr = io.BufferedReader(rfio)
			self._stdin_internal = io.TextIOWrapper(rfbr)
			wfio = io.FileIO(self.output_wend, mode="w")
			wfbr = io.BufferedWriter(wfio)
			self._stdout_internal = io.TextIOWrapper(wfbr, line_buffering=True)
		else:
			self._stdin_internal = io.FileIO(self.input_rend, mode="r")
			self._stdout_internal = io.FileIO(self.output_wend, mode="w")
		self.thread = Thread(target=self.run_stub)
		self.thread.start()
	def run_stub(self):
		try:
			self.func(self._stdin_internal, self._stdout_internal)
		except:
			# TODO: Implement some sort of way of telling when the pipeline burst?
			pass
		if not self._stdout_internal.closed:
			self._stdout_internal.close()
			#print("fitting closing stdout", file=sys.stderr)
	def wait(self):
		self.thread.join()


class SelectPipeline(object):
	def __init__(self, infileobj=None, outfileobj=None):
		self.infileobj = infileobj
		self.outfileobj = outfileobj
		self.chain = []
		self.pipeline = []
	def add(self, link):
		self.chain.append(link)
	def run(self):
		last = self.infileobj
		chain_len = len(self.chain)
		for link in self.chain:
			self.pipeline.append(SelectPipe(infh=last, outfh=link.stdin))
			last = link.stdout
		if self.outfileobj is None:
			self.outfileobj = last
		else:
			self.pipeline.append(SelectPipe(infh=last, outfh=self.outfileobj))
		for segment in self.pipeline:
			segment.start()
	def finish(self):
		import subprocess
		for link in reversed(self.chain):
			if type(link) in [subprocess.Popen, SelectPipeFitting]:
				link.wait()
		for segment in self.pipeline:
			segment.join()
# }}}
# PATH MANIPULATION AND INTERROGATION{{{

def get_scriptdir():
	return os.path.dirname(os.path.realpath(sys.argv[0]))

def get_scriptdir_soft():
	return os.path.dirname(os.path.abspath(sys.argv[0]))

def get_userconfig_dir():
	"""
	I wrote this because apparently some desktop environments don't
	bother setting XDG_CONFIG_HOME. So what this does, is it uses
	that environment variable if it exists, otherwise returns a
	canned reply that points to ~/.config.
	"""
	if 'XDG_CONFIG_HOME' in os.environ:
		return os.environ['XDG_CONFIG_HOME']
	return os.path.join(os.environ['HOME'], '.config')

def splitpath(x):
	"""
	A version of `os.path.split` that keeps on splitting until the splitting's done.
	Returns a list.
	"""
	a, b = os.path.split(x)
	out = []
	while a != '' and a != '/':
		out.append(b)
		a, b = os.path.split(a)
	out.append(b)
	if a == '/':
		out.append(a)
	out.reverse()
	return out

def splitexts(x):
	"""
	A version of `os.path.splitext` that keeps on splitting until
	the splitting's done. It will return a list of all of the resultant
	filename fragments.

	>>> jlib.splitexts("/home/jayson/woof.tar.gz")
	['/home/jayson/woof', '.tar', '.gz']

	"""
	ret = collections.deque()
	base = x
	base, ext = os.path.splitext(base)
	while (ext != ''):
		ret.appendleft(ext)
		base, ext = os.path.splitext(base)
	ret.appendleft(base)
	return list(ret)


def find_mountpoint(path, ascend_mountpoint=False):
	"""
	Finds the root directory for the filesystem that <path> belongs to.
	In other words, `find_mountpoint("/dev/null")` will return `'/dev'`.

	Note that calling find_mountpoint on a mountpoint will return that same
	mountpoint. (ie, `find_mountpoint("/dev")` will return `'/dev'`).
	Setting the `ascend_mountpoint` parameter to True will incite this
	function to return the mountpoint's mountpoint, instead.

	"""
	base = os.path.abspath(path)
	if ascend_mountpoint and os.path.ismount(base):
		base, spoke = os.path.split(base)
	while not os.path.ismount(base):
		base, spoke = os.path.split(base)
	return base

def find_path_ascending(f, startdir, enddir='/', multiple=False, iter_limit=256):
	"""
	Searches for file/dir `f`, starting in `startdir`.

	If it isn't found there, startdir's parent dir will be checked,
	then that parent's parent, and so on, until either a match is found,
	enddir is encountered, or iter_limit attempts have been made.

	If a match is found, its absolute pathname is returned, otherwise
	you get None, son!

	Setting `multiple` to True changes the behavior of this function:
	instead of a single path or None value, a list will be returned
	containing every occurrence of file/dir `f` from `startdir` up to
	`enddir`, in order of occurrence.  If none are found, you will of
	course be handed an empty list.

	"""
	startdir = os.path.abspath(startdir)
	enddir = os.path.abspath(enddir)
	base = startdir
	i = 0
	if multiple:
		ret = []
	while True:
		i += 1
		if i > iter_limit:
			break
		testfn = os.path.join(base, f)
		if os.path.exists(testfn):
			if multiple:
				ret.append(testfn)
			else:
				return testfn
		if base == enddir:
			break
		base, spoke = os.path.split(base)
	if multiple:
		return ret
	return None

class UnixSearchPath(list):# {{{
	"""A class for dealing with Unix-style search path declarations, a la the PATH environment variable."""
	# This definition does not work with python2. Boo python2.
	#def __init__(self, *args, joinfunc=lambda x,y: os.path.join(x,y), searchfunc=lambda x: os.path.exists(x)):
	def __init__(self, *args, **kwargs):
		kwargs_ok = set(['joinfunc', 'searchfunc'])
		for k in kwargs.keys():
			if k not in kwargs_ok:
				raise Python2SucksError("Disallowed keyword argument: {}".format(k))
		self.joinfunc = kwargs.get('joinfunc', lambda x, y: os.path.join(x, y))
		self.searchfunc = kwargs.get('searchfunc', lambda x: os.path.exists(x))
		"""Creates a new UnixSearchPath. With args like list(). Because it's a subclass of list.
		If you supply an alternate searchfunc, it will be used as a filter when the find() or find_all() methods are invoked.
		If you supply an alternate joinfunc, it will be used to combine the elements of the SearchPath with the find target."""
		super(UnixSearchPath, self).__init__(args)
	@classmethod
	def from_string(cls, pathstr):
		"""Run this like: UnixSearchPath.from_string("/bin:/usr/bin:/sbin")  , and you'll get a UnixSearchPath, all filled out."""
		return cls(*pathstr.split(':'))
	def to_string(self):
		"""Call this method to turn a UnixSearchPath (list) back into a flat string."""
		return ':'.join(self)
	def find(self, target):
		"""Iterates through the SearchPath, looking for and returning the first occurrence of target.
		If target is not found, ValueError will be raised."""
		results = self.find_all(target)
		if len(results) < 1:
			raise ValueError(target)
		return results[0]
	def find_all(self, target):
		"""Returns all occurrences of target in the SearchPath, ordered by, well, search order.
		If no occurrences are found, you'll get back an empty list.  Because empty list."""
		return [x for x in [self.joinfunc(x, target) for x in self] if self.searchfunc(x)]
	def exists(self, target):
		"""Somewhat like the find() method, except you're getting back a True or False."""
		try:
			self.find(target)
			return True
		except ValueError:
			return False
# }}}
class KeywordSearchPath(UnixSearchPath):# {{{
	"""Like a UnixSearchPath, but specific target matches can be added via a "key=destination" mechanism.
	Therefore, a KeywordSearchPath derived from this:
		/bin:/usr/bin:puppydog=/usr/local/bin/woof.bin:/opt/local/bin
	Will cause a standard search behavior for the paths not assigned a keyword. In other words, running find("grep") will kick off a search for "/bin/grep", followed by "/usr/bin/grep", then "/opt/local/bin/grep", before finally falling out with a ValueError. If, however, find("puppydog") is performed, the search will immediately return "/usr/local/bin/woof.bin".
	This class was cooked up specifically for jnotes.py, so that a combination of directory searches and specific keyword jumps can be combined to make pulling up documentation quick and painless. Your mileage may vary."""
	def find_all(self, target):
		keywords = {}
		paths = []
		for item in self:
			frags = item.split('=', 1)
			if len(frags) == 1:
				paths.append(item)
			else:
				keywords[frags[0]] = frags[1]

		return \
			[target] if os.path.isabs(target) and os.path.exists(target) \
			else [keywords[target]] if target in keywords else \
			[] + [x for x in [self.joinfunc(x, target) for x in paths] if self.searchfunc(x)]
# }}}

def get_syspath():
	"""
	Sugar function to retrieve and split out the system PATH

	"""
	return UnixSearchPath.from_string(os.environ['PATH'])

def locate_binary(bin_name, altpath=None):
	"""
	Iterates through the system PATH for the supplied binary name,
	returning the absolute path to the first occurrence found,
	or None if it's not located.

	"""
	if altpath is not None:
		pathiterator = altpath
	else:
		pathiterator = get_syspath()
	for path_elem in pathiterator:
		if os.path.exists(os.path.join(path_elem, bin_name)):
			return os.path.abspath(os.path.join(path_elem, bin_name))
	raise FileNotFoundError(bin_name)

def search_binary(pat, altpath=None):
	"""Applies a match filter against each of the (+x) binaries in the
	system path, returning the absolute path of each match.

	 The match filter is only applied to the filename portion of each binary,
	 so a search for r'^ld' will, for example, return '/sbin/ldconfig' and
	 '/usr/bin/ld', among others.

	No checks are performed to ensure sanity of the results, so if you're
	being extra cautious, you may want to ask some questions of each
	returned result, such as:

	* Are you set executable?
	* Are you set executable FOR ME?
	* Are you something I can actually execute (a file (or a valid symlink
	  that eventually resolves to a file, and not something silly like
	  a directory or FIFO)?

	"""
	import re
	if altpath is not None:
		pathiterator = altpath
	else:
		pathiterator = get_syspath()
	cpat = re.compile(pat)
	ret = []
	for path_elem in pathiterator:
		if not os.path.isdir(path_elem):
			continue
		for f in os.listdir(path_elem):
			if not cpat.search(f):
				continue
			fn = os.path.join(path_elem, f)
			ret.append(fn)
	return ret
	
def splitext_compressed(fn):
	"""
	Works like `os.path.splitext()`, except in the case of compressed files,
	specifically the ones where it's convention to tack an extra extension
	on the end denoting the compression type.

	Think: `'file.txt.gz'`.

	This function will include any compressed extensions as well, so
	supplying `'file.txt.gz'` will return `('file', '.txt.gz')`,
	`'file.txt.gz.bz2'` will return `('file', '.txt.gz.bz2')`,
	`'file.gz'` will return `('file', '.gz')` and `'file.txt.md5sum.bz2'`
	will return `('file.txt', '.md5sum.bz2')`.

	"""
	fileext = ''
	fileroot, ext = os.path.splitext(fn)
	while ext.lower() in compressed_exts:
		fileext = ext + fileext
		fileroot, ext = os.path.splitext(fileroot)
	fileext = ext + fileext
	return fileroot, fileext

class IterWalk(object):# {{{
	"""
	This is just a simple object that acts as a shortcut to get an iterator that walks
	recursively down a directory tree.
	"""
	def __init__(self, walkdir, include_dirs=False, include_files=True, sort_key=None):
		self.walkdir = walkdir
		self.include_dirs = include_dirs
		self.include_files = include_files
		self.sort_key = sort_key
	def __iter__(self):
		for root, dirs, files in os.walk(self.walkdir):
			if self.sort_key is not None:
				dirs.sort(key=self.sort_key)
				files.sort(key=self.sort_key)
			if self.include_dirs:
				for x in [os.path.join(root, d) for d in dirs]:
					yield x
			if self.include_files:
				for x in [os.path.join(root, f) for f in files]:
					yield x
# }}}

def iter_file_or_dir(path, followlinks=False):
	"""
	Returns a generator which will yield different results depending on
	the nature of the path supplied.

	In the case of a directory, it will yield all of the files contained
	within that directory, recursively. As with `os.walk()`, symlinks
	will not be traversed unless `followlinks` is True. Files are returned
	in "natural sort" order (see `natsort.py`), because I like that.

	In the case of anything that isn't a directory, it will just yield
	that filesystem element's path.

	If you supply this function with a path that doesn't exist, it won't
	yield anything.

	"""
	from . import natsort
	if os.path.isdir(path):
		for root, dirs, files in os.walk(path, followlinks=followlinks):
			dirs.sort(key=natsort.nocase)
			files.sort(key=natsort.nocase)
			for f in files:
				yield os.path.join(root, f)
	elif os.path.exists(path):
		yield path


class FakeDirEntry:
	"""
	Since os.DirEntry doesn't allow us to use it, and I've got code that
	expects that it's working on os.DirEntry objects, I've had to roll
	my own.

	arguments:

	basedir — The base directory for this FakeDirEntry. Use "." if you're
			  describing an element in the current directory.
	name — the name of the file, directory, symlink, whatever.
	is_file — set True if you already know it's a file, False if you know
			  it's not, or leave it None and it'll get looked up the first
			  time the user runs the `is_file()` method.
	is_dir — same as is_file, but for directories.
	is_symlink — same as is_file, but for symlinks.
	inode — set this to the element's inode if you know it, else leave it
			None and it'll get looked up the first time the user runs
			the inode() method.
	
	As for how it works post-instantiation, just go look at the documentation
	for `os.DirEntry`.

	"""
	__slots__ = ['basedir', 'name', '_is_file', '_is_dir', '_is_symlink', '_inode']
	def __init__(self, basedir, name, is_file=None, is_dir=None, is_symlink=None, inode=None):
		self.basedir = basedir
		self.name = name
		self._is_file = is_file
		self._is_dir = is_dir
		self._is_symlink = is_symlink
		self._inode = inode
	@property # path
	def path(self):
		return os.path.join(self.basedir, self.name)
	def stat(self, follow_symlinks=True):
		return os.stat(self.path, follow_symlinks=follow_symlinks)
	def inode(self):
		if self._inode is None:
			self._inode = self.stat(follow_symlinks=False).st_ino
		return self._inode
	def is_file(self):
		if self._is_file is None:
			import stat
			self._is_file = stat.S_ISREG(self.stat(follow_symlinks=True).st_mode)
		return self._is_file
	def is_dir(self):
		if self._is_dir is None:
			import stat
			self._is_dir = stat.S_ISDIR(self.stat(follow_symlinks=True).st_mode)
		return self._is_dir
	def is_symlink(self):
		if self._is_symlink is None:
			import stat
			self._is_symlink = stat.S_ISLNK(self.stat(follow_symlinks=False).st_mode)
		return self._is_symlink
# }}}

def scanwalk(top, topdown=True, onerror=None, followlinks=False):# {{{
    """
	Just like os.walk, except it returns juicy fresh os.DirEntry objects,
	rather than overcooked, sad, lumpy paths.

	In fact, this is almost EXACTLY like os.walk, because I copied
	walk straight out of python 3.8's os module, and modified a couple
	of bits. I'm definitely not laying claim to this code by including
	it in my library.
    """
    top = os.fspath(top)
    dirs = []
    nondirs = []
    walk_dirs = []

    # We may not have read permission for top, in which case we can't
    # get a list of the files the directory contains.  os.walk
    # always suppressed the exception then, rather than blow up for a
    # minor reason when (say) a thousand readable directories are still
    # left to visit.  That logic is copied here.
    try:
        # Note that scandir is global in this module due
        # to earlier import-*.
        scandir_it = os.scandir(top)
    except OSError as error:
        if onerror is not None:
            onerror(error)
        return

    with scandir_it:
        while True:
            try:
                try:
                    entry = next(scandir_it)
                except StopIteration:
                    break
            except OSError as error:
                if onerror is not None:
                    onerror(error)
                return

            try:
                is_dir = entry.is_dir()
            except OSError:
                # If is_dir() raises an OSError, consider that the entry is not
                # a directory, same behaviour than os.path.isdir().
                is_dir = False

            if is_dir:
                dirs.append(entry)
            else:
                nondirs.append(entry)

            if not topdown and is_dir:
                # Bottom-up: recurse into sub-directory, but exclude symlinks to
                # directories if followlinks is False
                if followlinks:
                    walk_into = True
                else:
                    try:
                        is_symlink = entry.is_symlink()
                    except OSError:
                        # If is_symlink() raises an OSError, consider that the
                        # entry is not a symbolic link, same behaviour than
                        # os.path.islink().
                        is_symlink = False
                    walk_into = not is_symlink

                if walk_into:
                    walk_dirs.append(entry.path)

    # Yield before recursion if going top down
    if topdown:
        yield top, dirs, nondirs

        # Recurse into sub-directories
        islink, join = os.path.islink, os.path.join
        for dirname in dirs:
            new_path = join(top, dirname)
            # Issue #23605: os.path.islink() is used instead of caching
            # entry.is_symlink() result during the loop on os.scandir() because
            # the caller can replace the directory entry during the "yield"
            # above.
            if followlinks or not islink(new_path):
                yield from scanwalk(new_path, topdown, onerror, followlinks)
    else:
        # Recurse into sub-directories
        for new_path in walk_dirs:
            yield from scanwalk(new_path, topdown, onerror, followlinks)
        # Yield after recursion if going bottom up
        yield top, dirs, nondirs
# }}}

# HACKS
# As alluded to in https://stackoverflow.com/questions/128573/using-property-on-classmethods and https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
class classproperty:
	def __init__(self, fget):
		self.fget = fget
	def __get__(self, owner_self, owner_cls):
		return self.fget(owner_cls)

class manydict(dict):# {{{
	"""
	This is more or less a dict, except any keys added to it will be
	treated as set()s. Any attempt to reassign a key's value will instead
	result in that value being add()ed to the existing set:

	>>> wuf = manydict()
	>>> wuf['bark'] = 'woof'
	>>> wuf['bark'] = 'arf'
	>>> wuf['bark'] = 'wan'
	>>> wuf['bark']
	{'wan', 'woof', 'arf'}

	If you want to alter a key in a manydict, use an appropriate set() method
	on the key:

	>>> wuf['bark'].remove('wan')
	>>> wuf['bark']
	{'woof', 'arf'}

	If you want to discard any existing contents of a key, use the replace()
	method:

	>>> wuf.replace('bark', 'miau')
	>>> wuf['bark']
	{'miau'}

	Since lists are not hashable and thus cannot normally be add()ed to a
	set, I've added a potentially useful behavior: if you try to do this:

	>>> wuf['bark'] = ['mew', 'meow', 'murr', 'nyan']

	This is essentially what will happen internally:

	wuf['bark'].update(set(['mew', 'meow', 'murr', 'nyan']))
	
	Thus giving you a quick and simple way to add multiple items to a key
	without breaking kayfabe. Be sure to mind your types, however...
	if you add a tuple, you'll get a tuple:

	>>> wuf['bark'] = ('hiss', '*scratch*')
	>>> wuf['bark']
	{'nyan', 'miau', 'meow', ('hiss', '*scratch*'), 'mew', 'murr'}
	"""
	def __setitem__(self, k, v):
		if k not in self:
			super(self.__class__, self).__setitem__(k, set())
		if type(v) is list:
			self[k].update(v)
		else:
			self[k].add(v)
	def replace(self, k, v):
		if k in self:
			del self[k]
		self[k] = v
# }}}

# This is sugar to take out some repetitive drudgery.
# Initialize it with a bunch of options as a hash (hint: x = easy_opt(opts.__dict__), where opts came from optparse.parse_args).
# Then, if you want to check for existence AND value of an arbitrary arg, access it as an attribute:
# >>> if x.stufftodo == "wash the dog":
# If the attribute doesn't exist, you'll get None back, so you don't have to do existence testing and exception handling.
# If you DO want that sort of thing, access it as a hash value:
# >>> heregoesnothing = x['geronimo']
# If dict key 'geronimo' doesn't exist, you're in for a ride!

tty_interactive = False
if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
	tty_interactive = True

class short_md5(object):# {{{
	def __init__(self, val):
		self.val = val
	def digest(self):
		import struct
		a, b = struct.unpack('QQ', self.val.digest())
		return struct.pack('Q', a ^ b)
	def hexdigest(self):
		import binascii
		return binascii.hexlify(self.digest())
# }}}
class shorter_md5(short_md5):# {{{
	def digest(self):
		import struct
		c = super(shorter_md5,self).digest()
		d, e = struct.unpack('II', c)
		return struct.pack('I', d ^ e)
# }}}
def runtime_dir():# {{{
	"""
	Returns what is hopefully a sane runtime directory, i.e., someplace
	relatively save to write scratch files and the like.

	On Darwin systems, this function returns the value of os.environ['TMPDIR'].

	On Linux systems, this function returns the value of
	os.environ['XDG_RUNTIME_DIR'], if it's present. Otherwise, it falls back
	to os.environ['TMPDIR'].

	If the requisite environment variables are not defined, this function will
	return "/tmp". If /tmp doesn't exist, it will raise RuntimeError.
	"""

	environ_variable = "TMPDIR"

	if sys.platform in ['linux', 'linux2']:
		if "XDG_RUNTIME_DIR" in os.environ:
			environ_variable = "XDG_RUNTIME_DIR"
	
	if environ_variable not in os.environ:
		if os.access("/tmp", os.W_OK):
			return "/tmp"
		else:
			raise RuntimeError("Could not find a suitable candidate for runtime dir!")
	return os.environ[environ_variable]
# }}}
class Netstat(list):# {{{
	if sys.platform == 'darwin':
		portsep = '.'
	else:
		portsep = ':'
	def __init__(self):
		super(Netstat, self).__init__()
		self.refresh()
	def refresh(self):
		import subprocess
		del self[0:len(self)]
		statinfo = subprocess.check_output(['netstat', '-an'])
		for x in statinfo.splitlines():
			frags = x.split()
			while len(frags) < 6:
				frags.append('')
			for idx in (3, 5):
				ipport = frags.pop(idx)
				port = ipport.split(self.portsep)[-1]
				addr = '.'.join(ipport.split(self.portsep)[:-1])
				frags.insert(idx, port)
				frags.insert(idx, addr)
			if not frags[0].startswith('tcp') and not frags[0].startswith('udp'):
				continue
			self.append(NetstatEntry(*frags))
# }}}
NetstatEntry = collections.namedtuple('NetstatEntry', 'proto recvq sendq localaddr localport remoteaddr remoteport state'.split()) 

class PollableQueue(Queue.Queue):# {{{
	def __init__(self):
		import socket
		super().__init__()
		# Create a pair of connected sockets
		if os.name == 'posix':
			self._putsocket, self._getsocket = socket.socketpair()
		else:
			# Compatibility on non-POSIX systems
			server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			server.bind(('127.0.0.1', 0))
			server.listen(1)
			self._putsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self._putsocket.connect(server.getsockname())
			self._getsocket, _ = server.accept()
			server.close()
	def fileno(self):
		return self._getsocket.fileno()
	def put(self, item):
		super().put(item)
		self._putsocket.send(b'x')
	def get(self):
		self._getsocket.recv(1)
		return super().get()
# }}}

class jstr(str):# {{{
	def as_human_readable(self, expected_len=200):
		import binascii, hashlib
		if is_ascii(self):
			if len(self) < 200:
				return self
			else:
				return cooked_str('<<%s ASCII characters %%%s>>' % (len(self), shorter_md5(hashlib.md5(self)).hexdigest()), self)
		elif len(self) < 100:
			return cooked_str('<0x' + binascii.hexlify(self) + '>', self)
		else:
			return cooked_str('<<%s binary bytes %%%s>>' % (len(self), shorter_md5(hashlib.md5(self)).hexdigest()), self)
	to_human_readable = staticmethod(as_human_readable)
# }}}
# Fuck this noise, peep unicode_enforcer below.
if sys.version_info.major < 3:# {{{
	unicode_goodness = False
	class junicode(unicode):
		def as_human_readable(self, expected_len=200):
			import binascii, hashlib
			if not unicode_goodness and is_ascii(self):
				if len(self) < 200:
					return self
				else:
					return cooked_str('<<%s ASCII characters %%%s>>' % (len(self), shorter_md5(hashlib.md5(self.encode('utf-8'))).hexdigest()), self)
			elif unicode_goodness:
				if len(self) < 200:
					return self
				else:
					return cooked_str('<<%s UTF8 characters %%%s>>' % (len(self), shorter_md5(hashlib.md5(self.encode('utf-8'))).hexdigest()), self)
			elif len(self) < 100:
				return cooked_str('<0x' + binascii.hexlify(self.encode('utf-8')) + '>', self)
			else:
				return cooked_str('<<%s binary bytes %%%s>>' % (len(self), shorter_md5(hashlib.md5(self.encode('utf-8'))).hexdigest()), self)
		to_human_readable = staticmethod(as_human_readable)
# }}}
class jstr(str):# {{{
	def as_human_readable(self, expected_len=200):
		import binascii, hashlib
		if is_ascii(self):
			if len(self) < 200:
				return self
			else:
				return cooked_str('<<%s ASCII characters %%%s>>' % (len(self), shorter_md5(hashlib.md5(self.encode('utf-8'))).hexdigest()), self)
		elif len(self) < 100:
			return cooked_str('<0x' + binascii.hexlify(self.encode('utf-8')).decode() + '>', self)
		else:
			return cooked_str('<<%s binary bytes %%%s>>' % (len(self), shorter_md5(hashlib.md5(self.encode('utf-8'))).hexdigest()), self)
	to_human_readable = staticmethod(as_human_readable)
# }}}

# Inelegant as fuck, but effective as fuck
# Use it by changing something like this:
#
# html = renderer.render(fucky_text)
#
# with this:
#
# html = unicode_enforcer(lambda x: renderer.render(x), fucky_text)
def unicode_enforcer(lambdafunc, fucker):# {{{
	try:
		return lambdafunc(fucker)
	except UnicodeEncodeError:
		try:
			return lambdafunc(fucker.encode('utf-8'))
		except UnicodeEncodeError:
			return lambdafunc(fucker.decode('utf-8'))
# }}}
class cooked_str(str):# {{{
	def __new__(self, value, original):
		self = str.__new__(cooked_str, value)
		self.original = original
		return self
	def as_original(self):
		return self.original
		# }}}

class easy_opt(object):# {{{
	def __init__(s, opts):
		s._opts = opts
	def __getattr__(s, x):
		if x not in s._opts:
			return False
		return s._opts[x]
	def __getitem__(s, x):
		return s._opts[x]
	def __contains__(s, x):
		return x in s._opts
# }}}
class proppadict(dict):# {{{
	def __getattr__(self, attr):
		if attr in self:
			return self[attr]
		else:
			raise AttributeError
	def __setattr__(self, attr, val):
			self[attr] = val
	def __delattr__(self, attr):
			del(self[attr])
	def copy(self):
		return proppadict(self.items())
# }}}


	



class GhettoUpdatingLine(object):# {{{
	__slots__ = ['buf', 'fh', 'mute']
	def __init__(s, fh=sys.stderr):
		s.buf = ''
		s.mute = False
		s.fh = fh
	def update(s, msg):
		if s.mute: return
		if msg is not None:
			s.buf = msg
		s.fh.write("\x1b\r[2K%s" % s.buf)
		s.fh.flush()
	def line(s, msg, fh=None):
		if s.mute:
			s.fh.write("%s\n")
			s.fh.flush()
		else:
			if fh is not None and fh != s.fh:
				s.fh.write("\x1b\r[2K")
				s.fh.flush()
				fh.write("%s\n" % msg)
				fh.flush()
				s.fh.write("%s" % s.buf)
				s.fh.flush()
			else:
				s.fh.write("\x1b\r[2K%s\n%s" % (msg, s.buf))
				s.fh.flush()
	def speakup(s):
		s.mute = False
	def shutup(s):
		s.mute = True
	def __del__(s):
		s.fh.write("\n")
		s.fh.flush()
# }}}
class TempFilePool:# {{{
	debug = False
	registry = set()
	@classmethod
	def register(cls, **kwargs):
		import tempfile
		tf = tempfile.mkstemp(**kwargs)
		os.close(tf[0])
		cls.registry.add(tf[1])
		if cls.debug: print("# Registered and provided: %s" % tf[1], file=sys.stderr)
		return tf[1]
	@classmethod
	def register_fifo(cls, **kwargs):
		import tempfile
		fn = tempfile.mktemp(**kwargs)
		os.mkfifo(fn)
		cls.registry.add(fn)
		if cls.debug: print("# Registered and provided fifo: %s" % fn, file=sys.stderr)
		return fn
	@classmethod
	def deregister(cls):
		if f not in cls.registry: return
		if os.path.exists(f): os.unlink(f)
		cls.registry.remove(f)
		if cls.debug: print("# Deregistered and removed: %s" % f, file=sys.stderr)
	@classmethod
	def deregister_all(cls):
		if cls.debug: print("# deregister_all called", file=sys.stderr)
		while len(cls.registry) > 0:
			f = cls.registry.pop()
			if os.path.exists(f):
				if cls.debug: print("# Culling abandoned tempfile %s" % f, file=sys.stderr)
				os.unlink(f)
			else:
				if cls.debug: print("# Tempfile %s not deregistered, but already gone" % f, file=sys.stderr)
		if cls.debug: print("# deregister_all finished", file=sys.stderr)

atexit.register(TempFilePool.deregister_all)
# }}}

def ss(buf):# {{{
	import base64, bz2
	return base64.encodestring(bz2.compress(buf))
# }}}
def ssz(buf):# {{{
	import base64
	return base64.encodestring(buf.encode("zlib"))
# }}}
def rs(buf):# {{{
	import base64, bz2
	return bz2.decompress(base64.decodestring(buf))
# }}}
def rsz(buf):# {{{
	import base64
	return base64.decodestring(buf).decode("zlib")
# }}}

def getstat(src):# {{{
	"""I took shutil.copystat and split it into two functions, so you can
	run getstat() on a file, do stuff to said file, and then push the
	previous mode bits, atime, mtime, and flags back onto the file
	with setstat().

	So in reality, *this* function is functionally identical to os.stat. """
	return os.stat(src)
# }}}
def setstat(dst, st):# {{{
	"""I took shutil.copystat and split it into two functions, so you can
	run getstat() on a file, do stuff to said file, and then push the
	previous mode bits, atime, mtime, and flags back onto the file
	with setstat().

	The magic happens here, and by magic, I mean just the stuff that
	shutil.copystat does... """
	import stat
	mode = stat.S_IMODE(st.st_mode)
	if hasattr(os, 'utime'):
		os.utime(dst, (st.st_atime, st.st_mtime))
	if hasattr(os, 'chmod'):
		os.chmod(dst, mode)
	if hasattr(os, 'chflags') and hasattr(st, 'st_flags'):
		try:
			os.chflags(dst, st.st_flags)
		except OSError as why:
			for err in 'EOPNOTSUPP', 'ENOTSUP':
				if hasattr(errno, err) and why.errno == getattr(errno, err):
					break
			else:
				raise
# }}}

def bitflip(val):# {{{
	b = val
	b = (b & 0xF0) >> 4 | (b & 0x0F) << 4
	b = (b & 0xCC) >> 2 | (b & 0x33) << 2
	b = (b & 0xAA) >> 1 | (b & 0x55) << 1
	return b
# }}}

########################
#
# Custom class - Base26
#
# {{{

intspecials = 'abs add and cmp truediv divmod floordiv invert rtruediv rdivmod reduce reduce_ex rfloordiv rlshift rmod rmul ror rpow rrshift rshift rsub rtruediv rxor sub truediv trunc xor'

def returnthisclassfrom(specials):
	specialnames = ['__%s__' % s for s in specials.split()]
	def wrapit(cls, method):
		return lambda *a: cls(method(*a))
	def dowrap(cls):
		for n in specialnames:
			method = getattr(cls, n)
			setattr(cls, n, wrapit(cls, method))
		return cls
	return dowrap

@returnthisclassfrom(intspecials)
class Base26(int):
	def __new__(cls, value, precision=4):
		if type(value) in StringTypes:
			return cls.from_str(value, precision)
		self = int.__new__(Base26, value)
		self.precision = precision
		return self
	@classmethod
	def from_str(cls, value, *args):
		i = 1
		v = 0
		precision = len(value)
		while len(value) > 0:
			x = value[-1:]
			value = value[:-1]
			t = ord(x) - ord('a')
			v += t * i
			i *= 26
		return Base26(v, precision=precision)
	def __str__(self):
		t = self
		s = []
		while (t > 25):
			s.insert(0, chr(ord('a') + (t % 26)))
			t /= 26
		s.insert(0, chr(ord('a') + t))
		return ''.join(s).rjust(self.precision, 'a')
	def __add__(self, other):
		return type(self)(int(self).__add__(int(other)), self.precision)
	def __repr__(self):
		return "%s(%s)" % (self.__class__.__name__, repr(str(self)))
	def __cmp__(self, other):
		return int(self).__cmp__(int(other))
# }}}
#
########################



class MissingIndexError(Exception):
	pass

class DuplicateIndexError(Exception):
	pass

class ImmutableKeyError(Exception):
	pass

class Encyclopedia(object):# {{{
	def __init__(self, indices):
		self.datastore = {}
		for idx in indices:
			self.datastore[idx] = {}
	def __iter__(self):
		return iter(self.datastore[self.datastore.keys()[0]].values())
	def add_index(self, idx):
		if self.datastore.has_key('idx'):
			raise DuplicateIndexError(idx)
		for d in self:
			if not d.has_key(idx):
				raise MissingIndexError(d)
		self.datastore[idx] = {}
		for d in self:
			self.datastore[idx][d[idx]] = d
	def add(self, d):
		for idx in self.datastore.keys():
			if not d.has_key(idx):
				raise MissingIndexError(idx)
			if self.datastore[idx].has_key(d[idx]):
				raise DuplicateIndexError(idx)
		for idx in self.datastore.keys():
			self.datastore[idx][d[idx]] = d
	def exists(self, idx, val):
		return self.datastore[idx].has_key(val)
	def get(self, idx, val):
		return self.datastore[idx][val]
	def update(self, idx, ival, key, val):
		if self.datastore.has_key(key):
			raise ImmutableKeyError(key)
		self.datastore[idx][ival][key] = val
	def __len__(self):
		return len(self.datastore[self.datastore.keys()[0]].values())
	def __getitem__(self, key):
		return self.datastore[key]
# }}}
class Python2SucksError(Exception):
	pass


def _listcodecs(dir):# {{{
	import os, codecs, encodings
	names = []
	for filename in os.listdir(dir):
		if filename[-3:] != '.py':
			continue
		name = filename[:-3]
		# Check whether we've found a true codec
		try:
			codecs.lookup(name)
		except LookupError:
			# Codec not found
			continue
		except Exception as reason:
			# Probably an error from importing the codec; still it's
			# a valid code name
			if _debug:
				print('* problem importing codec %r: %s' % (name, reason))
		names.append(name)
	return names	
# }}}
def list_codecs(include_aliases=False):# {{{
	import os, codecs, encodings 
	names = set()
	names.update(_listcodecs(encodings.__path__[0]))
	if include_aliases:
		from encodings.aliases import aliases
		names.update(aliases.keys())
	return sorted(list(names))
# }}}
def host_address_size():# {{{
	import struct
	return struct.calcsize("P") * 8
# }}}
def histlist():# {{{
	import readline
	ret = []
	for i in range(readline.get_current_history_length()):
		ret.append(readline.get_history_item(i + 1))
	return ret
# }}}
def history():# {{{
	return "\n".join(histlist())
# }}}
common_file_exclusions = [
	'.DS_Store',
	'.AppleDouble',
	'.AppleDB',
]

def pypy_read(fn):# {{{
	fh = open(fn)
	data = fh.read()
	fh.close()
	return data
# }}}
# PROCESS FORKING AND DAEMONIZATION{{{

def forkmerunning(kill_parent=True):
	"""
	Performs all actions necessary to complete the traditional
	UNIX "fork and daemonize" operation, save the closing and
	redirection of stdin/stdout/stderr. If you want those too,
	execute forkme() instead.

	If kill_parent is set to True, the parent process will
	just go away. If it's set to False, this function will
	return True for the parent process, and False for
	the grandchild. Note that since we're doing a double
	fork, there is no way to get the grandchild pid.
	"""
	try:
		pid = os.fork()
	except OSError:
		print("Couldn't fork!", file=sys.stderr)
		raise
	if pid > 0:
		if kill_parent:
			sys.exit(0)
		else:
			return True

	os.chdir('/')
	os.setsid()
	os.umask(0)

	try:
		pid = os.fork()
	except OSError:
		print("Couldn't fork!", file=sys.stderr)
		raise
	if pid > 0:
		sys.exit(0)
	else:
		return False

def forkme(kill_parent=True):
	"""
	Does all the things that are needful when you think
	"fork and daemonize".
	"""
	is_parent = forkmerunning(kill_parent=kill_parent)

	if not is_parent:
		sys.stdout.flush()
		sys.stderr.flush()

		if hasattr(os, "devnull"):
			redirect = os.devnull
		else:
			redirect = "/dev/null"

		null_fh = open(redirect, 'w')
		null_fd = null_fh.fileno()
		sys.stdout = null_fh
		sys.stderr = null_fh
		#null_fd = os.open(redirect, os.O_RDWR)
		for fd in range(3):
			try:
				os.close(fd)
			except OSError:
				pass
		# As an extra pedantic bit of precaution, we capture the
		# file descriptor we get after opening our null interface
		# (which should be 0!) and explicitly redirect accordingly.
		for fd in range(3):
			if fd != null_fd:
				os.dup2(null_fd, fd)
	return is_parent
# }}}

def splice(dest, donor, copy=True):# {{{
	"""
	An update function for dict trees.
	"""
	# TODO: configurable handling of sets
	if sys.version_info.major < 3:
		methname = 'iteritems'
		mappingtype = collections.Mapping
	else:
		import collections.abc
		methname = 'items'
		mappingtype = collections.abc.Mapping
	for k, v in getattr(donor, methname)():
		if isinstance(v, mappingtype):
			dest[k] = splice(dest.get(k, {}), v)
		else:
			if copy and hasattr(v, 'copy'):
				dest[k] = v.copy()
			else:
				dest[k] = v
	return dest
# }}}
def dict_concatenate(*dicts):
	"""
	Returns a dict* which is the product of `splice()`ing the
	supplied dicts together.

	* Technically, what you'll get back is initialized as
	  `dicts[0].__class__()`.
	"""
	res = dicts[0].__class__()
	for d in dicts:
		splice(res, d)
	return res

# Refresher: Base64 encoded data uses the characters a-z, A-Z, 0-9, '+', and '/',
# with a special guest appearance of '=' on the end as padding, if necessary.
base64_ords = set([43, 61] + list(range(47, 58)) + list(range(65, 91)) + list(range(97, 123)))
base64_linesize = 76
base64_binsize	= (base64_linesize // 4) * 3
class Base64StreamDecoder(object):# {{{
	""" This is an interface for decoding an indeterminate amount of
	base64-encoded data.

	Chunks of data (of type bytes) are given to the decoder object using the
	feed() method. Any whitespace or invalid characters will be stripped out
	and the remaining data will be accumulated in an internal buffer. If this
	buffer contains enough data to decode, the decodable portion will be parted
	out and returned, otherwise a bytes object of length 0 will be returned.
	This way, one can safely reconstruct the decoded output by simply
	concatenating the feed() method's output. When all data has been fed to
	the decoder object, calling the finish() method will decode and return any
	remaining data in the buffer.
	"""
	def __init__(self):
		self.buf = b''
	def feed(self, data):
		import binascii
		ret = b''
		self.buf += bytes([x for x in data[:] if x in base64_ords])
		while len(self.buf) >= base64_linesize:
			chunk = self.buf[:base64_linesize]
			self.buf = self.buf[base64_linesize:]
			ret += binascii.a2b_base64(chunk)
		return ret
	def finish(self):
		import binascii
		ret = binascii.a2b_base64(self.buf)
		self.buf = b''
		return ret
# }}}
class Base64StreamEncoder(object):# {{{
	""" This is an interface for encoding an indeterminate amount of binary
	data into base64.

	Chunks of data (of type bytes) are given to the encoder object by using
	the feed() method.	This data will be accumulated in an internal buffer,
	and if enough data exists to produce one or more 76-character lines of
	base64-encoded output, the encodable portion will be parted out and
	returned (including newline characters) as a bytes object, otherwise a
	zero-length bytes object will be returned. This way, an appropriate output
	stream can be generated by simply concatenating the output of the feed()
	method. When all data to be encoded has been fed to the encoder object,
	calling the finish() method will encode any remaining data in the buffer,
	adding padding characters if appropriate along with a final newline
	character.
	"""
	def __init__(self):
		self.buf = b''
	def feed(self, data):
		import binascii
		ret = b''
		self.buf += data
		while len(self.buf) >= base64_binsize:
			chunk = self.buf[:base64_binsize]
			self.buf = self.buf[base64_binsize:]
			ret += binascii.b2a_base64(chunk)
		return ret
	def finish(self):
		import binascii
		chunk = self.buf
		self.buf = b''
		return binascii.b2a_base64(chunk)
# }}}
def round_properly(value, precision=0):# {{{
	"""
	I don't know who came up with this "round to even" tomfuckery, but I was
	always taught that when you round some shit, everything below .5 rounds the
	the fuck down, and everything .5 and above rounds the motherfuck up.
	"""
	if precision != 0:
		adjvalue = value * (10 ** precision)
	else:
		adjvalue = value
	intvalue = int(adjvalue)
	if adjvalue > intvalue and adjvalue >= (intvalue + .5):
		roundvalue = intvalue + 1
	else:
		roundvalue = intvalue
	if precision != 0:
		return roundvalue / (10 ** precision)
	else:
		return roundvalue
# }}}


class OrderedSet(collections.OrderedDict, collections.MutableSet):# {{{
	"""
	Lifted from:
	https://stackoverflow.com/questions/1653970/does-python-have-an-ordered-set

	NOTE: Don't use this. Go install the `orderedset` module from PIP instead.
	You can do much more useful things with it:
	>>> import orderedset
	>>> orse = orderedset.OrderedSet(['xid', 'pid', 'x', 'y'])
	>>> orse.index('xid')
	0
	>>> orse[0]
	'xid'

	"""
	def update(self, *args, **kwargs):
		if kwargs:
			raise TypeError("update() takes no keyword arguments")
		for s in args:
			for e in s:
				 self.add(e)
	def add(self, elem):
		self[elem] = None
	def discard(self, elem):
		self.pop(elem, None)
	def __le__(self, other):
		return all(e in other for e in self)
	def __lt__(self, other):
		return self <= other and self != other
	def __ge__(self, other):
		return all(e in self for e in other)
	def __gt__(self, other):
		return self >= other and self != other
	def __repr__(self):
		return 'OrderedSet([%s])' % (', '.join(map(repr, self.keys())))
	def __str__(self):
		return '{%s}' % (', '.join(map(repr, self.keys())))
	difference = property(lambda self: self.__sub__)
	difference_update = property(lambda self: self.__isub__)
	intersection = property(lambda self: self.__and__)
	intersection_update = property(lambda self: self.__iand__)
	issubset = property(lambda self: self.__le__)
	issuperset = property(lambda self: self.__ge__)
	symmetric_difference = property(lambda self: self.__xor__)
	symmetric_difference_update = property(lambda self: self.__ixor__)
	union = property(lambda self: self.__or__)
# }}}

class Lut:
	"""
	Oftentimes, when interfacing with APIs (especially of the C variety),
	you find yourself needing to resolve a symbolic name from an id value,
	or vice-versa. That's what this class is for. It stores data in two
	dicts, one keyed by id, the other keyed by value.

	stuff = Lut()
	stuff.add(0, "No")
	stuff.add(1, "Yes")
	stuff.add(2, "Maybe")
	stuff.add(3, "Probably")

	You can then easily resolve ids to name, or names to id:

	>>> stuff.name(1)
	'Yes'
	>>> stuff.id("Probably")
	3

	If you instantiate the class with `allow_duplicates=True`, adding the same
	id or name to a Lut more than once will cause lists to be returned on
	lookup.

	>>> things = Lut(allow_duplicates=True)
	>>> things.add(5, 'KEY_0')
	>>> things.add(5, 'KEY_RIGHTPAREN')
	>>> things.name(5)
	['KEY_0', 'KEY_RIGHTPAREN']

	If you want an attempt to add a duplicate to the LUT to raise an exception,
	set `allow_duplicates` to False instead. Default behavior is
	`allow_duplicates=None`, which will cause reassignment.
	"""
	def __init__(self, *args, allow_duplicates=None):
		self.allow_duplicates=allow_duplicates
		self.byid   = {}
		self.byname = {}
		for id_val, name_val in args:
			self.add(id_val, name_val) 
	def add(self, id_val, name_val):
		for key, table, val, exc in (
			(id_val, self.byid, name_val, KeyError),
			(name_val, self.byname, id_val, ValueError)
		):
			if key in table:
				if self.allow_duplicates is None:
					table[key] = val
				elif self.allow_duplicates:
					if not isinstance(table[key], list):
						# Convert existing value to list
						table[key] = [table[key]]
					table[key].append(val)
				else:
					# Hack: if raising an exception due to a duplicate
					# name_val, be sure to remove the corresponding id_val
					# that was just added prior
					if exc is ValueError:
						del self.byid[id_val]
					raise exc(key)
			else:
				table[key] = val
	def name(self, id_val):
		return self.byid[id_val]
	def id(self, name_val):
		return self.byname[name_val]
	@property
	def names(self):
		return self.byname.keys()
	@property
	def ids(self):
		return self.byid.keys()


class Nalpha:# {{{
	render_attrs = {
		'lowercase': {
			'start': ord('a'),
			'len': 26,
		},
		'uppercase': {
			'start': ord('A'),
			'len': 26,
		},
		'digits': {
			'start': ord('0'),
			'len': 10,
		}
	}
	def __init__(self, val=None, padlen=3, lowercase=1, uppercase=0, digits=0):
		self.val = val
		self.padlen = padlen
		self.attrs = {}
		self.attrs['lowercase'] = lowercase
		self.attrs['uppercase'] = uppercase
		self.attrs['digits'] = digits
		# Sanity check to make sure nothing was added with the same priority
		priorities = [ self.attrs[x] for x in self.attrs if self.attrs[x] > 0 ]
		if len(priorities) != len(set(priorities)):
			raise ValueError("Attempted to initialize Nalpha with duplicate priorities!")
	def parameters(self):
		import functools
		attrs = sorted([ x for x in self.attrs if self.attrs[x] > 0 ], key=lambda x: self.attrs[x])
		base = sum([ self.render_attrs[x]['len'] for x in attrs ])
		valchars = functools.reduce(lambda a, b: a + b, [ [ chr(x + self.render_attrs[y]['start']) for x in range(self.render_attrs[y]['len']) ] for y in attrs ])
		return (attrs, base, valchars)
	def as_str(self):
		attrs, base, valchars = self.parameters()
		valscratch = self.val
		keepgoing = True
		digitchars = []
		while keepgoing:
			digitval = valscratch % base
			valscratch //= base
			digitchars.insert(0, valchars[digitval])
			if valscratch == 0:
				keepgoing = False
		while len(digitchars) < self.padlen:
			digitchars.insert(0, valchars[0])
		return ''.join(digitchars)
	def parse(self, data):
		attrs, base, valchars = self.parameters()
		scratch = list(data)
		mod = 1
		val = 0
		while len(scratch) > 0:
			char = scratch.pop()
			val += (valchars.index(char) * mod)
			mod *= base
		return val
	def __str__(self):
		return "{:n}".format(self.val)
	def __repr__(self):
		return "<{}({})>".format(self.__class__.__name__, self.val)
# }}}


def tenacious_execute(cursor, *args, **kwargs):# {{{
	import sqlite3, time
	while True:
		try:
			return cursor.execute(*args)
			break
		except sqlite3.OperationalError as e:
			if 'database is locked' not in e.args:
				raise
			time.sleep(0.01)
# }}}
def lsblk_get_devices(as_dict=True):# {{{
	"""
	Runs `lsblk` to get a list of block devices, their children, filesystem types, mountpoints,
	et cetera... does a little bit of additional trickery in order to return results as a dict.
	"""
	import json, subprocess
	procargs = ['lsblk', '--fs', '-J']
	blockdev_data = json.loads(subprocess.check_output(procargs))['blockdevices']
	if as_dict:
		return dict([ (x['name'], x) for x in blockdev_data ])
	else:
		return blockdev_data
# }}}
def lsblk_get_device_for_mountpoint(mountpoint):# {{{
	"""
	Calls `lsblk_get_devices()` and parses the output, searching for the requested mountpoint
	and returning its dict. If the device is deeper down than the toplevel, the dict will also
	be given an appropriate 'parent' key.
	"""
	keepGoing = True
	blockdevs = collections.deque(lsblk_get_devices(as_dict=False))
	while len(blockdevs) > 0:
		current = blockdevs.popleft()
		if current['mountpoint'] == mountpoint:
			return current
		if 'children' in current:
			for kid in current['children']:
				kid['parent'] = current
				blockdevs.append(kid)
	raise Exception("Mountpoint not found!")
# }}}

def ssh_portforward(host, destport, username=None, allow_pwprompt=False):# {{{
	"""
	Uses socket.bind() to find a random available local port, and connects it to the requested
	remote port via ssh.
	"""
	import subprocess, socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind(("127.0.0.1", 0))
	localport = sock.getsockname()[1]
	ssh_args = ['-q', '-oServerAliveInterval=60']
	if not allow_pwprompt:
		ssh_args.append('-oBatchMode=yes')
	if username is not None:
		ssh_args.extend(['-l', username])
	procargs = ['ssh'] + ssh_args + ['-L', '{}:127.0.0.1:{}'.format(localport, destport), '-f', host, 'sleep 10']
	sock.close()
	proc = subprocess.Popen(procargs)
	proc.communicate()
	return localport
# }}}
# ARGPARSE HELP FORMATTERS{{{

# This class simply combines the great tastes of ArgumentDefaultsHelpFormatter and RawDescriptionHelpFormatter. 
class CustomHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
	pass

# Here's my snippet for getting a standard help setup up and running:

#	import argparse
#	# ArgumentParser setup.{{{
#	parser_kwargs = {}
#	parser_kwargs['description'] = __doc__.splitlines()[0]
#	if len(__doc__.splitlines()) > 2:
#		parser_kwargs['epilog'] = "\n".join(__doc__.splitlines()[2:])
#	parser_kwargs['formatter_class'] = jlib.SomewhatPhisticatedHelpFormatter
#	# }}}
#	parser = argparse.ArgumentParser(**parser_kwargs)

# This class represents an attempt to take more control over formatting
# the description and epilog sections. It's named what it is because it
# isn't SoPhisticated; it's only SomewhatPhisticated.
# Theory of operation:
# Format your text however you want, just like you would with
# argparse.RawDescriptionHelpFormatter, with this exception: any line you
# start with a tab character will get line-wrapped.
class SomewhatPhisticatedHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
	def __init__(self, *args, **kwargs):
		self.debug = False
		for k, v in get_fabulous().items():
			setattr(self, k, v)
		# The default argparse formatters don't like us having a good time.
		# And by having a good time, we mean "having as many consecutive
		# newlines as we damn well please". So, we do a little mufufu here
		# by taking their precious "long break matcher" regex and replacing
		# it with something that NEVER MATCHES. MUFUFU, MOFOFO!
		super(self.__class__, self).__init__(*args, **kwargs)
		#self._long_break_matcher = argparse._re.compile("(?!x)x")
	def print(self, msg):
		if self.debug:
			print(msg)
	def _fill_text(self, text, width, indent):
		ret = ''
		self.print("_fill_text: {}, {}, {}".format(repr(text), repr(width), repr(indent)))
		text = text.replace("\uf8f8", "\n")
		for line in text.splitlines(keepends=True):
			self.print(self.fg256("green", "line") + ": {}".format(repr(line)))
			if line.startswith('\t'):
				import textwrap
				retval = textwrap.fill(line[1:], width, initial_indent=indent, subsequent_indent=indent) + "\n"
			else:
				retval = indent + line
			self.print(self.fg256("yellow", "line") + ": {}".format(repr(retval)))
			ret += retval
		ret = ret.replace("\n","\uf8f8")
		self.print(self.fg256("yellow", "ret: ") + repr(ret))
		return ret
	def format_help(self):
		help = self._root_section.format_help()
		if help:
			help = self._long_break_matcher.sub('\n\n', help)
			help = help.strip('\n') + '\n'
		help = help.replace("\uf8f8", "\n")
		return help
	#def _split_lines(self, *args, **kwargs):
	#	self.print(self.fg256("green", "_split_lines(") + "{}".format(repr(args)) + self.fg256("green", ", ") + "{}".format(repr(kwargs) + self.fg256("green", ")")))
	#	ret = super(self.__class__, self)._split_lines(*args, **kwargs)
	#	self.print(self.fg256("yellow", "_split_lines output: ") + "{}".format(repr(ret)))
	#	return ret
	#def _format_text(self, *args, **kwargs):
	#	self.print(self.fg256("green", "_format_text(") + "{}".format(repr(args)) + self.fg256("green", ", ") + "{}".format(repr(kwargs) + self.fg256("green", ")")))
	#	ret = super(self.__class__, self)._format_text(*args, **kwargs)
	#	self.print(self.fg256("yellow", "_format_text output: ") + "{}".format(repr(ret)))
	#	return ret
	def add_text(self, *args, **kwargs):
		#args = tuple([ None if x is None else x.replace("\n", "\uf8f8") for x in args ])
		self.print(self.fg256("green", "add_text(") + "{}".format(repr(args)) + self.fg256("green", ", ") + "{}".format(repr(kwargs) + self.fg256("green", ")")))
		ret = super(self.__class__, self).add_text(*args, **kwargs)
		self.print(self.fg256("yellow", "add_text output: ") + "{}".format(repr(ret)))
		return ret
	#def format_usage(self, *args, **kwargs):
	#	self.print(self.fg256("green", "format_usage(") + "{}".format(repr(args)) + self.fg256("green", ", ") + "{}".format(repr(kwargs) + self.fg256("green", ")")))
	#	ret = super(self.__class__, self).format_usage(*args, **kwargs)
	#	self.print(self.fg256("yellow", "format_usage output: ") + "{}".format(repr(ret)))
	#	return ret
	#def format_help(self, *args, **kwargs):
	#	self.print(self.fg256("green", "format_help(") + "{}".format(repr(args)) + self.fg256("green", ", ") + "{}".format(repr(kwargs) + self.fg256("green", ")")))
	#	ret = super(self.__class__, self).format_help(*args, **kwargs)
	#	self.print(self.fg256("yellow", "format_help output: ") + "{}".format(repr(ret)))
	#	return ret
# }}}

def kill_thread(thread_obj):
	"""
	Uses voodoo incantation `ctypes.pythonapi.PyThreadState_SetAsyncExc()` to
	compel a thread to disapparate.

	Adapted from: https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
	"""
	import threading, ctypes
	thread_id = [ x for x, y in threading._active.items() if y == thread_obj ][0]
	res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
	if res > 1:
		ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
		raise RuntimeError("Thread refused to die!")
