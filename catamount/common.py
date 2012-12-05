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

# This file contains code that is common between the different components.

# IMPORT

import os
import re
import sys
import math
import argparse

from csv import reader as csvreader
from time import mktime
from dateutil import parser as dateparser
from ConfigParser import RawConfigParser

import Image
import ImageDraw
import ImageFont


# CONSTANTS/GLOBALS

APP_NAME = 'CatAmount'
APP_VERSION = '13518.834'
APP_COPYRIGHT = 'Copyright (C) 2012 Michael Rickard'

DATE_FMT_ID = '%Y%m%d-%H%M'
DATE_FMT_ID_SHORT = '%Y%m%d'
DATE_FMT_ISO = '%Y-%m-%d %H:%M:%S'
DATE_FMT_ISO_SHORT = '%Y-%m-%d %H:%M'

tiny_number_font = {
	'0': '00000011100101001010010100111000000',
	'1': '00000001000110000100001000111000000',
	'2': '00000011100001001110010000111000000',
	'3': '00000011100001001110000100111000000',
	'4': '00000010100101001110000100001000000',
	'5': '00000011100100001110000100111000000',
	'6': '00000011100100001110010100111000000',
	'7': '00000011100001000010001000010000000',
	'8': '00000011100101001110010100111000000',
	'9': '00000011100101001110000100111000000',
	'.': '00000000000000000000000000010000000',
}

image_colors = {
	'bg': '#FFFFFF',
	'fg': '#000000',
	'border': '#C0C0C0',
	'text': '#000000',
	'cluster': '#FFB0B0',
	'crossing': '#80E080',
	'trail': '#C0C0F0',
	'grid': '#E0E0E0',
	'grid_accent': '#B0B0B0',
	'limit': '#FF0000',
	'whodunit': '#B0B0E0'
}


# CLASSES

