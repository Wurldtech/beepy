# $Id: tls.py,v 1.2 2004/06/27 07:38:32 jpwarren Exp $
# $Revision: 1.2 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (C) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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

import logging
from beepy.core import debug
log = logging.getLogger('beepy')

##
## TLS related code
##
try:
    from twisted.internet import ssl
    from OpenSSL import SSL
    
except ImportError:
    log.debug('ssl not supported without twisted')
    raise

#from POW import Ssl

from tcp import BeepProtocol, BeepClientFactory, BeepServerFactory
from beepy.core.tlssession import TLSListener, TLSInitiator

## This code adds the TLS functionality to the base protocol
## classes

class TLSProtocol(BeepProtocol):
    """ The TLS Protocol implements the TLS transport layer
    """
    TLS = 0
    
    def startTLS(self):
        """ start the TLS layer
        """
        if self.factory.privateKeyFileName:
            keyfile = self.factory.privateKeyFileName
        else:
            log.info('Private key filename not specified. Requesting it...')
            keyfile = self.factory.getPrivateKeyFilename()

        if self.factory.certificateFileName:
            certfile = self.factory.certificateFileName
        else:
            log.info('Certificate filename not specified. Requesting it...')            
            certfile = self.factory.getCertificateFilename()
            
        log.debug('Starting server side TLS...')

        self.transport.startTLS(ServerTLSContext(keyfile, certfile))

        self.TLS = 1
        log.debug('Started server side TLS.')

class TLSServerProtocol(TLSProtocol, TLSListener):
    """ A TLS Server Protocol
    """

class TLSClientProtocol(TLSProtocol, TLSInitiator):
    """ A TLS Client Protocol
    """

    def startTLS(self):
        log.debug('Starting client side TLS...')

        self.transport.startTLS(ClientTLSContext())
        self.TLS = 1
        log.debug('Started client side TLS.')
        
class TLSServerFactory(BeepServerFactory):
    protocol = TLSServerProtocol

    privateKeyFileName = None
    certificateFileName = None

    def getPrivateKeyFilename(self):
        """ This method will only get called if the keyfile
        is not set when it is required. This allows the option
        of runtime definition of the keyfile name.
        Override this method in your servers if you don't want
        to set the filename at compile time.
        """
        raise NotImplementedError('Either set a key filename first, or implement this method.')

    def getCertificateFilename(self):
        """ This method will get called if the certificate
        filename is not set when it is required.
        Override this method in your servers if you don't want
        to set the filename at compile time.
        """
        raise NotImplementedError('Either set a certificate filename first, or implement this method.')

class TLSClientFactory(BeepClientFactory):
    protocol = TLSClientProtocol

class ClientTLSContext(ssl.ContextFactory):
    isClient = 1

    def getContext(self):
        return SSL.Context(ssl.SSL.TLSv1_METHOD)

class ServerTLSContext(ssl.DefaultOpenSSLContextFactory):
    """ A default TLS context factory to use for TLS
    connections
    """
    isClient = 0
    def __init__(self, privateKeyFileName, certificateFileName, sslmethod=SSL.TLSv1_METHOD):
        ssl.DefaultOpenSSLContextFactory.__init__(self, privateKeyFileName, certificateFileName, sslmethod)
           
