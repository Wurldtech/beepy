# $Id: createTLSTestKeyCerts.py,v 1.2 2004/01/15 05:41:13 jpwarren Exp $
# $Revision: 1.2 $
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
# This script creates the test keys and certificates for use in TLS
# testing. Also gives an example of how to do this yourself for your
# own keys.

if __name__ != '__main__':
    print "Do not import this module."
    
from OpenSSL import crypto

def createKeyPair():
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 1024)
    return key

def createCertReq(pkey, digest="md5", **name):
    req = crypto.X509Req()
    subj = req.get_subject()

    [ setattr(subj, key, value) for (key,value) in name.items() ]

    req.set_pubkey(pkey)
    req.sign(pkey, digest)

    return req

def createCertificate(req, (issuerCert, issuerKey), serial=0, notBefore=0, notAfter=(3600*24*365*5), digest="md5"):

    cert = crypto.X509()
    cert.set_serial_number(serial)
    cert.gmtime_adj_notBefore(notBefore)
    cert.gmtime_adj_notAfter(notAfter)
    cert.set_issuer(issuerCert.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(issuerKey, digest)
    return cert

## First, generate a certificate authority's key and cert
## This is a self-signed key

caKey = createKeyPair()
caReq = createCertReq(caKey, CN='beepy CA')
caCert = createCertificate( caReq, (caReq, caKey) )

## Create a server key and cert
serverKey = createKeyPair()
serverReq = createCertReq(serverKey, CN='beepy Server')
serverCert = createCertificate( serverReq, (caCert, caKey) )

## Create a client key and cert
clientKey = createKeyPair()
clientReq = createCertReq(clientKey, CN='beepy Client')
clientCert = createCertificate( clientReq, (caCert, caKey) )

## Save all the keys and certs to disk

for (key,value) in (
    { 'caKey': caKey, 'serverKey': serverKey, 'clientKey': clientKey }.items()
    ):
    fp = open('%s.pem' % key, 'w')
    fp.write( crypto.dump_privatekey( crypto.FILETYPE_PEM, value ) )
    fp.close()

for (key, value) in (
    { 'caCert': caCert, 'serverCert': serverCert, 'clientCert': clientCert }.items()
    ):
    fp = open('%s.pem' % key, 'w')
    fp.write( crypto.dump_certificate( crypto.FILETYPE_PEM, value ) )
    fp.close()