class GraphicBase(object):
	"""This is a base class containing image building code.

	It doesn't do much on its own, but other classes can inherit it
	and get basic image capability."""

	def __init__(self):
		# These all get filled in by the subclass
		self.x = 0
		self.y = 0
		self.max_x = 0
		self.min_x = 0
		self.max_y = 0
		self.min_y = 0
		self.spread_x = 0
		self.spread_y = 0
		self.catids = list()
		self.cat_colors = dict()
		self.legend_info = list()

	def create_image(self, outfilepath, scale):
		"""Create all the elements that are common to every image."""

		# Auto-find an appropriate image scale
		if scale == 'auto':
			for test_scale in range(0, 1000, 5):
				if test_scale == 0:
					test_scale = 1

				if 10000 % test_scale != 0:
					continue

				test_imgwidth = int(self.spread_x / test_scale)
				if test_imgwidth <= 1200:
					self.scale = test_scale
					break
		else:
			self.scale = scale

		self.padding = 34


		self.imgheight = int(self.spread_y / self.scale)
		self.imgwidth = int(self.spread_x / self.scale)

		# These give us the ability to recenter a small image
		self.img_max_x = self.max_x
		self.img_min_x = self.min_x
		self.img_max_y = self.max_y
		self.img_min_y = self.min_y

		# Don't create incredibly large images
		if self.imgheight > 10000 or self.imgwidth > 10000:
			error_text = 'ERROR: Image dimensions would exceed 10,000 pixels, not creating image.\n'
			error_text += 'Calculated image size is {0} by {1} pixels.\n'.format(self.imgheight, self.imgwidth)
			error_text += 'Current scale is 1 pixel = {0} meters.\n\n'.format(self.scale)
			sys.stderr.write(error_text)
			return False

		# Don't create incredibly small images
		min_size = 400
		if self.imgheight < min_size:
			self.img_min_y = self.y - (min_size * self.scale / 2)
			self.img_max_y = self.img_min_y + (min_size * self.scale)
			self.imgheight = min_size

		if self.imgwidth < min_size:
			self.img_min_x = self.x - (min_size * self.scale / 2)
			self.img_max_x = self.img_min_x + (min_size * self.scale)
			self.imgwidth = min_size

		self.newimage = Image.new(
			'RGB',
			(self.imgwidth + (self.padding * 2) + 1, self.imgheight + (self.padding * 2) + 84),
			image_colors['border']
		)
		self.draw = ImageDraw.Draw(self.newimage)
		fontpath = os.path.join(basepath, 'fonts', 'proggy.pil')
		self.font = ImageFont.load(fontpath)

		# These are the limit strings
		limit_fmt = '{0:0.1f}'
		max_x_str = limit_fmt.format(self.img_max_x)
		min_x_str = limit_fmt.format(self.img_min_x)
		max_y_str = limit_fmt.format(self.img_max_y)
		min_y_str = limit_fmt.format(self.img_min_y)

		# Draw a 1px border around the foreground, to show the limits
		self.draw.rectangle(
			[
				(self.padding - 1, self.padding - 1),
				(self.padding + self.imgwidth + 1, self.padding + self.imgheight + 1)
			],
			image_colors['border'], image_colors['fg']
		)

		# These are used for the placement of limit strings around the border
		half_wide_minus_half_text = self.padding + (self.imgwidth / 2) - (len(max_y_str) * 5 / 2)
		half_wide_plus_half_text = self.padding + (self.imgwidth / 2) + (len(max_y_str) * 5 / 2)
		half_tall_minus_half_text = self.padding + (self.imgheight / 2) - (len(max_x_str) * 5 / 2)
		half_tall_plus_half_text = self.padding + (self.imgheight / 2) + (len(max_x_str) * 5 / 2)

		# Draw background color where the limit strings will be
		self.draw.line(
			[
				(half_wide_minus_half_text, self.padding - 1),
				(half_wide_plus_half_text, self.padding - 1)
			],
			image_colors['border']
		)
		self.draw.line(
			[
				(half_wide_minus_half_text, self.padding + self.imgheight + 1),
				(half_wide_plus_half_text, self.padding + self.imgheight + 1)
			],
			image_colors['border']
		)
		self.draw.line(
			[
				(self.padding - 1, half_tall_plus_half_text),
				(self.padding - 1, half_tall_minus_half_text)
			],
			image_colors['border']
		)
		self.draw.line(
			[
				(self.padding + self.imgwidth + 1, half_tall_plus_half_text),
				(self.padding + self.imgwidth + 1, half_tall_minus_half_text)
			],
			image_colors['border']
		)

		# Use a new image for the foreground, so we don't have to work with padding
		self.fgimage = Image.new(
			'RGB',
			(self.imgwidth + 1, self.imgheight + 1),
			image_colors['bg']
		)
		self.fgdraw = ImageDraw.Draw(self.fgimage)

		# Determine how far apart to space the grid
		self.grid_factor = False
		try_grid_factor = 100
		while not self.grid_factor:
			grid_px_size = try_grid_factor / self.scale
			if grid_px_size > 12:
				self.grid_factor = try_grid_factor
			else:
				try_grid_factor *= 10

		# This is used for the grids, spaced grid_factor meters apart
		px_offset = self.grid_factor / self.scale

		# Draw a grid across the white rectangle, spacing to be grid_factor meters
		y_offset = (int(self.img_max_y) % self.grid_factor) / self.scale
		while y_offset < self.imgheight:
			self.fgdraw.line(
				[(0, y_offset), (self.imgwidth, y_offset)],
				image_colors['grid']
			)
			y_offset += px_offset
		
		x_offset = (self.grid_factor - (int(self.img_min_x) % self.grid_factor)) / self.scale
		while x_offset < self.imgwidth:
			self.fgdraw.line(
				[(x_offset, 0), (x_offset, self.imgheight)],
				image_colors['grid']
			)
			x_offset += px_offset

		# Draw a darker gray grid on top of the previous one, every ten major units
		accent_px_offset = (10 * self.grid_factor) / self.scale

		accent_y_offset = (int(self.img_max_y) % (self.grid_factor * 10)) / self.scale
		while accent_y_offset < self.imgheight:
			self.fgdraw.line(
				[(0, accent_y_offset), (self.imgwidth, accent_y_offset)],
				image_colors['grid_accent']
			)
			accent_y_offset += accent_px_offset

		accent_x_offset = ((self.grid_factor * 10) - (int(self.img_min_x) % (self.grid_factor * 10))) / self.scale
		while accent_x_offset < self.imgwidth:
			self.fgdraw.line(
				[(accent_x_offset, 0), (accent_x_offset, self.imgheight)],
				image_colors['grid_accent']
			)
			accent_x_offset += accent_px_offset

		# Draw number markers in the margin, as a ruler for the grid
		number_increment = self.grid_factor / 1000.0
		if self.grid_factor == 100:
			number_format = '{0:0.1f}'
		else:
			number_format = '{0:0.0f}'

		y_offset = ((int(self.img_max_y) % self.grid_factor) / self.scale) + self.padding
		y_value = (int(self.img_max_y) / self.grid_factor) * number_increment
		while y_offset < (self.imgheight + self.padding):
			y_str = number_format.format(y_value)
			self.draw_horizontal_numbers(
				1 + ((6 - len(y_str)) * 5),
				y_offset,
				y_str
			)
			self.draw_horizontal_numbers(
				self.padding + self.imgwidth + 4,
				y_offset,
				y_str
			)
			y_offset += px_offset
			y_value -= number_increment

		x_offset = ((self.grid_factor - (int(self.img_min_x) % self.grid_factor)) / self.scale) + self.padding
		x_value = ((int(self.img_min_x) / self.grid_factor) + 1) * number_increment
		while x_offset < (self.imgwidth + self.padding):
			x_str = number_format.format(x_value)
			self.draw_vertical_numbers(
				x_offset,
				self.imgheight + self.padding + ((len(x_str) * 5) + 3),
				x_str
			)
			self.draw_vertical_numbers(
				x_offset,
				self.padding - 4,
				x_str
			)
			x_offset += px_offset
			x_value += number_increment

		# This is how each subclass can have a different result
		self.draw_object_specific_graphics()

		# Paste the foreground onto the image
		self.newimage.paste(self.fgimage, (self.padding, self.padding))

		# Draw limit strings on top of the 1px border, straddling fg/bg
		# Needs to happen after foreground is pasted
		self.draw_horizontal_numbers(
			(half_wide_minus_half_text),
			(self.padding - 1),
			max_y_str
		)
		self.draw_horizontal_numbers(
			(half_wide_minus_half_text),
			(self.padding + self.imgheight + 1),
			min_y_str
		)
		self.draw_vertical_numbers(
			(self.padding - 1),
			(half_tall_plus_half_text),
			min_x_str
		)
		self.draw_vertical_numbers(
			(self.padding + self.imgwidth + 1),
			(half_tall_plus_half_text),
			max_x_str
		)

		# Save out the image
		self.newimage.save(outfilepath, 'PNG')

	def draw_object_specific_graphics(self):
		"""Each class that is based on this one can redefine this
		function to build its unique graphical output."""

		pass

	def draw_legend(self, cat_legend=False):
		"""Create the legend of informative text at the bottom left of
		each image."""

		legend_x = 4
		legend_y = self.imgheight + (self.padding * 2)
		row_offset = 12
		char_offset = 7

		for text_column in self.legend_info:
			# Calculate how many characters each column uses
			left_used = 0
			right_used = 0
			for text_line in text_column:
				if len(text_line[0]) > left_used:
					left_used = len(text_line[0])
				if len(text_line[1]) > right_used:
					right_used = len(text_line[1])

			# Pick out a format string based on the left column
			format_str = '{{0:>{0}}}:{{1}}'.format(left_used)

			# Write out the text
			row_count = 0
			for text_line in text_column:
				self.draw.text(
					(legend_x, legend_y + (row_count * row_offset)),
					format_str.format(text_line[0], text_line[1]),
					image_colors['text'], self.font
				)
				row_count += 1

			# Move the x location according to how many characters were used
			legend_x += (left_used + right_used + 3) * char_offset

		# Stop here if we don't need to add a cat legend
		if not cat_legend:
			return True

		# Begin drawing the cat legend
		row_count = 0
		rect_height = 10
		rect_width = 16
		longest_id = 0

		for catid in self.catids:
			if len(catid) > longest_id:
				longest_id = len(catid)

			key_x = legend_x
			key_y = legend_y + (row_count * row_offset)
			rect_points = [
				(key_x, key_y),
				(key_x + rect_width, key_y),
				(key_x + rect_width, key_y + rect_height),
				(key_x, key_y + rect_height)
			]
			self.draw.polygon(rect_points, image_colors['bg'], image_colors['fg'])
			self.draw.text((key_x + rect_width + 4, key_y), catid, image_colors['text'], self.font)

			colorimg = Image.new('RGB', (rect_width, rect_height), self.cat_colors[catid])
			colormask = Image.new('L', (rect_width, rect_height), '#000000')
			colormaskdraw = ImageDraw.Draw(colormask)
			half_dot = 2
			half_x = rect_width / 2
			half_y = rect_height / 2
			# Sample of the color field and edge in the box
			colormaskdraw.polygon(
				[
					(0, rect_height),
					(rect_width, rect_height),
					(rect_width, 0),
					(rect_width / 3, 0)
				],
				'#404040', '#FFFFFF'
			)
			# Sample of the color dot in the box
			colormaskdraw.ellipse(
				[
					(half_x - half_dot, half_y - half_dot),
					(half_x + half_dot, half_y + half_dot)
				],
				'#FFFFFF'
			)
			# Erase anything on the edges of the rectangle
			colormaskdraw.line(
				[
					(0, 0),
					(0, rect_height),
					(rect_width, rect_height),
					(rect_width, 0),
					(0, 0)
				],
				'#000000'
			)
			self.newimage.paste(colorimg, (key_x, key_y), colormask)

			row_count += 1
			if row_count % 6 == 0:
				row_count = 0
				legend_x += (longest_id + 5) * char_offset


	def draw_horizontal_numbers(self, x, y, text_to_draw):
		"""Using a trivial pixel font to draw 3x5 numbers horizontally."""

		number_counter = -1
		for number in text_to_draw:
			number_counter += 1
			bit_map = tiny_number_font[number]
			row_counter = 0
			point_counter = -1
			for point in bit_map:
				point_counter += 1
				if (point_counter % 5 == 0):
					point_counter = 0
					row_counter += 1
				if (point == '1'):
					self.draw.point(
						(
							(x + (number_counter * 5) + point_counter),
							((y - 4) + row_counter)
						),
						image_colors['fg']
					)

	def draw_vertical_numbers(self, x, y, text_to_draw):
		"""Using a trivial pixel font to draw 3x5 numbers vertically."""

		number_counter = -1
		for number in text_to_draw:
			number_counter += 1
			bit_map = tiny_number_font[number]
			column_counter = 0
			point_counter = -1
			for point in bit_map:
				point_counter += 1
				if (point_counter % 5 == 0):
					point_counter = 0
					column_counter += 1
				if (point == '1'):
					self.draw.point(
						(
							((x - 4) + column_counter),
							(y - (number_counter * 5) - point_counter)
						),
						image_colors['fg']
					)

	def img_x(self, real_x):
		"""Images are drawn at a scale, and have a different origin
		for their coordinate system. This does the translation between
		x in the real world, and x in the image."""

		relative_x = int((real_x - self.img_min_x) / self.scale)
		return relative_x

	def img_y(self, real_y):
		"""Images are drawn at a scale, and have a different origin
		for their coordinate system. This does the translation between
		y in the real world, and y in the image."""

		relative_y = int((real_y - self.img_min_y) / self.scale)
		return self.imgheight - relative_y


