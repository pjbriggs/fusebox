#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'fusebox',
    version = '0.0.1',
    py_modules = ['fusebox','boxfs'],
    install_requires = ['fusepy >= 2.0.2'],
    scripts = ['fusebox.py','manage_conf.py'],
    url = 'https://github.com/pjbriggs/fusebox',
    author = "Peter Briggs",
    author_email = 'peter.briggs@manchester.ac.uk',
    description = "Read-only virtual file systems implemented using FUSE",
    license = 'Artistic License 2.0'
)

