# $Id: util.py,v 1.1 2003/01/06 07:20:14 jpwarren Exp $
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
# Some general utility classes used by BEEPy

import threading
import Queue

class StatusObject:
	STATUS_OK = 0
	STATUS_ERR = 1

	def __init__(self):
		self.status = self.STATUS_OK
		self.lastException = None
		self.errLock = threading.Lock()

	def setStatus(self, status, lastException = None):
		self.errLock.acquire()
		self.status = status
		self.lastException = lastException
		self.errLock.release()

	def getStatus(self):
		self.errLock.acquire()
		exc = self.lastException
		self.errLock.release()
		return exc

class LoopingThread(threading.Thread):
	"""A looping thread provides a handy thread subclass that
	   has standard methods of stopping a thread asynchronously
	   and a simple looping structure.
	"""

	def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
		self._stop = threading.Event()
		threading.Thread.__init__(self, group, target, name, args, kwargs)

	def run(self):
		while(1):
			if self._stop.isSet():
				break
			self.loop()

	def stop(self):
		self._stop.set()


	def loop(self):
		raise NotImplementedError

class Monitor(LoopingThread):
	"""Monitors other threads for error conditions
	"""
	# This really should be using a Condition to provide
	# locking in the case of multiple, simultaneous errors.
	# I'll get to it later.

	def __init__(self, errEvent, timeout=1, name=None):
		self.monitorEvent = errEvent
		self.timeout = timeout
		self.monitoredObjects = []
		LoopingThread.__init__(self, name=name)

	def startMonitoring(self, monitoredObj):
		"""Add an isMonitored object to my list of
		   monitored objects.
		"""
		# check object can be monitored
		if not isinstance(monitoredObj, isMonitored):
			raise TypeError, 'object is not a subclass of isMonitored'

		# check the isMonitored is using the correct
		# errEvent which is the only one I look after

		if self.monitorEvent != monitoredObj.ismonitoredEvent:
			raise AttributeError, 'object is not using my errEvent for signalling'


		self.monitoredObjects.append(monitoredObj)

	def stopMonitoring(self, monitoredObj):
		"""Remove object from the list of monitored objects
		"""
		try:
			self.monitoredObjects.remove(monitoredObj)
		except ValueError:
			pass

	def handleError(self, exc, obj):
		"""handleError is an abstract function for handling
		   whatever errors you might encounter.
		   Default behaviour is just to raise them
		"""
		raise exc

	def loop(self):
		self.monitorEvent.wait(self.timeout)
		# When we get an errEvent, one of our monitored
		# objects had an error, so find which one
		for obj in self.monitoredObjects:
			err = obj.getError()
			if err:
				print "DEBUG: Error in monitored object!"
				self.handleError(err, obj)
				obj.clearError()

	def stop(self):
		LoopingThread.stop(self)
		# wake up this thread so it will exit
		self.monitorEvent.set()

class isMonitored(LoopingThread):
	"""A WatchedLoopingThread is monitored for error conditions
	   by a Monitor
	"""

	def __init__(self, monitorEvent, name=None):
		self.ismonitoredEvent = monitorEvent
		self.statusObj = StatusObject()
		LoopingThread.__init__(self, name=name)

	def setError(self, exc):
		"""setError() sets my error condition to the
		   exception that is passed in.
		"""
		self.statusObj.setStatus(StatusObject.STATUS_ERR, exc)
		self.ismonitoredEvent.set()

	def getError(self):
		return self.statusObj.getStatus()

	def clearError(self):
		self.statusObj.setStatus(StatusObject.STATUS_OK)
		self.ismonitoredEvent.clear()

class DataEnqueuer(isMonitored):
	"""A DataEnqueuer reads data from some sort of data source
	   and puts it onto the provided Queue. Synchonisation
	   with a corresponding DataDequeuer is performed via
	   a shared Event which is passed in.
	"""

	def __init__(self, event, dataq, errEvent, name=None):
		"""event is a threading.Event to be used for synchronisation
		   dataq is a Queue used to put the data onto.
		"""
		isMonitored.__init__(self, errEvent, name)
		self.event = event
		self.dataq = dataq

	def loop(self):
		try:
			self.enqueueData()
			self.event.set()
		except Exception, e:
			self.setError(e)

	def enqueueData(self):
		raise NotImplementedError

	def stop(self):
		isMonitored.stop(self)
		# set the event so that my wait() wakes up and
		# I stop more or less immediately.
		self.event.set()

class DataDequeuer(isMonitored):
	"""A DataDeQueuer gets data from the provided Queue and
	   does something with it. It synchronises with an associated
	   DataQueuer via the provided Event
	"""

	def __init__(self, event, dataq, errEvent, timeout=1, name=None):
		"""event is a threading.Event to be used for synchronisation
		   dataq is a Queue used to put the data onto.
		"""
		isMonitored.__init__(self, errEvent, name)
		self.event = event
		self.dataq = dataq
		self.timeout = timeout

	def loop(self):
		if not self.event.isSet():
			self.event.wait(self.timeout)
		#	print "%s: Event triggered! Data available!" % self
		try:
			if not self.dequeueData():
		#		print "%s: no more data." % self
				self.event.clear()

		except Exception, e:
			self.setError(e)

	def dequeueData(self):
		raise NotImplementedError

	def stop(self):
		isMonitored.stop(self)
		# set the event so that my wait() wakes up and
		# I stop more or less immediately.
		self.event.set()
