# $Id: statemachine.py,v 1.2 2002/08/13 13:08:23 jpwarren Exp $
# $Revision: 1.2 $
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
# I got really sick of mucking about with state machines within separate
# modules, so I've decided to write a generic state machine permissions
# type system.

import errors

class StateMachine:
	handlers = {}		# What to do in a given state
	startState = None	# Which state to start in
	endStates = []		# Terminal states

	def __init__(self):
		self.handlers = {}
		self.startState = None
		self.endStates = []

	def addState(self, name, handler, endstate = 0):
		self.handlers[name] = handler
		if endstate:
			self.endStates.append(name)

	def setStart(self, name):
		self.startState = name

	def run(self, cargo=None):
		try:
			handler = self.handlers[self.startState]
		except:
			raise StateMachineException("You must call .setStart() before .run()")
		if not self.endStates:
			raise StateMachineException("There must be at least one terminal state")

		while 1:
			(newState, cargo) = handler(cargo)
			if newState in self.endStates:
				break
			else:
				handler = self.handlers[newState]

class StateMachineException(errors.BEEPException):
	def __init__(self, args=None):
		self.args = args

class TransitionException(StateMachineException):
	def __init__(self, args=None):
		self.args = args
