# $Id: saslanonymousprofile.py,v 1.3 2002/08/08 06:52:56 jpwarren Exp $
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
# SASLProfile is the base SASL profile class
# It should be inherited from to implement particular
# SASL mechanisms

import profile
from beep.core import logging

import re
import base64

__profileClass__ = "SASL_ANONYMOUS_Profile"

class SASL_ANONYMOUS_Profile:
	data = []
	status = ''
	authentid = ''
	userid = ''
	locked = 0

	def __init__(self, data, status=None, authenid=None, userid=None, locked=0):
		try:
			self.data = self.decodeBlob(data)
		except SASLProfileException:
			try:
				self.data = data
				self.status = self.parseStatus(data)
			except SASLProfileException:
				raise SASLProfileException("Invalid blob format in data")

class SASLProfile(profile.Profile):
	""" This is an abstract class to provide the core SASL Profile API
	"""
	uri = "http://www.eigenmagic.com/beep/SASL"

	def doProcessing(self):
		"""doProcessing() isn't defined by the abstract SASLProfile.
		   Make sure you overload this in the subclass.
		"""
		raise NotImplementedError

	def decodeBlob(self, data):
		"""decodeBlob() extracts the data from the <blob> section of
		   the payload data and decodes it from base64.
		   It's really XML, but I don't think using a full parser
		   is warranted here.
		"""
		blobPattern = r'<blob>.*</blob>'
		blobRE = re.compile(blobPattern)

		match = re.search(blobRE, data)
		if match:
			decoded_data = base64.decodestring(match)
			return decoded_data
		else:
			raise SASLProfileException("No blob to decode in datablock")

	def parseStatus(self, data):
		"""parseStatus() extracts the status code from the <blob> block
		"""
		blobStatusPattern = r'<blob\sstatus=['"](.*)['"]\s/>'
		blobStatusRE = re.compile(blobStatusPattern)

		match = re.search(blobStatusRE, data)
		if match:
			return match.group(1)
		else:
			raise SASLProfileException("No status in blob")

class SASLProfileException(profile.ProfileException):
	def __init__(self, args):
		self.args = args
