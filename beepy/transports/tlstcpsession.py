# $Id: tlstcpsession.py,v 1.5 2003/01/06 07:19:07 jpwarren Exp $
# $Revision: 1.5 $
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

from beepy.core import constants
from beepy.core import logging
from beepy.core import frame

from beepy.core import session
from beepy.core import tlssession

import tcpsession

import POW

import sys
import re
import errno
import exceptions
import socket, select
import string
import threading
import SocketServer
import traceback

class TLSTCPCommsMixin(tcpsession.TCPCommsMixin):
	"""This class overloads the methods provided by TCPCommsMixin to
	   provide encryption.
	"""
	def __init__(self):
		self.framebuffer = ''
		self.newframe = None
		self.windowsize = {}			# dictionary for each channel's window size
		self.frameHeaderPattern = re.compile(".*\r\n")
		self.dataFrameTrailer = re.compile(frame.DataFrame.TRAILER)

		SEQFrameRE = frame.SEQFrame.type
		SEQFrameRE += ".*"
		SEQFrameRE += frame.SEQFrame.TRAILER
		self.SEQFramePattern = re.compile(SEQFrameRE)

	# Overload createChannel from Session
	def createChannel(self, channelnum, profile):
		"""This overloads createChannel() from class Session to
		   add window sizing via SEQ capabilities to the TCP transport
		   layer mapping, as per RFC 3081
		"""
		self.log.logmsg(logging.LOG_DEBUG, "Creating TLS Channel via Mixin")
		session.Session.createChannel(self, channelnum, profile)
		self.windowsize[channelnum] = 4096

	def deleteChannel(self, channelnum):
		"""This overloads deleteChannel() from class Session to
		   blank out the window size dictionary for the closed
		   channel. Memory management, basically.
		"""
		session.Session.deleteChannel(self, channelnum)
		self.log.logmsg(logging.LOG_DEBUG, "%s windowsize: %s" % (self, self.windowsize))
		del self.windowsize[channelnum]

	def getInputFrame(self):
		"""getInputFrame reads a frame off the wire and places it
		in the Session inbound Queue.
		"""
		try:
			# use select to poll for pending data inbound
			inbit, outbit, oobit = select.select([self.connection], [], [], 0)
			if inbit:
#				self.log.logmsg(logging.LOG_DEBUG, "socket: %s" % self.connection)
				data = self.sl.read(constants.MAX_INBUF)
				if data:
					self.framebuffer += data
