# $Id: errors.py,v 1.2 2004/01/15 05:41:13 jpwarren Exp $
# $Revision
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
#

"""
Customised exceptions used throughout BEEPy.

This code is fairly redundant, but allows all exceptions
in BEEPy to inherit from a common superclass.

@version: $Revision: 1.2 $
@author: Justin Warren
"""

import exceptions

class BEEPException(exceptions.Exception):
	def __init__(self, args=None):
		self.args = args

	def __repr__(self):
		return `self.args`
