# $Id: saslotpprofile.py,v 1.6 2004/01/06 04:18:08 jpwarren Exp $
# $Revision: 1.6 $
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
#
# This file implements the SASL OTP (One Time Password) mechanism as a profile
#

import saslprofile

from beepy.core import constants
from beepy.core import session
from profile import ProfileException, TerminalProfileException

import md5, sha
import re
import shelve
import struct
import string

import traceback
import logging
from beepy.core import debug
log = logging.getLogger('SASLOTPProfile')

__profileClass__ = "SASLOTPProfile"
uri = "http://iana.org/beep/SASL/OTP"

class SASLOTPProfile(saslprofile.SASLProfile):
    """A SASLOTPProfile is a SASL Profile that implements
       the OTP mechanism for one time password authentication.
    """

    def __init__(self, session, profileInit=None, init_callback=None):
        saslprofile.SASLProfile.__init__(self, session)
        self.tuning = 0
        self.algo = 'md5'
        self.sentchallenge = 0
        self.generator = OTPGenerator()
        self.passphrase = ''

    def processFrame(self, theframe):
        """All processFrame should do is move the session from
           non-authenticated to authenticated.
        """
        self.channel.deallocateMsgno(theframe.msgno)
        try:
            error = self.parseError(theframe.payload)
            if error:

                self.session.authenticationFailed(error[0], error[1])

            status = self.parseStatus(theframe.payload)
            if status:
                # do status code processing
                log.debug("status: %s" % status)

                if status == 'complete':
                    # Server completed authentication
                    self.session.authenticationSucceeded()

                elif status == 'abort':
                    # other end has aborted negotiation, so we reset
                    # to our initial state
                    self.session.authentid = None
                    self.session.userid = None

                elif status == 'continue':
                    log.debug("continue during authentication")

            else:
                blob = self.decodeBlob(theframe.payload)
                if blob:
                    log.debug("blob: %s" % blob)

                    # First we need to make sure we have the authentid
                    if not self.session.authentid:
                        log.debug("obtaining authentid...")
                        (self.session.authentid, self.session.userid) = self.splitAuth(blob)

                    # ok, here is where we need to do different things
                    # if we're a client or a server.

                    if isinstance(self.session, session.Listener):
                        # Do listener stuff
                        log.debug("OTP session is listener")
                        if self.sentchallenge:

                            # If we sent the challenge, this should be a
                            # response to the challenge, so do authentication

                            if self.authenticate(blob):

                                data = '<blob status="complete"/>'
                                self.channel.sendReply(theframe.msgno, data)
                                log.debug("Queued success message.")
                                self.session.authenticationSucceeded()

                            else:
                                # Authentication failed, respond appropriately.
                                log.info("OTP authentication failed.")
                                data = '<error code="535">Authentication Failed</error>'
                                self.channel.sendError(theframe.msgno, data)
                        else:
                            log.debug("sending OTP challenge...")
                            self.sendChallenge(theframe.msgno)

                    else:
                        # Do initiator stuff
                        log.debug("OTP session is initiator")
                        # If I'm an initiator, this blob should be a challenge, so
                        # I need to send my corresponding authentication.
#                        try:
                        self.respondToChallenge(blob, theframe)
#                        except:
#                            self.log.logmsg(logging.LOG_DEBUG, "raise worked")
#                            raise NotImplementedError('test')

                        log.debug("Finished responding to challenge")

        except Exception, e:
            traceback.print_exc()
            raise TerminalProfileException("Exception: %s" % e)
            

    def respondToChallenge(self, challenge, theframe):
        log.debug("Responding to challenge...")
        # The challenge string should be 4 tokens
        parts = string.split(challenge, ' ')
        if len(parts) != 4:
            raise ProfileException('Challenge (%s) has %d tokens, not 4' % (challenge, len(parts) ) )
        # First part is the algorithm
        algo = parts[0][4:]
        sequence = string.atoi(parts[1])

# FIXME: This is commented out so I can test the library.
        if not self.passphrase:
#            passphrase = self.getPassphraseFromUser()
            log.debug("No passphrase...")
            raise ProfileException("Passphrase not set")

        # The OTP to be used is calculated as N-1 where N is the sequence
        # sent as part of the challenge.
        passhash = self.generator.createHash(self.session.userid, algo, parts[2], self.passphrase, sequence-1)
        data = 'hex:' + self.generator.convertBytesToHex(passhash)
        data = self.encodeBlob(data)
        self.channel.sendMessage(data)

    def getPassphraseFromUser():
        """When you implement an application that makes use of this
           library, you will need to instanciate this class and
           implement this function to interface with the user to
           get the passphrase. It should return a string containing
           the passphrase.
        """
        raise NotImplementedError

    def authenticate(self, blob):
        log.debug("Authenticating client...")
        # convert to bytestring
        passhash = self.parseResponse(blob)
        return self.generator.authenticate(self.algo, self.session.userid, passhash)

    def parseResponse(self, data):
        """parseResponse() converts whatever we received from the
           other end into a bytestring. It needs to recognise
           word:, hex:, init-word: and init-hex formats.
        """
        # for now just string off the hex: at the beginning and
        # convert from hex to bytes
        data = data[4:]
        log.debug('parsing response: %s' % data)
        data = self.generator.convertHexToBytes(data)
        log.debug('converted to: %s' % data)
        return data

    def setAlgorithm(self, algo):
        if self.algo != 'md5' or 'sha':
            raise ProfileException('Hash algorithm not supported')
        self.algo = algo

    def setPassphrase(self, passphrase):
        self.passphrase = passphrase

    def sendAuth(self, passphrase, authentid, userid=None):
        """doAuthentication() performs the authentication phase of a OTP
           session in a single call.
        """
        self.passphrase = passphrase
        self.session.authentid = authentid
        if userid:
            self.session.userid = userid
        else:
            self.session.userid = authentid

        data = self.session.userid + '\000' + self.session.authentid
        data = self.encodeBlob(data)
        return self.channel.sendMessage(data)

    def splitAuth(self, data):
        """splitAuth() undoes the concatenation of userid and authentid
           separated by a NUL character.
        """
        regex = re.compile('\000')
        parts = re.split(regex, data)
        if len(parts) != 2:
            raise ProfileException('Invalid format for authorisation blob')
        return parts

    def sendChallenge(self, msgno):
        """sendChallenge() formats and sends a reply to the client
           based on the userid and authentid sent as a message
        """
        try:
            challenge = self.generator.getChallenge(self.session.userid)
            data = self.encodeBlob(challenge)
            self.channel.sendReply(msgno, data)
            self.sentchallenge = 1

        except KeyError, e:
            log.error('KeyError fetching challenge. User not in dbase?')
            data = '<error code="535">Authentication Failed</error>'
            self.channel.sendError(msgno, data)

