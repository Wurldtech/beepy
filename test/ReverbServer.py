# $Id: ReverbServer.py,v 1.1 2003/01/03 02:39:11 jpwarren Exp $
# $Revision: 1.1 $
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
# This file demonstrates the use of BEEPy to create a simple server.
# This server supports a single profile (in addition to the BEEP 
# Management profile): the Reverb profile. The Reverb profile responds to
# a MSG with the following format:
#
# <repeat_number> <delay> <content>
#

import sys
try:
	from beepy.core.logging import *
	from beepy.transports import tcpsession
	from beepy.profiles import profile
	from beepy.profiles import reverbprofile

except ImportError:
	sys.path.append('../')
	from beepy.core.logging import *
	from beepy.transports import tcpsession
	from beepy.profiles import profile
	from beepy.profiles import reverbprofile

if __name__ == '__main__':
	log = Log()

	profileDict = profile.ProfileDict()
	profileDict[reverbprofile.uri] = reverbprofile
	server = tcpsession.TCPSessionListener(log, profileDict, 'localhost', 1976)

	def cleanup():
		server.close()
		while server.isActive():
			pass

	sys.exitfunc = cleanup

	while(1):
		pass

else:
	print "You're not supposed to load this as a module."
	sys.exit()
