# $Id: createTLSKeyfile.py,v 1.2 2003/01/30 09:24:30 jpwarren Exp $
# $Revision: 1.2 $
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
# This script creates keyfiles for use by the test of the TLSProfile

import sys
import POW

if __name__ != '__main__':
	print "Do not import this module."

# Default is to use rsa keys



privateFile = open('TLSprivate.key', 'w')
publicFile = open('TLSpublic.key', 'w')

passphrase = 'TeSt'

md5 = POW.Digest( POW.MD5_DIGEST )
md5.update( passphrase )
password = md5.digest()

rsa = POW.Asymmetric( POW.RSA_CIPHER, 1024 )
privateFile.write( rsa.pemWrite( POW.RSA_PRIVATE_KEY, POW.DES_EDE_CFB, password ) )
publicFile.write( rsa.pemWrite( POW.RSA_PUBLIC_KEY ) )

privateFile.close()
publicFile.close()
