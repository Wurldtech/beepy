# $Id: tlssession.py,v 1.4 2004/01/15 05:41:13 jpwarren Exp $
# $Revision: 1.4 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (C) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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

"""
Specialised Session subclasses for TLS capabilities.

These don't do much except add some class structure to
BEEPy that is used at the transport layer. Some refactoring
of code may be required to neaten up the inheritence,
but it appears to be functional.
"""
import session

class TLSSession(session.Session):
	"""
	A TLSSession is a specialised type of Session
	used for TLS over a transport.
	"""

class TLSListener(session.Listener, TLSSession):
	"""
	A TLSListener is a Listener that uses
	TLS for transport security.
	"""

class TLSInitiator(session.Initiator, TLSSession):
	"""
	A TLSInitiator is an Initiator that uses
	TLS for transport security.
	"""

class TLSSessionException(session.SessionException):
	def __init__(self, args=None):
		self.args = args
