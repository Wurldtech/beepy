# $Id: testall.py,v 1.12 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.12 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#
#
# The top level testing class.
# This is used for testing various aspects of the beepy library
# Happily snarfed from http://diveintopython/ after seeing it
# in the code for py-beep

import sys, os, re, unittest

sys.path.append('..')

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
    
except ImportError:
    print "TLS not available, skipping TLS tests..."

def unitTest():
    """ Load tests defined in modules above and execute them
    """
    modules = map(__import__, moduleNames)
    load = unittest.defaultTestLoader.loadTestsFromModule
    return unittest.TestSuite(map(load, modules))

if __name__ == '__main__':
    unittest.main(defaultTest='unitTest')
