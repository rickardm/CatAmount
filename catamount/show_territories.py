#!/usr/bin/env python

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

# This file provides a way to visualize relationships between cat territories.

# IMPORT

import math

import Image
import ImageDraw

import catamount.common as catcm


# CLASSES

class STDataPool(catcm.DataPool):
	"""Extension of a DataPool, to add things specific to show_territories.

	This adds the ability to divide the data into trails, and display
	territory graphics."""

	def __init__(self, dot_size, perimeter_resolution):
		catcm.DataPool.__init__(self)

		self.dot_size = dot_size
		self.perimeter_resolution = perimeter_resolution

		self.legend_start_date = '0'
		self.legend_end_date = '0'

	def create_trails(self):
		"""Create a Trail for each cat in the list of fixes"""

		self.trails = dict()

		for fix in self.fixes:
			if fix.catid not in self.trails:
				new_trail = catcm.Trail(fix.catid)
				self.trails[fix.catid] = new_trail

			self.trails[fix.catid].fixes.append(fix)

		for trail in self.trails.itervalues():
			trail.find_bounds()

	def calculate_angles(self):
		"""Have each Trail find the angles and angle distance for its fixes."""

		for trail in self.trails.itervalues():
			trail.calculate_angles()

	def draw_object_specific_graphics(self):
		"""Draw graphics of all territories on the feedback image."""

		# Write information about the image across the bottom
		column_1 = list()
		column_1.append(('X Range', '{0:0.1f} km'.format(self.spread_x / 1000)))
		column_1.append(('Y Range', '{0:0.1f} km'.format(self.spread_y / 1000)))
		column_1.append(('Start Date', self.legend_start_date))
		column_1.append(('End Date', self.legend_end_date))

		column_2 = list()
		column_2.append(('Scale', '1 px = {0} m'.format(self.scale)))

		self.legend_info = [column_1, column_2]
		self.draw_legend(True)

		# Draw a border around each cat's datapool
		# Currently uses radial concept to find points around the perimeter of a range
		for trail in self.trails.itervalues():
			fixes_by_angle = dict()
			for degree in range(0, 360):
				fixes_by_angle[degree] = list()
			for fix in trail.fixes:
				degrees_per_section = self.perimeter_resolution
				angle = int(math.floor(fix.angle_from_center / degrees_per_section)) * degrees_per_section
				fixes_by_angle[angle].append(fix)

			border_points = list()
			for degree in range(0, 360):
				available_fixes = fixes_by_angle[degree]

				if not available_fixes:
					continue

				available_fixes = sorted(available_fixes, key=lambda fix: fix.distance_from_center)
				farthest_fix = available_fixes[-1]
				pt_img_x = self.img_x(farthest_fix.x)
				pt_img_y = self.img_y(farthest_fix.y)
				border_points.append((pt_img_x, pt_img_y))

			borderimg = Image.new('RGB', (self.imgwidth, self.imgheight), self.cat_colors[trail.catid])
			bordermask = Image.new('L', (self.imgwidth, self.imgheight), '#000000')
			bordermaskdraw = ImageDraw.Draw(bordermask)
			bordermaskdraw.polygon(border_points, '#404040', '#FFFFFF')
			self.fgimage.paste(borderimg, (0, 0), bordermask)


		# Create a colored dot for every fix. We do these in chrono
		# order across all cats, so that newer points wind up on top,
		# the least obscured, and older points are more obscured.
		px_radius = self.dot_size / 2
		for fix in self.fixes:
			img_x = self.img_x(fix.x)
			img_y = self.img_y(fix.y)
			self.fgdraw.ellipse(
				[(img_x - px_radius, img_y - px_radius), (img_x + px_radius, img_y + px_radius)],
				self.cat_colors[fix.catid]
			)



