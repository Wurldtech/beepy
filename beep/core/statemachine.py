# $Id: statemachine.py,v 1.5 2002/09/17 06:51:44 jpwarren Exp $
# $Revision: 1.5 $
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

	def __init__(self):
		self.startState = None
		self.terminalStates = []
		self.fsmMap = {}
		self.handlers = {}
		self.currentState = None
		self.nextState = None

	def addState(self, state, handler, terminal=0):
		if self.fsmMap.has_key(state):
			raise StateMachineException("State %s already exists" % state)
		else:
			self.handlers[state] = handler
			self.fsmMap[state] = {}

		if terminal:
			self.terminalStates.append(state)

	def setStart(self, state):
		if state not in self.fsmMap.keys():
			raise StateMachineException("state %s not defined. Cannot set as start state." % state)
		self.startState = state

	def addTransition(self, state, event, nextState):
		"""addTransition sets up the rule for what to do if an event
		   occurs in a given state. 
		   Simply: in state, if event occurs, transition to nextState
		"""
		if not self.fsmMap.has_key(state):
			raise StateMachineException("Cannot add transition to non-existant state")

		self.fsmMap[state][event] = nextState

	def transition(self, event):

		"""transition is used to change the state of the FSM from
		   the current state to the next state by telling it an
		   event has occurred. This is a sortof callback mechanism.
		"""
#		print "%s: transition: event %s in state %s" % (self, event, self.currentState)

		if not self.fsmMap.has_key(self.currentState):
			raise StateMachineException("StateMachine is in invalid state. Cannot transition.")

		# transitioning is suspended if state is terminal
#		print "DEBUG: self: %s" % self
#		print "DEBUG: currentState: %s" % self.currentState
#		print "DEBUG: nextState: %s" % self.nextState
#		print "DEBUG: terminalStates: %s" % self.terminalStates
#		print "DEBUG: event: %s" % event
#		print self.__dict__

		if self.currentState in self.terminalStates:
			return

		# A form of locking, first check that someone else hasn't
		# already requested a state transition. If they have, we do
		# nothing. First state transition takes precedence
		if self.nextState != self.currentState:
			return

		# make sure this event is valid for the current state
		try:
			if not self.fsmMap[self.currentState].has_key(event):
				raise StateMachineException("No rule for event %s in state %s" % (event, self.currentState))
			else:
				self.nextState = self.fsmMap[self.currentState][event]

		except KeyError, e:
			StateMachineException("no map entry for current state: %s" % self.currentState)

	def run(self):
		try:
			self.currentState = self.startState
			self.nextState = self.startState
			handler = self.handlers[self.startState]
		except:
			raise StateMachineException("You must call .setStart() before .run()")
		if not self.terminalStates:
			raise StateMachineException("There must be at least one terminal state")

		while self.currentState not in self.terminalStates:
			handler()

			# If nextState is different from the currentState, transition()
			# has been called to flag a state transition.
			if self.nextState != self.currentState:
				print "DEBUG: changing state from %s to %s" % (self.currentState, self.nextState)
				handler = self.handlers[self.nextState]
				self.currentState = self.nextState

class StateMachineException(errors.BEEPException):
	def __init__(self, args=None):
		self.args = args

class TransitionException(StateMachineException):
	def __init__(self, args=None):
		self.args = args
