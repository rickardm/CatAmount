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

# This file provides facilities to find time/space groupings of several cats, called crossings.

# IMPORT

import os
import sys
import argparse

from csv import reader as csvreader

import catamount.common as catcm
import catamount.find_crossings as catfx
import catamount.sun_metrics as catsm


# BEGIN SCRIPT

argman = argparse.ArgumentParser(
		prog='FIND_CROSSINGS',
		description='Find crossings in GPS collar data',
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
	'-c', '--catids',
	dest='catids', action='store',
	type=catcm.comma_string_to_list, default=False,
	help='Limit crossings to those involving these cats. Separate cat ids with commas.'
)

argman.add_argument(
	'-r', '--radius',
	dest='radius', action='store',
	type=int, default=catcm.cfg_crossing_radius,
	help='Design radius of a crossing.'
)

argman.add_argument(
	'-t', '--time_cutoff',
	dest='time_cutoff', action='store',
	type=catcm.hours_arg_to_seconds, default=catcm.cfg_crossing_time_cutoff,
	help='Design time cutoff of a crossing in hours.'
)

argman.add_argument(
	'-d1', '--start_date',
	dest='start_date', action='store',
	type=catcm.date_string_to_objects, default=catcm.cfg_crossing_start_date,
	help='Limit crossings to ones that start after this date. YYYY-MM-DD.'
)

argman.add_argument(
	'-d2', '--end_date',
	dest='end_date', action='store',
	type=catcm.date_string_to_objects, default=catcm.cfg_crossing_end_date,
	help='Limit crossings to ones that start before this date. YYYY-MM-DD.'
)

argman.add_argument(
	'-x', '--text_style',
	dest='text_style', action='store',
	choices=['csv', 'csv-all', 'descriptive', 'descriptive-all'], default='csv',
	help='Text output style: csv, csv-all, descriptive, descriptive-all.'
)

argman.add_argument(
	'-z', '--crossingid',
	dest='crossingid', action='store',
	type=str, default=False,
	help='Zoom in on a specific crossing.'
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

# Create a SunMetrics object so any fixes can compute day and night
sun_metrics = catsm.SunMetrics()

# Open and process the data file
with open(args.datafile_path, 'rb') as datafile:
	csvrows = csvreader(datafile)

	# Limit to certain cats, if requested
	if args.catids:
		csvrows = [csvrow for csvrow in csvrows if csvrow[1] in args.catids]

	# If no rows were retrieved, warn user that cat is not represented in the current data
	if not csvrows:
		sys.exit('No CSV data was found after checking cat ids. Cat ids were {0}'.format(','.join(args.catids)))

	# Create a new DataPool object to work with
	datapool = catfx.FXDataPool(args.radius, args.time_cutoff)

	# For every row, create a Fix object and add it to the DataPool
	for csvrow in csvrows:
		try:
			new_fix = catcm.Fix(csvrow, sun_metrics)
		except ValueError:
			sys.stderr.write('CSV row doesn\'t look like data: {0}\n'.format(csvrow))
			continue
		except IndexError:
			sys.stderr.write('CSV row doesn\'t have expected number of columns: {0}\n'.format(csvrow))
			continue

		# Add the fix to the datapool
		datapool.fixes.append(new_fix)


# Limit by date, if requested
if args.start_date:
	datapool.start_dateobj = args.start_date[0]
	datapool.start_time = args.start_date[1]

if args.end_date:
	datapool.end_dateobj = args.end_date[0]
	datapool.end_time = args.end_date[1]

datapool.filter_by_date()

# Filtering by date may have removed everything
if len(datapool.fixes) < 1:
	sys.exit('No data remaining after filtering by date. Try adjusting the date range.')


# Put remaining fixes in chronological order
datapool.order_by_time()

# Remove any duplicate entries, seen in some data sets
datapool.remove_duplicates()

# First we make clusters out of all points in the datapool
datapool.find_clusters()

# Now convert clusters to crossings if they qualify
datapool.clusters_to_crossings()


# Check to see if any crossings were found before continuing
if not datapool.crossings:
	sys.exit('No crossings were found for these parameters. Try different settings.')


# Get things ready to create an image
datapool.find_bounds()
datapool.find_catids()
datapool.find_cat_colors()

# Get image name and path ready
imagename = catcm.create_crossing_filename(args.start_date, args.end_date, args.catids, args.crossingid)
imagepath = os.path.join(args.outdir_path, imagename + '.png')

# Prepare date limiting strings for use in image legends
if args.start_date:
	datapool.legend_start_date = args.start_date[0].strftime(catcm.DATE_FMT_ISO_SHORT)

if args.end_date:
	datapool.legend_end_date = args.end_date[0].strftime(catcm.DATE_FMT_ISO_SHORT)

# If we're zooming in on a certain crossing, do so now
if args.crossingid:
	# Limit to one crossing
	crossing = datapool.return_crossing_by_id(args.crossingid)

	# Create a feedback image
	crossing.create_image(imagepath, 'auto')

	# Do a text report of this cluster; show all points by default
	if args.text_style == 'csv':
		crossing.csv_report
	else:
		crossing.descriptive_report(True)

	# Account of what was done
	sys.stderr.write('Crossing {0} shown.\n'.format(args.crossingid))

# Otherwise report on all crossings
else:
	# Create a feedback image
	datapool.create_image(imagepath, 100)

	# Do a text report on crossings found
	if args.text_style == 'descriptive-all':
		datapool.descriptive_report(True)
	elif args.text_style == 'descriptive':
		datapool.descriptive_report(False)
	elif args.text_style == 'csv-all':
		datapool.csv_report(True)
	else:
		datapool.csv_report(False)

	# Account of what was done
	sys.stderr.write('{0} crossings found.\n'.format(len(datapool.crossings)))
