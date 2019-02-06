#!/usr/bin/env python3

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

# Field work identifies sites with a certain time, location, activity.
# GPS data collects a history of an animal's movements.
# This uses field work as input, and looks for matching clusters in the GPS data.
# It tries to create links between the field work notes and GPS collar data.

# IMPORT

import os
import sys
import argparse

from csv import reader as csvreader
from csv import DictReader

import catamount.common as catcm
import catamount.match_survey_to_cluster as catms


# GLOBALS

# I do hereby swear, to the best of my knowledge, that the following
# is a complete list of headers for the CSV columns which contain DATE
# information germane to the site survey. I accept that it is my
# responsibility, if I change the CSV headers, to also change this
# list to match. Must match exactly, case sensitive.

date_headers = ['Estimated DOD', 'Date off', 'Pick-up Date']

# I do hereby swear, to the best of my knowledge, that the following
# is a complete list of headers for the CSV columns which contain
# LOCATION information germane to the site survey. I accept that it is
# my responsibility, if I change the CSV headers, to also change this
# list to match. Must match exactly, case sensitive.

location_easting_headers = ['Kill UTM E', 'Cache UTM E', 'Carcass Only UTM E']

location_northing_headers = ['Kill UTM N', 'Cache UTM N', 'Carcass Only UTM N']


# BEGIN SCRIPT

argman = argparse.ArgumentParser(
		prog='MATCH FIELD SURVEYS TO CLUSTERS',
		description='Find out which clusters most closely match site survey data.',
		epilog='For this to work, there needs to be a text database of collar data, a config file, and a file of site surveys.'
)

argman.add_argument(
	'-f', '--datafile_path',
	dest='datafile_path', action='store',
	type=catcm.check_file_arg, default=catcm.cfg_datafile_path,
	help='Search through this data file.'
)

argman.add_argument(
	'-s', '--survey_file_path',
	dest='survey_file_path', action='store',
	type=catcm.check_file_arg, default=catcm.cfg_matchsurvey_survey_file_path,
	help='This file contains site surveys, the basis for the search.'
)

argman.add_argument(
	'-r', '--radius',
	dest='radius', action='store',
	type=int, default=catcm.cfg_matchsurvey_radius,
	help='Design radius of a match, in meters.'
)

argman.add_argument(
	'-t', '--time_cutoff',
	dest='time_cutoff', action='store',
	type=catcm.hours_arg_to_seconds, default=catcm.cfg_matchsurvey_time_cutoff,
	help='Design time cutoff of a match, in hours.'
)

# Using the argument parser to do a lot of work:
# * Prefer command line arguments
# * Fall back on config file values
# * Convert to appropriate types
# * Check validity of arguments
args = argman.parse_args()

# Make sure integer arguments are in a reasonable range.
args.radius = catcm.constrain_integer(args.radius, 0, 1000)
args.time_cutoff = catcm.constrain_integer(args.time_cutoff, 0, 31536000)

#print('Process the data file...')

# Open and process the data file
with open(args.datafile_path, 'rt') as datafile:
	csvrows = csvreader(datafile)

	# Create a new DataPool object to work with
	datapool = catms.MSDataPool(args.radius, args.time_cutoff)

	# For every row, create a Fix object and it to the DataPool
	for csvrow in csvrows:
		try:
			new_fix = catcm.Fix(csvrow)
		except IndexError:
			sys.stderr.write('CSV row doesn’t have expected number of columns: {}\n'.format(csvrow))
			continue
		except:
			sys.stderr.write('CSV row doesn’t look like data: {}\n'.format(csvrow))
			continue

		# Add the fix to the datapool
		datapool.fixes.append(new_fix)

#print('Find all clusters in the data file...')

# Sort all of the fixes out into trails
datapool.sort_into_trails()

# Find clusters within those trails
datapool.find_all_clusters()

#print('Process the survey file...')

# Open and process the survey file
with open(args.survey_file_path, 'rt') as survey_file:
	csvrows = DictReader(survey_file)

	# Create a new SurveyPool object to work with
	surveypool = catms.SurveyPool(args.radius, args.time_cutoff)

	for csvrow in csvrows:
		survey = catms.Survey(csvrow, date_headers, location_easting_headers, location_northing_headers)

		surveypool.surveys.append(survey)

# Search for matching clusters
surveypool.search_for_matching_clusters(datapool)

#print('Preparing CSV report on surveys and matching clusters...')

# Report on matching clusters
surveypool.csv_report()

# Count number of successful maches
success_count = 0
for survey in surveypool.surveys:
	if len(survey.matching_clusters) > 0:
		success_count += 1

# Feedback to error channel
error_feedback = '{} fixes found in the data file.\n'.format(len(datapool.fixes))
error_feedback += ' {} clusters found across {} cats.\n'.format(len(datapool.clusters), len(datapool.catids))
error_feedback += ' {} surveys found in the surveys file.\n'.format(len(surveypool.surveys))
error_feedback += ' {0} surveys matched to clusters ({1:0.1f}% success).\n'.format(success_count, 100 * (success_count / len(surveypool.surveys)))

sys.stderr.write(error_feedback)
