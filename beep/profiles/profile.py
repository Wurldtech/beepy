# $Id: profile.py,v 1.1 2002/08/02 00:24:37 jpwarren Exp $
# $Revision: 1.1 $
#
# Profile objects
# This is an abstract class that should be inherited from to implement
# an actual profile.

from beep.core import constants
from beep.core import errors

# This is a special variable. It is used to dynamically instanciate
# the Profile by the Session (actually, the BEEPManagementProfile does it).
# Set this in your subclasses.
__profileClass__ = "Profile"

class Profile:
	log = None		# link into logging system
	uri = None		# URI identifying this profile, used by subclasses
	channel = None		# Channel this profile is bound to
	session = None		# Session this profile connects to via channel

	# Create a new Profile object
	def __init__(self, log, session):
		"""Subclasses of Profile should call this method from their
		__init__() methods.
		"""
		self.log = log
		self.session = session

	def setChannel(self, channel):
		"""setChannel() binds this Profile to the Channel
		it is processing. If this method is not called to set
		the Channel for the Profile, it will be unable to
		processMessages()
		"""
		self.channel = channel
		print "channel state:", self.channel.state
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
			self.doProcessing()

class ProfileException(errors.BEEPException):
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

	_profiles = None

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
