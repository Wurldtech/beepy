# $Id: debug.py,v 1.8 2007/07/28 01:45:22 jpwarren Exp $
# $Revision: 1.8 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>

"""
Customised debugging code.

@version: $Revision: 1.8 $
@author: Justin Warren
"""

import logging
import os
import sys

class MyLogger(logging.Logger):
    """
