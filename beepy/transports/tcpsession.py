# $Id: tcpsession.py,v 1.4 2003/01/08 05:38:12 jpwarren Exp $
# $Revision: 1.4 $
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

import re
import socket, select, errno
import threading
import exceptions
import Queue
import time
import sys, traceback

from beepy.core import constants
from beepy.core import logging
from beepy.core import session
from beepy.core import frame
from beepy.core import util


class TCPDataEnqueuer(util.DataEnqueuer):

	def __init__(self, log, sock, session, dataq, errEvent, read_timeout=1, name=None):

		self.log = log
		self.sock = sock
		self.connected = 1
		self.session = session
		self.framebuffer = ''
		self.newframe = None
		self.windowsize = {}
		self.frameHeaderPattern = re.compile(".*\r\n")
		self.dataFrameTrailer = re.compile(frame.DataFrame.TRAILER)
		SEQFrameRE = frame.SEQFrame.dataFrameType
		SEQFrameRE += ".*"
		SEQFrameRE += frame.SEQFrame.TRAILER
		self.SEQFramePattern = re.compile(SEQFrameRE)

		self.read_timeout = read_timeout


		# Initialise as a DataEnqueuer
		util.DataEnqueuer.__init__(self, dataq, errEvent, name)
		self.log.logmsg(logging.LOG_DEBUG, "Started thread: %s" % self)

	def loop(self):
		"""enqueueData reads a frame off the wire and places it
		   into the dataq.
		"""
		try:
			self.getDataBlock()
			self.findHeader()
			self.finishFrame()

		except socket.error, e:
			if e[0] == errno.EWOULDBLOCK:
				pass

			elif e[0] == errno.ECONNRESET:
				self.setError( TCPTerminalError("Connection closed by remote host") )
				self.stop()

			else:
				self.log.logmsg(logging.LOG_DEBUG, "socket.error: %s" % e)
				self.setError( TCPTerminalError("%s" % e) )
				self.stop()

		except select.error, e:
			if e[0] == 4:
				# Interrupted system call. Don't worry about it.
				# This is probably a CTRL-C job from somewhere.
				self.setError( TCPTerminalError("%s" % e) )
				self.stop()

		except frame.DataFrameException, e:
			self.setError( TCPTerminalError("%s" % e) )
			self.stop()

#		# Drop packets if queue is full, log a warning.
#		except Queue.Full:
#			self.log.logmsg(logging.LOG_WARN, "Session inbound queue full from %s" % self.client_address)
#			pass

		except TCPTerminalError, e:
			self.setError(e)
			self.stop()

		except Exception, e:
			self.log.logmsg(logging.LOG_ERR, "Unhandled exception in enqueueData(). Generating traceback..." )
			traceback.print_exc(file=self.log.logfile)

			self.setError( TCPTerminalError("Unhandled exception in enqueueData(): %s: %s" % (e.__class__, e)) )
			self.stop()

	def getDataBlock(self):
		""" getDataBlock retrieves a block of data from the socket.
		    It uses select() to wait on the socket until data
		    becomes available until self.read_timeout.
		    Any data receives is placed on self.framebuffer
		"""

		# use select to poll for pending data inbound
		inbit, outbit, oobit = select.select([self.sock], [], [], self.read_timeout)
		if inbit:
			data = self.getDataFromSocket()
