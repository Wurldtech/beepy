# A basic echoserver for testing purposes

import sys
sys.path.append('..')

from beepy.profiles import echoprofile
from beepy.transports.twistedsession import BeepServerFactory
from twisted.application import internet, service

# Put this here so we override twisted's logging
import logging
from beepy.core import debug
log = debug.log

factory = BeepServerFactory()
factory.addProfile(echoprofile)

application = service.Application('echobeep')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1976, factory).setServiceParent(serviceCollection)

