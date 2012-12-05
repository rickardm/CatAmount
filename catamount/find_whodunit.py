#! /usr/bin/env python

# CatAmount analyzes GPS collar data to find time/space relationships.
# Copyright (C) 2012 Michael Rickard
#  
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This code was based on a reading of work done by Mike Warren at the
# University of Alberta and Kyle Knopff at The Central East Slopes
# Cougar Study.

# This file provides facilities to find if any cat was near a given place and time

# IMPORT

from datetime import timedelta

from catamount.common import *


# CONSTANTS/GLOBALS

whodunit_dot_size = 4


# CLASSES

class FWDataPool(DataPool):
	"""Extension to a plain DataPool adding things useful for finding whodunit.

	This adds the ability to search the data for a match to a given
	request, and to display those matches."""

	def __init__(self, radius, time_cutoff, x, y):
		DataPool.__init__(self)

		self.radius = radius
		self.time_cutoff = time_cutoff
		self.x = x
		self.y = y

		self.legend_date = '0'

	def find_matches(self):
		"""Find fixes that match, and keep track of others which come close."""

		matches = list()
		close = list()

		for fix in self.fixes:
			distance = fix.distance_from(self)
			delay = fix.delay_from(self)
			closeness = (distance / self.radius) + (delay / self.time_cutoff)
			if distance <= self.radius and delay <= self.time_cutoff:
				new_match = Match(fix, 'Match', closeness, distance, delay)
				matches.append(new_match)
			else:
				new_close = Match(fix, 'Close', closeness, distance, delay)
				close.append(new_close)

		self.matches = sorted(matches, key=lambda match: match.closeness)
		self.close = sorted(close, key=lambda close: close.closeness)

	def csv_report(self):
		"""Create a CSV report describing all the matches that were found."""

		field_list = ['Status', 'Cat_ID', 'Date', 'East_N27', 'North_N27', 'Closeness', 'Distance', 'Delay']
		sys.stdout.write(','.join(field_list) + '\n')

		# First line will be the request data
		request_list = ['Request', '----', self.dateobj.strftime(DATE_FMT_ISO),
			'{:0.1f}'.format(self.x), '{:0.1f}'.format(self.y), '----', '----', '----']
		sys.stdout.write(','.join(request_list) + '\n')

		for match in self.matches:
			match.csv_report()

		for close in self.close[0:10]:
			close.csv_report()

	def descriptive_report(self, all_points):
		"""Create a descriptive report describing all the matches that were found."""

		output = '\nWhodunit Settings Are As Follows:\n'
		output += '  * Radius: {0} meters\n'.format(self.radius)
		output += '  * Time Cutoff: {0} hours\n'.format(self.time_cutoff / 3600)
		output += '  * Request Date: {0}\n'.format(self.legend_date)
		output += '  * Request X: {0}\n'.format(self.x)
		output += '  * Request Y: {0}\n'.format(self.y)
		output += '\nMatches Found:\n'
		sys.stdout.write(output)

		for match in self.matches:
			match.descriptive_report()

		sys.stdout.write('\nNext Closest Points:\n')

		for close in self.close[0:10]:
			close.descriptive_report()

	def draw_object_specific_graphics(self):
		"""Draw graphics of all the found matches on the feedback image."""

		# Write information about the image across the bottom
		column_1 = list()
		column_1.append(('Radius', '{0} meters'.format(self.radius)))
		column_1.append(('Time Cutoff', '{0} hours'.format(self.time_cutoff / 3600)))
		column_1.append(('Date', self.legend_date))
		column_1.append(('X', '{0}'.format(self.x)))
		column_1.append(('Y', '{0}'.format(self.y)))

		column_2 = list()
		column_2.append(('Matches Found', '{0}'.format(len(self.matches))))
		column_2.append(('X Range', '{0:0.1f} km'.format(self.spread_x / 1000)))
		column_2.append(('Y Range', '{0:0.1f} km'.format(self.spread_y / 1000)))
		column_2.append(('Scale', '1 px = {0} m'.format(self.scale)))

		self.legend_info = [column_1, column_2]
		self.draw_legend(True)

		# Create a circle representing the target radius
		img_x = self.img_x(self.x)
		img_y = self.img_y(self.y)
		radius = self.radius / self.scale
		circleimg = Image.new('RGB', (self.imgwidth, self.imgheight), image_colors['whodunit'])
		circlemask = Image.new('L', (self.imgwidth, self.imgheight), '#000000')
		circlemaskdraw = ImageDraw.Draw(circlemask)
		circlemaskdraw.ellipse(
			[(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
			'#000000', '#FFFFFF'
		)
		self.fgimage.paste(circleimg, (0, 0), circlemask)

		# Create a cross at the target location
		self.fgdraw.line([(img_x - 2, img_y), (img_x + 2, img_y)], image_colors['whodunit'])
		self.fgdraw.line([(img_x, img_y - 2), (img_x, img_y + 2)], image_colors['whodunit'])

		# Draw a faintly colored dot for every close point
		closeimg = Image.new('RGB', (self.imgwidth, self.imgheight), image_colors['bg'])
		closeimgdraw = ImageDraw.Draw(closeimg)
		closemask = Image.new('L', (self.imgwidth, self.imgheight), '#000000')
		closemaskdraw = ImageDraw.Draw(closemask)
		
	 	for close in self.close:
	 		img_x = self.img_x(close.fix.x)
	 		img_y = self.img_y(close.fix.y)
	 		radius = whodunit_dot_size / 2
	 		bigger = whodunit_dot_size
	 		closeimgdraw.ellipse(
				[(img_x - bigger, img_y - bigger), (img_x + bigger, img_y + bigger)],
				self.cat_colors[close.fix.catid], self.cat_colors[close.fix.catid]
			)
	 		closemaskdraw.ellipse(
				[(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
				'#404040', '#404040'
			)
		 
		self.fgimage.paste(closeimg, (0, 0), closemask)

		# Draw a colored dot for every match point
	 	for match in self.matches:
	 		img_x = self.img_x(match.fix.x)
	 		img_y = self.img_y(match.fix.y)
	 		radius = whodunit_dot_size / 2
	 		self.fgdraw.ellipse(
				[(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
				self.cat_colors[match.fix.catid], self.cat_colors[match.fix.catid]
			)

		# Draw a black dot for every point
		for fix in self.fixes:
			img_x = self.img_x(fix.x)
			img_y = self.img_y(fix.y)
			self.fgdraw.point((img_x, img_y), image_colors['fg'])


class Match(object):
	"""A Match is a wrapper around a Fix, describing how it matched.

	This lets us pin extra data and methods on a matching fix, such
	as why it matched, and the ability to describe that match."""

	def __init__(self, fix, status, closeness, distance, delay):
		self.fix = fix
		self.status = status
		self.closeness = closeness
		self.distance = distance
		self.delay = delay

	def csv_report(self):
		"""Create a CSV report describing this one match."""

		field_list = [
			self.status,
			self.fix.catid,
			self.fix.dateobj.strftime(DATE_FMT_ISO),
			'{:0.1f}'.format(self.fix.x),
			'{:0.1f}'.format(self.fix.y),
			'{:0.3f}'.format(self.closeness),
			'{:0.1f}'.format(self.distance),
			'{:0.1f}'.format(self.delay / 3600)
		]
		sys.stdout.write(','.join(field_list) + '\n')

	def descriptive_report(self):
		"""Create a descriptive report describing this one match. """

		field_list = [
			self.fix.catid,
			self.fix.dateobj.strftime(DATE_FMT_ISO),
			'{:0.1f} east'.format(self.fix.x),
			'{:0.1f} north'.format(self.fix.y),
			'{:6.3f}'.format(self.closeness),
			'{:6.1f} m'.format(self.distance),
			'{:6.1f} h'.format(self.delay / 3600)
		]
		sys.stdout.write('    ' + ', '.join(field_list) + '\n')


