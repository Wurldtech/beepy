# $Id: tcpsession.py,v 1.13 2002/10/07 05:52:04 jpwarren Exp $
# $Revision: 1.13 $
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

	def __init__(self, log, profileDict, host, port, daemon=0):

		session.SessionListener.__init__(self, log, profileDict)

		self.address = (host, port)

		# and finally, do the thread bits
		threading.Thread.__init__(self)
		self.shutdown = threading.Event()

		# I want to act like a daemon
		if daemon:
			self.setDaemon(1)
		self.start()

	def server_bind(self):
		self.allow_reuse_address = 1
		SocketServer.TCPServer.server_bind(self)

	def _stateINIT(self):
		self.log.logmsg(logging.LOG_INFO, "Starting listener on %s[%s]..." % self.address )
		SocketServer.TCPServer.__init__(self, self.address, TCPListenerSession)

		# Make socket non-blocking
		self.socket.setblocking(0)
		self.transition('ok')

	def _stateACTIVE(self):
		if self.shutdown.isSet():
			self.transition('close')

		self.handle_request()

	def _stateCLOSING(self):
		self.log.logmsg(logging.LOG_DEBUG, "closing all ListenerSessions...")
		while self.sessionList:
			for sessId in self.sessionList.keys():
				sess = self.sessionList[sessId]
				self.log.logmsg(logging.LOG_DEBUG, "closing sessId: %s: %s..." % (sessId, sess))
				sess.close()
				sess.join()
				self.removeSession(sessId)

		self.transition('ok')

	def _stateTERMINATE(self):
		self.socket.close()

		self.log.logmsg(logging.LOG_INFO, "Listener %s[%s] exitted." % self.address)
		self.transition('ok')

	def finish_request(self, request, client_address):
		requestHandler = self.RequestHandlerClass(request, client_address, self)
		self.addSession(requestHandler)

	def close_request(self, request):
		pass

	def close(self):
		self.shutdown.set()

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
#					self.log.logmsg(logging.LOG_DEBUG, "gotdata: %s" % data)
					# Check for oversized frames. If framebuffer goes over
					# constants.MAX_FRAME_SIZE + constants.MAX_INBUF then
					# the frame is too large.
					if len(self.framebuffer) > (constants.MAX_FRAME_SIZE + constants.MAX_INBUF):
						raise session.TerminateException("Frame too large")

					# Detect a complete frame
					# First, check for SEQ frames. These have a higher priority.
					match = re.search(self.SEQFramePattern, self.framebuffer)
					while match:
						framedata = self.framebuffer[:match.end()]
						newframe = frame.SEQFrame(self.log, databuffer=framedata)

						# Process the SEQ frame straight away
						self.processSEQFrame(newframe)

						# slice the framebuffer to only include the trailing
						# non frame data what probably belongs to the next frame
						self.framebuffer = self.framebuffer[match.end():]
						match = re.search(self.SEQFramePattern, self.framebuffer)

					# Look for the frame trailer
					match = re.search(self.dataFrameTrailer, self.framebuffer)
					# If found, create a Frame object
					while match:
						framedata = self.framebuffer[:match.end()]
						newframe = frame.DataFrame(self.log, databuffer=framedata)
						self.pushFrame(newframe)
#						self.log.logmsg(logging.LOG_DEBUG, "%s: pushedFrame: %s" % (self, newframe) )

						# slice the framebuffer to only include the trailing
						# non frame data what probably belongs to the next frame
						self.framebuffer = self.framebuffer[match.end():]
						match = re.search(self.dataFrameTrailer, self.framebuffer)
				else:
					raise session.TerminateException("Connection closed by remote host")

		except socket.error, e:
			if e[0] == errno.EWOULDBLOCK:
				pass

			elif e[0] == errno.ECONNRESET:
				raise session.TerminateException("Connection closed by remote host")

			else:
				self.log.logmsg(logging.LOG_DEBUG, "socket.error: %s" % e)
				raise session.TerminateException("%s" % e)

		except frame.DataFrameException, e:
			raise session.TerminateException(e)

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
				self.wfile.write(data)
				self.wfile.flush()
		except Exception, e:
			self.log.logmsg(logging.LOG_WARN, "Exception in sendPendingFrame(): %s" % e)
			pass

	# Need to deal with SEQ frames
	def processSEQFrame(self):
		raise NotImplementedError

