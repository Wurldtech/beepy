# $Id: tlssession.py,v 1.2 2003/01/09 00:20:53 jpwarren Exp $
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

class TLSSession(session.Session):
	"""A TLSSession is a specialised type of Session
	"""

class TLSListener(session.Listener, TLSSession):
	"""A TLSListener is a Listener that uses
	   TLS for transport security.
	"""


class TLSInitiator(session.Initiator, TLSSession):
	"""A TLSInitiator is an Initiator that uses
	   TLS for transport security.
	"""

class TLSSessionException(session.SessionException):
	def __init__(self, args=None):
		self.args = args