#			self.log.logmsg(logging.LOG_DEBUG, "Read event")
			if data:
				self.log.logmsg(logging.LOG_DEBUG, "Received: %s" % data)
				self.framebuffer += data
				# Check for oversized frames. If framebuffer goes over
				# constants.MAX_FRAME_SIZE + constants.MAX_INBUF then
				# the frame is too large.
				if len(self.framebuffer) > (constants.MAX_FRAME_SIZE + constants.MAX_INBUF):
					raise TCPTerminalError("Frame too large")
			else:
				raise TCPTerminalError("Connection closed by remote host")

	def findHeader(self):
		""" findHeader() attempts to find a new frame header
		    in the framedata so far received in the framebuffer.
		    If a frame header is found, a new frame object is
		    started.
		"""
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
					self.newframe = frame.DataFrame(databuffer=headerdata)

	def finishFrame(self):
		""" finishFrame() adds framebuffer data to a frame object
		    (if one has been started) as payload data. If it
		    finds a frame trailer, the completed frame is placed
		    onto the session inbound queue and the state is reset
		    to look for the next frame header.
		"""
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
					raise TCPTerminalError("Payload larger than expected size")
				else:
					self.newframe.payload += framedata
					# The frame is now complete
					self.dataq.put(self.newframe)
					self.newframe = None

			else:
				# I append the data to the current frame payload
				# after checking that it isn't too long.
				if len(self.newframe.payload) + len(self.framebuffer) > self.newframe.size:
					self.log.logmsg(logging.LOG_DEBUG, "size: %s, expected: %s" % ( len(self.newframe.payload) + len(self.framebuffer), self.newframe.size ) )
					self.log.logmsg(logging.LOG_DEBUG, "payload: %s, buffer: %s" % ( self.newframe.payload, self.framebuffer ) ) 
					raise TCPTerminalError("Payload larger than expected size")
				else:
					self.newframe.payload += self.framebuffer
					self.framebuffer = ''

	def getDataFromSocket(self):
		""" This method abstracts the method for getting data from
		    the socket. This comes in handy when subclassing this
		    class, as in TLSTCPDataEnqueuer, which uses a slightly
		    different mechanism for getting data.
		    This encourages easy code re-use, which is always good.
		"""
		return self.sock.recv(constants.MAX_INBUF)

	# Need to deal with SEQ frames
	def processSEQFrame(self):
		raise NotImplementedError

	def tuningReset(self):
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)
		self.terminate()

	def cleanup(self):
		try:
			if self.connected:
				self.sock.shutdown(2)
				self.sock.close()
				self.connected = 0
			util.DataEnqueuer.stop(self)
			self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)
		except socket.error, e:
			if e[0] == errno.ENOTCONN:
				pass

		except Exception, e:
			self.log.logmsg(logging.LOG_ERR, "Unhandled exception while stopping. Generating traceback...")
			traceback.print_exc(file=self.log.logfile)

class TCPDataDequeuer(util.DataDequeuer):
	"""A TCPDataDequeuer takes frames off the session outbound queue
	   and sends them over the wire.
	"""
	def __init__(self, log, sock, session, dataq, errEvent, name=None):
		self.log = log
		self.sock = sock
		self.session = session

		# Initialise as a DataDequeuer
		util.DataDequeuer.__init__(self, dataq, errEvent, name)
		self.log.logmsg(logging.LOG_DEBUG, "Started thread: %s" % self)

	def dequeueData(self):
		try:
			data = self.dataq.get()
			if data:
				sent = self.sendDataToSocket(data)
#				self.log.logmsg(logging.LOG_DEBUG, "Sent %d bytes>> %s" % (sent, data) )
				return 1
		except Queue.Empty:
			pass

		except Exception, e:
			self.log.logmsg(logging.LOG_ERR, "Unhandled Error: %s: %s" % (e.__class__, e) )
			traceback.print_exc(file=self.log.logfile)

	def sendDataToSocket(self, data):
		""" This method abstracts the method for getting sending data
		    to socket. This comes in handy when subclassing this
		    class, as in TLSTCPDataDequeuer, which uses a slightly
		    different mechanism for sending data.
		    This encourages easy code re-use, which is always good.
		"""
		return self.sock.send(data)

	def tuningReset(self):
		""" A Tuning Reset should flush the outbound DataQueue
		"""
		while self.dequeueData():
			pass
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)
		self.terminate()

	def stop(self):
		util.DataDequeuer.stop(self)

	def cleanup(self):
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)

class TCPError(exceptions.Exception):
	def __init__(self, args=None):
		self.args = args

