# $Id: tlstcpsession.py,v 1.9 2003/01/30 09:24:30 jpwarren Exp $
# $Revision: 1.9 $
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
# 
# This class implements a datastream that works over TCP but adds a layer
# of encryption. The encryption parameters are negotiated by the corresponding
# TLS profile in beep/profiles

import re
import string
import socket, select
import threading
import exceptions
import time
import traceback

from beepy.core import constants
from beepy.core import logging
from beepy.core import session
from beepy.core import frame
from beepy.core import util
import tcpsession

import POW

class TLSTCPDataEnqueuer(tcpsession.TCPDataEnqueuer):
    """ A TLSTCPDataEnqueuer is identical to a TCPDataEnqueuer
        except that it uses a TLS socket object instead of a 
        standard socket.
    """
    def __init__(self, log, sock, tls_sock, session, dataq, errEvent, read_timeout=1, name=None):
        self.tls_sock = tls_sock
        tcpsession.TCPDataEnqueuer.__init__(self, log, sock, session, dataq, errEvent, read_timeout, name)

    def getDataFromSocket(self):
        """ A TLS session uses a TLS session object to get
            data from instead of the underlying socket.
        """
        self.sock_mutex.acquire()
        if self.connected:
            try:
                data = self.tls_sock.read(constants.MAX_INBUF)
                self.sock_mutex.release()
                return data

            except POW.SSLError, e:
                self.sock_mutex.release()
                self.log.logmsg(logging.LOG_ERR, "SSL Error during read: %s: %s" % (e) )
#                self.log.traceback()

#    def stop(self):
    def cleanup(self):
        try:
            self.sock_mutex.acquire()
            if self.connected:

                # The POW implementation requires shutdown() to be called
                # twice for some reason relating to the underlying SSL
                # implementation. Two shutdown() calls with no exception
                # mean the connection was shutdown successfully.

                while 1:
                    try:
                        self.tls_sock.shutdown()
                        break
                    except:
                        time.sleep(0.25)

                self.sock.shutdown(2)
                self.sock.close()
                self.connected = 0
            self.sock_mutex.release()

            util.DataEnqueuer.stop(self)
            self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)

        except socket.error, e:
            self.sock_mutex.release()
            if e[0] == errno.ENOTCONN:
                pass

        except Exception, e:
            self.sock_mutex.release()
            self.log.logmsg(logging.LOG_ERR, "Unhandled exception while stopping. Generating traceback...")
            self.log.traceback()


class TLSTCPDataDequeuer(tcpsession.TCPDataDequeuer):
    """ A TLSTCPDataDequeuer is identical to a TCPDataDequeuer
        except that it uses a TLS socket object instead of a 
        standard socket.
    """
    def __init__(self, log, sock, tls_sock, session, dataq, errEvent, name=None):
        self.tls_sock = tls_sock
        tcpsession.TCPDataDequeuer.__init__(self, log, sock, session, dataq, errEvent, name)

    def sendDataToSocket(self, data):
        """ A TLS session uses a TLS session object to send
            data instead of the underlying socket.
        """
        try:
            return self.tls_sock.write(data)
        except POW.SSLError, e:
            self.log.logmsg(logging.LOG_ERR, "SSL Error during write: %s: %s" % (e) )
#            self.log.traceback()
#            self.transition('error')

class TLSTCPListener(tcpsession.TCPListener):

    def __init__(self, conn, client_address, sessmgr, oldsession, certificate, key, read_timeout=1):

        tcpsession.TCPListener.__init__(self, conn, client_address, sessmgr, read_timeout)

        self.cert = certificate
        self.key = key
        self.store = POW.X509Store()
        # We only trust clients whose certificates are signed by us.
        self.store.addTrust( self.cert )

        self.sl = POW.Ssl( POW.TLSV1_SERVER_METHOD )
        self.sl.useCertificate( self.cert )
        self.sl.useKey( self.key )
        self.sl.setVerifyMode( POW.SSL_VERIFY_PEER )

        if self.sl.checkKey():
            self.log.logmsg(logging.LOG_INFO, "TLS Key checks out ok")
        else:
            self.log.logmsg(logging.LOG_INFO, "TLS Key doesn't check out")

        sessmgr.replaceSession(oldsession.ID, self)
        self.oldsession = oldsession

        self.log.logmsg(logging.LOG_INFO, "%s: initialized" % self)

    def _stateINIT(self):
        # This join goes here because we won't be in a new thread until
        # we get here. __init__ above is called from what is by now oldsession
        self.log.logmsg(logging.LOG_DEBUG, "Waiting on old Session thread to exit: %s" % self.oldsession )
        self.oldsession.join()
        self.log.logmsg(logging.LOG_DEBUG, "Tuning reset: reconnected to %s[%s]." % self.client_address )

        # configure TLS
        try:
            self.sl.setFd( self.sock.fileno() )
            self.sock.setblocking(1)
            self.sl.accept()
            self.sock.setblocking(0)
            self.log.logmsg(logging.LOG_DEBUG, "TLS accept() successful.")

            # Connect established
            peerCert = self.sl.peerCertificate()