class Fix(object):
	"""A Fix is a single datum, a point in time and space.

	Its basic elements are time and location. Each fix is unique. Each
	fix involves only one cat. Each fix can do basic procedures such
	as calculate its distance or time from another fix."""

	def __init__(self, csvrow):
		self.csvrow = csvrow
		self.set_values_from_csv()

		self.status = None # home or away
		self.day_period = 'FIXME' # day or night

	def __repr__(self):
		return 'Fix(csvrow={0!r})'.format(self.csvrow)

	def __str__(self):
		return '{0}, {1}, {2}, {3}, {4}'.format(self.id, self.catid, self.dateobj.strftime(DATE_FMT_ISO), self.x, self.y)

	def set_values_from_csv(self):
		"""Process the raw data from CSV into attributes"""

		self.id = self.csvrow[0]
		self.catid = self.csvrow[1]
		self.dateobj = dateparser.parse(self.csvrow[4])
		self.time = mktime(self.dateobj.timetuple())
		self.x = float(self.csvrow[7])
		self.y = float(self.csvrow[6])

	def distance_from(self, other):
		"""Calculate the distance of this fix from another object."""

		delta_x = math.fabs(self.x - other.x)
		delta_y = math.fabs(self.y - other.y)
		return math.sqrt((delta_x ** 2) + (delta_y ** 2))

	def delay_from(self, other):
		"""Calculate the time offset of this fix from anoethr oject."""

		if isinstance(other, Cluster):
			return math.fabs(self.time - other.end_time)
		else:
			return math.fabs(self.time - other.time)

	def csv_report(self, parent_id, cat_id=False):
		"""Create one line of csv output representing this fix."""

		field_list = [
			parent_id,
			self.id,
			self.dateobj.strftime(DATE_FMT_ISO),
			'{:0.1f}'.format(self.x),
			'{:0.1f}'.format(self.y),
			self.status,
			self.day_period
		]

		# Add the cat ID if requested. Crossings need this.
		if cat_id:
			field_list.insert(1, self.catid)

		sys.stdout.write(','.join(field_list) + '\n')

	def descriptive_report(self, cat_id=False):
		"""Describe this fix in descriptive text output."""

		short_status = {'home': 'O', 'away': '.'}

		field_list = [
			self.id,
			self.dateobj.strftime(DATE_FMT_ISO),
			'{:0.1f}'.format(self.x),
			'{:0.1f}'.format(self.y),
			short_status[self.status]
		]

		# Add the cat ID if requested. Crossings need this.
		if cat_id:
			field_list.insert(0, self.catid)

		sys.stdout.write('    ' + ', '.join(field_list) + '\n')

	def calculate_angle_and_distance(self, other):
		"""Calculate the angle and angular distance of this fix from an object."""

		self.distance_from_center = self.distance_from(other)

		#        0
		#     q4 | q1
		# 270 ---+--- 90
		#     q3 | q2
		#       180

		if self.x >= other.x and self.y >= other.y:
			# Quadrant 1, 0 to 90
			delta_x = self.x - other.x
			delta_y = self.y - other.y

			prelim_angle = math.degrees(math.atan(delta_x / (delta_y + 0.001)))
			self.angle_from_center = prelim_angle

		elif self.x >= other.x:
			# Quadrant 2, 90 to 180
			delta_x = self.x - other.x
			delta_y = other.y - self.y

			prelim_angle = math.degrees(math.atan(delta_y / (delta_x + 0.001)))
			self.angle_from_center = 90.0 + prelim_angle

		elif self.y <= other.y:
			# Quadrant 3, 180 to 270
			delta_x = other.x - self.x
			delta_y = other.y - self.y

			prelim_angle = math.degrees(math.atan(delta_x / (delta_y + 0.001)))
			self.angle_from_center = 180.0 + prelim_angle

		else:
			# Quadrant 4, 270 to 360
			delta_x = other.x - self.x
			delta_y = self.y - other.y

			prelim_angle = math.degrees(math.atan(delta_y / (delta_x + 0.001)))
			self.angle_from_center = 270.0 + prelim_angle


