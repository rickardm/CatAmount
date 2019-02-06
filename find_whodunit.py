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

# This file provides facilities to find if any cat was near a given place and time

# IMPORT

import os
import sys
import time
import argparse
import datetime

from csv import reader as csvreader

import catamount.common as catcm
import catamount.find_whodunit as catfw


# BEGIN SCRIPT

argman = argparse.ArgumentParser(
		prog='FIND_WHODUNIT',
		description='Find what cat was near a given place and time',
		epilog='For this to work, there needs to be a text database of collar data, and a config file')

argman.add_argument(
	'-f', '--datafile_path',
	dest='datafile_path', action='store',
	type=catcm.check_file_arg, default=catcm.cfg_datafile_path,
	help='Interpret this data file.'
)

argman.add_argument(
	'-o', '--outdir_path',
	dest='outdir_path', action='store',
	type=catcm.check_dir_arg, default=catcm.cfg_outdir_path,
	help='Specify an output directory.'
)

argman.add_argument(
	'-r', '--radius',
	dest='radius', action='store',
	type=int, default=catcm.cfg_whodunit_radius,
	help='Design radius of a match.'
)

argman.add_argument(
	'-t', '--time_cutoff',
	dest='time_cutoff', action='store',
	type=catcm.hours_arg_to_seconds, default=catcm.cfg_whodunit_time_cutoff,
	help='Design time cutoff of a match in hours.'
)

argman.add_argument(
	'-d', '--date',
	dest='date', action='store',
	type=catcm.date_string_to_objects, default=False, required=True,
	help='Date to use as basis for the search. YYYY-MM-DD.'
)

argman.add_argument(
	'-cx', '--x_coordinate',
	dest='x', action='store',
	type=int, default=False, required=True,
	help='X Coordinate (NAD27) to use as basis for the search.'
)

argman.add_argument(
	'-cy', '--y_coordinate',
	dest='y', action='store',
	type=int, default=False, required=True,
	help='Y Coordinate (NAD27) to use as basis for the search.'
)

argman.add_argument(
	'-x', '--text_style',
	dest='text_style', action='store',
	choices=['csv', 'descriptive'], default='csv',
	help='Text output style: csv, descriptive.'
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
args.x = catcm.constrain_integer(args.x, 0, 1000000)
args.y = catcm.constrain_integer(args.y, 0, 10000000)

# Open and process the data file
with open(args.datafile_path, 'rt') as datafile:
	csvrows = csvreader(datafile)

	# Create a new DataPool object to work with
	datapool = catfw.FWDataPool(args.radius, args.time_cutoff, args.x, args.y)

	# For every row, create a Fix object and add it to the DataPool
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


# Limit data to within X times the time cutoff of the target date
datapool.dateobj = args.date[0]
datapool.time = args.date[1]

date_limit = datetime.timedelta(seconds=args.time_cutoff * 5)

datapool.start_dateobj = datapool.dateobj - date_limit
datapool.start_time = time.mktime(datapool.start_dateobj.timetuple())

datapool.end_dateobj = datapool.dateobj + date_limit
datapool.end_time = time.mktime(datapool.end_dateobj.timetuple())

datapool.filter_by_date()

# Filtering by date may have removed everything
if len(datapool.fixes) < 1:
	sys.exit('No data remaining after filtering by date. Check the request date.')


# Limit data to within X times the radius of the target coordinates
datapool.x = args.x
datapool.y = args.y

datapool.filter_by_location(args.radius * 5)

# Filtering by location may have removed everything
if len(datapool.fixes) < 1:
	sys.exit('No data remaining after filtering by location. Check the request coordinates.')


# Put remaining fixes in chronological order
datapool.order_by_time()

# Remove any duplicate entries, seen in some data sets
datapool.remove_duplicates()

# Find any matches
datapool.find_matches()

# Get things ready to create an image
datapool.find_bounds()
datapool.find_catids()
datapool.find_cat_colors()

# Get image name and path ready
imagename = catfw.create_filename(args.date, args.x, args.y)
imagepath = os.path.join(args.outdir_path, imagename + '.png')

# Prepare date for legend
datapool.legend_date = args.date[0].strftime(catcm.DATE_FMT_ISO)

# Create a feedback image
datapool.create_image(imagepath, 'auto')

# Do a text report on crossings found
if args.text_style == 'descriptive':
	datapool.descriptive_report(False)
else:
	datapool.csv_report()

# Account of what was done
sys.stderr.write('{0} matches found.\n'.format(len(datapool.matches)))
