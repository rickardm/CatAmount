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

# This file provides facilities to identify one cat's time/space groupings, called clusters.

# IMPORT

import sys
import pytz
import time
import datetime

from dateutil import parser as dateparser

import catamount.common as catcm
import catamount.find_clusters as catfc


# GLOBALS

mountain_time = pytz.timezone('US/Mountain') # Assumed time zone of dates in survey file
default_date = datetime.datetime(datetime.MINYEAR, 1, 1, 12, 0) # Noon becomes default hour of dates in survey file

minimum_time = 315536400 # 1980-01-01
maximum_time = 1893456000 # 2030-01-01
minimum_location = {'x': 400000, 'y': 3500000}
maximum_location = {'x': 650000, 'y': 6000000}



# CLASSES

class MSDataPool(catcm.DataPool):
	"""Extension of a plain DataPool, adding things useful for matching field surveys.

	It adds sorting of all fixes into trails, and making a list of all clusters."""

	def __init__(self, radius, time_cutoff):
		catcm.DataPool.__init__(self)

		self.radius = radius
		self.time_cutoff = time_cutoff

		# These two are vestiges of reusing the clustering from find_clusters
		self.minimum_count = 0
		self.minimum_stay = 0

		self.trails = dict()
		self.clusters = list()

	def sort_into_trails(self):
		# First, how many cats are we dealing with?
		self.find_catids()

		# Create a trail for each cat; using FCTrail because it has the clustering method (for now)
		for catid in self.catids:
			new_trail = catfc.FCTrail(catid, self.radius, self.time_cutoff, self.minimum_count, self.minimum_stay)

			self.trails[catid] = new_trail

		# Distribute all fixes into the trail containers
		for fix in self.fixes:
			self.trails[fix.catid].fixes.append(fix)

		# Neaten up the trails that have been created
		for catid in self.catids:
			self.trails[catid].remove_duplicates()
			self.trails[catid].order_by_time()

	def find_all_clusters(self):
		# Have each trail find its own clusters, and add them to the main list
		for catid in self.catids:
			self.trails[catid].find_clusters()

			for cluster in self.trails[catid].clusters:
				self.clusters.append(cluster)

		# Put clusters in chronological order
		self.clusters = sorted(self.clusters, key=lambda cluster: cluster.start_time)

class SurveyPool(object):
	"""This turns a survey file into something manageable to use as the basis for a search."""

	def __init__(self, radius, time_cutoff):
		self.radius = radius
		self.time_cutoff = time_cutoff

		self.surveys = list()

	def search_for_matching_clusters(self, datapool):
		"""For each survey, look for a matching cluster in the datapool."""

		for survey in self.surveys:
			# Don't search if the survey has major problems
			if survey.major_problems:
				continue

			matches = list()
			
			for cluster in datapool.clusters:
				distance = cluster.distance_from(survey)
				delay = survey.delay_from(cluster)
				closeness = (distance / self.radius) + (delay / self.time_cutoff)
				if distance <= self.radius and delay <= self.time_cutoff:
					cluster.closeness = closeness
					matches.append(cluster)

			survey.matching_clusters = sorted(matches, key=lambda cluster: cluster.closeness)

	def csv_report(self):
		"""For each survey, display any matching clusters that were found."""

		field_list = ['ID', 'Avg_UTM_E', 'Avg_UTM_N', 'Avg_Date', 'Major_Prob', 'Minor_Prob', 'Best_Match', 'Secd_Match', 'Thrd_Match']
		sys.stdout.write(','.join(field_list) + '\n')

		for survey in self.surveys:
			survey.csv_report()