class Trail(GraphicBase):
	"""A Trail is a series of Fixes in chronological order.

	Where fixes are a lot of points, A Trail is the theoretical line
	that connects those points and demonstrates the order in which the
	cat passed through them. Each cat has a trail that is unique and
	distinct."""

	def __init__(self, catid):
		self.fixes = list()
		self.catid = catid
		self.start_time = 0
		self.start_dateobj = False
		self.end_time = sys.maxint
		self.end_dateobj = False

		self.clusters = list()

	def order_by_time(self):
		"""Put all of the fixes in order by time."""

		self.fixes = sorted(self.fixes, key=lambda fix: fix.time)

	def remove_duplicates(self):
		"""Ensure that no two fixes have the same time."""

		seen = dict()
		unique = list()
		for fix in self.fixes:
			if fix.time in seen:
				sys.stderr.write('WARNING: Two points with the same timestamp found! One removed.\n')
				for unique_fix in unique:
					if unique_fix.time == fix.time:
						sys.stderr.write('     Kept: {0}\n'.format(unique_fix))
				sys.stderr.write('Discarded: {0}\n\n'.format(fix))
				continue
			seen[fix.time] = 1
			unique.append(fix)
		self.fixes = unique

	def find_bounds(self):
		"""Find how far in each direction the data extends."""

		x_list = [fix.x for fix in self.fixes]
		y_list = [fix.y for fix in self.fixes]

		self.max_x = max(x_list)
		self.min_x = min(x_list)
		self.max_y = max(y_list)
		self.min_y = min(y_list)

		self.spread_x = self.max_x - self.min_x
		self.spread_y = self.max_y - self.min_y

		self.x = self.min_x + (self.spread_x / 2)
		self.y = self.min_y + (self.spread_y / 2)

	def calculate_angles(self):
		"""Calculate the angle and angular distance for every fix."""

		for fix in self.fixes:
			fix.calculate_angle_and_distance(self)

	def filter_by_date(self):
		"""Remove any fixes that don't fall between the start and end dates."""

		self.fixes = [fix for fix in self.fixes if self.start_time <= fix.time <= self.end_time]


