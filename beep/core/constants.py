# $Id: constants.py,v 1.4 2002/08/13 06:29:21 jpwarren Exp $
# $Revision: 1.4 $
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

FrameTypes = [ 'data', 'seq' ]	# possible frame types

#Frame Header Keywords
DataFrameTypes = { 'MSG': 'MSG',
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
START_WINDOWSIZE = 4096

# These sizing values should be tuned to something reasonable.

MAX_INBUF = 1024			# Maximum input bytes at a time
MAX_OUTBUF = 1024			# Maximum output bytes at a time

MAX_INPUT_QUEUE_SIZE = 1024		# Max inbound queue size
MAX_OUTPUT_QUEUE_SIZE = 1024		# Max outbound queue size

MAX_FRAME_SIZE = 1024 * 16			# Upper bound for size of frames accepted
FRAGMENT_FRAME_SIZE = MAX_FRAME_SIZE		# Size frames may get to before payload is fragmented
MAX_HEADER_SIZE = 62		# Calculated maximum header size
TRAILER_SIZE = 5
MAX_PAYLOAD_SIZE = MAX_FRAME_SIZE - MAX_HEADER_SIZE - TRAILER_SIZE

ReplyCodes = { '200' : 'Success',
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

DEFAULT_MIME_CONTENT_TYPE = "application/octet-stream"
DEFAULT_MIME_TRANSFER_ENCODING = "binary"

# The Session finite state machine
SESSION_UNINITIALIZED = 0
SESSION_INITIALIZED = 1
SESSION_ACTIVE = 2
SESSION_PROCESSING = 3
SESSION_CLOSING = 4
SESSION_TUNING = 5
SESSION_CLOSED = 6
SESSION_EXITING = 7
SESSION_EXITED = 8

# The Channel finite state machine
CHANNEL_STOPPED = 0
CHANNEL_STARTING = 1
CHANNEL_ACTIVE = 2
CHANNEL_CLOSING = 3