# Created when TCPSessionListener accepts a connection and spawns a thread
# This really only inherits from StreamRequestHandler for typing reasons,
# since the implementation of SocketServer RequestHandlers appears to be
# badly broken
class TCPListenerSession(SocketServer.StreamRequestHandler, session.ListenerSession, threading.Thread, TCPCommsMixin):
#	log = None
#	request = None
#	connection = None
#	client_address = None
#	server = None

	# The __init__ strategy of the StreamRequestHandler 
	# (actually, the BaseRequestHandler) really breaks threading.
	# I should send in some patches or something to make it
	# do better threading so it's actually halfway useful and
	# I don't need to do these kludges.
	def __init__(self, request, client_address, server):

		threading.Thread.__init__(self)
		self.shutdown = threading.Event()

		self.request = request
		self.connection = request
		self.client_address = client_address
		self.server = server

		# Get the log info from the server
		self.log = self.server.log

		# initialise as a TCPListenerSession
		session.ListenerSession.__init__(self, self.server.log, self.server.profileDict)

		self.log.logmsg(logging.LOG_INFO, "Connection from %s[%s]." % self.client_address)
		self.start()

	def __del__(self):
		self.server = None
		self.log = None

	def _stateINIT(self):
		# configure as a SocketServer
		SocketServer.StreamRequestHandler.setup(self)

		# Now, configure the socket as non-blocking
		self.connection.setblocking(0)
		self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
#		self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.createChannelZero()
		# send the queued greeting message
		self.queueOutboundFrames()
		self.sendPendingFrame()
		while not self.channels[0].profile.receivedGreeting:
			try:
				self.getInputFrame()
				self.processFrames()

			except session.TerminateException, e:
				self.log.logmsg( logging.LOG_ERR, "Terminating Session: %s" % e)
				self.transition('error')
				return

			except Exception, e:
				self.log.logmsg(logging.LOG_DEBUG, "Error occurred setting up connection: %s" % e)
				self.transition('error')
				return

		self.transition('ok')
		return

	def _stateACTIVE(self):
		if self.shutdown.isSet():
			self.transition('close')
		self._mainLoop()

	def _mainLoop(self):
		try:
			# First, try to read a frame
			self.getInputFrame()

			# Then try to process any pending frames
			self.processFrames()

			# Finally, send a frame if any are pending
			self.sendPendingFrame()

		except session.TuningReset, e:
			self.log.logmsg( logging.LOG_INFO, "Tuning reset: %s" % e )
			self.transition('reset')
			return

		except session.TerminateException, e:
			self.log.logmsg( logging.LOG_ERR, "Terminating Session: %s" % e)
			self.transition('error')
			return

	def _stateCLOSING(self):
		self.closeAllChannels()
		while len(self.channels.keys()) > 0:
			if len(self.channels.keys()) == 1 and self.channels.has_key(0):
				self.log.logmsg(logging.LOG_DEBUG, "only channel zero left")
				self.deleteChannel(0)
				break
			try:
				self._mainLoop()
			except Exception, e:
				self.log.logmsg(logging.LOG_DEBUG, "exception closing channels: %s" % e)
				self.transition('error')

		self.transition('ok')

	def _stateTUNING(self):
		self.log.logmsg(logging.LOG_INFO, "state->TUNING")
		# Flush all outbound buffers, including channel outbound buffers
		self.log.logmsg(logging.LOG_DEBUG, "Flushing channel queues...")
		self.flushChannelOutbound()

		self.log.logmsg(logging.LOG_DEBUG, "Flushing outbound queue...")
		while not self.outbound.empty():
			self.sendPendingFrame()

		self.log.logmsg(logging.LOG_DEBUG, "Deleting channels...")
		self.deleteAllChannels()

		self.transition('ok')

	def _stateTERMINATE(self):
		"""TERMINATE state is reached from the ACTIVE state if an error
		   occurs that results in immediate session shutdown. This is
		   usually things like loss of synchronisation or remote host
		   closing the connection.
		"""
		SocketServer.StreamRequestHandler.finish(self)
		self.connection.close()
		self.request.close()

		self.log.logmsg(logging.LOG_INFO, "Session from %s[%s] finished." % self.client_address)
		self.transition('ok')

	def close(self):
		self.log.logmsg(logging.LOG_DEBUG, "call to %s.close()" % self)
		self.shutdown.set()

