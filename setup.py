# $Id: setup.py,v 1.6 2004/09/28 01:19:19 jpwarren Exp $
# $Revision: 1.6 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (c) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from distutils.core import setup

setup(name='BEEPy',
	version='0.5',
	description='A Python BEEP Library',
	author='Justin Warren',
	author_email='daedalus@eigenmagic.com',
	license='LGPL',
	url='http://beepy.sourceforge.net',
	packages=['beepy', 'beepy.core', 'beepy.transports', 'beepy.profiles'],
)
