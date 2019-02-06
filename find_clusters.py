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

import os
import sys
import argparse

from csv import reader as csvreader

import catamount.common as catcm
import catamount.find_clusters as catfc
import catamount.sunmetrics as catsm


# BEGIN SCRIPT

argman = argparse.ArgumentParser(
		prog='FIND_CLUSTERS',
		description='Find clusters in GPS collar data',
		epilog='For this to work, there needs to be a text database of collar data, and a config file'
)

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
	'-c', '--catid',
	dest='catid', action='store',
	type=str, required=True,
	help='Show clusters for this cat.'
)

argman.add_argument(
	'-r', '--radius',
	dest='radius', action='store',
	type=int, default=catcm.cfg_cluster_radius,
	help='Design radius of a cluster.'
)

argman.add_argument(
	'-t', '--time_cutoff',
	dest='time_cutoff', action='store',
	type=catcm.hours_arg_to_seconds, default=catcm.cfg_cluster_time_cutoff,
	help='Design time cutoff of a cluster in hours.'
)

argman.add_argument(
	'-mc', '--minimum_count',
	dest='minimum_count', action='store',
	type=int, default=catcm.cfg_cluster_minimum_count,
	help='Minimum number of points to qualify as a cluster.'
)

argman.add_argument(
	'-ms', '--minimum_stay',
	dest='minimum_stay', action='store',
	type=catcm.hours_arg_to_seconds, default=catcm.cfg_cluster_minimum_stay,
	help='Minimum elapsed hours of clusters.'
)

argman.add_argument(
	'-d1', '--start_date',
	dest='start_date', action='store',
	type=catcm.date_string_to_objects, default=catcm.cfg_cluster_start_date,
	help='Limit clusters to ones that start after this date. YYYY-MM-DD'
)

argman.add_argument(
	'-d2', '--end_date',
	dest='end_date', action='store',
	type=catcm.date_string_to_objects, default=catcm.cfg_cluster_end_date,
	help='Limit clusters to ones that start before this date. YYYY-MM-DD'
)

argman.add_argument(
	'-x', '--text_style',
	dest='text_style', action='store',
	choices=['csv', 'csv-all', 'descriptive', 'descriptive-all'], default='csv',
	help='Text output style: csv, csv-all, descriptive, descriptive-all'
)

argman.add_argument(
	'-z', '--clusterid',
	dest='clusterid', action='store',
	type=str, default=False,
	help='Zoom in on a specific cluster.'
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
args.minimum_count = catcm.constrain_integer(args.minimum_count, 0, 100)
args.minimum_stay = catcm.constrain_integer(args.minimum_stay, 0, 8640000)

# Create a SunMetrics object so any fixes can compute day and night
sun_metrics = catsm.SunMetrics()

# Open and process the data file
with open(args.datafile_path, 'rt') as datafile:
	csvrows = csvreader(datafile)

	# Limit to just one cat
	csvrows = [csvrow for csvrow in csvrows if csvrow[int(catcm.cfg_data_column_catid)] == args.catid]

	# If no rows were retrieved, warn user that cat is not represented in the current data
	if not csvrows:
		sys.exit('No CSV data was found for cat with id {0}.'.format(args.catid))

	# Create a new Trail object, which is a series of fixes
	trail = catfc.FCTrail(args.catid, args.radius, args.time_cutoff, args.minimum_count, args.minimum_stay)

	# For every row, create a Fix object and add it to the Trail
	for csvrow in csvrows:
		try:
			new_fix = catcm.Fix(csvrow, sun_metrics)
		except IndexError:
			sys.stderr.write('CSV row doesn’t have expected number of columns: {}\n'.format(csvrow))
			continue
		except:
			sys.stderr.write('CSV row doesn’t look like data: {}\n'.format(csvrow))
			continue

		# Add the fix to the trail
		trail.fixes.append(new_fix)


# Limit by date, if requested
if args.start_date:
	trail.start_dateobj = args.start_date[0]
	trail.start_time = args.start_date[1]

if args.end_date:
	trail.end_dateobj = args.end_date[0]
	trail.end_time = args.end_date[1]

trail.filter_by_date()

# Filter by date may have removed everything
if len(trail.fixes) < 1:
	sys.exit('No data remaining after filtering by date. Try adjusting the date range.')

# Put the current collecton of fixes in order by time
trail.order_by_time()

# Remove any duplicate entries, seen in some data sets
trail.remove_duplicates()

# Find the farthest distance in each direction
trail.find_bounds()

# Find clusters
trail.find_clusters()

# Calculate averages, after all points have been added
trail.calculate_cluster_averages()

# Get image name and path ready
imagename = catfc.create_filename(args.catid, args.start_date, args.end_date, args.clusterid)
imagepath = os.path.join(args.outdir_path, imagename + '.png')

# Prepare date limiting strings for use in image legends
if args.start_date:
	trail.legend_start_date = args.start_date[0].strftime(catcm.DATE_FMT_ISO_SHORT)

if args.end_date:
	trail.legend_end_date = args.end_date[0].strftime(catcm.DATE_FMT_ISO_SHORT)

# If we're zooming in on a certain cluster, do so now
if args.clusterid:
	# Limit to one cluster
	cluster = trail.return_cluster_by_id(args.clusterid)

	# Create feedback image
	cluster.create_image(imagepath, 'auto')

	# Do a text report of this cluster; show all points by default
	if args.text_style == 'csv':
		cluster.csv_report
	else:
		cluster.descriptive_report(True)

	# Account of what was done
	sys.stderr.write('Cluster {0} shown.\n'.format(args.clusterid))

# Otherwise report on all clusters
else:
	# Apply limiting filters to collection of clusters
	trail.filter_clusters_by_count()
	trail.filter_clusters_by_stay()

	# Create feedback image
	trail.create_image(imagepath, 50)

	# Do a text report of all clusters found
	if args.text_style == 'descriptive-all':
		trail.descriptive_report(True)
	elif args.text_style == 'descriptive':
		trail.descriptive_report(False)
	elif args.text_style == 'csv-all':
		trail.csv_report(True)
	else:
		trail.csv_report(False)

	# Account of what was done
	sys.stderr.write('{0} clusters found.\n'.format(len(trail.clusters)))