class Cluster(GraphicBase):
	"""A Cluster is a collection of Fixes that are close in space and time.

	A Cluster is a way of interpreting a Trail, by finding places
	where a cat spent a significant amount of time. Each Trail may or
	may not have any Clusters."""

	def __init__(self, first_fix):
		self.home_fixes = [first_fix]
		self.away_fixes = list()
		self.all_fixes = [first_fix]
		self.id = first_fix.dateobj.strftime(DATE_FMT_ID)
		self.catid = first_fix.catid

	def distance_from(self, other):
		"""Calculate the distance of this cluster form another object."""

		delta_x = math.fabs(self.x - other.x)
		delta_y = math.fabs(self.y - other.y)
		return math.sqrt((delta_x ** 2) + (delta_y ** 2))

	def delay_from(self, other):
		"""Calculate the time offset of this cluster from another object."""

		# This assumes that comparisons are made in chronological
		# order, where the current item (self) is later in the
		# chronology than the one it is being compared to (other).

		if isinstance(other, Cluster):
			time_separation = self.start_time - other.end_time
			if time_separation <= 0:
				return 0.0
			else:
				return time_separation
		else:
			return math.fabs(self.start_time - other.time)

	def add_fix(self, fix):
		"""Incorporate a new fix into the cluster."""

		self.all_fixes.append(fix)

		if (fix.status == 'home'):
			self.home_fixes.append(fix)
			self.recalculate_core_data()
		elif (fix.status == 'away'):
			self.away_fixes.append(fix)

	def recalculate_core_data(self):
		"""Recalculate the core data, notably used when a fix as added."""

		self.start_time = self.home_fixes[0].time
		self.start_dateobj = self.home_fixes[0].dateobj
		self.end_time = self.home_fixes[-1].time
		self.end_dateobj = self.home_fixes[-1].dateobj

		self.elapsed_time = self.end_time - self.start_time

		sum_x = 0
		sum_y = 0
		for fix in self.home_fixes:
			sum_x += fix.x
			sum_y += fix.y

		self.x = sum_x / len(self.home_fixes)
		self.y = sum_y / len(self.home_fixes)

	def calculate_averages(self):
		"""Calculate the extremes and averages, after all fixes have landed."""

		x_list = [fix.x for fix in self.all_fixes]
		y_list = [fix.y for fix in self.all_fixes]

		self.max_x = max(x_list)
		self.min_x = min(x_list)
		self.max_y = max(y_list)
		self.min_y = min(y_list)

		self.spread_x = self.max_x - self.min_x
		self.spread_y = self.max_y - self.min_y

		sum_distance = 0
		for home_fix in self.home_fixes:
			sum_distance += home_fix.distance_from(self)
		self.avg_distance = sum_distance / len(self.home_fixes)

		self.max_excursion = 0
		for away_fix in self.away_fixes:
			fix_excursion = away_fix.distance_from(self)
			if fix_excursion > self.max_excursion:
				self.max_excursion = fix_excursion

		self.fidelity = 100.0 * (float(len(self.home_fixes)) / len(self.all_fixes))

		short_status = {'home': 'O', 'away': '.'}
		away_pattern = ''
		for fix in self.all_fixes:
			away_pattern += short_status[fix.status]
		self.away_pattern = away_pattern


