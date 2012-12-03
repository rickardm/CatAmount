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

# This file provides a way to visualize relationships between cat territories.

# IMPORT

from catamount.show_territories import *


# BEGIN SCRIPT

argman = argparse.ArgumentParser(
		prog='SHOW_TERRITORIES',
		description='Depiction of territories based on GPS collar data',
		epilog='For this to work, there needs to be a text database of collar data, and a config file')

argman.add_argument(
	'-f', '--datafile_path',
	dest='datafile_path', action='store',
	type=check_file_arg, default=cfg_datafile_path,
	help='Interpret this data file.'
)

argman.add_argument(
	'-o', '--outdir_path',
	dest='outdir_path', action='store',
	type=check_dir_arg, default=cfg_outdir_path,
	help='Specify an output directory.'
)

argman.add_argument(
	'-c', '--catids',
	dest='catids', action='store',
	type=comma_string_to_list, default=False,
	help='Limit territories shown to these cats. Separate cat ids with commas.'
)

argman.add_argument(
	'-s', '--dot_size',
	dest='dot_size', action='store',
	type=int, default=cfg_territory_dot_size,
	help='Size of graphic dot in pixels.'
)

argman.add_argument(
	'-r', '--perimeter_resolution',
	dest='perimeter_resolution', action='store',
	type=int, default=cfg_territory_perimeter_resolution,
	help='Resolution of perimeter in degrees.'
)

argman.add_argument(
	'-d1', '--start_date',
	dest='start_date', action='store',
	type=date_string_to_objects, default=cfg_territory_start_date,
	help='Limit points shown to after this date. YYYY-MM-DD.'
)

argman.add_argument(
	'-d2', '--end_date',
	dest='end_date', action='store',
	type=date_string_to_objects, default=cfg_territory_end_date,
	help='Limit points shown to before this date. YYYY-MM-DD.'
)

# Using the argument parser to do a lot of work:
# * Prefer command line arguments
# * Fall back on config file values
# * Convert to appropriate types
# * Check validity of arguments
args = argman.parse_args()

# Make sure integer arguments are in a reasonable range.
args.dot_size = constrain_integer(args.dot_size, 2, 100)
args.perimeter_resolution = constrain_integer(args.perimeter_resolution, 1, 120)

# Open and process the data file
with open(args.datafile_path, 'rb') as datafile:
	csvrows = csvreader(datafile)

	# Limit to certain cats, if requested
	if args.catids:
		csvrows = [csvrow for csvrow in csvrows if csvrow[1] in args.catids]

	# If no rows were retrieved, warn user that cat is not represented in the current data
	if not csvrows:
		sys.exit('No CSV data was found after checking cat ids. Cat ids were {0}.'.format(','.join(args.catids)))

	# Create a new DataPool object to work with
	datapool = STDataPool(args.dot_size, args.perimeter_resolution)

	# For every row, create a Fix object and add it to the DataPool
	for csvrow in csvrows:
		try:
			new_fix = Fix(csvrow)
		except ValueError:
			sys.stderr.write('CSV row doesn\'t look like data: {0}\n'.format(csvrow))
			continue
		except IndexError:
			sys.stderr.write('CSV row doesn\'t have expected number of columns: {0}\n'.format(csvrow))
			continue

		# Add this fix to the pool
		datapool.fixes.append(new_fix)

# Filter by date, if requested
if args.start_date:
	datapool.start_dateobj = args.start_date[0]
	datapool.start_time = args.start_date[1]

if args.end_date:
	datapool.end_dateobj = args.end_date[0]
	datapool.end_time = args.end_date[1]

datapool.filter_by_date()

# Filtering by date may have removed everything
if len(datapool.fixes) < 1:
	sys.exit('No data remaining after filtering by date. Check the date range.')

# Put remaining fixes in chronological order
datapool.order_by_time()

# Remove any duplicates, seen in some data sets
datapool.remove_duplicates()

# Divide fixes up into trails, which are used for graphing
datapool.create_trails()
datapool.calculate_angles()

# Get things ready to create an image.
datapool.find_bounds()
datapool.find_catids()
datapool.find_cat_colors()

# Create an image
imagename = create_territory_filename(args.start_date, args.end_date, args.catids)
imagepath = os.path.join(args.outdir_path, imagename + '.png')

# Prepare date limiting strings for use in image legends
if args.start_date:
	datapool.legend_start_date = args.start_date[0].strftime(DATE_FMT_ISO_SHORT)

if args.end_date:
	datapool.legend_end_date = args.end_date[0].strftime(DATE_FMT_ISO_SHORT)

# Create a feedback image
datapool.create_image(imagepath, 'auto')

# Accounting of what was found
sys.stderr.write('{0} territories shown.\n'.format(len(datapool.trails)))