class TCPInitiatorSession(session.InitiatorSession, threading.Thread, TCPCommsMixin):

	server_address = ()		# Address of remote end
	connection = None		# socket connection to server
	wfile = None			# File object to access connection outbound

	def __init__(self, log, profileDict, host, port, sessmgr):
		threading.Thread.__init__(self)
		self.shutdown = threading.Event()

		session.InitiatorSession.__init__(self, log, profileDict)
		self.server_address = (host, port)
		self.sessmgr = sessmgr
		self.start()

	def _stateINIT(self):
		"""INIT for an Initiator attempts to connect to the remote server
		"""
		# Attempt to connect to the remote end
		self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.connection.connect(self.server_address)
			self.wfile = self.connection.makefile('wb', constants.MAX_OUTBUF)
			self.createChannelZero()
			# send the queued greeting message
			self.log.logmsg(logging.LOG_DEBUG, "Sending greeting...")
			self.queueOutboundFrames()
			self.sendPendingFrame()
			while not self.channels[0].profile.receivedGreeting:
				self.getInputFrame()
				self.processFrames()
			self.transition('ok')

		except Exception, e:
			self.log.logmsg(logging.LOG_ERR, "Connection to remote host failed: %s" % e)
			self.transition('error')

	def _stateACTIVE(self):
		if self.shutdown.isSet():
			self.transition('close')
		self._mainLoop()

	def _mainLoop(self):
		try:
			# First, try to read a frame
			self.getInputFrame()

			# Then try to process any pending frames
			self.processFrames()

			# Finally, send a frame if any are pending
			self.sendPendingFrame()

		except session.TuningReset, e:
			self.log.logmsg( logging.LOG_INFO, "Tuning reset: %s" % e )
			self.transition('reset')
			return

		except session.TerminateException, e:
			self.log.logmsg( logging.LOG_ERR, "Terminating Session: %s" % e)
			self.transition('error')
			return

	def _stateCLOSING(self):
		self.closeAllChannels()
		while len(self.channels.keys()) > 0:
			if len(self.channels.keys()) == 1 and self.channels.has_key(0):
				self.log.logmsg(logging.LOG_DEBUG, "only channel zero left")
				self.deleteChannel(0)
			try:
				self._mainLoop()
			except Exception, e:
				self.log.logmsg(logging.LOG_DEBUG, "exception closing channels: %s" % e)
				self.transition('error')

		self.transition('ok')

	def _stateTUNING(self):
		self.log.logmsg(logging.LOG_INFO, "state->TUNING")
		# Flush all outbound buffers, including channel outbound buffers
		self.log.logmsg(logging.LOG_DEBUG, "Flushing channel queues...")
		self.flushChannelOutbound()

		self.log.logmsg(logging.LOG_DEBUG, "Flushing outbound queue...")
		while not self.outbound.empty():
			self.sendPendingFrame()

		self.log.logmsg(logging.LOG_DEBUG, "Deleting channels...")
		self.deleteAllChannels()

		self.transition('ok')

	def _stateTERMINATE(self):
		self.wfile.flush()
		self.wfile.close()
		self.connection.close()
		self.transition('ok')

	def close(self):
		self.shutdown.set()

class TCPInitiatorSessionManager(session.InitiatorManager, threading.Thread):

	def __init__(self, log, profileDict, daemon=1):
		threading.Thread.__init__(self)
		self.shutdown = threading.Event()

		session.InitiatorManager.__init__(self, log, profileDict)

		if daemon:
			self.setDaemon(1)
		self.start()

	def _stateINIT(self):
		self.transition('ok')

	def _stateACTIVE(self):
		if self.shutdown.isSet():
			self.transition('close')
		pass

	def _stateCLOSING(self):
		while self.sessionList:
			for sessId in self.sessionList.keys():
				sess = self.sessionList[sessId]
				sess.close()
				sess.join()
				self.removeSession(sessId)

		self.transition('ok')

	def _stateTERMINATE(self):
		self.deleteAllSessions()
		self.transition('ok')

	def close(self):
		self.shutdown.set()

	def connectInitiator(self, host, port, profileDict=None):
		if not profileDict:
			profileDict = self.profileDict
		client = TCPInitiatorSession(self.log, profileDict, host, port, self)
		self.addSession(client)
		return client
