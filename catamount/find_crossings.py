#!/usr/bin/env python3

# CatAmount analyzes GPS collar data to find time/space relationships.
# Copyright (C) 2012-2019 Michael Rickard
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

# This file provides facilities to find time/space groupings of several cats, called crossings.

# IMPORT

import sys

from PIL import Image
from PIL import ImageDraw

import catamount.common as catcm


# CONSTANTS/GLOBALS

crossing_dot_size = 4


# CLASSES

class FXDataPool(catcm.DataPool):
	"""An extension to a plain DataPool to add things for finding crossings.

	This adds the ability to find crossings and display them."""

	def __init__(self, radius, time_cutoff):
		catcm.DataPool.__init__(self)

		self.radius = radius
		self.time_cutoff = time_cutoff

		self.legend_start_date = '0'
		self.legend_end_date = '0'

	def find_clusters(self):
		"""Search through a list of fixes and identify clusters.

		This is based on find_clusters for a single cat, then adapted
		to find clusters across multiple cats."""

		self.clusters = list()

		fixes = list(self.fixes) # A new list of all fixes
		already_used = dict() # A map of which points have already been used
		cats_involved = dict() # A map of which cats are involved in the cluster

		# Consider each fix in the list in turn
		while fixes:
			# Take the first fix from the list
			current_item = fixes.pop(0)

			# If this fix has already been used in another cluster, skip it
			if '{0}-{1}'.format(current_item.catid, current_item.time) in already_used:
				continue

			# Search ahead in the list of fixes, looking for matches
			if fixes:
				# This list keeps track of unmatched points in case they turn out to be "away" points
				potential_away_fixes = list()

				for fix in fixes:
					# If this fix has already been used in another cluster, skip it
					if '{0}-{1}'.format(fix.catid, fix.time) in already_used:
						continue

					# If we have gone past the time limit we can stop searching forward
					if fix.delay_from(current_item) > self.time_cutoff:
						break

					# If time is okay and distance is okay, we found a match
					if fix.distance_from(current_item) <= self.radius:

						# Create a new cluster if necessary
						if isinstance(current_item, catcm.Fix):
							first_fix = current_item
							first_fix.status = 'home'
							current_item = catcm.Cluster(first_fix)
							cats_involved[first_fix.catid] = 1

						if not fix.catid in cats_involved:
							cats_involved[fix.catid] = 1

						# Add any away fixes that have accumulated
						for away_fix in potential_away_fixes:
							# Only add away fixes if they are for a cat already involved in this cluster
							if away_fix.catid in cats_involved:
								away_fix.status = 'away'
								current_item.add_fix(away_fix)

						# Add the matched fix to the cluster
						fix.status = 'home'
						current_item.add_fix(fix)

						# Empty the potential away points list
						potential_away_fixes = list()

						# Mark the matched point as having already appeared in a cluster
						already_used['{0}-{1}'.format(fix.catid, fix.time)] = 1

					# If we didn't find a match, this point becomes a potential away point
					else:
						potential_away_fixes.append(fix)

			# This is seen when we are able to pop one, but not search ahead
			else:
				pass

			# All attempts to create a cluster aroud the current fix have finished

			# If we made a cluster, time to commit it to the list
			if isinstance(current_item, catcm.Cluster):
				self.clusters.append(current_item)
				current_item = False
				cats_involved = dict()
			# If we did not make a cluster, this is an unmatched point that is okay to drop
			else:
				pass

		# When all fixes have been examined, we may still have a
		# cluster that needs to be committed
		if isinstance(current_item, catcm.Cluster):
			self.clusters.append(current_item)

	def clusters_to_crossings(self):
		"""Turn a cluster into a crossing if it involves more than one cat."""

		self.crossings = list()
		for cluster in self.clusters:
			# Get a list of cats involved in the cluster
			catids = list()
			seen = dict()
			for fix in cluster.all_fixes:
				if fix.catid in seen:
					continue
				catids.append(fix.catid)
				seen[fix.catid] = 1

			# At this point we can stop if the cluster only involves one cat
			if len(catids) < 2:
				continue

			# Do the following if the cluster involves more than one cat
			catids = sorted(catids)
			crossingid = '{0}-{1}'.format(cluster.home_fixes[0].dateobj.strftime(catcm.DATE_FMT_ID), '_'.join(catids))
			self.crossings.append(
				Crossing(crossingid, cluster.home_fixes, cluster.away_fixes, cluster.all_fixes, catids, self.radius, self.time_cutoff, self.legend_start_date, self.legend_end_date)
			)

	def return_crossing_by_id(self, crossingid):
		"""Return a certain crossing based on its ID."""

		for crossing in self.crossings:
			if crossing.id == crossingid:
				return crossing
		return False

	def find_bounds(self):
		"""Find how far in each direction the data extends.

		We redefine the base class function, in order to pull data
		from the crossings found rather than the whole datapool."""

		x_list = [crossing.x for crossing in self.crossings]
		y_list = [crossing.y for crossing in self.crossings]

		# Add radius amount, because x and y of the crossing are the center of the crossing
		self.max_x = max(x_list) + self.radius
		self.min_x = min(x_list) - self.radius
		self.max_y = max(y_list) + self.radius
		self.min_y = min(y_list) - self.radius

		self.spread_x = self.max_x - self.min_x
		self.spread_y = self.max_y - self.min_y

		self.x = self.min_x + (self.spread_x / 2)
		self.y = self.min_y + (self.spread_y / 2)

	def find_catids(self):
		"""Find which cats were involved in the current set of crossings.

		We redefine the base class function, in order to pull data
		from the crossings found rather than the whole datapool."""

		catids = list()
		seen = dict()
		for crossing in self.crossings:
			for catid in crossing.catids:
				if catid in seen:
					continue
				catids.append(catid)
				seen[catid] = 1
		self.catids = sorted(catids)

	def csv_report(self, all_points):
		"""Create a CSV report describing all the crossings that were found."""

		field_list = ['Cross_ID', 'Start_Date', 'End_Date', 'Elapsed', 'Center_X', 'Center_Y', 'No._Cats', 'A_Time', 'A_Dist', 'B_Time', 'B_Dist', 'C_Time', 'C_Dist']
		sys.stdout.write(','.join(field_list) + '\n')

		for crossing in self.crossings:
			crossing.csv_report()

		if all_points:
			sys.stdout.write('\n')

			fix_field_list = ['Cross_ID', 'Cat_ID', 'Fix_ID', 'Date', 'X', 'Y', 'Status', 'Day_Pd']
			sys.stdout.write(','.join(fix_field_list) + '\n')

			empty_field_list = ['', '', '', '', '', '', '', '']

			for crossing in self.crossings:
				crossing.fixes_csv_report()

				sys.stdout.write(','.join(empty_field_list) + '\n')

	def descriptive_report(self, all_points):
		"""Create a descriptive report describing all the crossings that were found."""

		output = '\nCrossing Settings Are As Follows:\n'
		output += '  * Radius: {0} meters\n'.format(self.radius)
		output += '  * Time Cutoff: {0} hours\n'.format(self.time_cutoff // 3600)
		output += '  * Start Date: {0}\n'.format(self.legend_start_date)
		output += '  * End Date: {0}\n'.format(self.legend_end_date)
		output += '\nCrossings Found:\n\n'
		sys.stdout.write(output)

		for crossing in self.crossings:
			crossing.descriptive_report(all_points)

	def draw_object_specific_graphics(self):
		"""Draw graphics of all crossings on the feedback image."""

		# Write information about the image across the bottom
		column_1 = list()
		column_1.append(('Radius', '{0} meters'.format(self.radius)))
		column_1.append(('Time Cutoff', '{0} hours'.format(self.time_cutoff // 3600)))
		column_1.append(('Start Date', self.legend_start_date))
		column_1.append(('End Date', self.legend_end_date))

		column_2 = list()
		column_2.append(('Crossings Found', '{0}'.format(len(self.crossings))))
		column_2.append(('X Range', '{0:0.1f} km'.format(self.spread_x / 1000)))
		column_2.append(('Y Range', '{0:0.1f} km'.format(self.spread_y / 1000)))
		column_2.append(('Scale', '1 px = {0} m'.format(self.scale)))

		self.legend_info = [column_1, column_2]
		self.draw_legend(True)

		# Draw a faintly colored dot for every away point
		awayimg = Image.new('RGB', (self.imgwidth, self.imgheight), catcm.image_colors['bg'])
		awayimgdraw = ImageDraw.Draw(awayimg)
		awaymask = Image.new('L', (self.imgwidth, self.imgheight), '#000000')
		awaymaskdraw = ImageDraw.Draw(awaymask)
		
		for crossing in self.crossings:
			for away_fix in crossing.away_fixes:
				img_x = self.img_x(away_fix.x)
				img_y = self.img_y(away_fix.y)
				radius = crossing_dot_size / 2
				bigger = crossing_dot_size
				awayimgdraw.ellipse(
					[(img_x - bigger, img_y - bigger), (img_x + bigger, img_y + bigger)],
					self.cat_colors[away_fix.catid], self.cat_colors[away_fix.catid]
				)
				awaymaskdraw.ellipse(
					[(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
					'#404040', '#404040'
				)
		
		self.fgimage.paste(awayimg, (0, 0), awaymask)

		# Draw a colored dot for every home point
		for crossing in self.crossings:
			for home_fix in crossing.home_fixes:
				img_x = self.img_x(home_fix.x)
				img_y = self.img_y(home_fix.y)
				radius = crossing_dot_size / 2
				self.fgdraw.ellipse(
					[(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
					self.cat_colors[home_fix.catid], self.cat_colors[home_fix.catid]
				)

		# Draw a black dot for every point
		for crossing in self.crossings:
			for fix in crossing.all_fixes:
				img_x = self.img_x(fix.x)
				img_y = self.img_y(fix.y)
				self.fgdraw.point((img_x, img_y), catcm.image_colors['fg'])



class Crossing(catcm.Cluster):
	"""A Crossing is a time when two or more cats share the same time and space.

	A Crossing is like a meeting of two or more cats. It is also like
	a Cluster that involves more than one cat."""

	def __init__(self, crossingid, home_fixes, away_fixes, all_fixes, catids, radius, time_cutoff, legend_start_date, legend_end_date):
		self.id = crossingid
		self.home_fixes = sorted(home_fixes, key=lambda home_fix: home_fix.time)
		self.away_fixes = sorted(away_fixes, key=lambda away_fix: away_fix.time)
		self.all_fixes = sorted(all_fixes, key=lambda all_fix: all_fix.time)
		self.catids = catids

		self.radius = radius
		self.time_cutoff = time_cutoff
		self.legend_start_date = legend_start_date
		self.legend_end_date = legend_end_date

		# All points are present when a Crossing is created, so we can go ahead and do averages, sums, etc
		self.recalculate_core_data()
		self.calculate_averages()
		self.find_cat_colors()
		self.find_closest_meeting()

	def find_cat_colors(self):
		"""Get the unique color for each cat involved in this crossing."""

		self.cat_colors = dict()
		for catid in self.catids:
			if catid in self.cat_colors:
				continue

			self.cat_colors[catid] = catcm.catid_to_color(catid)

	def find_closest_meeting(self):
		"""Find which of the points in the crossing constitute the closest meeting.

		Closest meeting is defined as two points, within the crossing
		radius, which have the least time between them."""

		closest_time = sys.maxsize
		closest_meetings = list()

		# For all but one cat id
		for index in range(0, len(self.catids) - 1):
			# Divide home fixes into a query list and field list based on cat id
			query_catid = self.catids[index]
			query_fixes = list()
			field_fixes = list()
			for home_fix in self.home_fixes:
				if home_fix.catid == query_catid:
					query_fixes.append(home_fix)
				else:
					field_fixes.append(home_fix)

			# For every fix in the query list, check every fix in the field
			for query_fix in query_fixes:
				for field_fix in field_fixes:
					# If the time between the fixes is shorter
					if query_fix.delay_from(field_fix) < closest_time:
						# Then we have a new closest meeting
						closest_time = query_fix.delay_from(field_fix)
						closest_meetings.insert(0, (query_fix, field_fix))

		# Keep the top 3
		self.closest_meetings = closest_meetings[0:3]

	def csv_report(self):
		"""Create a CSV report describing this one crossing."""

		field_list = [
			self.id,
			self.start_dateobj.strftime(catcm.DATE_FMT_ISO),
			self.end_dateobj.strftime(catcm.DATE_FMT_ISO),
			'{:0.2f}'.format(self.elapsed_time / 3600),
			'{:0.1f}'.format(self.x),
			'{:0.1f}'.format(self.y),
			'{}'.format(len(self.catids))
		]

		for count in range(0, 3):
			try:
				close_meeting = self.closest_meetings[count]
				first = close_meeting[0]
				second = close_meeting[1]
				field_list.append('{:0.2f}'.format(first.delay_from(second) / 3600))
				field_list.append('{:0.2f}'.format(first.distance_from(second)))
			except IndexError:
				field_list.append('----')
				field_list.append('----')

		sys.stdout.write(','.join(field_list) + '\n')

	def fixes_csv_report(self):
		"""Have each fix in this crossing do a csv report."""

		for fix in self.all_fixes:
			fix.csv_report(self.id, cat_id=True)

	def descriptive_report(self, all_points):
		"""Create a descriptive report describing this one crossing."""

		output = 'Crossing {0}\n'.format(self.id)
		output += '  Cats: {0}\n'.format(', '.join(self.catids))
		output += '  Dates: From {0} to {1} (utc)\n'.format(self.start_dateobj.strftime(catcm.DATE_FMT_ISO), self.end_dateobj.strftime(catcm.DATE_FMT_ISO))
		output += '  Elapsed Time: {0:0.2f} hours\n'.format(self.elapsed_time / 3600)
		output += '  Center Location: {0:0.2f} east, {1:0.2f} north (NAD27)\n'.format(self.x, self.y)
		output += '  Closest Meetings:\n'

		for closest_meeting in self.closest_meetings:
			first = closest_meeting[0]
			second = closest_meeting[1]
			output += '    {0:0.2f} hours, {1:0.2f} meters:\n'.format(first.delay_from(second) / 3600, first.distance_from(second))
			output += '      {0}, {1:0.02f} east, {2:0.02f} north, {3} utc\n'.format(first.catid, first.x, first.y, first.dateobj.strftime(catcm.DATE_FMT_ISO))
			output += '      {0}, {1:0.02f} east, {2:0.02f} north, {3} utc\n'.format(second.catid, second.x, second.y, second.dateobj.strftime(catcm.DATE_FMT_ISO))

		sys.stdout.write(output)
	
		if all_points:
			sys.stdout.write('  All Points In This Crossing:\n')
			for fix in self.all_fixes:
				fix.descriptive_report(cat_id=True)

		sys.stdout.write('\n')

	def draw_object_specific_graphics(self):
		"""Draw graphics about this one crossing on the feedback image."""

		# Write information about the image across the bottom
		column_1 = list()
		column_1.append(('Radius', '{0} meters'.format(self.radius)))
		column_1.append(('Time Cutoff', '{0} hours'.format(self.time_cutoff // 3600)))
		column_1.append(('Start Date', self.legend_start_date))
		column_1.append(('End Date', self.legend_end_date))

		column_2 = list()
		column_2.append(('Crossing ID', self.id))
		column_2.append(('Start Date', self.start_dateobj.strftime(catcm.DATE_FMT_ISO_SHORT)))
		column_2.append(('End Date', self.end_dateobj.strftime(catcm.DATE_FMT_ISO_SHORT)))
		column_2.append(('Center X', '{0:0.1f}'.format(self.x)))
		column_2.append(('Center Y', '{0:0.1f}'.format(self.y)))

		closest = self.closest_meetings[0]
		first = closest[0]
		second = closest[1]
		column_2.append(('Closest', '{0:0.2f} hr, {1:0.2f} m'.format((first.delay_from(second) / 3600), first.distance_from(second))))

		column_2.append(('Scale', '1 px = {0} m'.format(self.scale)))

		self.legend_info = [column_1, column_2]
		self.draw_legend(True)

		# Coordinates for the center of the crossing
		img_x = self.img_x(self.x)
		img_y = self.img_y(self.y)

		# Draw a circle representing the design radius of the crossing
		radius = self.radius / self.scale
		circleimg = Image.new('RGB', (radius * 2, radius * 2), catcm.image_colors['crossing'])
		circlemask = Image.new('L', (radius * 2, radius * 2), '#000000')
		circlemaskdraw = ImageDraw.Draw(circlemask)
		circlemaskdraw.ellipse([(0, 0), ((radius * 2) - 1, (radius * 2) - 1)], '#000000', '#FFFFFF')
		self.fgimage.paste(circleimg, (img_x - radius, img_y - radius), circlemask)

		# Draw a cross at the center of the crossing
		self.fgdraw.line([(img_x - 2, img_y), (img_x + 2, img_y)], catcm.image_colors['crossing'])
		self.fgdraw.line([(img_x, img_y - 2), (img_x, img_y + 2)], catcm.image_colors['crossing'])

		# Draw a faintly colored dot for every away point
		awayimg = Image.new('RGB', (self.imgwidth, self.imgheight), catcm.image_colors['bg'])
		awayimgdraw = ImageDraw.Draw(awayimg)
		awaymask = Image.new('L', (self.imgwidth, self.imgheight), '#000000')
		awaymaskdraw = ImageDraw.Draw(awaymask)
	
		for away_fix in self.away_fixes:
			img_x = self.img_x(away_fix.x)
			img_y = self.img_y(away_fix.y)
			radius = crossing_dot_size / 2
			bigger = crossing_dot_size
			awayimgdraw.ellipse(
				[(img_x - bigger, img_y - bigger), (img_x + bigger, img_y + bigger)],
				self.cat_colors[away_fix.catid], self.cat_colors[away_fix.catid]
			)
			awaymaskdraw.ellipse(
				[(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
				'#404040', '#404040'
			)
		
		self.fgimage.paste(awayimg, (0, 0), awaymask)

		# Draw a colored dot for each home point
		for home_fix in self.home_fixes:
			img_x = self.img_x(home_fix.x)
			img_y = self.img_y(home_fix.y)
			radius = crossing_dot_size / 2
			self.fgdraw.ellipse(
				[(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
				self.cat_colors[home_fix.catid], self.cat_colors[home_fix.catid]
			)

		# Create a scatter plot of all fixes
		for fix in self.all_fixes:
			img_x = self.img_x(fix.x)
			img_y = self.img_y(fix.y)
			self.fgdraw.point((img_x, img_y), catcm.image_colors['fg'])


# FUNCTIONS

def create_filename(start_date=False, end_date=False, catids=False, crossingid=False):
	"""Create a filename for find_crossing text and image output."""

	name_parts = ['crossings']

	date_part = catcm.process_dates_for_filename(start_date, end_date)
	if date_part:
		name_parts.append(date_part)

	if catids:
		name_parts.append('_'.join(catids))
	else:
		name_parts.append('all')

	if crossingid:
		name_parts.append(crossingid.replace('-', '').replace('_', ''))

	return '_'.join(name_parts)
