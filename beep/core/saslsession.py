# $Id: saslsession.py,v 1.2 2002/08/22 05:03:35 jpwarren Exp $
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

import session

class SASLSession(session.Session):
#	authentid = ''
#	userid = ''

	def __init__(self, log, profileDict, authentid, userid=None):
		self.authentid = authentid
		if userid:
			self.userid = userid
		else:
			self.userid = authentid
		session.Session.__init__(self, log, profileDict)

class SASLListenerSession(session.ListenerSession, SASLSession):

	def __init__(self, log, profileDict, authentid, userid=None):
		SASLSession.__init__(self, log, profileDict, authentid, userid)

		self.nextChannelNum = 2

class SASLInitiatorSession(session.InitiatorSession, SASLSession):
	def __init__(self, log, profileDict, authentid, userid=None):
		SASLSession.__init__(self, log, profileDict, authentid, userid)

		self.nextChannelNum = 1

class SASLSessionException(session.SessionException):
	def __init__(self, args=None):
		self.args = args
