# $Id: createTLSKeyfile.py,v 1.5 2004/09/28 01:19:21 jpwarren Exp $
# $Revision: 1.5 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (c) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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

if __name__ != '__main__':
    print "Do not import this module."

import sys

## This is here so that we can test with two different
## SSL libraries. I was using POW, which uses M2Crypto and
## appears to be a bit complicated, and hard to install.
## I now use pyOpenSSL, which looks more direct and nicer.
powmode = 0

privateFile = open('TLSprivate.key', 'w')
publicFile = open('TLSpublic.key', 'w')
passphrase = 'TeSt'

if powmode:
    import POW

    md5 = POW.Digest( POW.MD5_DIGEST )
    md5.update( passphrase )
    password = md5.digest()

    rsa = POW.Asymmetric( POW.RSA_CIPHER, 1024 )
    privateFile.write( rsa.pemWrite( POW.RSA_PRIVATE_KEY, POW.DES_EDE_CFB, password ) )
    publicFile.write( rsa.pemWrite( POW.RSA_PUBLIC_KEY ) )

else:

    from OpenSSL import crypto

    rsa = crypto.PKey()
    rsa.generate_key(crypto.TYPE_RSA, 1024)

    privateFile.write( crypto.dump_privatekey( crypto.FILETYPE_PEM, rsa ) )
#    publicFile.write( crypto.dump_RSAPublicKey( crypto.FILETYPE_PEM, rsa ) )    

privateFile.close()
publicFile.close()
