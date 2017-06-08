# Detector controller for gamma measurements
# Copyright (C) 2016  Norwegain Radiation Protection Authority
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors: Dag Robole,

class Message(object):
	"""
	Description:
		Class used to store a protocol message
	"""
	def __init__(self, command='', arguments={}):
		"""
		Description:
			Initialize message
		Arguments:
			command - (optional) A command as described by the protocol
			arguments (optional) Map of valid arguments for the command
		"""
		self.command = command
		self.arguments = arguments
		
	def __str__(self):
		return self.command + ' ' + str(self.arguments)
