# $Id: tcpsession.py,v 1.3 2002/08/05 07:07:16 jpwarren Exp $
# $Revision: 1.3 $
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
# This class implements a DataStream object that communicates via TCP

from beep.core import constants
from beep.core import logging
from beep.core import session
from beep.core import frame

import sys
import re
import errno
import exceptions
import socket, select
import string
import threading
import SocketServer

# This uses heaps of multiple inheritence, for the following reasons:
# SocketServer.ThreadingTCPServer provides a relatively neat interface for
# providing a TCP socket server with thread support.
# SessionListener is necessary because, well, that's what this really does.
# the ThreadingTCPServer is just an implementation detail for this particular
# kind of SessionListener.
# threading.Thread is required because for some stupid reason, a ThreadingTCPServer
# only creates a thread for whatever you put in the finish_request bits, which
# I find really dumb.

class TCPSessionListener(SocketServer.TCPServer, session.SessionListener, threading.Thread):

	state = constants.SESSION_UNINITIALIZED
	address = ()

	def __init__(self, log, profileDict, host, port):

		session.SessionListener.__init__(self, log, profileDict)
		self.log.logmsg(logging.LOG_INFO, "Starting listener on %s[%s]..." % (host, port) )

		self.address = (host, port)
		SocketServer.TCPServer.__init__(self, self.address, TCPListenerSession)

		# Make socket non-blocking
		self.socket.setblocking(0)

		# and finally, do the thread bits
		threading.Thread.__init__(self)

		self.state = constants.SESSION_INITIALIZED
#		self.log.logmsg(logging.LOG_DEBUG, "%s -> SESSION_INITIALIZED" % self)
		# I want to act like a daemon
		self.setDaemon(1)
		self.start()

	def run(self):

		self.state = constants.SESSION_ACTIVE
#		self.log.logmsg(logging.LOG_DEBUG, "%s -> SESSION_ACTIVE" % self)

		while self.state != constants.SESSION_CLOSING:
			self.handle_request()

#		self.log.logmsg(logging.LOG_DEBUG, "%s -> SESSION_CLOSED" % self)
		self.log.logmsg(logging.LOG_INFO, "Listener %s[%s] exitted." % self.address)

	def finish_request(self, request, client_address):
		requestHandler = self.RequestHandlerClass(request, client_address, self)
		self.addSession(requestHandler)

	def close_request(self, request):
		self.removeSession(request)

	def close(self):
		session.SessionManager.close(self)
		self.socket.close()

class TCPCommsMixin:
	"""This class is used to supply the common methods used
	by both Initiator and Listener TCPSessions to read and write
	frames to/from the wire. Saves writing things more than
	once.
	"""
	framebuffer = ''
	windowsize = {}			# dictionary for each channel's window size
	dataFrameTrailer = re.compile(frame.DataFrame.TRAILER)
	SEQFrameRE = frame.SEQFrame.type
	SEQFrameRE += ".*"
	SEQFrameRE += frame.SEQFrame.TRAILER
	SEQFramePattern = re.compile(SEQFrameRE)

	# Overload createChannel from Session
	def createChannel(self, channelnum, profile):
		"""This overloads createChannel() from class Session to
		   add window sizing via SEQ capabilities to the TCP transport
		   layer mapping, as per RFC 3081
		"""
		session.Session.createChannel(self, channelnum, profile)
		self.windowsize[channelnum] = 4096

	def deleteChannel(self, channelnum):
		"""This overloads deleteChannel() from class Session to
		   blank out the window size dictionary for the closed
		   channel. Memory management, basically.
		"""
		session.Session.deleteChannel(self, channelnum)
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
				data = self.connection.recv(constants.MAX_INBUF)
				if data:
					self.framebuffer += data

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
				self.wfile.write(data)
				self.wfile.flush()
		except Exception, e:
			self.log.logmsg(logging.LOG_WARN, "Exception in sendPendingFrame(): %s" % e)
			pass