class DataPool(GraphicBase):
	"""A DataPool is a collection of Fixes belonging to different cats.

	It has all the data of the original data file, plus the ability to
	work with that data. A Datapool is used for search-based functions
	like find_crossings and find_whodunit."""

	def __init__(self):
		self.fixes = list()
		self.start_time = 0
		self.start_dateobj = False
		self.end_time = sys.maxint
		self.end_dateobj = False
		self.x = 0
		self.y = 0

	def order_by_time(self):
		"""Put all fixes in order by time."""

		self.fixes = sorted(self.fixes, key=lambda fix: fix.time)

	def filter_by_date(self):
		"""Remove any fixes that don't fall between the start and end time."""

		self.fixes = [fix for fix in self.fixes if self.start_time <= fix.time <= self.end_time]

	def filter_by_location(self, distance_limit):
		"""Remove any fixes that are not within a given distance from the center."""

		self.fixes = [fix for fix in self.fixes if fix.distance_from(self) <= distance_limit]

	def find_bounds(self):
		"""Find how far in each direction the data extends."""

		x_list = [fix.x for fix in self.fixes]
		y_list = [fix.y for fix in self.fixes]

		self.max_x = max(x_list)
		self.min_x = min(x_list)
		self.max_y = max(y_list)
		self.min_y = min(y_list)

		self.spread_x = self.max_x - self.min_x
		self.spread_y = self.max_y - self.min_y

		if not self.x:
			self.x = self.min_x + (self.spread_x / 2)

		if not self.y:
			self.y = self.min_y + (self.spread_y / 2)

	def find_catids(self):
		"""Get the ID of each cat who is represented in the data."""

		catids = list()
		seen = dict()
		for fix in self.fixes:
			if fix.catid in seen:
				continue
			seen[fix.catid] = 1
			catids.append(fix.catid)

		self.catids = sorted(catids)

	def find_cat_colors(self):
		"""For every cat, find their unique color."""

		self.cat_colors = dict()
		for catid in self.catids:
			self.cat_colors[catid] = catid_to_color(catid)

	def remove_duplicates(self):
		"""Ensure that no two fixes, from the same cat, have the same time."""

		unique = list()
		seen = dict()
		for fix in self.fixes:
			fix_id = '{0}-{1}'.format(fix.catid, fix.time)
			if fix_id in seen:
				sys.stderr.write('WARNING: Two points with the same timestamp found. One removed.\n')
				for unique_fix in unique:
					unique_fix_id = '{0}-{1}'.format(unique_fix.catid, unique_fix.time)
					if unique_fix_id == fix_id:
						sys.stderr.write('     Kept: {0}\n'.format(unique_fix))
				sys.stderr.write('Discarded: {0}\n\n'.format(fix))
				continue
			seen[fix_id] = 1
			unique.append(fix)
		self.fixes = unique




