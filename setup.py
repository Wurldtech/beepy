# $Id: setup.py,v 1.8 2007/07/28 01:45:22 jpwarren Exp $
# $Revision: 1.8 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>

from distutils.core import setup

setup(name='BEEPy',
	version='0.6',
	description='A Python BEEP Library',
	author='Justin Warren',
	author_email='daedalus@eigenmagic.com',
	license='MIT',
	url='http://beepy.sourceforge.net',
	packages=['beepy', 'beepy.core', 'beepy.transports', 'beepy.profiles'],
)
