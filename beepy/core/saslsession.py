# $Id: saslsession.py,v 1.3 2003/12/09 02:37:30 jpwarren Exp $
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

from beepy.core.session import Session, SessionException

import logging
from beepy.core import debug
log = logging.getLogger('SASLSession')

class SASLSession(Session):

    def __init__(self):
        self.userid = None
        self.authentid = None
        
        Session.__init__(self)

    def authenticationSucceeded(self):
        log.info('Authentication succeeded')

    def authenticationFailed(self, errorCode, errorReason):
        log.error('Authentication failed: [%s] %s' % (errorCode, errorReason) )
        raise SessionException('Authentication Failed')
        
    def useridRequested(self):
        """ This is a callback that should be overloaded in servers
        or client for when authentication information is required.
        """
        log.debug('userid requested')
        raise NotImplementedError('useridRequested must be defined')
    
    def authentidRequested(self):
        """ This is a callback that should be overloaded in servers
        or clients for when authentication information is required.
        """
        log.debug('authentid requested')
        raise NotImplementedError('authentidRequested must be defined')
