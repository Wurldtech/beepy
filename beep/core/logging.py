# $Id: logging.py,v 1.2 2002/08/02 03:36:41 jpwarren Exp $
# $Revision: 1.2 $
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

""" This class provides a method for centralised logging throughout
    the library. Code throughout the beep library will log based on 
    the setting for the debuglevel in this class. A single Log
    instance should be created at started and passed to all classes
    that require access to logging.
"""

LOG_CRIT = 0		# Critical internal beep library error
LOG_ERR = 1		# A handled error condition occurred
LOG_WARN = 2		# An error occurred, but it's not a big deal
LOG_NOTICE = 3		# Something happened that you should probably look at
LOG_INFO = 4		# Something happened that might be interesting
LOG_DEBUG = 5		# Loads of stuff about how the internal processing
			# is done.

class Log:
	log = None			# File for logfile
	logfile = ''			# String for path to logfile
#	debuglevel = LOG_ERR		# Default log level is 1
	debuglevel = LOG_DEBUG		

	def __init__(self, logfile=None):
		# Attempt to open the logfile for writing
		if logfile:
			try:
				self.log = open(logfile, "w")
			except:
				raise LogException("Cannot open logfile: %s" % logfile)
			if log:
				self.logfile = logfile
		else:
			self.log = sys.stderr
			self.logfile = 'STDERR'

	def logmsg(self, msglevel, *msgs):
		if msglevel <= self.debuglevel:
			stamp = time.asctime(time.localtime())
			self.log.write(stamp)
			self.log.write(": [")
			self.log.write(str(msglevel))
			self.log.write("]: ")
			for string in msgs:
				try:
					self.log.write(string)
				except Exception, e:
					raise LogException("Exception logging message: %s" % e)
			self.log.write("\n")

class LogException(errors.BEEPException):
	def __init__(self, args=None):
		self.args = args

