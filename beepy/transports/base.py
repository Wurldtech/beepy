# $Id: base.py,v 1.9 2007/09/03 03:20:13 jpwarren Exp $
# $Revision: 1.9 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#
##
## Imports
##
#import logging
from beepy.core.debug import log
#log = logging.getLogger('beepy')

import traceback
import sys

import socket
import select

##
## Base classes to duplicate core needed twisted functionality
##
MAX_RECV = 8192

class TCPTransport:

    def __init__(self, sock):
        self.sock = sock

    def __del__(self):
        log.debug('deleting TCPTransport: %s' % self)
        self.sock.close()

    def write(self, data):
        self.sock.send(data)

    def close(self):
        self.sock.close()

    def loseConnection(self):
        self.sock.close()
        
    def connectionLost(self):
        self.sock.close()

class Reason:
    def __init__(self, msg):
        self.msg = msg

    def trap(self, type):
        if self.__class__ == type:
            pass
        else:
            return self

    def getErrorMessage(self):
        return self.msg

class ConnectionDone(Reason):
    """
    Used when connection terminates normally.
    """
        
class SelectReactor:
    """ A reactor manages the main looping part of a client or server
    """
    def __init__(self):
        self.insocks = {}
        self.outsocks = {}
        self.factoryList = []
        self.running = 0

        sys.exitfunc = self.crash
        
        pass

    def iterate(self):
        """ Run a single cycle of the main processing loop
        """
        ## process incoming events
        insocks, outsocks, e = select.select( self.insocks.keys(), self.outsocks.keys(), [], 0.1 )
        for sock in insocks:
            newsock, address = sock.accept()
            self.insocks[sock].handleConnect(newsock, self)
            self.factoryList.append(self.insocks[sock])

        for factory in self.factoryList:
            factory.iterate()

        pass

    def run(self):
        """ Run the main loop continuously
        """
        try:
            self.running = 1
            while(self.running):
                self.iterate()
                pass
            
        finally:
            self.crash()
        pass

    def stop(self):
        """ Interrupt the main loop and shut down
        """
        self.running = 0
        self.crash()
        pass

    def crash(self):
        """ Hard exit
        """
        log.debug('crashing out...')
        try:
            for factory in self.factoryList:
                log.debug('closing factory: %s' % factory)
                factory.crash()
                self.factoryList.remove(factory)
                pass
            
            for sock in self.insocks.keys():
                log.debug('closing insock: %s' % sock)
                sock.close()
                del self.insocks[sock]
                pass
            
            for sock in self.outsocks.keys():
                log.debug('closing outsock: %s' % sock)
                sock.close()
                del self.outsocks[sock]
                pass
        ## FIXME
        ## Need to remove this bare except at some point
        ## Probably after fixing up the session startup/shutdown code
        except:
            traceback.print_exc()

        log.debug('Crash finished.')
        log.debug('insocks: %s' % self.insocks)
        log.debug('outsocks: %s' % self.outsocks)
        log.debug('factories: %s' % self.factoryList)
        pass
    
    def listenTCP(self, port, factory, interface=''):
        """ Add a listening factory on a given port. If no specific
        interface is provided, listen on all interfaces.

        @type port: integer 
        @param port: The port number to listen on
        @type factory: a Factory class
        @param factory: the type of Factory to use for connections
                        received on the port
        @type interface: string
        @param interface: A specific interface to listen on

        """
        ## create a listening socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((interface, port))
        sock.listen(5)

        self.insocks[sock] = factory
        
        pass

    def connectTCP(self, host, port, factory):
        """ Initiate a connection to a remote host
        
        @type host: string
        @param host: remote host to connect to
        @type port: integer
        @param port: port number to connect to
        @type factory: Factory object
        @param factory: the Factory to use to manage the connection

        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        self.outsocks[sock] = factory

    def removeFactory(self, factory):
        self.factoryList.remove(factory)
    
    pass

reactor = SelectReactor()

class LineReceiver:
    """ A LineReceiver reads data one line at a time
    """
    databuf = ''
    delimiter = '\r\n'
    line_mode = 1
    factory = None
    transport = None

    def __del__(self):
        log.debug('Deleting LineReceiver...')
        del self.transport
    
    def setRawMode(self):
        """ Receive raw data
        """
        self.line_mode = 0
        pass

    def dataReceived(self, data):
        log.debug('data received: %s' % data)
        self.databuf += data
        log.debug('databuf is: %s' % self.databuf)

        ## We're a line receiver, so we need to check for newlines
        if self.line_mode:
            line, self.databuf = self.databuf.split(self.delimiter, 1)
            if line:
                self.lineReceived(line)
        else:
            self.rawDataReceived(data)

    def lineReceived(self, line):
        log.debug('received line: %s' % line)
        self.rawDataReceived(line)

    def rawDataReceived(line):
        log.debug('raw data received')

    def handleConnect(self, factory, sock):
        self.factory = factory
        self.transport = TCPTransport(sock)
        self.connectionMade()

    def connectionMade(self):
        pass

    def connectionLost(self):
        log.debug('Connection lost!')
        self.connected = 0
        self.transport.connectionLost()

#    def loseConnection(self):
#        self.transport.close()
#        self.connected = 0

class Factory:
    """ A factory starts Protocols when initiated
    """
    protocol = LineReceiver

    def __str__(self):
        return 'Factory.protocol: %s' % self.protocol
    
    def handleConnect(self, sock, reactor):
        """ A connect event occurred.
        """
        self.proto = self.protocol()
        self.proto.handleConnect(self, sock)
        log.debug('Connect event received')
        self.sock = sock
        self.reactor = reactor
        self.connected = 1
        pass

    def iterate(self):
        """ Check for inbound and outbound data
        """
        log.debug('iterating factory: %s' % self)
        if not self.connected:
            raise ValueError('Factory not connected!')
        
        i, o, e = select.select([self.sock], [self.sock], [], 0.1)
        for sock in i:
            data = sock.recv(MAX_RECV)
            if data:
                log.debug('Received data on factory.')
                self.proto.dataReceived(data)

            else:
                log.debug('proto is: %s' % self.proto)
                log.debug('  %s' % self.proto.connectionLost)                
                self.proto.connectionLost(ConnectionDone('Finished'))

    def isConnected(self):
        return self.connected

    def close(self):
        log.debug('closing factory...')
        self.sock.close()
        self.connected = 0
        self.reactor.removeFactory(self)

    def crash(self):
        """ Hard exit
        """
        self.sock.close()
        self.connected = 0
    pass

class ServerFactory(Factory):
    """ A ServerFactory starts protocols when a connection
    is received from a client.
    """
    pass

class ClientFactory(Factory):
    """ A ClientFactory initiates protocol connections to a
    remote server.
    """
    pass
