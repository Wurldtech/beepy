# $Id: createTLSKeyfile.py,v 1.6 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.6 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
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