class OTPUserEntry:
    def __init__(self, username, algo, seed, passphrasehash, sequence):
        self.username = username
        self.algo = algo
        self.seed = seed
        self.passphrasehash = passphrasehash
        self.sequence = sequence

class OTPdbase:
    """This is a Mixin class to provide standard OTP database
       access methods.
    """

    def __init__(self, dbasefile="OTPdbase.pik"):
        self.dbasefile = dbasefile

    def storeDBEntry(self, dbEntry):
        """storeDBEntry() stores a single OTPUserEntry in the
           database file set at initialisation. It uses the
           shelve module.
        """
        dbase = shelve.open(self.dbasefile)
        dbase[dbEntry.username] = dbEntry
        dbase.close()

    def retrieveDBEntry(self, username):
        dbase = shelve.open(self.dbasefile)
        dbEntry = dbase[username]
        dbase.close
        return dbEntry

class OTPGenerator(OTPdbase):
    def __init__(self, dbasefile="OTPdbase.pik"):

        OTPdbase.__init__(self, dbasefile)
        self.otpDict = OTPDictionary()

    def promptAndGenerate(self):
        try:
            # Get the inputs and validate them
            username = raw_input("Enter username: ")
            self.validateUsername(username)
            passphrase = raw_input("Enter passphrase: ")
            self.validatePassphrase(passphrase)
            seed = raw_input("Enter seed: ")
            self.validateSeed(seed)
            algo = raw_input("Enter algorithm: ")
            self.validateAlgorithm(algo)
            sequence = string.atoi(raw_input("Enter sequence number: "))
            self.validateSequence(sequence)

            return self.createOTP(username, algo, seed, passphrase, sequence)

        except ValueError, e:
            print "Error: %s" % e

    def createOTP(self, username, algo, seed, passphrase, sequence):
        """createOTP() should be used if you want to get
           all the relevent information using your own
           user interface and just use the hash generation
           code within this library.
        """

        passhash = self.createHash(username, algo, seed, passphrase, sequence)
        hexhash = self.convertBytesToHex(passhash)

        # Store new OTP info in dbase
        dbEntry = OTPUserEntry(username, algo, seed, hexhash, sequence)
        self.storeDBEntry(dbEntry)
        return passhash

    def createHash(self, username, algo, seed, passphrase, sequence):
        # Convert seed to lower case
        seed = string.lower(seed)

        # Generate the hash
        passphrasehash = self.generateHash(algo, seed + passphrase)

        for i in range(0, sequence):
            temp = self.generateHash(algo, passphrasehash)
            passphrasehash = temp

        return passphrasehash

    def validateUsername(self, username):
        # See if an entry already exists for the user
        try:
            dbEntry = self.retrieveDBEntry(username)
            if dbEntry:
                raise ValueError("Entry already exists for that username")
        except KeyError:
            pass

    def validatePassphrase(self, passphrase):
        if not 10 < len(passphrase):
            raise ValueError("Passphrase too short")

        if len(passphrase) > 63:
            log.notice("Passphrase longer than recommended length of 63 characters.")

    def validateSeed(self, seed):
        if not 0 <= len(seed) < 16:
            raise ValueError("Seed length invalid")

        regex = re.compile(r'[^a-zA-Z0-9]')
        match = regex.search(seed)
        if match:
            raise ValueError("Invalid char in seed: %s" % match.group(0))

    def validateAlgorithm(self, algo):
        if not algo == 'md5' or algo == 'sha':
            raise ValueError("Algorithm not supported")

    def validateSequence(self, seq):
        if seq < 0:
            return 0
        return 1

    def generateHash(self, algo, data):
        if algo == 'md5':
            md = md5.new(data).digest()
            # Fold into 64 bits
            temp = []
            d = struct.unpack('16B', md)
            result = ''
            for i in range(8):
                val = d[i] ^ d[i+8]
                result += chr(val)

            return result

        elif algo == 'sha':
            raise NotImplementedError

        else:
            raise NotImplementedError

    def convertBytesToHex(self, bytestring):
        """This method only accepts 8 byte bytestrings
        """
        if len(bytestring) != 8:
            raise ValueError('Illegal bytestring of length %d' % len(bytestring))

        bytes = struct.unpack('8B', bytestring)
        retstring = ''

        for i in range(8):
            retstring += "%02x" % bytes[i]

        return retstring

    def convertHexToBytes(self, hexstring):
        """This method converts a 16 character hex string
           and converts it to a bytestring.
        """
        bytes = ''
        if len(hexstring) != 16:
            raise ValueError("Illegal hash")

        for i in range(0, 16, 2):
            bytes += chr( string.atoi( hexstring[i:i+2], 16 ) )

        return bytes

    def convertBytesToLong(self, bytestring):
        if len(bytestring) != 8:
            raise ValueError('Invalid bytestring')
        bytes = struct.unpack('8B', bytestring)
        val = 0L
        for i in range(8):
            val = (val << 8) | (bytes[i] & 0xFF)

        return val

    def convertLongToBytes(self, hashlong):
        bytes = []
        for i in range(8,0,-1):
            bytes.insert(0, chr(hashlong & 0xFF) )
            hashlong >>= 8

        # convert list to string
        retstring = ''
        for x in bytes:
            retstring += x
        return retstring

    def convertBytesToWords(self, bytestring):
        hashlong = self.convertBytesToLong(bytestring)
        return self.otpDict.convertHashlongToWords(hashlong)

    def convertWordsToBytes(self, wordstring):
        hashlong = self.otpDict.convertWordsToHashlong(wordstring)
        return self.convertLongToBytes(hashlong)

    def authenticate(self, algo, username, bytestring):
        """authenticate() takes the username and passphrase hash it
           receives (presumably from a client) and checks it
           against the expected OTP in the dbase.
           passhash is an 8 byte string
        """
        dbEntry = self.retrieveDBEntry(username)
        mypasshash = self.generateHash(algo, bytestring)
        mypasshash = self.convertBytesToHex(mypasshash)
        log.debug('comparing dbEntry: %s to %s' % (dbEntry.passphrasehash, mypasshash) )
        if mypasshash == dbEntry.passphrasehash:
            # Authentication successful, modify dbase to save current OTP
            dbEntry.passphrasehash = mypasshash
            self.storeDBEntry(dbEntry)
            return 1

    def getChallenge(self, username):
        """getChallenge() looks up the username in the OTP dbase
           and builds the appropriate OTP challenge string.
        """
        challenge = 'otp-'
        dbEntry = self.retrieveDBEntry(username)
        challenge += dbEntry.algo
        challenge += ' '
        challenge += '%s ' % dbEntry.sequence
        challenge += dbEntry.seed
        challenge += ' ext'
        return challenge

