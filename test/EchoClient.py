# $Id: EchoClient.py,v 1.2 2003/01/01 23:37:39 jpwarren Exp $
# $Revision: 1.2 $
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
# This is the client side of the example EchoServer code used in the HOWTO.

import sys
import time
try:
	from beep.core.logging import *
	import beep.profiles.profile
	import beep.transports.tcpsession
	import beep.profiles.echoprofile
except ImportError:
	sys.path.append('../')
	from beep.core.logging import *
	import beep.profiles.profile
	import beep.transports.tcpsession
	import beep.profiles.echoprofile

def quit():
	client.close()
	while client.isActive():
		pass

sys.exitfunc = quit

# Setup basic configuration doodads
log = Log()
profileDict = beep.profiles.profile.ProfileDict()

# We only support ECHO profile
profileDict['http://www.eigenmagic.com/beep/ECHO'] = beep.profiles.echoprofile

# And we will only request ECHO profile with default params
profileList = [['http://www.eigenmagic.com/beep/ECHO', None, None]]

# Create the client and wait for it to become active
log.logmsg(LOG_INFO, "Connecting to server...")
clientmgr = beep.transports.tcpsession.TCPInitiatorSessionManager(log, profileDict)
while not clientmgr.isActive():
	pass

client = clientmgr.connectInitiator('localhost', 1976)

while not client.isActive():
	if client.isExited():
		log.logmsg(LOG_ERR, "Client connection failed.")
		sys.exit()
	pass
clientid = client.ID
# Create a channel using ECHO and wait for it to become active
channelnum = client.startChannel(profileList)
while not client.isChannelActive(channelnum):
	pass

# Channel is now active and working, so let's try sending
# some messages over it.
channel = client.getActiveChannel(channelnum)
if not channel:
	print "Erk! Channel isn't active!"
	exit

msgno = channel.sendMessage('Hello!\n')
# Any replies should be handled by the profile
while channel.isMessageOutstanding(msgno):
	pass

#client.closeChannel(channelnum)
#while client.isChannelActive(channelnum):
#	pass

client.close()
while client.isAlive():
	pass
