# $Id: test_saslanonymousprofile.py,v 1.7 2003/12/08 03:25:30 jpwarren Exp $
# $Revision: 1.7 $
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
import threading
import logging

sys.path.append('../')
from beepy.core import constants
from beepy.profiles import profile
from beepy.profiles import saslanonymousprofile
from beepy.profiles import echoprofile

import dummyclient

log = logging.getLogger('SASLAnonymousTest')

class SASLAnonymousProfileTest(unittest.TestCase):

    def test_SASLClient(self):
        """Test SASL Anonymous with Initiator"""
        # Create a server
        


        # Connect a client
        client = clientmgr.connectInitiator('localhost', 1976)
        clientid = client.ID
        while not client.isActive():
            time.sleep(0.25)

        self.clientlog.logmsg(logging.LOG_DEBUG, "Client connected.")

        # Start a channel using SASL/ANONYMOUS authentication
        profileList = [[saslanonymousprofile.uri,None,None]]
        event = threading.Event()
        channelnum = client.startChannel(profileList, event)
        event.wait(30)

        channel = client.getActiveChannel(channelnum)

        if not channel:
            if client.isChannelError(channelnum):
                error = client.getChannelError(channelnum)

        else:
            # Send our authentication information
            msgno = channel.profile.sendAuth('justin')
            while client.isAlive():
                time.sleep(0.25)

            # old client will have exited, so get the new client
            # for the same connection, as it has the same id
            self.clientlog.logmsg(logging.LOG_DEBUG, "Getting new client...")
            client = clientmgr.getSessionById(clientid)
            self.clientlog.logmsg(logging.LOG_DEBUG, "New client: %s" % client)

            while not client.isActive():
                time.sleep(0.25)
            self.clientlog.logmsg(logging.LOG_DEBUG, "Got new client...")

            # Create a channel on the new, authenticated, session
            # using the echo profile
            profileList = [[echoprofile.uri,None,None]]
            event = threading.Event()
            channelnum = client.startChannel(profileList, event)
            event.wait(30)
            channel = client.getActiveChannel(channelnum)

            if not channel:
                if client.isChannelError(channelnum):
                    error = client.getChannelError(channelnum)

            else:

                self.clientlog.logmsg(logging.LOG_DEBUG, "Got active channel...")

                # send a message
                msgno = channel.sendMessage('Hello!')
                self.clientlog.logmsg(logging.LOG_DEBUG, "Sent Hello (msgno: %d)" % msgno)
    
                while channel.isMessageOutstanding():
                    time.sleep(0.25)
    
        client.stop()
        while not client.isExited():
            time.sleep(0.25)
        self.clientlog.logmsg(logging.LOG_DEBUG, "closed client...")

        clientmgr.close()
        while not clientmgr.isExited():
            time.sleep(0.25)

        sess.close()
        while not sess.isExited():
            time.sleep(0.25)

        self.clientlog.logmsg(logging.LOG_DEBUG, "Test complete.")


if __name__ == '__main__':

    unittest.main()

