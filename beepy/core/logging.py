# $Id: logging.py,v 1.3 2003/01/08 05:38:11 jpwarren Exp $
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
# BEEP logging class
#
# Defines standard beep library logging functions
#
# Logs to STDERR by default, or to a logfile if defined

import sys
import errors
import time
import threading

import constants

""" This class provides a method for centralised logging throughout
    the library. Code throughout the beep library will log based on 
    the setting for the loglevel in this class. A single Log
    instance should be created at started and passed to all classes
    that require access to logging.
"""

LOG_CRIT = 0		# Critical internal beep library error
LOG_ERR = 1		# A handled error condition occurred
LOG_WARN = 2		# An error occurred, but it's not a big deal
LOG_NOTICE = 3		# Something happened that you should probably know about
LOG_INFO = 4		# Something happened that might be interesting
LOG_DEBUG = 5		# Loads of stuff about how the internal processing is done.

class Log:

	def __init__(self, filename=constants.DEFAULT_LOGFILE, loglevel=constants.DEFAULT_LOGLEVEL, prefix=''):
		self.mutex = threading.Lock()
		# Attempt to open the logfile for writing
		if filename:
			try:
				self.logfile = open(logfile, "w+")
				self.filename = filename
				print "logfile %s opened successfully." % filename
			except:
				raise LogException("Cannot open logfile: %s" % filename)
		else:
			self.logfile = sys.stderr
			self.filename = 'STDERR'

		self.loglevel = loglevel
		self.prefix = prefix

	def logmsg(self, msglevel, *msgs ):
		if self.loglevel == -1:
			return

		if msglevel <= self.loglevel:
			stamp = time.strftime(constants.LOG_TIME_FORMAT, time.localtime())

			self.mutex.acquire()
			self.logfile.write(stamp)
			self.logfile.write(": [")
			self.logfile.write(str(msglevel))
			self.logfile.write("]: ")
			self.logfile.write(self.prefix)
			for string in msgs:
				try:
					self.logfile.write(string)
				except Exception, e:
					raise LogException("Exception logging message: %s" % e)

			self.logfile.write("\n")
			self.logfile.flush()
			self.mutex.release()

class LogException(errors.BEEPException):
	def __init__(self, args=None):
		self.args = args


