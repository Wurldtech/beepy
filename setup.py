# $Id: setup.py,v 1.9 2007/09/03 03:20:03 jpwarren Exp $
# $Revision: 1.9 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>

from distutils.core import setup

setup(name='BEEPy',
	version='0.6.1',
	description='A Python BEEP Library',
	author='Justin Warren',
	author_email='daedalus@eigenmagic.com',
	license='MIT',
	url='http://beepy.sourceforge.net',
	packages=['beepy', 'beepy.core', 'beepy.transports', 'beepy.profiles'],
)
