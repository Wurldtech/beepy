# $Id: errors.py,v 1.5 2007/09/03 03:20:03 jpwarren Exp $
# $Revision
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

"""
Customised exceptions used throughout BEEPy.

This code is fairly redundant, but allows all exceptions
in BEEPy to inherit from a common superclass.

@version: $Revision: 1.5 $
@author: Justin Warren
"""

import exceptions

class BEEPException(exceptions.Exception):
	def __init__(self, args=None):
		self.args = args

	def __repr__(self):
		return `self.args`
