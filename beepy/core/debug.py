# $Id: debug.py,v 1.1 2003/12/08 03:25:30 jpwarren Exp $
# $Revision: 1.1 $
#
# Customised logging stuff

import logging
import os
import sys

class MyLogger(logging.Logger):

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
