#!/usr/bin/env python

import setuptools, configparser

parser = configparser.ConfigParser()
parser.read("setup.cfg")


version = parser['metadata']['version']
setuptools.setup(
	name         = "jlib",
	version      = version,
	author       = "Jayson Larose",
	author_email = "jayson@interlaced.org",
	url          = "https://github.com/jaysonlarose/jlib",
	description  = "Jays' Steaming Pile of Python Cruft",
	download_url = f"https://github.com/jaysonlarose/jlib/releases/download/{version}/jlib-{version}.tar.gz",
	packages     = ['jlib'],
	install_requires = open("requirements.txt", "r").read().splitlines()
)
