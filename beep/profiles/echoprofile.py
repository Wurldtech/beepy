# $Id: echoprofile.py,v 1.4 2002/10/07 05:52:04 jpwarren Exp $
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
#
# EchoProfile implements an example profile that simply
# echoes back whatever the content of a frame is.
# It sends a Reply to each Message it receives.

import profile
from beep.core import logging

__profileClass__ = "EchoProfile"
uri = "http://www.eigenmagic.com/beep/ECHO"

class EchoProfile(profile.Profile):

	def doProcessing(self):
		theframe = self.channel.recv()
		if theframe:
			self.log.logmsg(logging.LOG_DEBUG, "EchoProfile: processing frame: %s" % theframe)
			try:
				if theframe.isMSG():
					self.channel.sendReply(theframe.msgno, theframe.payload)

				if theframe.isRPY():
					self.channel.deallocateMsgno(theframe.msgno)

			except Exception, e:
				raise ProfileException("Exception echoing: %s" % e)
