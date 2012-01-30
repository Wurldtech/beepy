# Fix paths until BEEPy is actually installed in /usr/lib/python...
import sys
sys.path.append('..')

# The rest of the imports
import commands
import signal
import xmlrpcprofile
from beepy.profiles import profile
from beepy.transports.tcp import BeepListenerFactory
from twisted.internet import reactor
from twisted.internet import protocol

def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def execute(cmd, args):
    return commands.getstatusoutput(" ".join([cmd] + args))

cmds = {
    # Format = { 'name': (function, run in thread) }
    'add': (add, False),
    'multiply': (multiply, False),
    'execute': (execute, True)
}

def int_handler(signum, frame):
    def real_handler():
        print "User interruption. Terminating"
        reactor.stop()
    reactor.callFromThread(real_handler)
    
signal.signal(signal.SIGINT, int_handler)

factory = BeepListenerFactory()
factory.addProfile(xmlrpcprofile.uri,
    profile.ProfileFactory(xmlrpcprofile.XmlRpcServer, cmds))

# Set up main loop to listen for connections
reactor.listenTCP(7331, factory)

# Main loop
reactor.run()
print "Done!"
