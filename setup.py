#!/usr/bin/env python

from distutils.core import setup

version = __import__("JaysTerm").__version__
setup(
	name = "JaysTerm",
	version = version,
	author = "Jayson Larose",
	author_email = "jayson@interlaced.org",
	url = "https://github.com/jaysonlarose/jlib",
	description = "Jays' Steaming Pile of Python Cruft",
	download_url = f"https://github.com/jaysonlarose/jlib/releases/download/{version}/jlib-{version}.tar.gz",
	packages=['jlib'],
)