class TCPTerminalError(TCPError):
	"""A TCPTerminalError is something that should cause the
	   connection to be dropped.
	"""

class TCPSessionTerminated(TCPError):
	"""This gets set when a ListenerSession or InitiatorSession
	   terminates. It passes back to the Monitor to let it
	   know that this thread has exited.
	"""

class TCPListenerSession(session.ListenerSession, util.isMonitored):

	def __init__(self, sock, client_address, sessmgr, read_timeout=1):
		self.sock = sock

		self.client_address = client_address
		self.sessmgr = sessmgr

		self.read_timeout = read_timeout

		# Using a single monitorEvent from the sessmgr means
		# that the sessmgr will only create a single Monitor
		# for the process that will monitor all Sessions
		# and their TCP I/O threads (Dataqueuers)
		util.isMonitored.__init__(self, sessmgr.monitorEvent, name="server: %s[%s]" % client_address)

		session.ListenerSession.__init__(self, sessmgr.log, sessmgr.profileDict)

		self.log.logmsg(logging.LOG_INFO, "Handling session from: %s[%s]" % self.client_address)
		self.log.logmsg(logging.LOG_DEBUG, "Started thread: %s" % self)

		self.start()

	def _stateINIT(self):

		self.startIOThreads(self.sock)

		self.createChannelZero()

		self.transition('ok')
		return

	def _stateACTIVE(self):
		if self._stop.isSet():
			self.transition('close')
			return
		self._mainLoop()

	def _mainLoop(self):
		try:
			self.processFrames()

		except session.TuningReset, e:
			self.log.logmsg( logging.LOG_INFO, "Tuning reset: %s" % e )
			self.transition('reset')
			return

		except session.TerminateException, e:
			self.log.logmsg( logging.LOG_NOTICE, "Terminating SessionID %d: %s" % (self.ID, e) )
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
				return

		self.transition('ok')

	def _stateTUNING(self):
		self.log.logmsg(logging.LOG_INFO, "state->TUNING")
		# Flush all outbound buffers, including channel outbound buffers
		self.log.logmsg(logging.LOG_DEBUG, "Flushing channel queues...")
		self.inputDataQueue.tuningReset()
		self.sessmgr.monitor.stopMonitoring(self.inputDataQueue)
		self.outputDataQueue.tuningReset()
		self.sessmgr.monitor.stopMonitoring(self.inputDataQueue)

		self.log.logmsg(logging.LOG_DEBUG, "Deleting channels...")
		self.deleteAllChannels()

		self.sessmgr.monitor.stopMonitoring(self)

		self.log.logmsg(logging.LOG_INFO, "Tuning reset complete." )
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)

		self.transition('ok')

	def _stateTERMINATE(self):
		"""TERMINATE state is reached from the ACTIVE state if an error
		   occurs that results in immediate session shutdown. This is
		   usually things like loss of synchronisation or remote host
		   closing the connection.
		"""
		self.inputDataQueue.stop()
		self.outputDataQueue.stop()

		self.sessmgr.monitor.stopMonitoring(self.inputDataQueue)
		self.sessmgr.monitor.stopMonitoring(self.outputDataQueue)
		self.sessmgr.monitor.stopMonitoring(self)
		self.sessmgr.removeSession(self.ID)

		self.log.logmsg(logging.LOG_INFO, "Session from %s[%s] finished." % self.client_address)
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)
		self.transition('ok')

	def startIOThreads(self, sock):
		""" startIOThreads instanciates the IO threads for the Session.
		    This is done as a method to allow subclasses to overload this
		    part of the initialisation easily.
		"""
		self.inputDataQueue = TCPDataEnqueuer(self.log, sock, self, self.inbound, self.ismonitoredEvent, self.read_timeout, name="inputQ: %s[%s]" % self.client_address)
		self.outputDataQueue = TCPDataDequeuer(self.log, sock, self, self.outbound, self.ismonitoredEvent, name="outputQ: %s[%s]" % self.client_address )
		self.sessmgr.monitor.startMonitoring(self.inputDataQueue)
		self.sessmgr.monitor.startMonitoring(self.outputDataQueue)
		self.inputDataQueue.start()
		self.outputDataQueue.start()

	def sendFrame(self, theframe):
		data = str(theframe)
		try:
			self.outbound.put(data)
		except Queue.Full:
			self.setError( SessionOutboundQueueFull('Outbound queue full') )

	def recvFrame(self):
		try:
			theframe = self.inbound.get()
			return theframe
		except:
			raise

	def close(self):
		self.stop()

