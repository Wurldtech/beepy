# $Id: echoprofile.py,v 1.1 2002/08/02 00:24:38 jpwarren Exp $
# $Revision: 1.1 $
#
# EchoProfile implements an example profile that simply
# echoes back whatever the content of a frame is.
# It sends a Reply to each Message it receives.

import profile
from beep.core import logging

__profileClass__ = "EchoProfile"

class EchoProfile(profile.Profile):
	uri = "http://www.eigenmagic.com/beep/ECHO"

	def doProcessing(self):
		theframe = self.channel.recv()
		if theframe:
			self.log.logmsg(logging.LOG_DEBUG, "EchoProfile: processing frame: %s" % theframe)
			try:
				if theframe.isMSG():
					self.channel.sendReply(theframe.msgno, theframe.payload)
			except Exception, e:
				raise ProfileException("Exception echoing: %s" % e)
