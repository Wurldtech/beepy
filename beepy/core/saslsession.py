# $Id: saslsession.py,v 1.9 2004/09/28 01:19:20 jpwarren Exp $
# $Revision: 1.9 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (c) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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
Specialised classes for SASL operation of sessions.

Adds a userid and an authentid to a standard session as well
as some methods to query these variables by applications.

You would use these classes when you're writing something that
makes use of SASL authentication.

@version: $Revision: 1.9 $
@author: Justin Warren
"""
#import logging
from debug import log
#log = logging.getLogger('beepy')

from beepy.core.session import Session, Listener, Initiator, SessionException

class SASLSession(Session):
    """
    A base Session subclass used for SASL sessions.
    """
    userid = None
    authentid = None

#    def __init__(self):
#        self.userid = None
#        self.authentid = None
#        
#        Session.__init__(self)

    def authenticationSucceeded(self):
        log.info('Server authentication succeeded')
        log.debug('my credentials: authentid: %s, userid: %s' % (self.authentid, self.userid))

    def authenticationFailed(self, errorCode, errorReason):
        log.error('Authentication failed: [%s] %s' % (errorCode, errorReason) )
        raise SessionException('Authentication Failed')
        
    def useridRequested(self):
        """
        This is a callback that should be overloaded in servers
        or client for when authentication information is required.
        """
        log.debug('userid requested')
        raise NotImplementedError('useridRequested must be defined')
    
    def authentidRequested(self):
        """
        This is a callback that should be overloaded in servers
        or clients for when authentication information is required.
        """
        log.debug('authentid requested')
        raise NotImplementedError('authentidRequested must be defined')

class SASLListener(Listener, SASLSession):
    """ A SASL capable Listener
    """

class SASLInitiator(Initiator, SASLSession):
    """ A SASL capable Initiator
    """
