# Fix paths until BEEPy is actually installed in /usr/lib/python...
import sys
sys.path.append('..')

# The rest of the imports
import xmlrpcprofile
from beepy.transports.tcp import BeepSession, BeepInitiatorFactory
from twisted.internet import reactor


class MyClient(xmlrpcprofile.XmlRpcClient):
    
    def __init__(self):
        self.outstanding = 0
    
    def channelStarted(self, channel, uri, cdata):
        self.execRpcCall('add', [1,2])
        self.execRpcCall('multiply', [1,2])
        self.execRpcCall('execute', ['ls', ['-la']])
        self.outstanding = 3
    
    def handleCompleted(self, results):
        print "Result =", results[0]
        self.outstanding -= 1
        if self.outstanding == 0:
            self.close()
            
    def handleError(self, code, message):
        print "Error: %d / %s" % (code, message)
        self.close()
        
    def channelClosed(self):
        self.channel.session.close()


class MySession(BeepSession):
    
    def sessionStarted(self):
        self.newChannel(xmlrpcprofile.uri, MyClient())
        #self.newChannel("asdf", MyClient())
    
    def sessionClosed(self):
        print "Everything is done"
        reactor.stop()
    
    def channelStartingError(self, chnum, code, desc):
        print "Could not create channel: '%d %s'" % (code, desc)
        self.close()


class MyFactory(BeepInitiatorFactory):
    
    protocol = MySession
    
    def clientConnectionLost(self, connection, reason):
        BeepInitiatorFactory.clientConnectionLost(self, connection, reason)
        reactor.stop()


# Set up main loop to listen for connections
reactor.connectTCP('localhost', 7331, MyFactory())

# Main loop
reactor.run()
print "Done!"
