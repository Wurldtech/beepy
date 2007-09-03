# $Id: tlssession.py,v 1.7 2007/09/03 03:20:12 jpwarren Exp $
# $Revision: 1.7 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
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
