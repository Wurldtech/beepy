# $Id: tlstcpsession.py,v 1.1 2003/01/01 23:37:39 jpwarren Exp $
# $Revision: 1.1 $
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

import tcpsession

import sys
import re
import errno
import exceptions
import socket, select
import string
import threading
import SocketServer

class TLSTCPCommsMixin(TCPCommsMixin):
	"""This class overloads the methods provided by TCPCommsMixin to
	   provide encryption.
	"""
	def getInputFrame(self):
		"""getInputFrame reads a frame off the wire and places it
		in the Session inbound Queue.
		"""
		try:
			# use select to poll for pending data inbound
			inbit, outbit, oobit = select.select([self.connection], [], [], 0)
			if inbit:
#				self.log.logmsg(logging.LOG_DEBUG, "socket: %s" % self.connection)
				data = self.connection.recv(constants.MAX_INBUF)
				if data:

>>>
>>>					FIXME: Do decryption stuff here.
>>>

					self.framebuffer += data
					# Check for oversized frames. If framebuffer goes over
					# constants.MAX_FRAME_SIZE + constants.MAX_INBUF then
					# the frame is too large.
					if len(self.framebuffer) > (constants.MAX_FRAME_SIZE + constants.MAX_INBUF):
						raise TCPSessionException("Frame too large")

					# Detect a complete frame
					# First, check for SEQ frames. These have a higher priority.
					match = re.search(self.SEQFramePattern, self.framebuffer)
					if match:
						framedata = self.framebuffer[:match.end()]
						newframe = frame.SEQFrame(self.log, databuffer=framedata)

						# Process the SEQ frame straight away
						self.processSEQFrame(newframe)

						# slice the framebuffer to only include the trailing
						# non frame data what probably belongs to the next frame
						self.framebuffer = self.framebuffer[match.end():]

					# Look for the frame trailer
					match = re.search(self.dataFrameTrailer, self.framebuffer)

					# If found, create a Frame object
					if match:
						framedata = self.framebuffer[:match.end()]
						newframe = frame.DataFrame(self.log, databuffer=framedata)
						self.pushFrame(newframe)
#						self.log.logmsg(logging.LOG_DEBUG, "%s: pushedFrame: %s" % (self, newframe) )

						# slice the framebuffer to only include the trailing
						# non frame data what probably belongs to the next frame
						self.framebuffer = self.framebuffer[match.end():]
				else:
					raise TCPSessionException("Connection closed by remote host")

		except socket.error, e:
			if e[0] == errno.EWOULDBLOCK:
				pass

			elif e[0] == errno.ECONNRESET:
				raise TCPSessionException("Connection closed by remote host")

			else:
				self.log.logmsg(logging.LOG_DEBUG, "socket.error: %s" % e)
				raise

		except frame.DataFrameException, e:
			raise TCPSessionException(e)

		# Drop packets if queue is full, log a warning.
		except session.SessionInboundQueueFull:
			self.log.logmsg(logging.LOG_WARN, "Session inbound queue full from %s" % self.client_address)
			pass

		except TCPSessionException:
			raise

		except Exception, e:
			raise TCPSessionException("Unhandled Exception in getInputFrame(): %s: %s" % (e.__class__, e))

	def sendPendingFrame(self):
		try:
			data = self.pullFrame()
			if data:

>>>
>>>				FIXME: Do encryption stuff here
>>>

				self.wfile.write(data)
				self.wfile.flush()
		except Exception, e:
			self.log.logmsg(logging.LOG_WARN, "Exception in sendPendingFrame(): %s" % e)
			pass

class TLSTCPListenerSession(tcpsession.TCPListenerSession, TLSTCPCommsMixin):

	def __init__(self, request, client_address, server):
		raise NotImplementedError

		# Not quite sure what should go here yet
		tcpsession.TCPListenerSession.__init__(self, request, client_address, server)

class TLSTCPInitiatorSession(tcpsession.TCPInitiatorSession, TLSTCPCommsMixin):

	def __init__(self, log, profileDict, host, port):
		raise NotImplementedError

		# Whatever encryption setup stuff is needed here.
		tcpsession.TCPInitiatorSession.__init__(self, log, profileDict, host, port)

class TLSTCPSessionException(tcpsession.TCPSessionException):
	def __init__(self, args=None):
		self.args = args
