#!/usr/bin/env python

import setuptools

version = __import__("jlib").__version__
setuptools.setup(
	name         = "jlib",
	version      = version,
	author       = "Jayson Larose",
	author_email = "jayson@interlaced.org",
	url          = "https://github.com/jaysonlarose/jlib",
	description  = "Jays' Steaming Pile of Python Cruft",
	download_url = f"https://github.com/jaysonlarose/jlib/releases/download/{version}/jlib-{version}.tar.gz",
	packages     = ['jlib'],
)
