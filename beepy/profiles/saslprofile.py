# $Id: saslprofile.py,v 1.1 2003/01/01 23:36:50 jpwarren Exp $
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
# SASLProfile is the base SASL profile class
# It should be inherited from to implement particular
# SASL mechanisms

import profile
from beepy.core import logging

import re
import base64

__profileClass__ = "SASLProfile"
uri = "http://iana.org/beep/SASL"

class SASLProfile(profile.Profile):
	""" This is an abstract class to provide the core SASL Profile API
	"""

	def __init__(self, log, session):
		"""__init__() is used to set up special SASL data such
		   as certificates, user dbases, etc.
		"""
		profile.Profile.__init__(self, log, session)
		self.authentid = None
		self.authid = None

	def decodeBlob(self, data):
		"""decodeBlob() extracts the data from the <blob> section of
		   the payload data and decodes it from base64.
		   It's really XML, but I don't think using a full parser
		   is warranted here.
		"""
		blobPattern = r'<blob>(.*)</blob>'
		blobRE = re.compile(blobPattern, re.IGNORECASE | re.DOTALL)

#		self.log.logmsg(logging.LOG_DEBUG, "decoding blob: %s" % data)
		match = re.search(blobRE, data)
		if match:
#			self.log.logmsg(logging.LOG_DEBUG, "match group: %s" % match.group(1))
			try:
				decoded_data = base64.decodestring(match.group(1))
				return decoded_data
			except Exception, e:
				raise SASLProfileException("bad SASL data: %s" % e)
		else:
			raise SASLProfileException("No blob to decode in datablock")

	def encodeBlob(self, data):
		"""encodeBlob() takes the data passed in and returns the appropriate
		<blob></blob> structure with base64 encoded data.
		"""
		blob = "<blob>"
		blob += base64.encodestring(data)
		blob += "</blob>"

		return blob

	def parseStatus(self, data):
		"""parseStatus() extracts the status code from the <blob> block
		"""
#		self.log.logmsg(logging.LOG_DEBUG, "parsing status: %s" % data)
		blobStatusPattern = '<blob\sstatus=[\'"](.*)[\'"]\s*/>'
		blobStatusRE = re.compile(blobStatusPattern, re.IGNORECASE)

		match = re.search(blobStatusRE, data)
		if match:
			return match.group(1)
		else:
			return None

	def parseError(self, data):
		"""parseError() extracts the error code from the <error> block
		"""
#		self.log.logmsg(logging.LOG_DEBUG, "parsing error: %s" % data)
		blobErrorPattern = '<error\scode=[\'"](.*)[\'"]\s*>(.*)</error>'
		blobErrorRE = re.compile(blobErrorPattern, re.IGNORECASE)

		match = re.search(blobErrorRE, data)
		if match:
			code = match.group(1)
			errormsg = match.group(2)
			return code,errormsg
		else:
			return None

class SASLProfileException(profile.ProfileException):
	def __init__(self, args):
		self.args = args