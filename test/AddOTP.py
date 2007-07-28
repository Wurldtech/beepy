# $Id: AddOTP.py,v 1.8 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.8 $

import sys
sys.path.append('../')

from beepy.profiles import saslotpprofile

if __name__ != '__main__':
    print "Do not import this module."

generator = saslotpprofile.OTPGenerator()

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

