# $Id: echobulkclient.py,v 1.4 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.4 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

"""
This file defines a client for testing multi-channel priorities and
SEQ frames. The idea is that I need some way to test out the efficiency
of the window sizing mechanisms within the TCP transport that comes with