class OTPDictionary:
    sixwords = [ 
            "A",     "ABE",   "ACE",   "ACT",   "AD",    "ADA",   "ADD",
        "AGO",   "AID",   "AIM",   "AIR",   "ALL",   "ALP",   "AM",    "AMY",
        "AN",    "ANA",   "AND",   "ANN",   "ANT",   "ANY",   "APE",   "APS",
        "APT",   "ARC",   "ARE",   "ARK",   "ARM",   "ART",   "AS",    "ASH",
        "ASK",   "AT",    "ATE",   "AUG",   "AUK",   "AVE",   "AWE",   "AWK",
        "AWL",   "AWN",   "AX",   "AYE",   "BAD",   "BAG",   "BAH",   "BAM",
        "BAN",   "BAR",   "BAT",   "BAY",   "BE",    "BED",   "BEE",   "BEG",
        "BEN",   "BET",   "BEY",   "BIB",   "BID",   "BIG",   "BIN",   "BIT",
        "BOB",   "BOG",   "BON",   "BOO",   "BOP",   "BOW",   "BOY",   "BUB",
        "BUD",   "BUG",   "BUM",   "BUN",   "BUS",   "BUT",   "BUY",   "BY",
        "BYE",   "CAB",   "CAL",   "CAM",   "CAN",   "CAP",   "CAR",   "CAT",
        "CAW",   "COD",   "COG",   "COL",   "CON",   "COO",   "COP",   "COT",
        "COW",   "COY",   "CRY",   "CUB",   "CUE",   "CUP",   "CUR",   "CUT",
        "DAB",   "DAD",   "DAM",   "DAN",   "DAR",   "DAY",   "DEE",   "DEL",
        "DEN",   "DES",   "DEW",   "DID",   "DIE",   "DIG",   "DIN",   "DIP",
        "DO",    "DOE",   "DOG",   "DON",   "DOT",   "DOW",   "DRY",   "DUB",
        "DUD",   "DUE",   "DUG",   "DUN",   "EAR",   "EAT",   "ED",    "EEL",
        "EGG",   "EGO",   "ELI",   "ELK",   "ELM",   "ELY",   "EM",    "END",
        "EST",   "ETC",   "EVA",   "EVE",   "EWE",   "EYE",   "FAD",   "FAN",
        "FAR",   "FAT",   "FAY",   "FED",   "FEE",   "FEW",   "FIB",   "FIG",
        "FIN",   "FIR",   "FIT",   "FLO",   "FLY",   "FOE",   "FOG",   "FOR",
        "FRY",   "FUM",   "FUN",   "FUR",   "GAB",   "GAD",   "GAG",   "GAL",
        "GAM",   "GAP",   "GAS",   "GAY",   "GEE",   "GEL",   "GEM",   "GET",
        "GIG",   "GIL",   "GIN",   "GO",    "GOT",   "GUM",   "GUN",   "GUS",
        "GUT",   "GUY",   "GYM",   "GYP",   "HA",    "HAD",   "HAL",   "HAM",
        "HAN",   "HAP",   "HAS",   "HAT",   "HAW",   "HAY",   "HE",    "HEM",
        "HEN",   "HER",   "HEW",   "HEY",   "HI",    "HID",   "HIM",   "HIP",
        "HIS",   "HIT",   "HO",   "HOB",   "HOC",   "HOE",   "HOG",   "HOP",
        "HOT",   "HOW",   "HUB",   "HUE",   "HUG",   "HUH",   "HUM",   "HUT",
        "I",     "ICY",   "IDA",   "IF",    "IKE",   "ILL",   "INK",   "INN",
        "IO",    "ION",   "IQ",   "IRA",   "IRE",   "IRK",   "IS",    "IT",
        "ITS",   "IVY",   "JAB",   "JAG",   "JAM",   "JAN",   "JAR",   "JAW",
        "JAY",   "JET",   "JIG",   "JIM",   "JO",    "JOB",   "JOE",   "JOG",
        "JOT",   "JOY",   "JUG",   "JUT",   "KAY",   "KEG",   "KEN",   "KEY",
        "KID",   "KIM",   "KIN",   "KIT",   "LA",    "LAB",   "LAC",   "LAD",
        "LAG",   "LAM",   "LAP",   "LAW",   "LAY",   "LEA",   "LED",   "LEE",
        "LEG",   "LEN",   "LEO",   "LET",   "LEW",   "LID",   "LIE",   "LIN",
        "LIP",   "LIT",   "LO",   "LOB",   "LOG",   "LOP",   "LOS",   "LOT",
        "LOU",   "LOW",   "LOY",   "LUG",   "LYE",   "MA",    "MAC",   "MAD",
        "MAE",   "MAN",   "MAO",   "MAP",   "MAT",   "MAW",   "MAY",   "ME",
        "MEG",   "MEL",   "MEN",   "MET",   "MEW",   "MID",   "MIN",   "MIT",
        "MOB",   "MOD",   "MOE",   "MOO",   "MOP",   "MOS",   "MOT",   "MOW",
        "MUD",   "MUG",   "MUM",   "MY",    "NAB",   "NAG",   "NAN",   "NAP",
        "NAT",   "NAY",   "NE",   "NED",   "NEE",   "NET",   "NEW",   "NIB",
        "NIL",   "NIP",   "NIT",   "NO",    "NOB",   "NOD",   "NON",   "NOR",
        "NOT",   "NOV",   "NOW",   "NU",    "NUN",   "NUT",   "O",     "OAF",
        "OAK",   "OAR",   "OAT",   "ODD",   "ODE",   "OF",    "OFF",   "OFT",
        "OH",    "OIL",   "OK",   "OLD",   "ON",    "ONE",   "OR",    "ORB",
        "ORE",   "ORR",   "OS",   "OTT",   "OUR",   "OUT",   "OVA",   "OW",
        "OWE",   "OWL",   "OWN",   "OX",    "PA",    "PAD",   "PAL",   "PAM",
        "PAN",   "PAP",   "PAR",   "PAT",   "PAW",   "PAY",   "PEA",   "PEG",
        "PEN",   "PEP",   "PER",   "PET",   "PEW",   "PHI",   "PI",    "PIE",
        "PIN",   "PIT",   "PLY",   "PO",    "POD",   "POE",   "POP",   "POT",
        "POW",   "PRO",   "PRY",   "PUB",   "PUG",   "PUN",   "PUP",   "PUT",
        "QUO",   "RAG",   "RAM",   "RAN",   "RAP",   "RAT",   "RAW",   "RAY",
        "REB",   "RED",   "REP",   "RET",   "RIB",   "RID",   "RIG",   "RIM",
        "RIO",   "RIP",   "ROB",   "ROD",   "ROE",   "RON",   "ROT",   "ROW",
        "ROY",   "RUB",   "RUE",   "RUG",   "RUM",   "RUN",   "RYE",   "SAC",
        "SAD",   "SAG",   "SAL",   "SAM",   "SAN",   "SAP",   "SAT",   "SAW",
        "SAY",   "SEA",   "SEC",   "SEE",   "SEN",   "SET",   "SEW",   "SHE",
        "SHY",   "SIN",   "SIP",   "SIR",   "SIS",   "SIT",   "SKI",   "SKY",
        "SLY",   "SO",    "SOB",   "SOD",   "SON",   "SOP",   "SOW",   "SOY",
        "SPA",   "SPY",   "SUB",   "SUD",   "SUE",   "SUM",   "SUN",   "SUP",
        "TAB",   "TAD",   "TAG",   "TAN",   "TAP",   "TAR",   "TEA",   "TED",
        "TEE",   "TEN",   "THE",   "THY",   "TIC",   "TIE",   "TIM",   "TIN",
        "TIP",   "TO",    "TOE",   "TOG",   "TOM",   "TON",   "TOO",   "TOP",
        "TOW",   "TOY",   "TRY",   "TUB",   "TUG",   "TUM",   "TUN",   "TWO",
        "UN",    "UP",    "US",   "USE",   "VAN",   "VAT",   "VET",   "VIE",
        "WAD",   "WAG",   "WAR",   "WAS",   "WAY",   "WE",    "WEB",   "WED",
        "WEE",   "WET",   "WHO",   "WHY",   "WIN",   "WIT",   "WOK",   "WON",
        "WOO",   "WOW",   "WRY",   "WU",    "YAM",   "YAP",   "YAW",   "YE",
        "YEA",   "YES",   "YET",   "YOU",   "ABED",  "ABEL",  "ABET",  "ABLE",
        "ABUT",  "ACHE",  "ACID",  "ACME",  "ACRE",  "ACTA",  "ACTS",  "ADAM",
        "ADDS",  "ADEN",  "AFAR",  "AFRO",  "AGEE",  "AHEM",  "AHOY",  "AIDA",
        "AIDE",  "AIDS",  "AIRY",  "AJAR",  "AKIN",  "ALAN",  "ALEC",  "ALGA",
        "ALIA",  "ALLY",  "ALMA",  "ALOE",  "ALSO",  "ALTO",  "ALUM",  "ALVA",
        "AMEN",  "AMES",  "AMID",  "AMMO",  "AMOK",  "AMOS",  "AMRA",  "ANDY",
        "ANEW",  "ANNA",  "ANNE",  "ANTE",  "ANTI",  "AQUA",  "ARAB",  "ARCH",
        "AREA",  "ARGO",  "ARID",  "ARMY",  "ARTS",  "ARTY",  "ASIA",  "ASKS",
        "ATOM",  "AUNT",  "AURA",  "AUTO",  "AVER",  "AVID",  "AVIS",  "AVON",
        "AVOW",  "AWAY",  "AWRY",  "BABE",  "BABY",  "BACH",  "BACK",  "BADE",
        "BAIL",  "BAIT",  "BAKE",  "BALD",  "BALE",  "BALI",  "BALK",  "BALL",
        "BALM",  "BAND",  "BANE",  "BANG",  "BANK",  "BARB",  "BARD",  "BARE",
        "BARK",  "BARN",  "BARR",  "BASE",  "BASH",  "BASK",  "BASS",  "BATE",
        "BATH",  "BAWD",  "BAWL",  "BEAD",  "BEAK",  "BEAM",  "BEAN",  "BEAR",
        "BEAT",  "BEAU",  "BECK",  "BEEF",  "BEEN",  "BEER",  "BEET",  "BELA",
        "BELL",  "BELT",  "BEND",  "BENT",  "BERG",  "BERN",  "BERT",  "BESS",
        "BEST",  "BETA",  "BETH",  "BHOY",  "BIAS",  "BIDE",  "BIEN",  "BILE",
        "BILK",  "BILL",  "BIND",  "BING",  "BIRD",  "BITE",  "BITS",  "BLAB",
        "BLAT",  "BLED",  "BLEW",  "BLOB",  "BLOC",  "BLOT",  "BLOW",  "BLUE",
        "BLUM",  "BLUR",  "BOAR",  "BOAT",  "BOCA",  "BOCK",  "BODE",  "BODY",
        "BOGY",  "BOHR",  "BOIL",  "BOLD",  "BOLO",  "BOLT",  "BOMB",  "BONA",
        "BOND",  "BONE",  "BONG",  "BONN",  "BONY",  "BOOK",  "BOOM",  "BOON",
        "BOOT",  "BORE",  "BORG",  "BORN",  "BOSE",  "BOSS",  "BOTH",  "BOUT",
        "BOWL",  "BOYD",  "BRAD",  "BRAE",  "BRAG",  "BRAN",  "BRAY",  "BRED",
        "BREW",  "BRIG",  "BRIM",  "BROW",  "BUCK",  "BUDD",  "BUFF",  "BULB",
        "BULK",  "BULL",  "BUNK",  "BUNT",  "BUOY",  "BURG",  "BURL",  "BURN",
        "BURR",  "BURT",  "BURY",  "BUSH",  "BUSS",  "BUST",  "BUSY",  "BYTE",
        "CADY",  "CAFE",  "CAGE",  "CAIN",  "CAKE",  "CALF",  "CALL",  "CALM",
        "CAME",  "CANE",  "CANT",  "CARD",  "CARE",  "CARL",  "CARR",  "CART",
        "CASE",  "CASH",  "CASK",  "CAST",  "CAVE",  "CEIL",  "CELL",  "CENT",
        "CERN",  "CHAD",  "CHAR",  "CHAT",  "CHAW",  "CHEF",  "CHEN",  "CHEW",
        "CHIC",  "CHIN",  "CHOU",  "CHOW",  "CHUB",  "CHUG",  "CHUM",  "CITE",
        "CITY",  "CLAD",  "CLAM",  "CLAN",  "CLAW",  "CLAY",  "CLOD",  "CLOG",
        "CLOT",  "CLUB",  "CLUE",  "COAL",  "COAT",  "COCA",  "COCK",  "COCO",
        "CODA",  "CODE",  "CODY",  "COED",  "COIL",  "COIN",  "COKE",  "COLA",
        "COLD",  "COLT",  "COMA",  "COMB",  "COME",  "COOK",  "COOL",  "COON",
        "COOT",  "CORD",  "CORE",  "CORK",  "CORN",  "COST",  "COVE",  "COWL",
        "CRAB",  "CRAG",  "CRAM",  "CRAY",  "CREW",  "CRIB",  "CROW",  "CRUD",
        "CUBA",  "CUBE",  "CUFF",  "CULL",  "CULT",  "CUNY",  "CURB",  "CURD",
        "CURE",  "CURL",  "CURT",  "CUTS",  "DADE",  "DALE",  "DAME",  "DANA",
        "DANE",  "DANG",  "DANK",  "DARE",  "DARK",  "DARN",  "DART",  "DASH",
        "DATA",  "DATE",  "DAVE",  "DAVY",  "DAWN",  "DAYS",  "DEAD",  "DEAF",
        "DEAL",  "DEAN",  "DEAR",  "DEBT",  "DECK",  "DEED",  "DEEM",  "DEER",
        "DEFT",  "DEFY",  "DELL",  "DENT",  "DENY",  "DESK",  "DIAL",  "DICE",
        "DIED",  "DIET",  "DIME",  "DINE",  "DING",  "DINT",  "DIRE",  "DIRT",
        "DISC",  "DISH",  "DISK",  "DIVE",  "DOCK",  "DOES",  "DOLE",  "DOLL",
        "DOLT",  "DOME",  "DONE",  "DOOM",  "DOOR",  "DORA",  "DOSE",  "DOTE",
        "DOUG",  "DOUR",  "DOVE",  "DOWN",  "DRAB",  "DRAG",  "DRAM",  "DRAW",
        "DREW",  "DRUB",  "DRUG",  "DRUM",  "DUAL",  "DUCK",  "DUCT",  "DUEL",
        "DUET",  "DUKE",  "DULL",  "DUMB",  "DUNE",  "DUNK",  "DUSK",  "DUST",
        "DUTY",  "EACH",  "EARL",  "EARN",  "EASE",  "EAST",  "EASY",  "EBEN",
        "ECHO",  "EDDY",  "EDEN",  "EDGE",  "EDGY",  "EDIT",  "EDNA",  "EGAN",
        "ELAN",  "ELBA",  "ELLA",  "ELSE",  "EMIL",  "EMIT",  "EMMA",  "ENDS",
        "ERIC",  "EROS",  "EVEN",  "EVER",  "EVIL",  "EYED",  "FACE",  "FACT",
        "FADE",  "FAIL",  "FAIN",  "FAIR",  "FAKE",  "FALL",  "FAME",  "FANG",
        "FARM",  "FAST",  "FATE",  "FAWN",  "FEAR",  "FEAT",  "FEED",  "FEEL",
        "FEET",  "FELL",  "FELT",  "FEND",  "FERN",  "FEST",  "FEUD",  "FIEF",
        "FIGS",  "FILE",  "FILL",  "FILM",  "FIND",  "FINE",  "FINK",  "FIRE",
        "FIRM",  "FISH",  "FISK",  "FIST",  "FITS",  "FIVE",  "FLAG",  "FLAK",
        "FLAM",  "FLAT",  "FLAW",  "FLEA",  "FLED",  "FLEW",  "FLIT",  "FLOC",
        "FLOG",  "FLOW",  "FLUB",  "FLUE",  "FOAL",  "FOAM",  "FOGY",  "FOIL",
        "FOLD",  "FOLK",  "FOND",  "FONT",  "FOOD",  "FOOL",  "FOOT",  "FORD",
        "FORE",  "FORK",  "FORM",  "FORT",  "FOSS",  "FOUL",  "FOUR",  "FOWL",
        "FRAU",  "FRAY",  "FRED",  "FREE",  "FRET",  "FREY",  "FROG",  "FROM",
        "FUEL",  "FULL",  "FUME",  "FUND",  "FUNK",  "FURY",  "FUSE",  "FUSS",
        "GAFF",  "GAGE",  "GAIL",  "GAIN",  "GAIT",  "GALA",  "GALE",  "GALL",
        "GALT",  "GAME",  "GANG",  "GARB",  "GARY",  "GASH",  "GATE",  "GAUL",
        "GAUR",  "GAVE",  "GAWK",  "GEAR",  "GELD",  "GENE",  "GENT",  "GERM",
        "GETS",  "GIBE",  "GIFT",  "GILD",  "GILL",  "GILT",  "GINA",  "GIRD",
        "GIRL",  "GIST",  "GIVE",  "GLAD",  "GLEE",  "GLEN",  "GLIB",  "GLOB",
        "GLOM",  "GLOW",  "GLUE",  "GLUM",  "GLUT",  "GOAD",  "GOAL",  "GOAT",
        "GOER",  "GOES",  "GOLD",  "GOLF",  "GONE",  "GONG",  "GOOD",  "GOOF",
        "GORE",  "GORY",  "GOSH",  "GOUT",  "GOWN",  "GRAB",  "GRAD",  "GRAY",
        "GREG",  "GREW",  "GREY",  "GRID",  "GRIM",  "GRIN",  "GRIT",  "GROW",
        "GRUB",  "GULF",  "GULL",  "GUNK",  "GURU",  "GUSH",  "GUST",  "GWEN",
        "GWYN",  "HAAG",  "HAAS",  "HACK",  "HAIL",  "HAIR",  "HALE",  "HALF",
        "HALL",  "HALO",  "HALT",  "HAND",  "HANG",  "HANK",  "HANS",  "HARD",
        "HARK",  "HARM",  "HART",  "HASH",  "HAST",  "HATE",  "HATH",  "HAUL",
        "HAVE",  "HAWK",  "HAYS",  "HEAD",  "HEAL",  "HEAR",  "HEAT",  "HEBE",
        "HECK",  "HEED",  "HEEL",  "HEFT",  "HELD",  "HELL",  "HELM",  "HERB",
        "HERD",  "HERE",  "HERO",  "HERS",  "HESS",  "HEWN",  "HICK",  "HIDE",
        "HIGH",  "HIKE",  "HILL",  "HILT",  "HIND",  "HINT",  "HIRE",  "HISS",
        "HIVE",  "HOBO",  "HOCK",  "HOFF",  "HOLD",  "HOLE",  "HOLM",  "HOLT",
        "HOME",  "HONE",  "HONK",  "HOOD",  "HOOF",  "HOOK",  "HOOT",  "HORN",
        "HOSE",  "HOST",  "HOUR",  "HOVE",  "HOWE",  "HOWL",  "HOYT",  "HUCK",
        "HUED",  "HUFF",  "HUGE",  "HUGH",  "HUGO",  "HULK",  "HULL",  "HUNK",
        "HUNT",  "HURD",  "HURL",  "HURT",  "HUSH",  "HYDE",  "HYMN",  "IBIS",
        "ICON",  "IDEA",  "IDLE",  "IFFY",  "INCA",  "INCH",  "INTO",  "IONS",
        "IOTA",  "IOWA",  "IRIS",  "IRMA",  "IRON",  "ISLE",  "ITCH",  "ITEM",
        "IVAN",  "JACK",  "JADE",  "JAIL",  "JAKE",  "JANE",  "JAVA",  "JEAN",
        "JEFF",  "JERK",  "JESS",  "JEST",  "JIBE",  "JILL",  "JILT",  "JIVE",
        "JOAN",  "JOBS",  "JOCK",  "JOEL",  "JOEY",  "JOHN",  "JOIN",  "JOKE",
        "JOLT",  "JOVE",  "JUDD",  "JUDE",  "JUDO",  "JUDY",  "JUJU",  "JUKE",
        "JULY",  "JUNE",  "JUNK",  "JUNO",  "JURY",  "JUST",  "JUTE",  "KAHN",
        "KALE",  "KANE",  "KANT",  "KARL",  "KATE",  "KEEL",  "KEEN",  "KENO",
        "KENT",  "KERN",  "KERR",  "KEYS",  "KICK",  "KILL",  "KIND",  "KING",
        "KIRK",  "KISS",  "KITE",  "KLAN",  "KNEE",  "KNEW",  "KNIT",  "KNOB",
        "KNOT",  "KNOW",  "KOCH",  "KONG",  "KUDO",  "KURD",  "KURT",  "KYLE",
        "LACE",  "LACK",  "LACY",  "LADY",  "LAID",  "LAIN",  "LAIR",  "LAKE",
        "LAMB",  "LAME",  "LAND",  "LANE",  "LANG",  "LARD",  "LARK",  "LASS",
        "LAST",  "LATE",  "LAUD",  "LAVA",  "LAWN",  "LAWS",  "LAYS",  "LEAD",
        "LEAF",  "LEAK",  "LEAN",  "LEAR",  "LEEK",  "LEER",  "LEFT",  "LEND",
        "LENS",  "LENT",  "LEON",  "LESK",  "LESS",  "LEST",  "LETS",  "LIAR",
        "LICE",  "LICK",  "LIED",  "LIEN",  "LIES",  "LIEU",  "LIFE",  "LIFT",
        "LIKE",  "LILA",  "LILT",  "LILY",  "LIMA",  "LIMB",  "LIME",  "LIND",
        "LINE",  "LINK",  "LINT",  "LION",  "LISA",  "LIST",  "LIVE",  "LOAD",
        "LOAF",  "LOAM",  "LOAN",  "LOCK",  "LOFT",  "LOGE",  "LOIS",  "LOLA",
        "LONE",  "LONG",  "LOOK",  "LOON",  "LOOT",  "LORD",  "LORE",  "LOSE",
        "LOSS",  "LOST",  "LOUD",  "LOVE",  "LOWE",  "LUCK",  "LUCY",  "LUGE",
        "LUKE",  "LULU",  "LUND",  "LUNG",  "LURA",  "LURE",  "LURK",  "LUSH",
        "LUST",  "LYLE",  "LYNN",  "LYON",  "LYRA",  "MACE",  "MADE",  "MAGI",
        "MAID",  "MAIL",  "MAIN",  "MAKE",  "MALE",  "MALI",  "MALL",  "MALT",
        "MANA",  "MANN",  "MANY",  "MARC",  "MARE",  "MARK",  "MARS",  "MART",
        "MARY",  "MASH",  "MASK",  "MASS",  "MAST",  "MATE",  "MATH",  "MAUL",
        "MAYO",  "MEAD",  "MEAL",  "MEAN",  "MEAT",  "MEEK",  "MEET",  "MELD",
        "MELT",  "MEMO",  "MEND",  "MENU",  "MERT",  "MESH",  "MESS",  "MICE",
        "MIKE",  "MILD",  "MILE",  "MILK",  "MILL",  "MILT",  "MIMI",  "MIND",
        "MINE",  "MINI",  "MINK",  "MINT",  "MIRE",  "MISS",  "MIST",  "MITE",
        "MITT",  "MOAN",  "MOAT",  "MOCK",  "MODE",  "MOLD",  "MOLE",  "MOLL",
        "MOLT",  "MONA",  "MONK",  "MONT",  "MOOD",  "MOON",  "MOOR",  "MOOT",
        "MORE",  "MORN",  "MORT",  "MOSS",  "MOST",  "MOTH",  "MOVE",  "MUCH",
        "MUCK",  "MUDD",  "MUFF",  "MULE",  "MULL",  "MURK",  "MUSH",  "MUST",
        "MUTE",  "MUTT",  "MYRA",  "MYTH",  "NAGY",  "NAIL",  "NAIR",  "NAME",
        "NARY",  "NASH",  "NAVE",  "NAVY",  "NEAL",  "NEAR",  "NEAT",  "NECK",
        "NEED",  "NEIL",  "NELL",  "NEON",  "NERO",  "NESS",  "NEST",  "NEWS",
        "NEWT",  "NIBS",  "NICE",  "NICK",  "NILE",  "NINA",  "NINE",  "NOAH",
        "NODE",  "NOEL",  "NOLL",  "NONE",  "NOOK",  "NOON",  "NORM",  "NOSE",
        "NOTE",  "NOUN",  "NOVA",  "NUDE",  "NULL",  "NUMB",  "OATH",  "OBEY",
        "OBOE",  "ODIN",  "OHIO",  "OILY",  "OINT",  "OKAY",  "OLAF",  "OLDY",
        "OLGA",  "OLIN",  "OMAN",  "OMEN",  "OMIT",  "ONCE",  "ONES",  "ONLY",
        "ONTO",  "ONUS",  "ORAL",  "ORGY",  "OSLO",  "OTIS",  "OTTO",  "OUCH",
        "OUST",  "OUTS",  "OVAL",  "OVEN",  "OVER",  "OWLY",  "OWNS",  "QUAD",
        "QUIT",  "QUOD",  "RACE",  "RACK",  "RACY",  "RAFT",  "RAGE",  "RAID",
        "RAIL",  "RAIN",  "RAKE",  "RANK",  "RANT",  "RARE",  "RASH",  "RATE",
        "RAVE",  "RAYS",  "READ",  "REAL",  "REAM",  "REAR",  "RECK",  "REED",
        "REEF",  "REEK",  "REEL",  "REID",  "REIN",  "RENA",  "REND",  "RENT",
        "REST",  "RICE",  "RICH",  "RICK",  "RIDE",  "RIFT",  "RILL",  "RIME",
        "RING",  "RINK",  "RISE",  "RISK",  "RITE",  "ROAD",  "ROAM",  "ROAR",
        "ROBE",  "ROCK",  "RODE",  "ROIL",  "ROLL",  "ROME",  "ROOD",  "ROOF",
        "ROOK",  "ROOM",  "ROOT",  "ROSA",  "ROSE",  "ROSS",  "ROSY",  "ROTH",
        "ROUT",  "ROVE",  "ROWE",  "ROWS",  "RUBE",  "RUBY",  "RUDE",  "RUDY",
        "RUIN",  "RULE",  "RUNG",  "RUNS",  "RUNT",  "RUSE",  "RUSH",  "RUSK",
        "RUSS",  "RUST",  "RUTH",  "SACK",  "SAFE",  "SAGE",  "SAID",  "SAIL",
        "SALE",  "SALK",  "SALT",  "SAME",  "SAND",  "SANE",  "SANG",  "SANK",
        "SARA",  "SAUL",  "SAVE",  "SAYS",  "SCAN",  "SCAR",  "SCAT",  "SCOT",
        "SEAL",  "SEAM",  "SEAR",  "SEAT",  "SEED",  "SEEK",  "SEEM",  "SEEN",
        "SEES",  "SELF",  "SELL",  "SEND",  "SENT",  "SETS",  "SEWN",  "SHAG",
        "SHAM",  "SHAW",  "SHAY",  "SHED",  "SHIM",  "SHIN",  "SHOD",  "SHOE",
        "SHOT",  "SHOW",  "SHUN",  "SHUT",  "SICK",  "SIDE",  "SIFT",  "SIGH",
        "SIGN",  "SILK",  "SILL",  "SILO",  "SILT",  "SINE",  "SING",  "SINK",
        "SIRE",  "SITE",  "SITS",  "SITU",  "SKAT",  "SKEW",  "SKID",  "SKIM",
        "SKIN",  "SKIT",  "SLAB",  "SLAM",  "SLAT",  "SLAY",  "SLED",  "SLEW",
        "SLID",  "SLIM",  "SLIT",  "SLOB",  "SLOG",  "SLOT",  "SLOW",  "SLUG",
        "SLUM",  "SLUR",  "SMOG",  "SMUG",  "SNAG",  "SNOB",  "SNOW",  "SNUB",
        "SNUG",  "SOAK",  "SOAR",  "SOCK",  "SODA",  "SOFA",  "SOFT",  "SOIL",
        "SOLD",  "SOME",  "SONG",  "SOON",  "SOOT",  "SORE",  "SORT",  "SOUL",
        "SOUR",  "SOWN",  "STAB",  "STAG",  "STAN",  "STAR",  "STAY",  "STEM",
        "STEW",  "STIR",  "STOW",  "STUB",  "STUN",  "SUCH",  "SUDS",  "SUIT",
        "SULK",  "SUMS",  "SUNG",  "SUNK",  "SURE",  "SURF",  "SWAB",  "SWAG",
        "SWAM",  "SWAN",  "SWAT",  "SWAY",  "SWIM",  "SWUM",  "TACK",  "TACT",
        "TAIL",  "TAKE",  "TALE",  "TALK",  "TALL",  "TANK",  "TASK",  "TATE",
        "TAUT",  "TEAL",  "TEAM",  "TEAR",  "TECH",  "TEEM",  "TEEN",  "TEET",
        "TELL",  "TEND",  "TENT",  "TERM",  "TERN",  "TESS",  "TEST",  "THAN",
        "THAT",  "THEE",  "THEM",  "THEN",  "THEY",  "THIN",  "THIS",  "THUD",
        "THUG",  "TICK",  "TIDE",  "TIDY",  "TIED",  "TIER",  "TILE",  "TILL",
        "TILT",  "TIME",  "TINA",  "TINE",  "TINT",  "TINY",  "TIRE",  "TOAD",
        "TOGO",  "TOIL",  "TOLD",  "TOLL",  "TONE",  "TONG",  "TONY",  "TOOK",
        "TOOL",  "TOOT",  "TORE",  "TORN",  "TOTE",  "TOUR",  "TOUT",  "TOWN",
        "TRAG",  "TRAM",  "TRAY",  "TREE",  "TREK",  "TRIG",  "TRIM",  "TRIO",
        "TROD",  "TROT",  "TROY",  "TRUE",  "TUBA",  "TUBE",  "TUCK",  "TUFT",
        "TUNA",  "TUNE",  "TUNG",  "TURF",  "TURN",  "TUSK",  "TWIG",  "TWIN",
        "TWIT",  "ULAN",  "UNIT",  "URGE",  "USED",  "USER",  "USES",  "UTAH",
        "VAIL",  "VAIN",  "VALE",  "VARY",  "VASE",  "VAST",  "VEAL",  "VEDA",
        "VEIL",  "VEIN",  "VEND",  "VENT",  "VERB",  "VERY",  "VETO",  "VICE",
        "VIEW",  "VINE",  "VISE",  "VOID",  "VOLT",  "VOTE",  "WACK",  "WADE",
        "WAGE",  "WAIL",  "WAIT",  "WAKE",  "WALE",  "WALK",  "WALL",  "WALT",
        "WAND",  "WANE",  "WANG",  "WANT",  "WARD",  "WARM",  "WARN",  "WART",
        "WASH",  "WAST",  "WATS",  "WATT",  "WAVE",  "WAVY",  "WAYS",  "WEAK",
        "WEAL",  "WEAN",  "WEAR",  "WEED",  "WEEK",  "WEIR",  "WELD",  "WELL",
        "WELT",  "WENT",  "WERE",  "WERT",  "WEST",  "WHAM",  "WHAT",  "WHEE",
        "WHEN",  "WHET",  "WHOA",  "WHOM",  "WICK",  "WIFE",  "WILD",  "WILL",
        "WIND",  "WINE",  "WING",  "WINK",  "WINO",  "WIRE",  "WISE",  "WISH",
        "WITH",  "WOLF",  "WONT",  "WOOD",  "WOOL",  "WORD",  "WORE",  "WORK",
        "WORM",  "WORN",  "WOVE",  "WRIT",  "WYNN",  "YALE",  "YANG",  "YANK",
        "YARD",  "YARN",  "YAWL",  "YAWN",  "YEAH",  "YEAR",  "YELL",  "YOGA",
        "YOKE"
    ]

    def convertHashlongToWords(self, hashlong):
        retstring = ''
        for i in range(6):
            index = self.getIndexFromHash(hashlong, i)
            retstring += self.sixwords[index]
            if i != 5:
                retstring += ' '

        return retstring

    def convertWordsToHashlong(self, wordstring):
        hashlong = 0L
        words = string.split(wordstring, ' ')
        if len(words) != 6:
            raise ValueError('Invalid wordstring')

        for i in range(6):
            index = self.sixwords.index(words[i])
            if i == 5:
                hashlong = (hashlong << 9) | (index >> 2)
            else:
                hashlong = (hashlong << 11) | index

        return hashlong

    def getIndexFromHash(self, hashlong, i):
        if i == 0:
            return int( (hashlong >> 53) & 0x7FF )
        elif i == 1:
            return int( (hashlong >> 42) & 0x7FF )
        elif i == 2:
            return int( (hashlong >> 31) & 0x7FF )
        elif i == 3:
            return int( (hashlong >> 20) & 0x7FF )
        elif i == 4:
            return int( (hashlong >> 9) & 0x7FF )
        elif i == 5:
            parity = 0
            temp = 0L
            for k in range(0, 64, 2):
                parity += temp & 0x03
                temp >>= 2

            return int( (((hashlong << 2) & 0x7FC) | (parity & 0x03)) & 0x7FF )

        else:
            raise ValueError("Invalid index to hashlong")
