# $Id: tcp.py,v 1.9 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.9 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

#import logging
from beepy.core.debug import log
#log = logging.getLogger('beepy')

from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, ServerFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.error import ConnectionDone, ConnectionLost
from twisted.protocols.basic import LineReceiver

import re

import traceback

from beepy.core.session import Session, Listener, Initiator, SessionException
from beepy.core.session import TUNING
from beepy.profiles import profile
from beepy.core import constants
from beepy.core import frame
from beepy.core import errors
from beepy.core import debug
from beepy.core.message import Message
from beepy.core.channel import ChannelException

class SEQBuffer:
    """
    A SEQ buffer is a data object that holds the current
    state of a channel buffer. It is used by SEQ frame
    processing to tune window sizes and queue pending
    data, if any.
    """
    STARTING_WINDOWSIZE = 4096
#    STARTING_WINDOWSIZE = 32
    MAX_WINDOWSIZE = 10 * STARTING_WINDOWSIZE
    MIN_WINDOWSIZE = 1

    ## This value determines the effect of a change in
    ## priority. Increasing the priority by one will add
    ## this amount to the windowsize, and a decrease will reduce it.
    PRIORITY_INCREMENT = STARTING_WINDOWSIZE / 2
    
    def __init__(self, channelnum):
        self.channelnum = channelnum

        ## The amount of space still available for this channel
        ## at the remote end.
        self.availspace = self.STARTING_WINDOWSIZE

        ## My window size for this channel
        self.windowsize = self.STARTING_WINDOWSIZE

        self.databuf = []
        self.cb = None

#        log.debug('created SEQBuffer for channel %d' % channelnum)

    def __str__(self):
        return 'SEQBuffer: %d %d %d (%s) %s' % (self.channelnum, self.windowsize, self.availspace, self.cb, self.databuf) 
        

