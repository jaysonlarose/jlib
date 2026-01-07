#!/usr/bin/env python3
"""
"natural sorting" algorithm.

The function `natural_key` was NOT written by Jayson Larose.

They found it here:

https://stackoverflow.com/questions/34518/natural-sorting-algorithm/6924517
"""

# TODO: add unicodedata.normalize("NKFD", <str>)?

from __future__ import print_function
import re, sys

def natural_key(string_):
	"""See http://www.codinghorror.com/blog/archives/001018.html"""
	return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]


def natural_key_lower(string_):
	return natural_key(string_.lower())

case = natural_key
nocase = natural_key_lower
natcmp = natural_key
natcasecmp = natural_key_lower

def cmp_natural(a, b):
	"""
	Perform "natural" sorting, the old "cmp" way.
	Suitable for feeding to something like sqlite3.Connection.create_collation().
	"""
	sa = natural_key(a)
	sb = natural_key(b)
	if sa == sb:
		return 0
	elif sa <sb:
		return -1
	else:
		return 1

def cmp_natural_nocase(a, b):
	"""
	Perform case-insensitive "natural" sorting, the old "cmp" way.
	Suitable for feeding to something like sqlite3.Connection.create_collation().
	"""
	sa = natural_key_lower(a)
	sb = natural_key_lower(b)
	if sa == sb:
		return 0
	elif sa <sb:
		return -1
	else:
		return 1

def natsort(seq, cmp=natcmp, key=None):
	if key is not None:
		mykey = lambda x: cmp(key(x))
	else:
		mykey = cmp
	seq.sort(key=mykey)

def natsorted(seq, cmp=natcmp, key=None):
	if not hasattr(seq, 'sort'):
		temp = list(seq)
	else:
		import copy
		temp = copy.copy(seq)
	natsort(temp, cmp=cmp, key=key)
	return temp



if __name__ == '__main__':
	import os, sys, argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", action="store_true", dest="case_sensitive", default=False, help="Do case-sensitive sort")
	args = parser.parse_args()

	if args.case_sensitive:
		sort_key = case
	else:
		sort_key = nocase

	sortme = []
	for line in sys.stdin:
		while len(line) > 0 and line[-1] in ['\r', '\n']:
			line = line[:-1]
		sortme.append(line)
	sortme.sort(key=sort_key)
	for element in sortme:
		print(element)
