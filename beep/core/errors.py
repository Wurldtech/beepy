# $Id: errors.py,v 1.1 2002/08/02 00:24:27 jpwarren Exp $
# $Revision
#
# Exceptions used by beepy BEEP core

import exceptions

class BEEPException(exceptions.Exception):
	def __init__(self, args=None):
		self.args = args
