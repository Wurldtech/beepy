# $Id: debug.py,v 1.2 2004/01/15 05:41:13 jpwarren Exp $
# $Revision: 1.2 $
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

"""
Customised debugging code.

@version: $Revision: 1.2 $
@author: Justin Warren
"""

import logging
import os
import sys

class MyLogger(logging.Logger):
    """
    MyLogger is a customised logging class used to debug BEEPy.
    """

    def __init__(self, name):
        pid = os.getpid()

        ## Check to see if we're using the twisted logger
        ## and don't log as verbosely if we are, since the twisted
        ## logger already spews an imperial bucketload of information.
        ## We prefer the metric system, but what can you do.
        ## Those crazy Americans!
        if sys.modules.has_key('twisted.python.log'):
            FORMAT = "%(levelname)s: %(name)s: %(message)s"
        else:
            FORMAT = "%(asctime)s [" + str(pid) + "] %(levelname)8s: %(name)s: %(message)s"
        level = logging.DEBUG
        logging.Logger.__init__(self, name, level)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(FORMAT)
        handler.setFormatter(formatter)
        self.addHandler(handler)
        return

logging.setLoggerClass(MyLogger)
log = logging.getLogger('default')