class TCPInitiatorSession(session.InitiatorSession, util.isMonitored):

	def __init__(self, log, profileDict, server_address, sessmgr, read_timeout=1):

		session.InitiatorSession.__init__(self, log, profileDict)
		util.isMonitored.__init__(self, sessmgr.monitorEvent, name="client: %s[%s]" % server_address)
		self.server_address = server_address
		self.sessmgr = sessmgr
		self.read_timeout = read_timeout
		self.log.logmsg(logging.LOG_DEBUG, "Started thread: %s" % self)

		self.start()

	def _stateINIT(self):
		"""INIT for an Initiator attempts to connect to the remote server
		"""
		# Attempt to connect to the remote end
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.sock.connect(self.server_address)

			self.startIOThreads(self.sock)

			self.createChannelZero()

			while not self.channels[0].profile.receivedGreeting:
				if self._stop.isSet():
					self.transition('close')
					return
				self.processFrames()
			self.log.logmsg(logging.LOG_DEBUG, 'initiator initialized successfully')
			self.transition('ok')
			return

		except Exception, e:
			self.log.logmsg(logging.LOG_ERR, "Connection to remote host failed: %s" % e)
			self.transition('error')
			return

	def _stateACTIVE(self):
		if self._stop.isSet():
			self.transition('close')
			return
		self._mainLoop()

	def _mainLoop(self):
		try:

			self.processFrames()

		except session.TuningReset, e:
			self.log.logmsg( logging.LOG_INFO, "Tuning reset: %s" % e )
			self.transition('reset')
			return

		except session.TerminateException, e:
			self.log.logmsg( logging.LOG_NOTICE, "Terminating Session: %s" % e)
			self.transition('error')
			return

	def _stateCLOSING(self):
		self.log.logmsg(logging.LOG_INFO, "Closing Session %d..." % self.ID)
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
				return

		self.transition('ok')

	def _stateTUNING(self):
		self.log.logmsg(logging.LOG_INFO, "state->TUNING")
		# Flush all outbound buffers, including channel outbound buffers
		self.log.logmsg(logging.LOG_DEBUG, "Flushing channel queues...")
		self.inputDataQueue.tuningReset()
		self.sessmgr.monitor.stopMonitoring(self.inputDataQueue)
		self.outputDataQueue.tuningReset()
		self.sessmgr.monitor.stopMonitoring(self.inputDataQueue)

		self.log.logmsg(logging.LOG_DEBUG, "Deleting channels...")

		self.deleteAllChannels()

		self.sessmgr.monitor.stopMonitoring(self)

		self.log.logmsg(logging.LOG_INFO, "Tuning reset complete.")
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)
		self.transition('ok')

	def _stateTERMINATE(self):
		self.inputDataQueue.stop()
		self.outputDataQueue.stop()

		self.sessmgr.monitor.stopMonitoring(self.inputDataQueue)
		self.sessmgr.monitor.stopMonitoring(self.outputDataQueue)
		self.sessmgr.monitor.stopMonitoring(self)
		self.sessmgr.removeSession(self.ID)

		self.log.logmsg(logging.LOG_NOTICE, "Session to %s[%s] exited." % self.server_address)
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)
		self.transition('ok')

	def startIOThreads(self, sock):
		""" startIOThreads instanciates the IO threads for the Session.
		    This is done as a method to allow subclasses to overload this
		    part of the initialisation easily.
		"""
		self.inputDataQueue = TCPDataEnqueuer(self.log, sock, self, self.inbound, self.ismonitoredEvent, self.read_timeout, name="inputQ: %s[%s]" % self.server_address )
		self.outputDataQueue = TCPDataDequeuer(self.log, sock, self, self.outbound, self.ismonitoredEvent, name="outputQ: %s[%s]" % self.server_address )
		self.sessmgr.monitor.startMonitoring(self.inputDataQueue)
		self.sessmgr.monitor.startMonitoring(self.outputDataQueue)
		self.inputDataQueue.start()
		self.outputDataQueue.start()

	def sendFrame(self, theframe):
		data = str(theframe)
		try:
			self.outbound.put(data)
		except Queue.Full:
			self.setError( SessionOutboundQueueFull('Outbound queue full') )

	def recvFrame(self):
		try:
			theframe = self.inbound.get()
			return theframe
		except:
			raise

	def close(self):
		self.stop()

