# $Id: createTLSCertfile.py,v 1.1 2003/01/04 00:10:33 jpwarren Exp $
# $Revision: 1.1 $
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
# This script creates a certificate file for use by the TLSProfile

import POW
import POW.pkix
import time

if __name__ != '__main__':
	print "Do not import this module."

# Default is to use rsa keys

privateFile = open('TLSprivate.key', 'r')
publicFile = open('TLSpublic.key', 'r')
certFile = open('TLScert.pem', 'w')

passphrase = 'TeSt'
md5 = POW.Digest( POW.MD5_DIGEST )
md5.update( passphrase )
password = md5.digest()

publicKey = POW.pemRead(POW.RSA_PUBLIC_KEY, publicFile.read())
privateKey = POW.pemRead(POW.RSA_PRIVATE_KEY, privateFile.read(), password)

c = POW.X509()

# Configure the certificate information
name = [ 
	['C', 'AU'], 
	['ST', 'Victoria'],
	['O', 'eigenmagic'],
	['CU', 'Justin Warren'],
	]

#c.setIssuer( name )
#c.setSubject( name )
c.setSerial(0)

# Expiry information
t1 = POW.pkix.time2utc( time.time() )
t2 = POW.pkix.time2utc( time.time() + 60*60*24*365 )
c.setNotBefore(t1)
c.setNotAfter(t2)

c.setPublicKey(publicKey)
c.sign(privateKey)

certFile.write( c.pemWrite() )

privateFile.close()
publicFile.close()
certFile.close()

