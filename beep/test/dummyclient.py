# $Id: dummyclient.py,v 1.3 2002/10/23 04:51:17 jpwarren Exp $
# $Revision: 1.3 $
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
# Dummy client code to simulate a BEEP client connecting to a server
# for testing the server

import sys
import socket, select

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
			self.sock.setblocking(0)
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		except:
			raise

	def sendmsg(self, msg):
		self.sock.send(msg)

	def getmsg(self, blocking=0):
		if blocking:
			self.sock.setblocking(1)
			data = None
			try:
				data = self.sock.recv(self.bufsize)
				return data
			except Exception, e:
				print "Exception occurred: %s" % e
		else:
			self.sock.setblocking(0)
			return self._getdata()

	def _getdata(self):
		inbit, outbit, oobit = select.select([self.sock], [], [], 0)
		if inbit:
			data = self.sock.recv(self.bufsize)
			if data:
				return data

	def terminate(self):
		self.wfile.flush()
		self.wfile.close()
		self.sock.close()
