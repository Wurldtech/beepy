# A basic echoserver for testing purposes

import sys
sys.path.append('..')

from beepy.profiles import echoprofile
from beepy.profiles import tlsprofile
from beepy.transports.twistedsession import TLSProtocol
from beepy.transports.twistedsession import TLSServerFactory

from twisted.internet import reactor
from twisted.application import internet, service

# Put this here so we override twisted's logging
import logging
from beepy.core import debug

log = debug.log

factory = TLSServerFactory()
factory.addProfile(echoprofile)
factory.addProfile(tlsprofile)

factory.privateKeyFileName = 'serverKey.pem'
factory.certificateFileName = 'serverCert.pem'

application = service.Application('tlsbeep')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1976, factory).setServiceParent(serviceCollection)

