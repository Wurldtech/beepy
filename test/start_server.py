# $Id: start_server.py,v 1.5 2003/01/07 07:40:00 jpwarren Exp $
# $Revision: 1.5 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (C) 2002 Justin Warren <daedalus@eigenmagic.com>
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

import unittest
import sys
import time

try:
	from beepy.core import constants
	from beepy.core import logging
	from beepy.transports import sleepytcpsession as tcpsession
	from beepy.profiles import profile
except ImportError:
	sys.path.append('../')
	from beepy.core import constants
	from beepy.core import logging
	from beepy.transports import sleepytcpsession as tcpsession
	from beepy.profiles import profile

if __name__ == '__main__':

	log = logging.Log()

	# create the server
	pdict = profile.ProfileDict()
	pdict['http://www.eigenmagic.com/beep/ECHO'] = 'echoprofile'
	listener = tcpsession.TCPSessionListener(log, pdict, 'localhost', 1976)

	def quit():
		listener.close()
		while listener.isActive():
			time.sleep(0.1)

	sys.exitfunc = quit

	# run forever
	while(1):
		time.sleep(30)
else:
	print "This isn't a module you should import, dude."


