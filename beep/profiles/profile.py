# $Id: profile.py,v 1.8 2002/10/07 05:52:04 jpwarren Exp $
# $Revision: 1.8 $
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
# Profile objects
# This is an abstract class that should be inherited from to implement
# an actual profile.

from beep.core import constants
from beep.core import errors
from beep.core import logging

# All payloads are expected to be MIME structured, so we include the
# library here.
import StringIO
import mimetools, mimetypes, MimeWriter

# This is a special variable. It is used to dynamically instanciate
# the Profile by the Session (actually, the BEEPManagementProfile does it).
# Set this in your subclasses.
__profileClass__ = "Profile"

class Profile:
#	log = None		# link into logging system
#	channel = None		# Channel this profile is bound to
#	session = None		# Session this profile connects to via channel
#	type = None		# Track the current message's MIME type
#	encoding = None		# track the current message's encoding

	# Create a new Profile object
	def __init__(self, log, session, profileInit=None):
		"""Subclasses of Profile should call this method from their
		__init__() methods.
		"""
		self.log = log
		self.session = session
		self.channel = None
		self.type = None
		self.encoding = None

	def setChannel(self, channel):
		"""setChannel() binds this Profile to the Channel
		it is processing. If this method is not called to set
		the Channel for the Profile, it will be unable to
		processMessages()
		"""
		self.channel = channel
		self.channel.transition(constants.CHANNEL_ACTIVE)

	def doProcessing(self):
		"""doProcessing() is where the real guts of the
		message processing takes place, so subclasses should
		implement this method to do work.
		"""
		pass

	def processMessages(self):
		if not self.channel:
			raise ProfileException("Profile not bound to Channel")

		else:
			try:
				self.doProcessing()

			except TuningReset:
				raise

			except Exception, e:
				raise ProfileException("Unmanaged exception in profile %s: %s" % (self, e) )

	def mimeDecode(self, payload):
		"""mimeDecode is a convenience function used to help
		   make life easier for profile programmers, like me.
		   It takes the payload and extracts the data from
		   the headers.
		"""
		self.type = constants.DEFAULT_MIME_CONTENT_TYPE
		instring = StringIO.StringIO(payload)
		headers = mimetools.Message(instring)
		msgtype = headers.gettype()
		if headers.getmaintype() == "multipart":
			raise ProfileException("cannot handle multipart MIME yet")
		else:
			self.type = msgtype

		msgencoding = headers.getencoding()
		# only support base64 or binary encodings, default is binary
		outstring = StringIO.StringIO()
		if msgencoding:
			self.encoding = msgencoding

		if self.encoding == "base64":
			mimetools.decode(instring, outstring, self.encoding)
		else:
			outstring = instring

		msg = ''
		msg = outstring.read()

		return msg

	def mimeEncode(self, payload, contentType=constants.DEFAULT_MIME_CONTENT_TYPE, encoding=None):
		"""mimeEncode is a convenience function used to help
		   make life easier for profile programmers, like me.
		   It takes a given payload and adds MIME headers to it.
		   Note: The separation between the MIME headers is a
		   single newline '\n', not '\r\n'. Not sure why, but MimeWriter
		   is doing it for some reason.
		"""
		outstring = StringIO.StringIO()
		writer = MimeWriter.MimeWriter(outstring)
		writer.startbody(contentType)
		if encoding:
			writer.addheader("Content-transfer-encoding", encoding)
		writer.flushheaders()
		outstring.write(payload)
		# convert StringIO to string
		# potential buffer overflow here
		outstring.seek(0)
		msg = outstring.read()

		if len(msg) > constants.MAX_PAYLOAD_SIZE:
			raise ProfileException("payload is large and should be fragmented")

		return msg

class ProfileException(errors.BEEPException):
	def __init__(self, args):
		self.args = args

class TuningReset(ProfileException):
	def __init__(self, args):
		self.args = args

# This class is used to manage profiles that are known by
# an application. It gets passed in to a Session so each Session
# knows what profiles it knows and how to bind them to Channels
# This is really just a wrapper around a dictionary that contains
# a uri to python module mapping.
#
# It ends up containing a whole swag of stuff that can be played
# with dynamically. (Yay!)
class ProfileDict:

	def __init__(self, profileList=None):
		self._profiles = {}
		if profileList:
			for profile in profileList:
				self.profiles[profile.uri] = profile

	# Convenience function to get profiles out
	# 
	def __getitem__(self, uri):
		return self._profiles[uri]

	# Add a profile map to the dictionary
	# uri is the uri used to refer to this profile
	# module is the path to the module for dynamic loading
	def __setitem__(self, uri, module):
		self._profiles[uri] = module

	def __delitem__(self, uri):
		del self._profiles[uri]

	# Get a list of URIs of supported profiles
	def getURIList(self):
		if self._profiles:
			return self._profiles.keys()

class ProfileDictException(errors.BEEPException):
	def __init__(self, args):
		self.args = args
