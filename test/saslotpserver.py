# A basic echoserver for testing purposes

import sys
sys.path.append('..')

from beepy.profiles import echoprofile
from beepy.profiles import saslotpprofile
from beepy.transports.twistedsession import SASLProtocol
from beepy.transports.twistedsession import SASLServerFactory

from twisted.internet import reactor
from twisted.application import internet, service

# Put this here so we override twisted's logging
import logging
from beepy.core import debug

log = debug.log

factory = SASLServerFactory()
factory.addProfile(echoprofile)
factory.addProfile(saslotpprofile)

application = service.Application('saslanonybeep')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1976, factory).setServiceParent(serviceCollection)

