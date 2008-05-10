# $Id: setup.py,v 1.10 2008/05/10 03:09:25 jpwarren Exp $
# $Revision: 1.10 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) Justin Warren <daedalus@eigenmagic.com>

from distutils.core import setup

setup(name='BEEPy',
	version='0.6.2',
	description='A Python BEEP Library',
	author='Justin Warren',
	author_email='daedalus@eigenmagic.com',
	license='MIT',
	url='http://beepy.sourceforge.net',
	packages=['beepy', 'beepy.core', 'beepy.transports', 'beepy.profiles'],
)
