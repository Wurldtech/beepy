# $Id: AddOTP.py,v 1.4 2003/01/07 07:39:59 jpwarren Exp $
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

import sys

try:
	from beepy.core import logging
	from beepy.profiles import saslotpprofile
except ImportError:
	sys.path.append('../')
	from beepy.core import logging
	from beepy.profiles import saslotpprofile

import dummyclient

if __name__ != '__main__':
	print "Do not import this module."

log = logging.Log()
#	log.loglevel = logging.LOG_DEBUG

generator = saslotpprofile.OTPGenerator(log)

#generator.promptAndGenerate()
username = 'justin'
passphrase = 'This is a test.'
seed = 'TeSt'
algo = 'md5'
sequence = 99

passhash = generator.createOTP(username, algo, seed, passphrase, sequence)

print "One Time Password is: %s" % generator.convertBytesToHex(passhash)
words = generator.convertBytesToWords(passhash)
print "  As words: %s" % words

