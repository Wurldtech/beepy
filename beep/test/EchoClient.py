# $Id: EchoClient.py,v 1.1 2002/09/19 02:36:46 jpwarren Exp $
# $Revision: 1.1 $
#
# This is an attempt to build the server side of a client/server 
# MessageNet setup using BEEPy.

import sys
import time
sys.path.append('../../')

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

# We only support MSGNET
profileDict['http://www.eigenmagic.com/beep/ECHO'] = beep.profiles.echoprofile

# And we will only request MSGNET with default params
profileList = [['http://www.eigenmagic.com/beep/ECHO', None, None]]

# Create the client and wait for it to become active
log.logmsg(LOG_INFO, "Connecting to server...")
client = beep.transports.tcpsession.TCPInitiatorSession(log, profileDict, 'localhost', 1976)
while not client.isActive():
	if client.isExited():
		log.logmsg(LOG_ERR, "Client connection failed.")
		sys.exit()
	pass
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
time.sleep(1)

client.closeChannel(channelnum)
while client.isChannelActive(channelnum):
	pass