class TCPSessionListener(session.SessionListener, util.LoopingThread):

	def __init__(self, log, profileDict, host, port, daemon=0, max_connect=5, max_concurrent=50, accept_timeout=1, read_timeout=1, name=None ):


		self.address = (host, port)

		session.SessionListener.__init__(self, log, profileDict)
		self.addState('PAUSED', self._statePAUSED)
		self.addTransition('ACTIVE', 'pause', 'PAUSED')
		self.addTransition('PAUSED', 'ok', 'ACTIVE')
		self.addTransition('PAUSED', 'close', 'CLOSE')
		util.LoopingThread.__init__(self, name=name)

		self.monitorEvent = threading.Event()
		self.monitor = SessionMonitor(self.log, self.monitorEvent, read_timeout, name)
		self.monitor.start()

		self.max_connect = max_connect
		self.max_concurrent = max_concurrent
		self.accept_timeout = accept_timeout
		self.read_timeout = read_timeout

		self.setDaemon(daemon)
		self.log.logmsg(logging.LOG_DEBUG, "Started thread: %s" % self)
		self.start()

	def _stateINIT(self):
		self.log.logmsg(logging.LOG_NOTICE, "Starting listener on %s[%s]..." % self.address )

		try:
			self.start_socket()
			self.transition('ok')
			return

		except Exception, e:
			self.log.logmsg(logging.LOG_ERR, "Unable to start listener: %s: %s" % (e.__class__, e) )
			self.transition('error')
			return

	def _stateACTIVE(self):
		if self._stop.isSet():
			self.transition('close')
			return

		try:
			# Check for incoming connections
			inbit, outbit, oobit = select.select([self.sock], [], [], self.accept_timeout)
			if inbit:
				# This means an incoming connection has come in
				client, addr = self.sock.accept()
				self.log.logmsg(logging.LOG_INFO, "Connection from %s[%s]" % addr)
				newSession = TCPListenerSession(client, addr, self, self.read_timeout)
				self.addSession(newSession)
				self.monitor.startMonitoring(newSession)

				# Now check that we haven't got too many sessions
				if len(self.sessionList) >= self.max_concurrent:
					self.log.logmsg(logging.LOG_ERR, 'Maximum concurrent session limit (%d) reached.' % self.max_concurrent )
					self.log.logmsg(logging.LOG_ERR, 'Not accepting any more connections for now.')
					self.transition('pause')
					return

		except select.error, e:
			if e[0] == 4:
				# Interrupted system call. Don't worry about it.
				# This is probably a CTRL-C job from somewhere.
				self.transition('error')
				return

		except Exception, e:
			traceback.print_exc(self.log.logfile)
			self.transition('error')
			return

	def _statePAUSED(self):
		if len(self.sessionList) < self.max_concurrent:
			self.log.logmsg(logging.LOG_ERR, 'Total concurrent sessions below maximum (5d) again.' % self.max_concurrent)
			self.log.logmsg(logging.LOG_ERR, 'Re-enabling acceptance of new connections...' % self.max_concurrent)
			self.transition('ok')
			return
		time.sleep(5)

	def _stateCLOSING(self):
		self.log.logmsg(logging.LOG_INFO, "Closing all ListenerSessions...")
		while self.sessionList:
			for sessId in self.sessionList.keys():
				sess = self.sessionList[sessId]
				self.log.logmsg(logging.LOG_DEBUG, "Closing sessId: %s..." % sessId)
				sess.stop()
				sess.join()
				self.monitor.stopMonitoring(sess)
				self.removeSession(sessId)
		self.log.logmsg(logging.LOG_INFO, "All ListenerSessions have exited." )

		self.transition('ok')

	def _stateTERMINATE(self):
		self.monitor.stop()
		self.sock.close()

		self.log.logmsg(logging.LOG_NOTICE, "Listener at %s[%s] exited." % self.address)
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)
		self.transition('ok')

	def removeSession(self, sessId):
		self.log.logmsg(logging.LOG_DEBUG, 'Removing session: %d.' % sessId )
		session.SessionListener.removeSession(self, sessId)

	def start_socket(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setblocking(0)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(self.address)
		self.sock.listen(self.max_concurrent)

	def close(self):
		self.stop()

class TCPInitiatorSessionManager(session.InitiatorManager, util.LoopingThread):

	def __init__(self, log, profileDict, daemon=1, timeout=1, name=None):
		util.LoopingThread.__init__(self, name=name)
		session.InitiatorManager.__init__(self, log, profileDict)

		self.timeout = timeout

		self.monitorEvent = threading.Event()
		self.monitor = SessionMonitor(self.log, self.monitorEvent, timeout, name)
		self.monitor.start()

		self.setDaemon(daemon)
		self.log.logmsg(logging.LOG_DEBUG, "Started thread: %s" % self)
		self.start()

	def _stateINIT(self):
		self.log.logmsg(logging.LOG_INFO, "InitiatorSessionManager initialised.")
		self.transition('ok')

	def _stateACTIVE(self):
		# Wait indefinitely until _stop is set.
		self._stop.wait()
		self.transition('close')

	def _stateCLOSING(self):
		while self.sessionList:
			for sessId in self.sessionList.keys():
				sess = self.sessionList[sessId]
				self.log.logmsg(logging.LOG_DEBUG, "InitiatorManager closing %s..." % sess)
				sess.stop()
				sess.join()
				self.removeSession(sessId)

		self.transition('ok')

	def _stateTERMINATE(self):
		self.deleteAllSessions()
		self.monitor.stop()
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)
		self.transition('ok')

	def connectInitiator(self, host, port, profileDict=None):
		if not profileDict:
			profileDict = self.profileDict
		client = TCPInitiatorSession(self.log, profileDict, (host, port), self)
		self.addSession(client)
		return client

	def close(self):
		self.stop()

class SessionMonitor(util.Monitor):
	"""A SessionMonitor monitors sessions and handles their behaviour
	   with respect to a SessionManager.
	"""
	def __init__(self, log, errEvent, timeout=10, name=None):
		self.log = log
		util.Monitor.__init__(self, errEvent, timeout, name)
		self.log.logmsg(logging.LOG_DEBUG, "Session monitor started.")
		self.log.logmsg(logging.LOG_DEBUG, "Started thread: %s" % self)

	def handleError(self, exc, obj):
		try:
			raise exc

		except TCPTerminalError, e:
			if isinstance(obj, TCPDataEnqueuer):
				self.log.logmsg(logging.LOG_DEBUG, "Terminating Session: %s" % exc)
				obj.session.transition('error')

			else:
				self.log.logmsg(logging.LOG_DEBUG, "Unhandled Terminal Error from %s: %s" % (obj, exc) )

		except Exception, e:
			self.log.logmsg(logging.LOG_DEBUG, "Unhandled Error from %s: %s" % (obj, exc) )

	def stop(self):
		self.log.logmsg(logging.LOG_DEBUG, "Stopped thread: %s" % self)
		util.Monitor.stop(self)