#					self.log.logmsg(logging.LOG_DEBUG, "gotdata: %s" % data)
					# Check for oversized frames. If framebuffer goes over
					# constants.MAX_FRAME_SIZE + constants.MAX_INBUF then
					# the frame is too large.
					if len(self.framebuffer) > (constants.MAX_FRAME_SIZE + constants.MAX_INBUF):
						raise session.TerminateException("Frame too large")
				else:
					raise session.TerminateException("Connection closed by remote host")

			# If the current new frame is complete, we search for
			# the header and create a new frame.
			if not self.newframe:
				# Ok, what we do is to first find the frame header
				match = re.search(self.frameHeaderPattern, self.framebuffer)
				if match:
					headerdata = self.framebuffer[:match.end()]
					self.framebuffer = self.framebuffer[match.end():]

					# If this is a SEQ frame, create it and process it
					if re.search(self.SEQFramePattern, headerdata):
						seqframe = frame.SEQFrame(self.log, databuffer=headerdata)
						self.processSEQFrame(seqframe)
					else:
						# start a new dataframe
						self.newframe = frame.DataFrame(self.log, databuffer=headerdata)

			# Populate our frame with payload data
			if self.newframe:
				# we scan the framebuffer for the frame trailer
				match = re.search(self.dataFrameTrailer, self.framebuffer)
				# If we find it, we should have a complete frame
				if match:
					# slice out this frame's data
					framedata = self.framebuffer[:match.start()]
					self.framebuffer = self.framebuffer[match.end():]
					# I append the data to the current frame payload
					# after checking that it isn't too long.
					if len(self.newframe.payload) + len(framedata) > self.newframe.size:
						self.log.logmsg(logging.LOG_DEBUG, "size: %s, expected: %s" % ( len(self.newframe.payload) + len(framedata), self.newframe.size ) )
						self.log.logmsg(logging.LOG_DEBUG, "payload: %s, buffer: %s" % ( self.newframe.payload, framedata ) ) 
						raise session.TerminateException("Payload larger than expected size")
					else:
						self.newframe.payload += framedata
						# The frame is now complete
						self.pushFrame(self.newframe)
						self.newframe = None
	#					self.log.logmsg(logging.LOG_DEBUG, "%s: pushedFrame: %s" % (self, newframe) )

				else:
					# I append the data to the current frame payload
					# after checking that it isn't too long.
					if len(self.newframe.payload) + len(self.framebuffer) > self.newframe.size:
						self.log.logmsg(logging.LOG_DEBUG, "size: %s, expected: %s" % ( len(self.newframe.payload) + len(self.framebuffer), self.newframe.size ) )
						self.log.logmsg(logging.LOG_DEBUG, "payload: %s, buffer: %s" % ( self.newframe.payload, self.framebuffer ) ) 
						raise session.TerminateException("Payload larger than expected size")
					else:
						self.newframe.payload += self.framebuffer
						self.framebuffer = ''

		except socket.error, e:
			if e[0] == errno.EWOULDBLOCK:
				pass

			elif e[0] == errno.ECONNRESET:
				raise session.TerminateException("Connection closed by remote host")

			else:
				self.log.logmsg(logging.LOG_DEBUG, "socket.error: %s" % e)
				raise session.TerminateException("%s" % e)

		except frame.DataFrameException, e:
			raise session.TerminateException("%s" % e)

		# Drop packets if queue is full, log a warning.
		except session.SessionInboundQueueFull:
			self.log.logmsg(logging.LOG_WARN, "Session inbound queue full from %s" % self.client_address)
			pass

		except session.TerminateException:
			raise

		except Exception, e:
			raise session.TerminateException("Unhandled Exception in getInputFrame(): %s: %s" % (e.__class__, e))


	def sendPendingFrame(self):
		try:
			data = self.pullFrame()
			if data:
				self.sl.write(data)
		except Exception, e:
			self.log.logmsg(logging.LOG_WARN, "sendPendingFrame(): %s: %s" % ( e.__class__, e) )
			traceback.print_exc(file=self.log.log)
			pass

class TLSTCPListenerSession(TLSTCPCommsMixin, tcpsession.TCPListenerSession, tlssession.TLSListenerSession):

	def __init__(self, conn, client_address, sessmgr, oldsession, keyFile, certFile, passphrase):
		threading.Thread.__init__(self)
		self.shutdown = threading.Event()

		TLSTCPCommsMixin.__init__(self)

		self.request = conn
		self.connection = conn
		self.client_address = client_address
		self.sessmgr = sessmgr
		self.oldsession = oldsession

		tlssession.TLSListenerSession.__init__(self, self.sessmgr.log, self.sessmgr.profileDict)

		kfd = open( keyFile, 'r' )
		cfd = open( certFile, 'r' )
		md5 = POW.Digest( POW.MD5_DIGEST )
		md5.update( passphrase )
		password = md5.digest()
		self.key = POW.pemRead( POW.RSA_PRIVATE_KEY, kfd.read(), password )
		self.cert = POW.pemRead( POW.X509_CERTIFICATE, cfd.read() )
		kfd.close()
		cfd.close()

		self.sl = POW.Ssl( POW.TLSV1_SERVER_METHOD )
		self.sl.useCertificate( self.cert )
		#self.sl.useKey( self.key )

#		self.sl.setVerifyMode( POW.SSL_VERIFY_PEER )