class Survey(object):
	"""This represents a single field survey, equivalent to one line in the survey spreadsheet."""

	def __init__(self, data_set, date_headers, location_easting_headers, location_northing_headers):
		self.data_set = data_set
		self.date_headers = date_headers
		self.location_easting_headers = location_easting_headers
		self.location_northing_headers = location_northing_headers
		self.x = 0
		self.y = 0

		self.attributes = dict()
		self.minor_problems = list()
		self.major_problems = list()
		self.matching_clusters = list()

		# Surveys arrive with all their data, so we can process them right away
		self.parse_survey_data()

		attributes_okay = self.test_attribute_presence()
		if not attributes_okay:
			self.major_problems.append('Internal header list did not match headers of the data file.')
			return

		self.find_average_time()
		self.find_average_location('x', 'easting')
		self.find_average_location('y', 'northing')

	def parse_survey_data(self):
		"""Turn input dict of keys and values into named attributes."""

		for data_key, data_value in self.data_set.items():
			self.attributes[data_key.strip()] = data_value.strip()

	def test_attribute_presence(self):
		"""Test if all data we are expecting are here, warn/abort/instruct if not."""

		all_headers = self.date_headers + self.location_easting_headers + self.location_northing_headers
		all_headers_okay = True

		for header in all_headers:
			try:
				temp = self.attributes[header]
			except KeyError:
				sys.stderr.write('Internal header list does not match headers of data file.\n')
				sys.stderr.write('Could not find a data column called "{}".\n'.format(header))
				sys.stderr.write('Please edit the internal header lists: "{}/match_survey_to_cluster.py".\n'.format(catcm.basepath))
				sys.stderr.write('Or, correct the headers in the data file.\n\n')
				all_headers_okay = False

		return all_headers_okay

	def find_average_time(self):
		"""Parse time values, then calculate the average time of this survey."""

		time_list = list()

		# Parse these into dates, then convert to seconds, then average
		for header in self.date_headers:
			this_value = self.attributes[header]

			# If the value is '', ignore it
			if not this_value:
				continue

			# Parse the string into a datetime object
			try:
				dateobj = dateparser.parse(this_value, default=default_date)
			except ValueError:
				self.minor_problems.append('This date string could not be parsed: {}. Please correct survey file.'.format(this_value))

			# Apply the default time zone
			dateobj = mountain_time.localize(dateobj)

			# Convert to seconds
			seconds = time.mktime(dateobj.timetuple())

			time_list.append(seconds)

		# Do not compute averages if there are no values
		if not time_list:
			self.major_problems.append('Survey has no date values, and cannot be used for searching')
			return False

		# Calculate the average
		self.time = sum(time_list) / len(time_list)

		# Add the average time as a datetime object
		self.dateobj = datetime.datetime.fromtimestamp(self.time)

		# Check if the average is in the expected range
		if not minimum_time < self.time < maximum_time:
			self.major_problems.append('Average time is out of range. Range is {} to {}, value is {}.'.format(minimum_time, maximum_time, self.time))

	def find_average_location(self, math_name, text_name):
		"""Parse location values, then calculate the average location of this survey."""

		location_list = list()

		# Get each value, try to convert to an integer
		for header in getattr(self, 'location_{}_headers'.format(text_name)):
			this_value = self.attributes[header]

			# If the value is '', ignore it
			if not this_value:
				continue

			# Convert to integer and note errors
			try:
				location = int(this_value)
				location_list.append(location)
			except ValueError:
				self.minor_problems.append('This {} value could not be converted to an integer: {}. Please correct survey file.'.format(text_name, this_value))

		# Do not compute averages if there are no values
		if not location_list:
			self.major_problems.append('Survey has no {} values, and cannot be used for searching.'.format(text_name))
			return False

		# Calculate averages
		setattr(self, 'max_{}'.format(math_name), max(location_list))
		setattr(self, 'min_{}'.format(math_name), min(location_list))
		setattr(self, 'spread_{}'.format(math_name), max(location_list) - min(location_list))
		setattr(self, math_name, sum(location_list) / len(location_list))

		# Check if the average is in the expected range
		if not minimum_location[math_name] < getattr(self, math_name) < maximum_location[math_name]:
			self.major_problems.append('Average {} value is out of range. Range is {} to {}, value is {}.'.format(text_name, minimum_location[math_name], maximum_location[math_name], getattr(self, math_name)))

	def delay_from(self, other):
		"""Find the time difference between this survey and another object, usually a cluster."""

		if isinstance(other, catcm.Cluster):
			if self.time < other.start_time:
				delay = other.start_time - self.time
			elif self.time > other.end_time:
				delay = self.time - other.end_time
			else:
				delay = 0
		else:
			delay = math.fabs(self.time - other.time)

		return delay

	def csv_report(self):
		"""Output one line of CSV output showing basic parameters and matching clusters."""

		field_list = [
			self.attributes['ID'],
			'{:0.1f}'.format(self.x),
			'{:0.1f}'.format(self.y),
			self.dateobj.strftime(catcm.DATE_FMT_ISO)
		]

		if self.major_problems:
			field_list.append('"{}"'.format(' '.join(self.major_problems)))
		else:
			field_list.append('')

		if self.minor_problems:
			field_list.append('"{}"'.format(' '.join(self.minor_problems)))
		else:
			field_list.append('')

		if self.major_problems:
			field_list.extend(['"Survey has major problems; matching is not possible."', '', '', ''])
		else:
			for index in range(0, 3):
				try:
					this_cluster = self.matching_clusters[index]
					field_list.append('{}|{}|{:0.1f}|{:0.1f},'.format(this_cluster.catid, this_cluster.id, this_cluster.x, this_cluster.y))
				except IndexError:
					field_list.append('')

		sys.stdout.write(','.join(field_list) + '\n')


# FUNCTIONS

def create_filename():
	"""Create a filename for match_survey text output."""

	return 'match_survey_to_cluster_{}'.format(datetime.datetime.now().strftime(catcm.DATE_FMT_ID_SHORT))