# FUNCTIONS

def find_catids(datafile_path):
	"""Scan the CSV file to learn what cat IDs it contains."""

	catid_regex = '^(M|F)[\d]+$'

	with open(datafile_path, 'rb') as datafile:
		csvrows = csvreader(datafile)
		seen = dict()
		catids = list()
		for csvrow in csvrows:
			try:
				if csvrow[1] in seen:
					continue

				regex_match = re.match(catid_regex, csvrow[1], re.I)
				if regex_match:
					catids.append(csvrow[1])
					seen[csvrow[1]] = 1
			except IndexError:
				continue

	if len(catids) > 0:
		return catids
	else:
		return False

def catid_to_color(catid):
	"""Turn a cat id into a unique color in a reproducible way."""

	# Expected format of the cat id is M123 and F123, amount of digits can vary
	regex_match = re.match('^(M|F)[\d]+$', catid, re.I)

	if not regex_match:
		return '#808080'

	cat_division = catid[0].lower()
	cat_numbers = catid[1:]

	if len(cat_numbers) > 3:
		cat_numbers[-3:]

	if len(cat_numbers) < 3:
		cat_numbers = '{0:0>3}'.format(cat_numbers)

	if int(cat_numbers) % 6 == 0:
		tier = 6
	elif int(cat_numbers) % 5 == 0:
		tier = 5
	elif int(cat_numbers) % 4 == 0:
		tier = 4
	elif int(cat_numbers) % 3 == 0:
		tier = 3
	elif int(cat_numbers) % 2 == 0:
		tier = 2
	else:
		tier = 1

	# Turn three-digit id into hex ready string
	format_map = {
		1: '{0}{2}{1}{1}{2}{0}',
		2: '{2}{2}{0}{1}{1}{0}',
		3: '{1}{2}{2}{1}{0}{0}',
		4: '{2}{2}{1}{1}{0}{0}',
		5: '{0}{2}{2}{1}{1}{0}',
		6: '{1}{2}{0}{1}{2}{0}'
	}
	sixstr = format_map[tier].format(cat_numbers[0], cat_numbers[1], cat_numbers[2])

	if cat_division == 'm':
		return '#{0:02X}{1:02X}{2:02X}'.format((186 - int(sixstr[0:2])), (220 - int(sixstr[2:4])), (254 - int(sixstr[4:6])))
	else:
		return '#{0:02X}{1:02X}{2:02X}'.format((254 - int(sixstr[0:2])), (220 - int(sixstr[2:4])), (186 - int(sixstr[4:6])))

def comma_string_to_list(comma_string):
	"""Convert comma-separated argument from command line into a list."""

	return comma_string.split(',')

def date_string_to_objects(date_str):
	"""Convert date string argument from command line into useful objects."""

	if not date_str:
		return False

	if date_str == '0':
		return False

	dateobj = dateparser.parse(date_str)
	return (dateobj, mktime(dateobj.timetuple()))

def hours_arg_to_seconds(hours_arg):
	"""Convert hour string argument from command line into seconds as an integer."""

	seconds = int(hours_arg) * 3600
	return seconds

def check_file_arg(file_arg):
	"""Check the validity of a file argument passed from the command line."""

	trylist = [file_arg, os.path.join(os.getcwd(), file_arg), os.path.expanduser(file_arg)]

	for path in trylist:
		if os.path.isfile(path):
			return os.path.abspath(path)

	# If we didn't turn up a valid file, raise an error
	raise argparse.ArgumentTypeError('Not a valid file: {0}'.format(file_arg))

def check_dir_arg(dir_arg):
	"""Check the validity of a directory argument passed from the command line."""

	trylist = [dir_arg, os.path.dirname(dir_arg), os.path.join(os.getcwd(), dir_arg), os.path.expanduser(dir_arg)]

	for path in trylist:
		if os.path.isdir(path):
			return os.path.abspath(path)

	# If we didn't turn up a valid dir, raise an error
	raise argparse.ArgumentTypeError('Not a valid dir: {0}'.format(dir_arg))

def constrain_integer(original_value, minimum_value, maximum_value):
	"""Ensures that a user-supplied integer value is in a reasonable range."""

	if minimum_value <= original_value <= maximum_value:
		return original_value
	if original_value < minimum_value:
		return minimum_value
	if original_value > maximum_value:
		return maximum_value