#		if self.sl.checkKey():
#			self.log.logmsg(logging.LOG_INFO, "TLS Key checks out ok")
#		else:
#			self.log.logmsg(logging.LOG_INFO, "TLS Key doesn't check out")

		sessmgr.replaceSession(oldsession.ID, self)

		self.inbound = self.oldsession.inbound
		self.newframe = self.oldsession.newframe
		self.framebuffer = self.oldsession.framebuffer

		self.log.logmsg(logging.LOG_INFO, "%s: initialized" % self)
		self.start()

	def _stateINIT(self):

		self.log.logmsg(logging.LOG_DEBUG, "Waiting on old Session thread to exit: %s" % self.oldsession )
		self.oldsession.join()
		self.log.logmsg(logging.LOG_DEBUG, "Tuning reset: reconnected to %s[%s]." % self.client_address )

		# configure TLS
		try:
			self.sl.setFd( self.connection.fileno() )
			self.connection.setblocking(1)
			self.sl.accept()
			self.connection.setblocking(0)

		except Exception, e:
			self.log.logmsg(logging.LOG_DEBUG, "Exception setting up TLS connection: %s: %s" % (e.__class__, e) )
			self.transition('error')

		# Connect established
		peerCert = self.sl.peerCertificate()
		if peerCert:
			self.log.logmsg(logging.LOG_DEBUG, "==== TLS Cert Parameters ===")
			self.log.logmsg(logging.LOG_DEBUG, "%s" % peerCert.pprint() )

		tcpsession.TCPListenerSession._stateINIT(self)

		self.transition('ok')

class TLSTCPInitiatorSession(TLSTCPCommsMixin, tcpsession.TCPInitiatorSession, tlssession.TLSInitiatorSession):

	def __init__(self, conn, server_address, sessmgr, oldsession, keyFile, certFile, passphrase ):
		threading.Thread.__init__(self)
		self.shutdown = threading.Event()

		TLSTCPCommsMixin.__init__(self)

		self.request = conn
		self.connection = conn
		self.server_address = server_address
		self.oldsession = oldsession

		# Read in the TLS key
		md5 = POW.Digest( POW.MD5_DIGEST )
		md5.update( passphrase )
		password = md5.digest()
		kfd = open( keyFile, 'r' )
		cfd = open( certFile, 'r' )
		self.key = POW.pemRead( POW.RSA_PRIVATE_KEY, kfd.read(), password )
		self.cert = POW.pemRead( POW.X509_CERTIFICATE, cfd.read() )
		kfd.close()
		cfd.close()

		self.sl = POW.Ssl( POW.TLSV1_CLIENT_METHOD )
		self.sl.useCertificate( self.cert )
		self.sl.useKey( self.key )

		tlssession.TLSInitiatorSession.__init__(self, sessmgr.log, sessmgr.profileDict)
		sessmgr.replaceSession(oldsession.ID, self)

		self.inbound = self.oldsession.inbound
		self.newframe = self.oldsession.newframe
		self.framebuffer = self.oldsession.framebuffer
		self.log.logmsg(logging.LOG_INFO, "%s: initialized" % self)
		self.start()

	def _stateINIT(self):
		self.log.logmsg(logging.LOG_DEBUG, "Waiting on old Session thread to exit: %s" % self.oldsession )
		self.oldsession.join()

		self.log.logmsg(logging.LOG_DEBUG, "Tuning reset: reconnected to %s[%s]." % self.server_address )

		try:
			# configure TLS
			self.sl.setFd( self.connection.fileno() )
			#
			self.connection.setblocking(1)
			self.sl.connect()
			self.connection.setblocking(0)

			# Connect established
			peerCert = self.sl.peerCertificate()
			self.log.logmsg(logging.LOG_DEBUG, "==== TLS Cert Parameters ===")
			self.log.logmsg(logging.LOG_DEBUG, "%s" % peerCert.pprint() )

			self.createChannelZero()
			self.queueOutboundFrames()
			self.sendPendingFrame()
			while not self.channels[0].profile.receivedGreeting:
				self.getInputFrame()
				self.processFrames()
			self.transition('ok')

		except Exception, e:
			self.log.logmsg(logging.LOG_ERR, "Connection to remote host failed: %s" % e)
			self.transition('error')

	def _stateTERMINATE(self):
		self.connection.close()
		self.transition('ok')
