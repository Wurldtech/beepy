# $Id: dummyclient.py,v 1.1 2002/08/02 00:24:40 jpwarren Exp $
# $Revision: 1.1 $
# Dummy client code to simulate a BEEP client connecting to a server
# for testing the server

import sys
import socket

#sys.path.append('../../')
#from beep.core import constants
#from beep.transports import tcpsession
#from beep.profiles import profile

class DummyClient:

	sock = None
	wfile = None
	server = ("localhost", 1976)
	bufsize = 8096
	inbuf = ''

	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.sock.connect(self.server)
			self.wfile = self.sock.makefile('wb', self.bufsize)
		except:
			raise

	def sendmsg(self, msg):
		self.sock.send(msg)

	def getmsg(self):
		inbuf = self.sock.recv(self.bufsize)
		return inbuf

	def terminate(self):
		self.wfile.flush()
		self.wfile.close()
		self.sock.close()
