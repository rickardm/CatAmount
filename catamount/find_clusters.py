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

# This file provides facilities to identify one cat's time/space groupings, called clusters.

# IMPORT

from catamount.common import *


# CLASSES

class FCTrail(Trail):
	"""An extension of a plain Trail, adding things that are useful for finding clusters.

	It adds the ability to find clusters, do calculations, and display clusters."""

	def __init__(self, catid, radius, time_cutoff, minimum_count, minimum_stay):
		Trail.__init__(self, catid)

		self.radius = radius
		self.time_cutoff = time_cutoff
		self.minimum_count = minimum_count
		self.minimum_stay = minimum_stay

		self.legend_start_date = '0'
		self.legend_end_date = '0'

	def find_clusters(self):
		"""Search through a list of fixes and identify clusters."""

		# Start with a new list of all points, and an empty mapping for used points
		fixes = list(self.fixes)
		already_used = dict()

		# Consider each point in turn
		while fixes:
			current_item = fixes.pop(0)

			# Don't try to make a cluster from a point that's already in another cluster
			if current_item.time in already_used:
				continue

			# Begin searching ahead in the chronology to find points matching the current one
			if fixes:
				potential_away_fixes = list()

				for fix in fixes:

					# If this fix has already been used in another cluster, don't consider it
					if fix.time in already_used:
						continue

					# If we reach the time cutoff, stop searching.
					if fix.delay_from(current_item) > self.time_cutoff:
						break

					# If the first two tests succeeded, and distance matches, we have a match
					if fix.distance_from(current_item) <= self.radius:

						# Create a new cluster if necessary
						if isinstance(current_item, Fix):
							first_fix = current_item
							first_fix.status = 'home'
							current_item = FCCluster(first_fix, self.radius, self.time_cutoff, self.minimum_count, self.minimum_stay, self.legend_start_date, self.legend_end_date)

						# Add any away points that may have accumulated.
						# This should come before adding the home fix, for chronology
						for away_fix in potential_away_fixes:
							away_fix.status = 'away'
							current_item.add_fix(away_fix)

						# Add the matching point to the cluster.
						# This should come after adding each away fix, for chronology
						fix.status = 'home'
						current_item.add_fix(fix)

						# Empty the list of potential away fixes
						potential_away_fixes = list()

						# Make a note that this fix has already appeared in a cluster
						already_used[fix.time] = 1

					# If the current point did not match, it is a potential away fix
					else:
						potential_away_fixes.append(fix)

			# This is seen when we are able to pop one, but not search ahead.
			# That means it's the last point from the list, unable to match anything
			else:
				pass

			# All attempts to create a cluster around the current_item have now finished

			# If we made a cluster, commit it to the list
			if isinstance(current_item, Cluster):
				self.clusters.append(current_item)
				current_item = False
			# If we did not make a cluster, current_item must be a fix that didn't match anything
			else:
				pass

		# When we run out of fixes to examine, we may still have a cluster that needs to be committed
		if isinstance(current_item, Cluster):
			self.clusters.append(current_item)


	def calculate_cluster_averages(self):
		"""Call the averaging function for each cluster."""

		for cluster in self.clusters:
			cluster.calculate_averages()

	def filter_clusters_by_count(self):
		"""Remove clusters that have fewer than the minumum number of clusters."""

		self.clusters = [cluster for cluster in self.clusters if len(cluster.home_fixes) >= self.minimum_count]

	def filter_clusters_by_stay(self):
		"""Remove clusters that have less than the minimum amount of elapsed time."""

		self.clusters = [cluster for cluster in self.clusters if cluster.elapsed_time >= self.minimum_stay]

	def return_cluster_by_id(self, clusterid):
		"""Return a certain cluster based on its ID."""

		for cluster in self.clusters:
			if cluster.id == clusterid:
				return cluster
		return False

	def csv_report(self, all_points):
		"""Create a CSV report describing the clusters that were found."""

		field_list = ['Cluster_ID', 'Start_Date', 'End_Date', 'Elapsed', 'Center_X', 'Center_Y', 'Home', 'Away', 'All', 'Avg_Dist', 'Max_Excurs', 'Fidelity']
		sys.stdout.write(','.join(field_list) + '\n')

		for cluster in self.clusters:
			cluster.csv_report()

		if all_points:
			sys.stdout.write('\n')

			fix_field_list = ['Cluster_ID', 'Fix_ID', 'Date', 'X', 'Y', 'Status', 'Day_Pd']
			sys.stdout.write(','.join(fix_field_list) + '\n')

			empty_field_list = ['', '', '', '', '', '', '']

			for cluster in self.clusters:
				cluster.fixes_csv_report()

				sys.stdout.write(','.join(empty_field_list) + '\n')

	def descriptive_report(self, all_points):
		"""Create a descriptive report describing the clusters that were found."""

		output = '\nCluster Settings Are As Follows:\n'
		output += '  * Cat ID: {0}\n'.format(self.catid)
		output += '  * Radius: {0} meters\n'.format(self.radius)
		output += '  * Time Cutoff: {0} hours\n'.format(self.time_cutoff / 3600)
		output += '  * Start Date: {0}\n'.format(self.legend_start_date)
		output += '  * End Date: {0}\n'.format(self.legend_end_date)
		output += '  * Minimum Count: {0} fixes\n'.format(self.minimum_count)
		output += '  * Minimum Stay: {0} hours\n'.format(self.minimum_stay / 3600)
		output += '\nClusters Found:\n\n'
		sys.stdout.write(output)

		for cluster in self.clusters:
			cluster.descriptive_report(all_points)

	def draw_object_specific_graphics(self):
		"""Draw graphics of all clusters on the feedback image."""

		# Write information about the image across the bottom
		column_1 = list()		
		column_1.append(('Cat ID', self.catid))
		column_1.append(('Radius', '{0} meters'.format(self.radius)))
		column_1.append(('Time Cutoff', '{0} hours'.format(self.time_cutoff / 3600)))
		column_1.append(('Start Date', self.legend_start_date))
		column_1.append(('End Date', self.legend_end_date))
		column_1.append(('Min. Count', '{0} fixes'.format(self.minimum_count)))
		column_1.append(('Min. Stay', '{0} hours'.format(self.minimum_stay / 3600)))

		column_2 = list()
		column_2.append(('Clusters Found', '{0}'.format(len(self.clusters))))
		column_2.append(('X Range', '{0:0.1f} km'.format(self.spread_x / 1000)))
		column_2.append(('Y Range', '{0:0.1f} km'.format(self.spread_y / 1000)))
		column_2.append(('Scale', '1 px = {0} m'.format(self.scale)))

		self.legend_info = [column_1, column_2]
		self.draw_legend()

		# Create circles around each cluster
		for cluster in self.clusters:
			img_x = self.img_x(cluster.x)
			img_y = self.img_y(cluster.y)
			radius = self.radius / self.scale
			self.fgdraw.ellipse(
				[(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
				image_colors['cluster'],
				image_colors['cluster']
			)

		# Create a scatter plot of all fixes
		for fix in self.fixes:
			img_x = self.img_x(fix.x)
			img_y = self.img_y(fix.y)
			self.fgdraw.point((img_x, img_y), image_colors['fg'])


class FCCluster(Cluster):
	"""An extension of a plain Cluster, adding things that are useful for display.
	It adds the ability to plot clusters, and output text reports."""

	def __init__(self, first_fix, radius, time_cutoff, minimum_count, minimum_stay, legend_start_date, legend_end_date):
		Cluster.__init__(self, first_fix)

		self.radius = radius
		self.time_cutoff = time_cutoff
		self.minimum_count = minimum_count
		self.minimum_stay = minimum_stay

		self.legend_start_date = legend_start_date
		self.legend_end_date = legend_end_date

	def csv_report(self):
		"""Create one line of CSV output for this cluster."""

		field_list = [
			self.id,
			self.start_dateobj.strftime(DATE_FMT_ISO),
			self.end_dateobj.strftime(DATE_FMT_ISO),
			'{:0.2f}'.format(self.elapsed_time / 3600),
			'{:0.1f}'.format(self.x),
			'{:0.1f}'.format(self.y),
			'{}'.format(len(self.home_fixes)),
			'{}'.format(len(self.away_fixes)),
			'{}'.format(len(self.all_fixes)),
			'{:0.1f}'.format(self.avg_distance),
			'{:0.1f}'.format(self.max_excursion),
			'{:0.1f}'.format(self.fidelity)
		]
		sys.stdout.write(','.join(field_list) + '\n')

	def fixes_csv_report(self):
		"""Have each fix in this cluster do a csv report."""

		for fix in self.all_fixes:
			fix.csv_report(self.id)

	def descriptive_report(self, all_points):
		"""Create a descriptive stanza for this cluster."""

		output = 'Cluster {}\n'.format(self.id)
		output += '  Dates: From {} to {} (utc)\n'.format(self.start_dateobj.strftime(DATE_FMT_ISO), self.end_dateobj.strftime(DATE_FMT_ISO))
		output += '  Elapsed Time: {:0.2f} hours\n'.format(self.elapsed_time / 3600)
		output += '  Center Location: {:0.2f} east, {:0.2f} north (NAD27)\n'.format(self.x, self.y)
		output += '  Points: {} in cluster, {} away from cluster, {} total\n'.format(len(self.home_fixes), len(self.away_fixes), len(self.all_fixes))
		output += '  Home/Away Pattern (O = home, . = away): "{}"\n'.format(self.away_pattern)
		output += '  Average Distance From Center (Inside Cluster): {:0.1f} meters\n'.format(self.avg_distance)
		if (self.away_fixes):
			output += '  Max Excursion From Center (Outside Cluster): {:0.1f} meters\n'.format(self.max_excursion)
		else:
			output += '  Max Excursion From Center (Outside Cluster): None\n'
		output += '  Site Fidelity ((No. Inside / Total No.) * 100): {:0.2f}%\n'.format(self.fidelity)
		output += '  Average Time Between Points: {:0.1f} hours\n'.format((self.elapsed_time / (len(self.all_fixes) - 1)) / 3600.0)
		sys.stdout.write(output)

		if all_points:
			sys.stdout.write('  All Points In This Cluster:\n')
			for fix in self.all_fixes:
				fix.descriptive_report()

		sys.stdout.write('\n')

	def draw_object_specific_graphics(self):
		"""Draw graphics about this one cluster on the feedback image."""

		# Write information about the image across the bottom
		column_1 = list()
		column_1.append(('Cat ID', self.catid))
		column_1.append(('Radius', '{0} meters'.format(self.radius)))
		column_1.append(('Time Cutoff', '{0} hours'.format(self.time_cutoff / 3600)))
		column_1.append(('Start Date', self.legend_start_date))
		column_1.append(('End Date', self.legend_end_date))
		column_1.append(('Min. Count', '{0}'.format(self.minimum_count)))
		column_1.append(('Min. Stay', '{0} hours'.format(self.minimum_stay / 3600)))

		column_2 = list()
		column_2.append(('Cluster ID', self.id))
		column_2.append(('Start Date', self.start_dateobj.strftime(DATE_FMT_ISO_SHORT)))
		column_2.append(('End Date', self.end_dateobj.strftime(DATE_FMT_ISO_SHORT)))
		column_2.append(('Center X', '{0:0.1f}'.format(self.x)))
		column_2.append(('Center Y', '{0:0.1f}'.format(self.y)))
		column_2.append(('Fidelity', '{0}/{1}, {2:0.2f}%'.format(len(self.home_fixes), len(self.all_fixes), self.fidelity)))
		column_2.append(('Scale', '1 px = {0} m'.format(self.scale)))

		self.legend_info = [column_1, column_2]
		self.draw_legend()

		# Coordinates for the center of the cluster
		img_x = self.img_x(self.x)
		img_y = self.img_y(self.y)

		# Draw a circle representing the design radius of the cluster
		radius = self.radius / self.scale
		circleimg = Image.new('RGB', (radius * 2, radius * 2), image_colors['cluster'])
		circlemask = Image.new('L', (radius * 2, radius * 2), '#000000')
		circlemaskdraw = ImageDraw.Draw(circlemask)
		circlemaskdraw.ellipse([(0, 0), ((radius * 2) - 1, (radius * 2) - 1)], '#000000', '#FFFFFF')
		self.fgimage.paste(circleimg, (img_x - radius, img_y - radius), circlemask)

		# Draw a line between all fixes
		fix_line_coords = list()
		for fix in self.all_fixes:
			pt_img_x = self.img_x(fix.x)
			pt_img_y = self.img_y(fix.y)
			fix_line_coords.append((pt_img_x, pt_img_y))
		self.fgdraw.line(fix_line_coords, image_colors['trail'])

		# Draw a cross at the center of the cluster
		self.fgdraw.line([(img_x - 2, img_y), (img_x + 2, img_y)], image_colors['cluster'])
		self.fgdraw.line([(img_x, img_y - 2), (img_x, img_y + 2)], image_colors['cluster'])

		# Create a scatter plot of all fixes
		for fix in self.all_fixes:
			pt_img_x = self.img_x(fix.x)
			pt_img_y = self.img_y(fix.y)
			self.fgdraw.point((pt_img_x, pt_img_y), image_colors['fg'])