#            if peerCert:
#                self.log.logmsg(logging.LOG_DEBUG, "==== TLS Cert Parameters ===")
#                self.log.logmsg(logging.LOG_DEBUG, "%s" % peerCert.pprint() )

            # IO threads use the TLS socket, not the actual socket
            self.startIOThreads(self.sock, self.sl)
            self.createChannelZero()

            self.transition('ok')
            return

        except POW.SSLError, e:
            self.log.logmsg(logging.LOG_ERR, "SSL Error during TLS setup: %s: %s" % (e.__class__, e) )
            self.log.traceback()
            self.transition('error')

        except Exception, e:
            self.log.logmsg(logging.LOG_DEBUG, "Exception setting up TLS connection: %s: %s" % (e.__class__, e) )
            self.log.traceback()
            self.transition('error')

    def startIOThreads(self, sock, tls_sock):
        self.inputAvailable = threading.Event()
        self.inputDataQueue = TLSTCPDataEnqueuer(self.log, sock, tls_sock, self, self.inbound, self.ismonitoredEvent, self.read_timeout)
        self.outputAvailable = threading.Event()
        self.outputDataQueue = TLSTCPDataDequeuer(self.log, sock, tls_sock, self, self.outbound, self.ismonitoredEvent )
        self.sessmgr.monitor.startMonitoring(self.inputDataQueue)
        self.sessmgr.monitor.startMonitoring(self.outputDataQueue)
        self.inputDataQueue.start()
        self.log.logmsg(logging.LOG_DEBUG, "Started inputDataQueue: %s" % self.inputDataQueue)
        self.outputDataQueue.start()
        self.log.logmsg(logging.LOG_DEBUG, "Started outputDataQueue: %s" % self.outputDataQueue)

class TLSTCPInitiator(tcpsession.TCPInitiator):

    def __init__(self, sock, server_address, sessmgr, oldsession, certificate, key, read_timeout=1 ):

        self.sock = sock

        tcpsession.TCPInitiator.__init__(self, sessmgr.log, sessmgr.profileDict, server_address, sessmgr, read_timeout)

        self.cert = certificate
        self.key = key

        self.sl = POW.Ssl( POW.TLSV1_CLIENT_METHOD )
        self.sl.useCertificate( self.cert )
        self.sl.useKey( self.key )

        sessmgr.replaceSession(oldsession.ID, self)
        self.oldsession = oldsession

        self.log.logmsg(logging.LOG_INFO, "%s: initialized" % self)

    def _stateINIT(self):
        self.log.logmsg(logging.LOG_DEBUG, "Waiting on old Session thread to exit: %s" % self.oldsession )
        self.oldsession.join()
        self.log.logmsg(logging.LOG_DEBUG, "Tuning reset: reconnected to %s[%s]." % self.server_address )

        try:
            # configure TLS
            self.sl.setFd( self.sock.fileno() )
            #
            self.sock.setblocking(1)
            self.sl.connect()
            self.sock.setblocking(0)
            self.log.logmsg(logging.LOG_DEBUG, "TLS connect() successful.")

            # Connect established
            peerCert = self.sl.peerCertificate()
#            self.log.logmsg(logging.LOG_DEBUG, "==== TLS Cert Parameters ===")
#            self.log.logmsg(logging.LOG_DEBUG, "%s" % peerCert.pprint() )

            self.startIOThreads(self.sock, self.sl)
            self.createChannelZero()

            while not self.channels[0].profile.receivedGreeting:
                if self._stop.isSet():
                    self.transition('close')
                    return
                self.processFrames()
            self.transition('ok')

        except POW.SSLError, e:
            self.log.logmsg(logging.LOG_ERR, "SSL Error during TLS setup: %s: %s" % (e.__class__, e) )
            self.log.traceback()
            self.transition('error')

        except Exception, e:
            self.log.logmsg(logging.LOG_ERR, "Connection to remote host failed: %s" % e)
            self.transition('error')

    def startIOThreads(self, sock, tls_sock):
        self.inputAvailable = threading.Event()
        self.inputDataQueue = TLSTCPDataEnqueuer(self.log, sock, tls_sock, self, self.inbound, self.ismonitoredEvent, self.read_timeout)
        self.outputAvailable = threading.Event()
        self.outputDataQueue = TLSTCPDataDequeuer(self.log, sock, tls_sock, self, self.outbound, self.ismonitoredEvent )
        self.sessmgr.monitor.startMonitoring(self.inputDataQueue)
        self.sessmgr.monitor.startMonitoring(self.outputDataQueue)
        self.inputDataQueue.start()
        self.log.logmsg(logging.LOG_DEBUG, "Started inputDataQueue: %s" % self.inputDataQueue)
        self.outputDataQueue.start()
        self.log.logmsg(logging.LOG_DEBUG, "Started outputDataQueue: %s" % self.outputDataQueue)
