# $Id: constants.py,v 1.8 2004/09/28 01:19:20 jpwarren Exp $
# $Revision: 1.8 $
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
Constant definitions for BEEPy.
Invariant data is defined here as a single reference point
for common data used throughout BEEPy.

@version: $Revision: 1.8 $
@author: Justin Warren
"""

FrameTypes = [ 'data', 'seq' ]	# possible frame types

#Frame Header Keywords
DataFrameTypes = { 'MSG': 'MSG',
		'RPY': 'RPY',
		'ANS': 'ANS',
		'ERR': 'ERR',
		'NUL': 'NUL' }

MessageType = { 'MSG': 'MSG',
		'RPY': 'RPY',
		'ANS': 'ANS',
		'ERR': 'ERR',
		'NUL': 'NUL' }

MoreTypes = { 	'.': '.',
		'*': '*' }

# Values taken from RFC3080
MIN_CHANNEL = 0
MAX_CHANNEL = 2147483647
MIN_MSGNO = 0
MAX_MSGNO = 2147483647
MIN_SEQNO = 0
MAX_SEQNO = 4294967295L
MIN_SIZE = 0
MAX_SIZE = 2147483647
MIN_ANSNO = 0
MAX_ANSNO = 2147483647

# Values from RFC3081
MIN_ACKNO = 0
MAX_ACKNO = 4294967295L
MIN_WINDOWSIZE = 1
MAX_WINDOWSIZE = 2147483647

MIN_CHANNEL_WINDOW = 1

ReplyCodes = {  '200' : 'Success',
		'421' : 'Service Not Available',
		'450' : 'Requested Action Not Taken',
		'451' : 'Requested Action Aborted',
		'454' : 'Temporary Authentication Failure',
		'500' : 'General Syntax Error',
		'501' : 'Syntax Error In Parameters',
		'504' : 'Parameter Not Implemented',
		'530' : 'Authentication Required',
		'534' : 'Authentication Mechanism Insufficient',
		'535' : 'Authentication Failure',
		'537' : 'Action Not Authorised For User',
		'538' : 'Authentication Mechanism Requires Encryption',
		'550' : 'Requested Action Not Taken',
		'553' : 'Parameter Invalid',
		'554' : 'Transaction Failed' }

# The Channel finite state machine
CHANNEL_STOPPED = 0
CHANNEL_STARTING = 1
CHANNEL_ACTIVE = 2
CHANNEL_CLOSING = 3

# Default logging
DEFAULT_LOGFILE = None
DEFAULT_LOGLEVEL = 5
DEFAULT_LOGMSG_LEVEL = 5
LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

