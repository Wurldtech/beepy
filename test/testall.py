# $Id: testall.py,v 1.4 2004/01/15 05:41:13 jpwarren Exp $
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
#
# The top level testing class.
# This is used for testing various aspects of the beepy library
# Happily snarfed from http://diveintopython/ after seeing it
# in the code for py-beep

import sys, os, re, unittest

moduleNames = [ 'test_creator',
                'test_parser',
                'test_parser_creator',
                'test_listener',
                'test_framing',
                'test_initiator',
                'test_echoprofile',
                'test_saslanonymousprofile',
                'test_saslotpprofile',
              ]

## Check to see if TLS/SSL is available.
## This is only supported if you have twisted at this point,
## so if you don't, we skip the test.
try:
    import beepy.transports.tls

    moduleNames.append('test_tlsprofile')
    
except:
    print "TLS not available, skipping TLS tests..."

def unitTest():
    """ Load tests defined in modules above and execute them
    """
    modules = map(__import__, moduleNames)
    load = unittest.defaultTestLoader.loadTestsFromModule
    return unittest.TestSuite(map(load, modules))

if __name__ == '__main__':
    unittest.main(defaultTest='unitTest')
