# $Id: EchoServer.py,v 1.3 2003/01/02 00:46:17 jpwarren Exp $
# $Revision: 1.3 $
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
# Management profile): the Echo profile. The Echo profile simply responds to
# any MSG frames it receives by echoing the contents of the frame back to
# the sender as a RPY to the MSG.

import sys
try:
	from beepy.core.logging import *
	import beepy.profiles.profile
	import beepy.transports.tcpsession
	import beepy.profiles.echoprofile
except ImportError:
	sys.path.append('../')
	from beepy.core.logging import *
	import beepy.profiles.profile
	import beepy.transports.tcpsession
	import beepy.profiles.echoprofile

if __name__ == '__main__':
	log = Log()

	profileDict = beepy.profiles.profile.ProfileDict()
	profileDict['http://www.eigenmagic.com/beep/ECHO'] = beepy.profiles.echoprofile
	server = beepy.transports.tcpsession.TCPSessionListener(log, profileDict, 'localhost', 1976)

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
