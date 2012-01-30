#!/usr/bin/twistd -ny
# Fix paths until BEEPy is actually installed in /usr/lib/python...
import sys
sys.path.insert(0, '..')

import signal
from beepy.profiles import profile
from twisted.internet import threads
from twisted.application import service

from beepy.transports.tcp import BeepListenerFactory
from twisted.internet import reactor
from twisted.internet import protocol

class Profile(profile.Profile):
    uri = "http://wurldtech.com/protoget"

    def __init__(self):
        profile.Profile.__init__(self)
        self.window = 10
        self.offset = 0
        self.done = False

    def generate(self):
        print "profile generate length %d window %d done? %s" % (self.length, self.window, self.done)
        if self.length == 0:
            if not self.done:
                self.channel.sendMessage("", {"type": "done"})
                self.done = True
                #self.close()
            return

        while self.length > 0 and self.window > 0:
            n = self.length
            if n > 4097:
                n = 4097

            self.channel.sendMessage(("x" * n), {"type": "data", "offset": str(self.offset)})

            self.window -= 1
            self.length -= n
            self.offset += n


    def channelStarted(self, channel, uri, cdata):
        print "profile init: cdata=<"+str(cdata)+">"
        print "profile started, channel="+str(channel.channelnum)
        self.channel = channel
        self.length = int(cdata)
        self.generate()

    def processMessage(self, msg):
        print "profile recv "+repr(msg)
        profile.Profile.processMessage(self, msg)
    
    def processRPY(self, msg):
        self.window += 1
        self.generate()
        
    def processERR(self, msg):
        self.window += 1
        self.close()


#class Protocol(BeepServerProtocol):
#    def channelStarted(self, channelnum, uri):
#        # This is the real start. It occurs after success RPY is received on
#        # client side, and after success RPY is sent on server side.
#        channel = self.getChannel(channelnum)
#        channel.profile.channelStarted()

#class Factory(BeepServerFactory):
#    protocol = Protocol

factory = BeepListenerFactory()
factory.addProfile(Profile.uri, profile.ProfileFactory(Profile))
reactor.listenTCP(7331, factory)

def int_handler(signum, frame):
    def real_handler():
        print "User interruption. Terminating"
        reactor.stop()
    reactor.callFromThread(real_handler)
    
signal.signal(signal.SIGINT, int_handler)

reactor.run()

print "Done!"