# Created when TCPSessionListener accepts a connection and spawns a thread
# This really only inherits from StreamRequestHandler for typing reasons,
# since the implementation of SocketServer RequestHandlers appears to be
# badly broken
class TCPListenerSession(SocketServer.StreamRequestHandler, session.ListenerSession, threading.Thread, TCPCommsMixin):
	log = None

	# This is here because BaseRequestHandler isn't implemented correctly
	# and as a consequence, neither is StreamRequestHandler
	request = None
	connection = None
	client_address = None
	server = None

	# The __init__ strategy of the StreamRequestHandler 
	# (actually, the BaseRequestHandler) really breaks threading.
	# I should send in some patches or something to make it
	# do better threading so it's actually halfway useful and
	# I don't need to do these kludges.
	def __init__(self, request, client_address, server):

		threading.Thread.__init__(self)

		self.request = request
		self.connection = request
		self.client_address = client_address
		self.server = server

		# Get the log info from the server
		self.log = self.server.log

		# initialise as a TCPListenerSession
		session.ListenerSession.__init__(self, self.server.log, self.server.profileDict)
		self.state = constants.SESSION_INITIALIZED
		self.log.logmsg(logging.LOG_INFO, "Connection from %s[%s]." % self.client_address)
		self.start()

	def setup(self):

		# configure as a SocketServer
		SocketServer.StreamRequestHandler.setup(self)

		# Now, configure the socket as non-blocking
		self.connection.setblocking(0)
#		self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

	def run(self):
		try:
			self.setup()
			self.handle()
			self.finish()
		finally:
			sys.exc_traceback = None

	def handle(self):

		if self.state != constants.SESSION_INITIALIZED:
			self.log.logmsg( logging.LOG_ERR, "%s: Attempt to become active before initializing." % self )
			return
		self.state = constants.SESSION_ACTIVE
#		self.log.logmsg( logging.LOG_DEBUG, "%s -> SESSION_ACTIVE" % self )

		while self.state < constants.SESSION_CLOSING:

			try:
				# First, try to read a frame
				self.getInputFrame()

				# Then try to process any pending frames
				self.processFrames()

				# Finally, send a frame if any are pending
				self.sendPendingFrame()

			except TCPSessionException, e:
				self.log.logmsg( logging.LOG_ERR, "Closing Session: %s" % e)
				self.state = constants.SESSION_CLOSING
				break

			except session.TerminateException, e:
				self.log.logmsg( logging.LOG_INFO, "Terminating Session: %s" % e)
				self.state = constants.SESSION_CLOSING
				break

#		self.log.logmsg( logging.LOG_DEBUG, "%s -> SESSION_CLOSING" % self )

	def finish(self):
		# I'm exiting if I get here
		self.state = constants.SESSION_EXITING
#		self.log.logmsg( logging.LOG_DEBUG, "%s -> SESSION_EXITING" % self)

		self.connection.close()
		self.request.close()
		SocketServer.StreamRequestHandler.finish(self)

		self.server.removeSession(self)
		self.state = constants.SESSION_EXITED
		self.log.logmsg(logging.LOG_INFO, "Session from %s[%s] finished." % self.client_address)

	# Need to deal with SEQ frames
	def processSEQFrame(self):
		raise NotImplementedError

class TCPInitiatorSession(session.InitiatorSession, threading.Thread, TCPCommsMixin):

	server_address = ()		# Address of remote end
	connection = None		# socket connection to server
	wfile = None			# File object to access connection outbound

	def __init__(self, log, profileDict, host, port):
		threading.Thread.__init__(self)

		session.InitiatorSession.__init__(self, log, profileDict)

		# Attempt to connect to the remote end
		self.server_address = (host, port)
		self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.connection.connect(self.server_address)
			self.wfile = self.connection.makefile('wb', constants.MAX_OUTBUF)

		except Exception, e:
			raise TCPSessionException(e)

		self.start()

	def run(self):
		self.state = constants.SESSION_ACTIVE
		while self.state != constants.SESSION_CLOSING:
			try:
				# First, try to read a frame
				self.getInputFrame()

				# Then try to process any pending frames
				self.processFrames()

				# Finally, send a frame if any are pending
				self.sendPendingFrame()

			except TCPSessionException, e:
				self.log.logmsg( logging.LOG_ERR, "Closing Session: %s" % e)
				self.state = constants.SESSION_CLOSING
				break

			except session.TerminateException, e:
				self.log.logmsg( logging.LOG_INFO, "Terminating Session: %s" % e)
				self.state = constants.SESSION_CLOSING
				break

	# Need to deal with SEQ frames
	def processSEQFrame(self):
		raise NotImplementedError

	def close(self):
		# First, shut down socket comms
		session.InitiatorSession.close(self)
		self.wfile.flush()
		self.wfile.close()
		self.connection.close()

class TCPSessionException(session.SessionException):
	def __init__(self, args=None):
		self.args = args