def process_dates_for_filename(start_date, end_date):
	"""Produce a date string suitable for use in a file name."""

	output = ''

	if start_date and end_date:
		output += '-{0}_to_{1}'.format(start_date[0].strftime(DATE_FMT_ID_SHORT), end_date[0].strftime(DATE_FMT_ID_SHORT))
	elif start_date:
		output += '-{0}_to_present'.format(start_date[0].strftime(DATE_FMT_ID_SHORT))
	elif end_date:
		output += '-beginning_to_{0}'.format(end_date[0].strftime(DATE_FMT_ID_SHORT))

	return output

def create_cluster_filename(catid, start_date=False, end_date=False, clusterid=False):
	"""Create a filename for cluster output based on essential settings."""

	filename = 'clusters'
	filename += '-{0}'.format(catid)
	filename += process_dates_for_filename(start_date, end_date)

	if clusterid:
		filename += '-{0}'.format(clusterid)

	return filename

def create_territory_filename(start_date=False, end_date=False, catids=False):
	"""Create a filename for territory output based on essential settings."""

	filename = 'territories'
	filename += process_dates_for_filename(start_date, end_date)

	if catids:
		filename += '-{0}'.format('_'.join(catids))
	else:
		filename += '-all'

	return filename

def create_crossing_filename(start_date=False, end_date=False, catids=False, crossingid=False):
	"""Create a filename for crossing output based on essential settings."""

	filename = 'crossings'
	filename += process_dates_for_filename(start_date, end_date)

	if catids:
		filename += '-{0}'.format('_'.join(catids))
	else:
		filename += '-all'

	if crossingid:
		filename += '-{0}'.format(crossingid)

	return filename

def create_whodunit_filename(date, x, y):
	"""Create a filename for whodunit output based on essential settings."""

	filename = 'whodunit'
	filename += '-{0}'.format(date[0].strftime(DATE_FMT_ID_SHORT))
	filename += '-{0}'.format(x)
	filename += '-{0}'.format(y)
	return filename


# BEGIN SCRIPT

basepath = os.getcwd()

# Read the config file
configfilepath = os.path.join(basepath, 'catamount.conf')

if not os.path.isfile(configfilepath):
	print('The config file seems to be missing. Check: {0}'.format(configfilepath))
	sys.exit()

# Use strings, even for integers, because that's what config file and command line deliver
fallback_values = {
	'datafile_path': 'data/ALLGPS.csv',
	'outdir_path': 'output',
	'radius': '200',
	'time_cutoff': '144',
	'minimum_count': '0',
	'minimum_stay': '0',
	'start_date': '0',
	'end_date': '0',
	'dot_size': '4',
	'perimeter_resolution': '9'
}

config = RawConfigParser(fallback_values)
config.read(configfilepath)

cfg_datafile_path = config.get('Global_Settings', 'datafile_path')
cfg_outdir_path = config.get('Global_Settings', 'outdir_path')

cfg_cluster_radius = config.get('Cluster_Settings', 'radius')
cfg_cluster_time_cutoff = config.get('Cluster_Settings', 'time_cutoff')
cfg_cluster_minimum_count = config.get('Cluster_Settings', 'minimum_count')
cfg_cluster_minimum_stay = config.get('Cluster_Settings', 'minimum_stay')
cfg_cluster_start_date = config.get('Cluster_Settings', 'start_date')
cfg_cluster_end_date = config.get('Cluster_Settings', 'end_date')

cfg_territory_dot_size = config.get('Territory_Settings', 'dot_size')
cfg_territory_perimeter_resolution = config.get('Territory_Settings', 'perimeter_resolution')
cfg_territory_start_date = config.get('Territory_Settings', 'start_date')
cfg_territory_end_date = config.get('Territory_Settings', 'end_date')

cfg_crossing_radius = config.get('Crossing_Settings', 'radius')
cfg_crossing_time_cutoff = config.get('Crossing_Settings', 'time_cutoff')
cfg_crossing_start_date = config.get('Crossing_Settings', 'start_date')
cfg_crossing_end_date = config.get('Crossing_Settings', 'end_date')

cfg_whodunit_radius = config.get('Whodunit_Settings', 'radius')
cfg_whodunit_time_cutoff = config.get('Whodunit_Settings', 'time_cutoff')

cfg_matchsurvey_survey_file_path = config.get('Match_Survey_Settings', 'survey_file_path')
cfg_matchsurvey_radius = config.get('Match_Survey_Settings', 'radius')
cfg_matchsurvey_time_cutoff = config.get('Match_Survey_Settings', 'time_cutoff')
