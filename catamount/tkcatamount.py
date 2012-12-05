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

# This file provides a TK GUI to apply settings and orchestrate various components.

# IMPORT

import Tkinter as tk
import tkFileDialog as tkfd
import ImageTk
import subprocess

from catamount.common import *

# CLASSES

class MainWindow(object):
	"""This is the primary window of the GUI."""

	def __init__(self):
		self.root = tk.Tk()
		self.root.title('{0} v{1}'.format(APP_NAME, APP_VERSION))
		self.root.grid()
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(0, weight=1)
		self.root.minsize(640, 480)

		self.default_grid_args = {'rowspan': 1, 'columnspan': 1, 'padx': 1, 'pady': 1, 'sticky': 'WENS'}
		self.spanning_grid_args = {'padx': 1, 'pady': 1, 'sticky': 'WENS'}
		self.arrow_grid_args = {'rowspan': 1, 'columnspan': 1, 'padx': 0, 'pady': 0, 'sticky': 'WENS'}
		self.value_grid_args = {'rowspan': 2, 'columnspan': 1, 'padx': 1, 'pady': 1, 'sticky': 'WENS'}


		self.create_variables()
		self.create_images()
		self.create_menus()
		self.create_uniframe()
		self.create_filesframe()
		self.create_modeframe()
		self.create_feedbackframe()
		self.create_clusterframe()
		self.create_territoryframe()
		self.create_crossingframe()
		self.create_whodunitframe()
		self.create_matchsurveyframe()
		self.refresh_catids()

		self.root.mainloop()

	def create_variables(self):
		self.datafile_path = tk.StringVar()
		self.datafile_path.set(cfg_datafile_path)

		self.datadir_path = os.path.dirname(self.datafile_path.get())

		self.catids = sorted(find_catids(self.datafile_path.get()))

		self.outdir_path = tk.StringVar()
		self.outdir_path.set(cfg_outdir_path)

		self.mode = tk.StringVar()
		self.mode.set('')

		self.feedback = tk.StringVar()
		self.feedback.set('Ready to start!')

		# Cluster Variables
		self.cluster_catid = tk.StringVar()
		self.cluster_catid.set('')

		self.cluster_radius = tk.StringVar()
		self.cluster_radius.set('{0} meters'.format(cfg_cluster_radius))

		self.cluster_time_cutoff = tk.StringVar()
		self.cluster_time_cutoff.set('{0} hours'.format(cfg_cluster_time_cutoff))

		self.cluster_minimum_count = tk.StringVar()
		self.cluster_minimum_count.set('{0} points'.format(cfg_cluster_minimum_count))

		self.cluster_minimum_stay = tk.StringVar()
		self.cluster_minimum_stay.set('{0} hours'.format(cfg_cluster_minimum_stay))

		self.cluster_start_date = tk.StringVar()
		self.cluster_start_date.set(cfg_cluster_start_date)

		self.cluster_end_date = tk.StringVar()
		self.cluster_end_date.set(cfg_cluster_end_date)

		self.cluster_clusterid = tk.StringVar()
		self.cluster_clusterid.set('')

		self.cluster_text_style = tk.StringVar()
		self.cluster_text_style.set('csv')

		# Territory Variabels
		self.territory_allcats = tk.StringVar()
		self.territory_allcats.set('all')

		self.territory_dot_size = tk.StringVar()
		self.territory_dot_size.set('{0} pixels'.format(cfg_territory_dot_size))

		self.territory_perimeter_resolution = tk.StringVar()
		self.territory_perimeter_resolution.set('{0} degrees'.format(cfg_territory_perimeter_resolution))

		self.territory_start_date = tk.StringVar()
		self.territory_start_date.set(cfg_territory_start_date)

		self.territory_end_date = tk.StringVar()
		self.territory_end_date.set(cfg_territory_end_date)

		# Crossing Variables
		self.crossing_allcats = tk.StringVar()
		self.crossing_allcats.set('all')

		self.crossing_radius = tk.StringVar()
		self.crossing_radius.set('{0} meters'.format(cfg_crossing_radius))

		self.crossing_time_cutoff = tk.StringVar()
		self.crossing_time_cutoff.set('{0} hours'.format(cfg_crossing_time_cutoff))

		self.crossing_start_date = tk.StringVar()
		self.crossing_start_date.set(cfg_crossing_start_date)

		self.crossing_end_date = tk.StringVar()
		self.crossing_end_date.set(cfg_crossing_end_date)

		self.crossing_crossingid = tk.StringVar()
		self.crossing_crossingid.set('')

		self.crossing_text_style = tk.StringVar()
		self.crossing_text_style.set('csv')

		# Whodunit Variables
		self.whodunit_radius = tk.StringVar()
		self.whodunit_radius.set('{0} meters'.format(cfg_whodunit_radius))

		self.whodunit_time_cutoff = tk.StringVar()
		self.whodunit_time_cutoff.set('{0} hours'.format(cfg_whodunit_time_cutoff))

		self.whodunit_date = tk.StringVar()
		self.whodunit_date.set('')

		self.whodunit_x = tk.StringVar()
		self.whodunit_x.set('')

		self.whodunit_y = tk.StringVar()
		self.whodunit_y.set('')

		self.whodunit_text_style = tk.StringVar()
		self.whodunit_text_style.set('csv')

		# Match Survey To Cluster Variables
		self.matchsurvey_radius = tk.StringVar()
		self.matchsurvey_radius.set('{0} meters'.format(cfg_matchsurvey_radius))

		self.matchsurvey_time_cutoff = tk.StringVar()
		self.matchsurvey_time_cutoff.set('{0} hours'.format(cfg_matchsurvey_time_cutoff))

		self.matchsurvey_survey_file_path = tk.StringVar()
		self.matchsurvey_survey_file_path.set(cfg_matchsurvey_survey_file_path)

		self.matchsurvey_survey_dir_path = os.path.dirname(self.matchsurvey_survey_file_path.get())

		# These rules are used for increment function: (min, max, increment, unit, tk_variable)
		self.variable_rules = {
			'cluster_radius': (0, 1000, 1, 'meters', self.cluster_radius),
			'cluster_time_cutoff': (0, 365, 1, 'hours', self.cluster_time_cutoff),
			'cluster_minimum_count': (0, 100, 1, 'points', self.cluster_minimum_count),
			'cluster_minimum_stay': (0, 100, 1, 'hours', self.cluster_minimum_stay),
			'territory_dot_size': (1, 100, 1, 'pixels', self.territory_dot_size),
			'territory_perimeter_resolution': (1, 120, 1, 'degrees', self.territory_perimeter_resolution),
			'crossing_radius': (0, 1000, 1, 'meters', self.crossing_radius),
			'crossing_time_cutoff': (0, 365, 1, 'hours', self.crossing_time_cutoff),
			'whodunit_radius': (0, 1000, 1, 'meters', self.whodunit_radius),
			'whodunit_time_cutoff': (0, 365, 1, 'hours', self.whodunit_time_cutoff),
			'matchsurvey_radius': (0, 1000, 1, 'meters', self.matchsurvey_radius),
			'matchsurvey_time_cutoff': (0, 365, 1, 'hours', self.matchsurvey_time_cutoff)
		}


	def create_images(self):
		self.selectfile = tk.BitmapImage(data=selectfile_data)
		self.selectdir = tk.BitmapImage(data=selectdir_data)
		self.large_up_arrow = tk.BitmapImage(data=large_up_arrow_data)
		self.large_down_arrow = tk.BitmapImage(data=large_down_arrow_data)
		self.small_up_arrow = tk.BitmapImage(data=small_up_arrow_data)
		self.small_down_arrow = tk.BitmapImage(data=small_down_arrow_data)

		# Save a reference
		self.selectfile.data = selectfile_data
		self.selectdir.data = selectdir_data
		self.large_up_arrow.data = large_up_arrow_data
		self.large_down_arrow.data = large_down_arrow_data
		self.small_up_arrow.data = small_up_arrow_data
		self.small_down_arrow.data = small_down_arrow_data

	def create_menus(self):
		self.topmenu = tk.Menu(self.root, relief='flat')

		self.stuffmenu = tk.Menu(self.topmenu, relief='flat', tearoff=0)
		self.stuffmenu.add_command(label='Quit', command=self.root.destroy)
		self.stuffmenu.add_command(label='About', command=self.show_about_window)

		self.topmenu.add_cascade(label='Menu', menu=self.stuffmenu)
		self.root.config(menu=self.topmenu)

	def create_uniframe(self):
		self.uniframe = tk.Frame(self.root)
		self.uniframe.grid(row=0, column=0, **self.default_grid_args)
		self.uniframe.columnconfigure(0, weight=1)
		self.uniframe.rowconfigure(0, weight=0)
		self.uniframe.rowconfigure(1, weight=0)
		self.uniframe.rowconfigure(2, weight=0)
		self.uniframe.rowconfigure(3, weight=1)

	def create_filesframe(self):
		self.filesframe = tk.Frame(self.uniframe)
		self.filesframe.grid(row=0, column=0, **self.default_grid_args)
		self.filesframe.columnconfigure(0, weight=1)
		self.filesframe.columnconfigure(1, weight=0)
		self.filesframe.columnconfigure(2, weight=1)
		self.filesframe.columnconfigure(3, weight=1)
		self.filesframe.columnconfigure(4, weight=0)
		self.filesframe.columnconfigure(5, weight=1)

		self.datafile_label = tk.Label(self.filesframe, text='Select Data File')
		self.datafile_select = tk.Button(
			self.filesframe, image=self.selectfile, command=self.set_datafile_path,
			cursor='hand2', borderwidth=1
		)

		self.datafile_label.grid(row=0, column=0, **self.default_grid_args)
		self.datafile_select.grid(row=0, column=1, **self.default_grid_args)

		self.outdir_label = tk.Label(self.filesframe, text='Select Output Dir', fg='#000')
		self.outdir_select = tk.Button(
			self.filesframe, image=self.selectdir, command=self.set_outdir_path,
			cursor='hand2', borderwidth=1
		)

		self.outdir_label.grid(row=0, column=3, **self.default_grid_args)
		self.outdir_select.grid(row=0, column=4, **self.default_grid_args)

	def create_feedbackframe(self):
		self.feedbackframe = tk.Frame(self.uniframe)
		self.feedbackframe.grid(row=1, column=0, **self.default_grid_args)
		self.feedbackframe.columnconfigure(0, weight=1)
		self.feedbackframe.rowconfigure(0, weight=1)

		self.feedback_label = tk.Label(self.feedbackframe, textvariable=self.feedback, fg='#A00', wraplength=512)

		self.feedback_label.grid(row=0, column=0, **self.default_grid_args)

	def create_modeframe(self):
		self.modeframe = tk.Frame(self.uniframe)
		self.modeframe.grid(row=2, column=0, **self.default_grid_args)
		self.modeframe.columnconfigure(0, weight=1)
		self.modeframe.columnconfigure(1, weight=1)
		self.modeframe.columnconfigure(2, weight=1)
		self.modeframe.columnconfigure(3, weight=1)
		self.modeframe.columnconfigure(4, weight=1)
		self.modeframe.rowconfigure(0, weight = 1)

		self.radio1 = tk.Radiobutton(
			self.modeframe, text='Find Clusters', value='cluster',
			variable=self.mode, command=self.update_workframe,
			indicatoron=0, cursor='hand2', borderwidth=1
		)
		self.radio2 = tk.Radiobutton(
			self.modeframe, text='Show Territories', value='territory',
			variable=self.mode, command=self.update_workframe,
			indicatoron=0, cursor='hand2', borderwidth=1
		)
		self.radio3 = tk.Radiobutton(
			self.modeframe, text='Find Crossings', value='crossing',
			variable=self.mode, command=self.update_workframe,
			indicatoron=0, cursor='hand2', borderwidth=1
		)
		self.radio4 = tk.Radiobutton(
			self.modeframe, text='Find Whodunit', value='whodunit',
			variable=self.mode, command=self.update_workframe,
			indicatoron=0, cursor='hand2', borderwidth=1
		)
		self.radio5 = tk.Radiobutton(
			self.modeframe, text='Match Survey To Cluster', value='matchsurvey',
			variable=self.mode, command=self.update_workframe,
			indicatoron=0, cursor='hand2', borderwidth=1
		)

		self.radio1.grid(row=0, column=0, **self.default_grid_args)
		self.radio2.grid(row=0, column=1, **self.default_grid_args)
		self.radio3.grid(row=0, column=2, **self.default_grid_args)
		self.radio4.grid(row=0, column=3, **self.default_grid_args)
		self.radio5.grid(row=0, column=4, **self.default_grid_args)

	def create_clusterframe(self):
		self.clusterframe = tk.Frame(self.uniframe, borderwidth=2, relief=tk.GROOVE, padx=4, pady=4)
		self.clusterframe.grid(row=3, column=0, rowspan=1, columnspan=1, padx=2, pady=2, sticky='WENS')
		self.clusterframe.columnconfigure(0, weight=1)
		self.clusterframe.columnconfigure(1, weight=0)
		self.clusterframe.columnconfigure(2, weight=0)
		self.clusterframe.columnconfigure(3, weight=1)
		self.clusterframe.columnconfigure(4, weight=1)
		self.clusterframe.columnconfigure(5, weight=1)
		self.clusterframe.rowconfigure(9, weight=1)

		# Column 0/1/2/3

		# Row 0
		self.cluster_catid_label = tk.Label(self.clusterframe, text='Select one cat')
		self.cluster_catid_menu = tk.OptionMenu(self.clusterframe, self.cluster_catid, *self.catids)

		self.cluster_catid_label.grid(row=0, column=0, **self.default_grid_args)
		self.cluster_catid_menu.grid(row=0, column=1, rowspan=1, columnspan=3, **self.spanning_grid_args)

		# Row 1/2
		self.cluster_radius_label = tk.Label(self.clusterframe, text='Radius')
		self.cluster_radius_large_up = tk.Button(
			self.clusterframe, image=self.large_up_arrow,
			command=lambda: self.increment('cluster_radius', 'up', 'large')
		)
		self.cluster_radius_large_down = tk.Button(
			self.clusterframe, image=self.large_down_arrow,
			command=lambda: self.increment('cluster_radius', 'down', 'large')
		)
		self.cluster_radius_small_up = tk.Button(
			self.clusterframe, image=self.small_up_arrow,
			command=lambda: self.increment('cluster_radius', 'up', 'small')
		)
		self.cluster_radius_small_down = tk.Button(
			self.clusterframe, image=self.small_down_arrow,
			command=lambda: self.increment('cluster_radius', 'down', 'small')
		)
		self.cluster_radius_value = tk.Label(self.clusterframe, textvariable=self.cluster_radius)

		self.cluster_radius_label.grid(row=1, column=0, **self.value_grid_args)
		self.cluster_radius_large_up.grid(row=1, column=1, **self.arrow_grid_args)
		self.cluster_radius_large_down.grid(row=2, column=1, **self.arrow_grid_args)
		self.cluster_radius_small_up.grid(row=1, column=2, **self.arrow_grid_args)
		self.cluster_radius_small_down.grid(row=2, column=2, **self.arrow_grid_args)
		self.cluster_radius_value.grid(row=1, column=3, **self.value_grid_args)

		# Row 3/4
		self.cluster_time_cutoff_label = tk.Label(self.clusterframe, text='Time Cutoff')
		self.cluster_time_cutoff_large_up = tk.Button(
			self.clusterframe, image=self.large_up_arrow,
			command=lambda: self.increment('cluster_time_cutoff', 'up', 'large')
		)
		self.cluster_time_cutoff_large_down = tk.Button(
			self.clusterframe, image=self.large_down_arrow,
			command=lambda: self.increment('cluster_time_cutoff', 'down', 'large')
		)
		self.cluster_time_cutoff_small_up = tk.Button(
			self.clusterframe, image=self.small_up_arrow,
			command=lambda: self.increment('cluster_time_cutoff', 'up', 'small')
		)
		self.cluster_time_cutoff_small_down = tk.Button(
			self.clusterframe, image=self.small_down_arrow,
			command=lambda: self.increment('cluster_time_cutoff', 'down', 'small')
		)
		self.cluster_time_cutoff_value = tk.Label(self.clusterframe, textvariable=self.cluster_time_cutoff)

		self.cluster_time_cutoff_label.grid(row=3, column=0, **self.value_grid_args)
		self.cluster_time_cutoff_large_up.grid(row=3, column=1, **self.arrow_grid_args)
		self.cluster_time_cutoff_large_down.grid(row=4, column=1, **self.arrow_grid_args)
		self.cluster_time_cutoff_small_up.grid(row=3, column=2, **self.arrow_grid_args)
		self.cluster_time_cutoff_small_down.grid(row=4, column=2, **self.arrow_grid_args)
		self.cluster_time_cutoff_value.grid(row=3, column=3, **self.value_grid_args)

		# Row 5/6
		self.cluster_minimum_count_label = tk.Label(self.clusterframe, text='Minimum Count')
		self.cluster_minimum_count_up = tk.Button(
			self.clusterframe, image=self.small_up_arrow,
			command=lambda: self.increment('cluster_minimum_count', 'up', 'small')
		)
		self.cluster_minimum_count_down = tk.Button(
			self.clusterframe, image=self.small_down_arrow,
			command=lambda: self.increment('cluster_minimum_count', 'down', 'small')
		)
		self.cluster_minimum_count_value = tk.Label(self.clusterframe, textvariable=self.cluster_minimum_count)

		self.cluster_minimum_count_label.grid(row=5, column=0, **self.value_grid_args)
		self.cluster_minimum_count_up.grid(row=5, column=2, **self.arrow_grid_args)
		self.cluster_minimum_count_down.grid(row=6, column=2, **self.arrow_grid_args)
		self.cluster_minimum_count_value.grid(row=5, column=3, **self.value_grid_args)

		# Row 7/8
		self.cluster_minimum_stay_label = tk.Label(self.clusterframe, text='Minimum Stay')
		self.cluster_minimum_stay_up = tk.Button(
			self.clusterframe, image=self.small_up_arrow,
			command=lambda: self.increment('cluster_minimum_stay', 'up', 'small')
		)
		self.cluster_minimum_stay_down = tk.Button(
			self.clusterframe, image=self.small_down_arrow,
			command=lambda: self.increment('cluster_minimum_stay', 'down', 'small')
		)
		self.cluster_minimum_stay_value = tk.Label(self.clusterframe, textvariable=self.cluster_minimum_stay)

		self.cluster_minimum_stay_label.grid(row=7, column=0, **self.value_grid_args)
		self.cluster_minimum_stay_up.grid(row=7, column=2, **self.arrow_grid_args)
		self.cluster_minimum_stay_down.grid(row=8, column=2, **self.arrow_grid_args)
		self.cluster_minimum_stay_value.grid(row=7, column=3, **self.value_grid_args)

		# Column 4/5

		# Row 1/2
		self.cluster_start_date_label = tk.Label(self.clusterframe, text='Start Date')
		self.cluster_start_date_entry = tk.Entry(self.clusterframe, textvariable=self.cluster_start_date)

		self.cluster_start_date_label.grid(row=1, column=4, **self.value_grid_args)
		self.cluster_start_date_entry.grid(row=1, column=5, **self.value_grid_args)

		# Row 3/4
		self.cluster_end_date_label = tk.Label(self.clusterframe, text='End Date')
		self.cluster_end_date_entry = tk.Entry(self.clusterframe, textvariable=self.cluster_end_date)

		self.cluster_end_date_label.grid(row=3, column=4, **self.value_grid_args)
		self.cluster_end_date_entry.grid(row=3, column=5, **self.value_grid_args)

		# Row 5/6
		self.cluster_clusterid_label = tk.Label(self.clusterframe, text='Zoom in on a\nsingle cluster')
		self.cluster_clusterid_entry = tk.Entry(self.clusterframe, textvariable=self.cluster_clusterid)

		self.cluster_clusterid_label.grid(row=5, column=4, **self.value_grid_args)
		self.cluster_clusterid_entry.grid(row=5, column=5, **self.value_grid_args)

		# Row 7/8
		self.cluster_text_style_label = tk.Label(self.clusterframe, text='Text output style')
		self.cluster_text_style_menu = tk.OptionMenu(
			self.clusterframe, self.cluster_text_style,
			'csv', 'csv-all', 'descriptive', 'descriptive-all'
		)

		self.cluster_text_style_label.grid(row=7, column=4, **self.value_grid_args)
		self.cluster_text_style_menu.grid(row=7, column=5, **self.value_grid_args)

		# Row 9
		self.cluster_go = tk.Button(
			self.clusterframe, text='Find Clusters', command=self.launch_find_clusters
		)

		self.cluster_go.grid(row=9, column=4, rowspan=1, columnspan=2, padx=1, pady=1, sticky='WES')

		self.clusterframe.grid_remove()

	def create_territoryframe(self):
		self.territoryframe = tk.Frame(self.uniframe, borderwidth=2, relief=tk.GROOVE, padx=4, pady=4)
		self.territoryframe.grid(row=3, column=0, rowspan=1, columnspan=1, padx=2, pady=2, sticky='WENS')
		self.territoryframe.columnconfigure(0, weight=0)
		self.territoryframe.columnconfigure(1, weight=1)
		self.territoryframe.columnconfigure(2, weight=1)
		self.territoryframe.columnconfigure(3, weight=0)
		self.territoryframe.columnconfigure(4, weight=1)
		self.territoryframe.rowconfigure(8, weight=1)

		# Column 0/1

		# Row 0
		self.territory_allcats_1 = tk.Radiobutton(
			self.territoryframe, text='Use all cats in the data file', value='all',
			variable=self.territory_allcats, command=self.toggle_territory_select_list,
			cursor='hand2', anchor=tk.W
		)
		self.territory_allcats_2 = tk.Radiobutton(
			self.territoryframe, text='Select one or more cats from a list', value='select',
			variable=self.territory_allcats, command=self.toggle_territory_select_list,
			cursor='hand2', anchor=tk.W
		)

		self.territory_allcats_1.grid(row=0, column=1, **self.default_grid_args)
		self.territory_allcats_2.grid(row=1, column=1, **self.default_grid_args)

		# Row 2-7
		self.territory_catids_scrollbar = tk.Scrollbar(self.territoryframe)
		self.territory_catids_list = tk.Listbox(self.territoryframe, selectmode=tk.EXTENDED, exportselection=0)

		self.territory_catids_scrollbar.grid(row=2, column=0, rowspan=6, columnspan=1, **self.spanning_grid_args)
		self.territory_catids_list.grid(row=2, column=1, rowspan=6, columnspan=1, **self.spanning_grid_args)

		# Column 2/3/4/5

		# Row 2
		self.territory_start_date_label = tk.Label(self.territoryframe, text='Start Date')
		self.territory_start_date_entry = tk.Entry(self.territoryframe, textvariable=self.territory_start_date)

		self.territory_start_date_label.grid(row=2, column=2, **self.default_grid_args)
		self.territory_start_date_entry.grid(row=2, column=3, rowspan=1, columnspan=2, **self.spanning_grid_args)

		# Row 3
		self.territory_end_date_label = tk.Label(self.territoryframe, text='End Date')
		self.territory_end_date_entry = tk.Entry(self.territoryframe, textvariable=self.territory_end_date)

		self.territory_end_date_label.grid(row=3, column=2, **self.default_grid_args)
		self.territory_end_date_entry.grid(row=3, column=3, rowspan=1, columnspan=3, **self.spanning_grid_args)

		# Row 4/5
		self.territory_dot_size_label = tk.Label(self.territoryframe, text='Dot size')
		self.territory_dot_size_small_up = tk.Button(
			self.territoryframe, image=self.small_up_arrow,
			command=lambda: self.increment('territory_dot_size', 'up', 'small')
		)
		self.territory_dot_size_small_down = tk.Button(
			self.territoryframe, image=self.small_down_arrow,
			command=lambda: self.increment('territory_dot_size', 'down', 'small')
		)
		self.territory_dot_size_value = tk.Label(self.territoryframe, textvariable=self.territory_dot_size)

		self.territory_dot_size_label.grid(row=4, column=2, **self.value_grid_args)
		self.territory_dot_size_small_up.grid(row=4, column=3, **self.arrow_grid_args)
		self.territory_dot_size_small_down.grid(row=5, column=3, **self.arrow_grid_args)
		self.territory_dot_size_value.grid(row=4, column=4, **self.value_grid_args)

		# Row 6/7
		self.territory_perimeter_resolution_label = tk.Label(self.territoryframe, text='Perimeter resolution')
		self.territory_perimeter_resolution_small_up = tk.Button(
			self.territoryframe, image=self.small_up_arrow,
			command=lambda: self.increment('territory_perimeter_resolution', 'up', 'small')
		)
		self.territory_perimeter_resolution_small_down = tk.Button(
			self.territoryframe, image=self.small_down_arrow,
			command=lambda: self.increment('territory_perimeter_resolution', 'down', 'small')
		)
		self.territory_perimeter_resolution_value = tk.Label(self.territoryframe, textvariable=self.territory_perimeter_resolution)

		self.territory_perimeter_resolution_label.grid(row=6, column=2, **self.value_grid_args)
		self.territory_perimeter_resolution_small_up.grid(row=6, column=3, **self.arrow_grid_args)
		self.territory_perimeter_resolution_small_down.grid(row=7, column=3, **self.arrow_grid_args)
		self.territory_perimeter_resolution_value.grid(row=6, column=4, **self.value_grid_args)

		# Row 8
		self.territory_go = tk.Button(
			self.territoryframe, text='Show Territories', command=self.launch_show_territories
		)

		self.territory_go.grid(row=8, column=2, rowspan=1, columnspan=3, padx=1, pady=1, sticky='WES')

		self.territory_catids_scrollbar.config(command=self.territory_catids_list.yview)
		self.territory_catids_list.config(yscrollcommand=self.territory_catids_scrollbar.set)
		self.territory_catids_list['state'] = tk.DISABLED

		self.territoryframe.grid_remove()

	def create_crossingframe(self):
		self.crossingframe = tk.Frame(self.uniframe, borderwidth=2, relief=tk.GROOVE, padx=4, pady=4)
		self.crossingframe.grid(row=3, column=0, rowspan=1, columnspan=1, padx=2, pady=2, sticky='WENS')
		self.crossingframe.columnconfigure(0, weight=0)
		self.crossingframe.columnconfigure(1, weight=1)
		self.crossingframe.columnconfigure(2, weight=1)
		self.crossingframe.columnconfigure(3, weight=0)
		self.crossingframe.columnconfigure(4, weight=0)
		self.crossingframe.columnconfigure(5, weight=1)
		self.crossingframe.rowconfigure(10, weight=1)

		# Column 0/1

		# Row 0
		self.crossing_allcats_1 = tk.Radiobutton(
			self.crossingframe, text='Use all cats in the data file', value='all',
			variable=self.crossing_allcats, command=self.toggle_crossing_select_list,
			cursor='hand2', anchor=tk.W
		)
		self.crossing_allcats_2 = tk.Radiobutton(
			self.crossingframe, text='Select two or more cats from a list', value='select',
			variable=self.crossing_allcats, command=self.toggle_crossing_select_list,
			cursor='hand2', anchor=tk.W
		)

		self.crossing_allcats_1.grid(row=0, column=1, **self.default_grid_args)
		self.crossing_allcats_2.grid(row=1, column=1, **self.default_grid_args)

		# Row 2-9
		self.crossing_catids_scrollbar = tk.Scrollbar(self.crossingframe)
		self.crossing_catids_list = tk.Listbox(self.crossingframe, selectmode=tk.EXTENDED, exportselection=0)

		self.crossing_catids_scrollbar.grid(row=2, column=0, rowspan=8, columnspan=1, **self.spanning_grid_args)
		self.crossing_catids_list.grid(row=2, column=1, rowspan=8, columnspan=1, **self.spanning_grid_args)

		# Column 2/3/4/5

		# Row 2/3
		self.crossing_radius_label = tk.Label(self.crossingframe, text='Radius')
		self.crossing_radius_large_up = tk.Button(
			self.crossingframe, image=self.large_up_arrow,
			command=lambda: self.increment('crossing_radius', 'up', 'large')
		)
		self.crossing_radius_large_down = tk.Button(
			self.crossingframe, image=self.large_down_arrow,
			command=lambda: self.increment('crossing_radius', 'down', 'large')
		)
		self.crossing_radius_small_up = tk.Button(
			self.crossingframe, image=self.small_up_arrow,
			command=lambda: self.increment('crossing_radius', 'up', 'small')
		)
		self.crossing_radius_small_down = tk.Button(
			self.crossingframe, image=self.small_down_arrow,
			command=lambda: self.increment('crossing_radius', 'down', 'small')
		)
		self.crossing_radius_value = tk.Label(self.crossingframe, textvariable=self.crossing_radius)

		self.crossing_radius_label.grid(row=2, column=2, **self.value_grid_args)
		self.crossing_radius_large_up.grid(row=2, column=3, **self.arrow_grid_args)
		self.crossing_radius_large_down.grid(row=3, column=3, **self.arrow_grid_args)
		self.crossing_radius_small_up.grid(row=2, column=4, **self.arrow_grid_args)
		self.crossing_radius_small_down.grid(row=3, column=4, **self.arrow_grid_args)
		self.crossing_radius_value.grid(row=2, column=5, **self.value_grid_args)

		# Row 4/5
		self.crossing_time_cutoff_label = tk.Label(self.crossingframe, text='Time Cutoff')
		self.crossing_time_cutoff_large_up = tk.Button(
			self.crossingframe, image=self.large_up_arrow,
			command=lambda: self.increment('crossing_time_cutoff', 'up', 'large')
		)
		self.crossing_time_cutoff_large_down = tk.Button(
			self.crossingframe, image=self.large_down_arrow,
			command=lambda: self.increment('crossing_time_cutoff', 'down', 'large')
		)
		self.crossing_time_cutoff_small_up = tk.Button(
			self.crossingframe, image=self.small_up_arrow,
			command=lambda: self.increment('crossing_time_cutoff', 'up', 'small')
		)
		self.crossing_time_cutoff_small_down = tk.Button(
			self.crossingframe, image=self.small_down_arrow,
			command=lambda: self.increment('crossing_time_cutoff', 'down', 'small')
		)
		self.crossing_time_cutoff_value = tk.Label(self.crossingframe, textvariable=self.crossing_time_cutoff)

		self.crossing_time_cutoff_label.grid(row=4, column=2, **self.value_grid_args)
		self.crossing_time_cutoff_large_up.grid(row=4, column=3, **self.arrow_grid_args)
		self.crossing_time_cutoff_large_down.grid(row=5, column=3, **self.arrow_grid_args)
		self.crossing_time_cutoff_small_up.grid(row=4, column=4, **self.arrow_grid_args)
		self.crossing_time_cutoff_small_down.grid(row=5, column=4, **self.arrow_grid_args)
		self.crossing_time_cutoff_value.grid(row=4, column=5, **self.value_grid_args)

		# Row 6
		self.crossing_start_date_label = tk.Label(self.crossingframe, text='Start Date')
		self.crossing_start_date_entry = tk.Entry(self.crossingframe, textvariable=self.crossing_start_date)

		self.crossing_start_date_label.grid(row=6, column=2, **self.default_grid_args)
		self.crossing_start_date_entry.grid(row=6, column=3, columnspan=3, **self.spanning_grid_args)

		# Row 7
		self.crossing_end_date_label = tk.Label(self.crossingframe, text='End Date')
		self.crossing_end_date_entry = tk.Entry(self.crossingframe, textvariable=self.crossing_end_date)

		self.crossing_end_date_label.grid(row=7, column=2, **self.default_grid_args)
		self.crossing_end_date_entry.grid(row=7, column=3, columnspan=3, **self.spanning_grid_args)

		# Row 8
		self.crossing_crossingid_label = tk.Label(self.crossingframe, text='Zoom in on a\nsingle crossing')
		self.crossing_crossingid_entry = tk.Entry(self.crossingframe, textvariable=self.crossing_crossingid)

		self.crossing_crossingid_label.grid(row=8, column=2, **self.default_grid_args)
		self.crossing_crossingid_entry.grid(row=8, column=3, columnspan=3, **self.spanning_grid_args)

		# Row 9
		self.crossing_text_style_label = tk.Label(self.crossingframe, text='Text output style')
		self.crossing_text_style_menu = tk.OptionMenu(
			self.crossingframe, self.crossing_text_style,
			'csv', 'csv-all', 'descriptive', 'descriptive-all'
		)

		self.crossing_text_style_label.grid(row=9, column=2, **self.default_grid_args)
		self.crossing_text_style_menu.grid(row=9, column=3, columnspan=3, **self.spanning_grid_args)

		# Row 10
		self.crossing_go = tk.Button(
			self.crossingframe, text='Find Crossings', command=self.launch_find_crossings
		)

		self.crossing_go.grid(row=10, column=2, rowspan=1, columnspan=4, padx=1, pady=1, sticky='WES')

		#self.refresh_catids()
		self.crossing_catids_scrollbar.config(command=self.crossing_catids_list.yview)
		self.crossing_catids_list.config(yscrollcommand=self.crossing_catids_scrollbar.set)
		self.crossing_catids_list['state'] = tk.DISABLED

		self.crossingframe.grid_remove()

	def create_whodunitframe(self):
		self.whodunitframe = tk.Frame(self.uniframe, borderwidth=2, relief=tk.GROOVE, padx=4, pady=4)
		self.whodunitframe.grid(row=3, column=0, rowspan=1, columnspan=1, padx=2, pady=2, sticky='WENS')
		self.whodunitframe.columnconfigure(0, weight=1)
		self.whodunitframe.columnconfigure(1, weight=0)
		self.whodunitframe.columnconfigure(2, weight=0)
		self.whodunitframe.columnconfigure(3, weight=1)
		self.whodunitframe.columnconfigure(4, weight=1)
		self.whodunitframe.columnconfigure(5, weight=1)
		self.whodunitframe.rowconfigure(5, weight=1)

		# Column 0/1/2/3

		# Row 0/1
		self.whodunit_radius_label = tk.Label(self.whodunitframe, text='Radius')
		self.whodunit_radius_large_up = tk.Button(
			self.whodunitframe, image=self.large_up_arrow,
			command=lambda: self.increment('whodunit_radius', 'up', 'large')
		)
		self.whodunit_radius_large_down = tk.Button(
			self.whodunitframe, image=self.large_down_arrow,
			command=lambda: self.increment('whodunit_radius', 'down', 'large')
		)
		self.whodunit_radius_small_up = tk.Button(
			self.whodunitframe, image=self.small_up_arrow,
			command=lambda: self.increment('whodunit_radius', 'up', 'small')
		)
		self.whodunit_radius_small_down = tk.Button(
			self.whodunitframe, image=self.small_down_arrow,
			command=lambda: self.increment('whodunit_radius', 'down', 'small')
		)
		self.whodunit_radius_value = tk.Label(self.whodunitframe, textvariable=self.whodunit_radius)

		self.whodunit_radius_label.grid(row=0, column=0, **self.value_grid_args)
		self.whodunit_radius_large_up.grid(row=0, column=1, **self.arrow_grid_args)
		self.whodunit_radius_large_down.grid(row=1, column=1, **self.arrow_grid_args)
		self.whodunit_radius_small_up.grid(row=0, column=2, **self.arrow_grid_args)
		self.whodunit_radius_small_down.grid(row=1, column=2, **self.arrow_grid_args)
		self.whodunit_radius_value.grid(row=0, column=3, **self.value_grid_args)

		# Row 2/3
		self.whodunit_time_cutoff_label = tk.Label(self.whodunitframe, text='Time Cutoff')
		self.whodunit_time_cutoff_large_up = tk.Button(
			self.whodunitframe, image=self.large_up_arrow,
			command=lambda: self.increment('whodunit_time_cutoff', 'up', 'large')
		)
		self.whodunit_time_cutoff_large_down = tk.Button(
			self.whodunitframe, image=self.large_down_arrow,
			command=lambda: self.increment('whodunit_time_cutoff', 'down', 'large')
		)
		self.whodunit_time_cutoff_small_up = tk.Button(
			self.whodunitframe, image=self.small_up_arrow,
			command=lambda: self.increment('whodunit_time_cutoff', 'up', 'small')
		)
		self.whodunit_time_cutoff_small_down = tk.Button(
			self.whodunitframe, image=self.small_down_arrow,
			command=lambda: self.increment('whodunit_time_cutoff', 'down', 'small')
		)
		self.whodunit_time_cutoff_value = tk.Label(self.whodunitframe, textvariable=self.whodunit_time_cutoff)

		self.whodunit_time_cutoff_label.grid(row=2, column=0, **self.value_grid_args)
		self.whodunit_time_cutoff_large_up.grid(row=2, column=1, **self.arrow_grid_args)
		self.whodunit_time_cutoff_large_down.grid(row=3, column=1, **self.arrow_grid_args)
		self.whodunit_time_cutoff_small_up.grid(row=2, column=2, **self.arrow_grid_args)
		self.whodunit_time_cutoff_small_down.grid(row=3, column=2, **self.arrow_grid_args)
		self.whodunit_time_cutoff_value.grid(row=2, column=3, **self.value_grid_args)

		# Column 4/5

		# Row 0/1
		self.whodunit_date_label = tk.Label(self.whodunitframe, text='Search Date')
		self.whodunit_date_entry = tk.Entry(self.whodunitframe, textvariable=self.whodunit_date)

		self.whodunit_date_label.grid(row=0, column=4, **self.value_grid_args)
		self.whodunit_date_entry.grid(row=0, column=5, **self.value_grid_args)

		# Row 2/3
		self.whodunit_x_label = tk.Label(self.whodunitframe, text='Search X')
		self.whodunit_x_entry = tk.Entry(self.whodunitframe, textvariable=self.whodunit_x)

		self.whodunit_x_label.grid(row=2, column=4, **self.value_grid_args)
		self.whodunit_x_entry.grid(row=2, column=5, **self.value_grid_args)

		# Row 4
		self.whodunit_y_label = tk.Label(self.whodunitframe, text='Search Y')
		self.whodunit_y_entry = tk.Entry(self.whodunitframe, textvariable=self.whodunit_y)

		self.whodunit_y_label.grid(row=4, column=4, **self.default_grid_args)
		self.whodunit_y_entry.grid(row=4, column=5, **self.default_grid_args)

		# Row 5
		self.whodunit_go = tk.Button(
			self.whodunitframe, text='Find Whodunit', command=self.launch_find_whodunit
		)

		self.whodunit_go.grid(row=5, column=4, rowspan=1, columnspan=2, padx=1, pady=1, sticky='WES')

		self.whodunitframe.grid_remove()

	def create_matchsurveyframe(self):
		self.matchsurveyframe = tk.Frame(self.uniframe, borderwidth=2, relief=tk.GROOVE, padx=4, pady=4)
		self.matchsurveyframe.grid(row=3, column=0, rowspan=1, columnspan=1, padx=2, pady=2, sticky='WENS')
		self.matchsurveyframe.columnconfigure(0, weight=1)
		self.matchsurveyframe.columnconfigure(1, weight=0)
		self.matchsurveyframe.columnconfigure(2, weight=0)
		self.matchsurveyframe.columnconfigure(3, weight=1)
		self.matchsurveyframe.columnconfigure(4, weight=1)
		self.matchsurveyframe.rowconfigure(5, weight=1)

		# Column 0/1/2/3

		# Row 0/1
		self.matchsurvey_radius_label = tk.Label(self.matchsurveyframe, text='Radius')
		self.matchsurvey_radius_large_up = tk.Button(
			self.matchsurveyframe, image=self.large_up_arrow,
			command=lambda: self.increment('matchsurvey_radius', 'up', 'large')
		)
		self.matchsurvey_radius_large_down = tk.Button(
			self.matchsurveyframe, image=self.large_down_arrow,
			command=lambda: self.increment('matchsurvey_radius', 'down', 'large')
		)
		self.matchsurvey_radius_small_up = tk.Button(
			self.matchsurveyframe, image=self.small_up_arrow,
			command=lambda: self.increment('matchsurvey_radius', 'up', 'small')
		)
		self.matchsurvey_radius_small_down = tk.Button(
			self.matchsurveyframe, image=self.small_down_arrow,
			command=lambda: self.increment('matchsurvey_radius', 'down', 'small')
		)
		self.matchsurvey_radius_value = tk.Label(self.matchsurveyframe, textvariable=self.matchsurvey_radius)

		self.matchsurvey_radius_label.grid(row=0, column=0, **self.value_grid_args)
		self.matchsurvey_radius_large_up.grid(row=0, column=1, **self.arrow_grid_args)
		self.matchsurvey_radius_large_down.grid(row=1, column=1, **self.arrow_grid_args)
		self.matchsurvey_radius_small_up.grid(row=0, column=2, **self.arrow_grid_args)
		self.matchsurvey_radius_small_down.grid(row=1, column=2, **self.arrow_grid_args)
		self.matchsurvey_radius_value.grid(row=0, column=3, **self.value_grid_args)

		# Row 2/3
		self.matchsurvey_time_cutoff_label = tk.Label(self.matchsurveyframe, text='Time Cutoff')
		self.matchsurvey_time_cutoff_large_up = tk.Button(
			self.matchsurveyframe, image=self.large_up_arrow,
			command=lambda: self.increment('matchsurvey_time_cutoff', 'up', 'large')
		)
		self.matchsurvey_time_cutoff_large_down = tk.Button(
			self.matchsurveyframe, image=self.large_down_arrow,
			command=lambda: self.increment('matchsurvey_time_cutoff', 'down', 'large')
		)
		self.matchsurvey_time_cutoff_small_up = tk.Button(
			self.matchsurveyframe, image=self.small_up_arrow,
			command=lambda: self.increment('matchsurvey_time_cutoff', 'up', 'small')
		)
		self.matchsurvey_time_cutoff_small_down = tk.Button(
			self.matchsurveyframe, image=self.small_down_arrow,
			command=lambda: self.increment('matchsurvey_time_cutoff', 'down', 'small')
		)
		self.matchsurvey_time_cutoff_value = tk.Label(self.matchsurveyframe, textvariable=self.matchsurvey_time_cutoff)

		self.matchsurvey_time_cutoff_label.grid(row=2, column=0, **self.value_grid_args)
		self.matchsurvey_time_cutoff_large_up.grid(row=2, column=1, **self.arrow_grid_args)
		self.matchsurvey_time_cutoff_large_down.grid(row=3, column=1, **self.arrow_grid_args)
		self.matchsurvey_time_cutoff_small_up.grid(row=2, column=2, **self.arrow_grid_args)
		self.matchsurvey_time_cutoff_small_down.grid(row=3, column=2, **self.arrow_grid_args)
		self.matchsurvey_time_cutoff_value.grid(row=2, column=3, **self.value_grid_args)

		# Column 4

		# Row 0/1
		self.matchsurvey_survey_file_path_button = tk.Button(
			self.matchsurveyframe, image=self.selectfile,
			command=self.set_survey_file_path
		)
		self.matchsurvey_survey_file_path_label = tk.Label(self.matchsurveyframe, textvariable=self.matchsurvey_survey_file_path, wraplength=300)

		self.matchsurvey_survey_file_path_button.grid(row=0, column=4, rowspan=4, padx=1, pady=1)
		self.matchsurvey_survey_file_path_label.grid(row=4, column=4, padx=1, pady=1)

		# Row 4
		self.matchsurvey_go = tk.Button(
			self.matchsurveyframe, text='Match Survey To Cluster', command=self.launch_match_survey_to_cluster
		)

		self.matchsurvey_go.grid(row=5, column=4, padx=1, pady=1, sticky='WES')

		self.matchsurveyframe.grid_remove()

	def set_datafile_path(self):
		fileoptions = {
			'filetypes': [('All files', '.*'), ('CSV files', '.csv'), ('Text files', '.txt')],
			'title': 'Select a data file to examine',
			'initialdir': self.datadir_path
		}
		datafile_path = tkfd.askopenfilename(**fileoptions)

		if not datafile_path:
			return False

		self.datafile_path.set(datafile_path)
		self.datadir_path = os.path.dirname(datafile_path)
		self.feedback.set('New data file: "{0}"'.format(datafile_path))

		self.refresh_catids()

	def set_outdir_path(self):
		diroptions = {
			'mustexist': True,
			'title': 'Select a default output path',
			'initialdir': self.outdir_path.get()
		}
		outdir_path = tkfd.askdirectory(**diroptions)

		if not outdir_path:
			return False

		self.outdir_path.set(outdir_path)
		self.feedback.set('New ouput directory: "{0}"'.format(outdir_path))

	def set_survey_file_path(self):
		fileoptions = {
			'filetypes': [('All files', '.*'), ('CSV files', '.csv'), ('Text files', '.txt')],
			'title': 'Select a survey file to examine',
			'initialdir': self.matchsurvey_survey_dir_path
		}
		survey_file_path = tkfd.askopenfilename(**fileoptions)

		if not survey_file_path:
			return False

		self.matchsurvey_survey_file_path.set(survey_file_path)
		self.matchsurvey_survey_dir_path = os.path.dirname(survey_file_path)
		self.feedback.set('New survey file: "{0}"'.format(survey_file_path))

	def check_datafile_exists(self):
		if os.path.isfile(self.datafile_path.get()):
			return True
		else:
			self.feedback.set('There is a problem with the data file.\nSee: {}'.format(self.datafile_path.get()))
			return False

	def refresh_catids(self):
		self.catids = sorted(find_catids(self.datafile_path.get()))

		# Empty the lists
		self.cluster_catid_menu['menu'].delete(0, tk.END)
		self.territory_catids_list.delete(0, tk.END)
		self.crossing_catids_list.delete(0, tk.END)

		# These need to be enabled to take values
		self.territory_catids_list['state'] = tk.NORMAL
		self.crossing_catids_list['state'] = tk.NORMAL

		# Refill the lists
		for catid in self.catids:
			self.cluster_catid_menu['menu'].add_command(label=catid, command=tk._setit(self.cluster_catid, catid))
			self.territory_catids_list.insert(tk.END, catid)
			self.crossing_catids_list.insert(tk.END, catid)

		# Reset the state of the lists that we might have changed
		self.toggle_territory_select_list()
		self.toggle_crossing_select_list()

	def update_workframe(self):
		if not self.check_datafile_exists():
			return False

		if not self.catids:
			no_catids = 'Unable to find cat IDs in data file.\n'
			no_catids += 'Expected ID format is M123 and F456.\n'
			no_catids += 'Cat ID is expected to be in a certain column of the tab-delimited data file.'
			self.feedback.set(no_catids)
			return False

		# First turn off all the work frames
		self.clusterframe.grid_remove()
		self.territoryframe.grid_remove()
		self.crossingframe.grid_remove()
		self.whodunitframe.grid_remove()
		self.matchsurveyframe.grid_remove()

		# Then turn on the one that is active
		mode = self.mode.get()
		getattr(self, mode + 'frame').grid()

		# Add some feedback
		update_mode_messages = {'cluster': 'Find Clusters', 'territory': 'Show Territories',
			'crossing': 'Find Crossings', 'whodunit': 'Find Whodunit', 'matchsurvey': 'Match Survey To Cluster'}

		self.feedback.set('{} Mode'.format(update_mode_messages[mode]))

	def increment(self, variable_name, direction, step_size):
		"""This is the logic for up and down settings buttons in the GUI."""

		if not variable_name in self.variable_rules:
			self.feedback.set('Attempting to increment an unknown variable.')
			return False

		var_rules = self.variable_rules[variable_name]
		var_min = var_rules[0]
		var_max = var_rules[1]
		var_incr = var_rules[2]
		var_unit = var_rules[3]
		tk_var = var_rules[4]

		if step_size == 'large':
			var_incr *= 10

		current_value = tk_var.get()
		current_value_list = current_value.split(' ')
		current_value_int = int(current_value_list[0])

		if direction == 'up':
			if current_value_int >= var_max:
				self.feedback.set('Maximum value for {0}: {1}'.format(variable_name, var_max))
				return False

			if current_value_int < var_min:
				current_value_int = var_min

			if current_value_int + var_incr > var_max:
				new_value = var_max
			else:
				new_value = current_value_int + var_incr

			tk_var.set('{0} {1}'.format(new_value, var_unit))

		elif direction == 'down':
			if current_value_int <= var_min:
				self.feedback.set('Minimum value for {0}: {1}'.format(variable_name, var_min))
				return False

			if current_value_int > var_max:
				current_value_int = var_max

			if current_value_int - var_incr < var_min:
				new_value = var_min
			else:
				new_value = current_value_int - var_incr

			current_value_int -= var_incr
			tk_var.set('{0} {1}'.format(new_value, var_unit))


	def remove_units(self, variable_value):
		"""I added the unit to some of the variable values, for legibility.
		This removes anything after the first space, getting rid of the unit."""

		return variable_value.split(' ')[0]

	def toggle_territory_select_list(self):
		if self.territory_allcats.get() == 'all':
			self.territory_catids_list['state'] = tk.DISABLED
		else:
			self.territory_catids_list['state'] = tk.NORMAL

	def toggle_crossing_select_list(self):
		if self.crossing_allcats.get() == 'all':
			self.crossing_catids_list['state'] = tk.DISABLED
		else:
			self.crossing_catids_list['state'] = tk.NORMAL

	def call_script(self, args, filename, function_name):
		script_process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		communication = script_process.communicate()

		if communication[1]:
			self.feedback.set(communication[1].replace('\r', ''))

		if communication[0]:
			if (function_name == 'find_clusters') and (self.cluster_text_style.get() == 'csv'):
				textfilename = filename + '.csv'
			elif (function_name == 'find_crossings') and (self.crossing_text_style.get() == 'csv'):
				textfilename = filename + '.csv'
			elif (function_name == 'find_whodunit') and (self.whodunit_text_style.get() == 'csv'):
				textfilename = filename + '.csv'
			elif function_name == 'match_survey_to_cluster':
				textfilename = filename + '.csv'
			else:
				textfilename = filename + '.txt'
			textwindow = TextWindow(communication[0].replace('\r', ''), self.outdir_path.get(), textfilename)

		imagefilepath = os.path.join(self.outdir_path.get(), filename + '.png')
		if os.path.isfile(imagefilepath):
			graphicwindow = GraphicWindow(imagefilepath)

	def launch_find_clusters(self):
		cluster_start_date = date_string_to_objects(self.cluster_start_date.get())
		cluster_end_date = date_string_to_objects(self.cluster_end_date.get())

		cluster_args = [sys.executable, os.path.join(basepath, 'find_clusters.py')]
		cluster_args.extend(['--datafile_path', self.datafile_path.get()])
		cluster_args.extend(['--outdir_path', self.outdir_path.get()])
		cluster_args.extend(['--catid', self.cluster_catid.get()])
		cluster_args.extend(['--radius', self.remove_units(self.cluster_radius.get())])
		cluster_args.extend(['--time_cutoff', self.remove_units(self.cluster_time_cutoff.get())])
		cluster_args.extend(['--minimum_count', self.remove_units(self.cluster_minimum_count.get())])
		cluster_args.extend(['--minimum_stay', self.remove_units(self.cluster_minimum_stay.get())])

		if cluster_start_date:
			cluster_args.extend(['--start_date', self.cluster_start_date.get()])

		if cluster_end_date:
			cluster_args.extend(['--end_date', self.cluster_end_date.get()])

		cluster_args.extend(['--text_style', self.cluster_text_style.get()])

		if self.cluster_clusterid.get():
			cluster_args.extend(['--clusterid', self.cluster_clusterid.get()])


		cluster_filename = create_cluster_filename(
			self.cluster_catid.get(), cluster_start_date, cluster_end_date, self.cluster_clusterid.get()
		)
		self.call_script(cluster_args, cluster_filename, 'find_clusters')


	def launch_show_territories(self):
		if self.territory_allcats.get() == 'all':
			territory_catids = False
		else:
			catids_indexes = self.territory_catids_list.curselection()
			territory_catids = list()
			for index in catids_indexes:
				territory_catids.append(self.territory_catids_list.get(index))

		territory_start_date = date_string_to_objects(self.territory_start_date.get())
		territory_end_date = date_string_to_objects(self.territory_end_date.get())

		territory_args = [sys.executable, os.path.join(basepath, 'show_territories.py')]
		territory_args.extend(['--datafile_path', self.datafile_path.get()])
		territory_args.extend(['--outdir_path', self.outdir_path.get()])

		if territory_catids:
			territory_args.extend(['--catids', ','.join(territory_catids)])

		territory_args.extend(['--dot_size', self.remove_units(self.territory_dot_size.get())])
		territory_args.extend(['--perimeter_resolution', self.remove_units(self.territory_perimeter_resolution.get())])

		if territory_start_date:
			territory_args.extend(['--start_date', self.territory_start_date.get()])

		if territory_end_date:
			territory_args.extend(['--end_date', self.territory_end_date.get()])

		territory_filename = create_territory_filename(
			territory_start_date, territory_end_date, territory_catids
		)
		self.call_script(territory_args, territory_filename, 'show_territories')

	def launch_find_crossings(self):
		if self.crossing_allcats.get() == 'all':
			crossing_catids = False
		else:
			catids_indexes = self.crossing_catids_list.curselection()
			crossing_catids = list()
			for index in catids_indexes:
				crossing_catids.append(self.crossing_catids_list.get(index))

		crossing_start_date = date_string_to_objects(self.crossing_start_date.get())
		crossing_end_date = date_string_to_objects(self.crossing_end_date.get())

		crossing_args = [sys.executable, os.path.join(basepath, 'find_crossings.py')]
		crossing_args.extend(['--datafile_path', self.datafile_path.get()])
		crossing_args.extend(['--outdir_path', self.outdir_path.get()])

		if crossing_catids:
			crossing_args.extend(['--catids', ','.join(crossing_catids)])

		crossing_args.extend(['--radius', self.remove_units(self.crossing_radius.get())])
		crossing_args.extend(['--time_cutoff', self.remove_units(self.crossing_time_cutoff.get())])

		if crossing_start_date:
			crossing_args.extend(['--start_date', self.crossing_start_date.get()])

		if crossing_end_date:
			crossing_args.extend(['--end_date', self.crossing_end_date.get()])

		crossing_args.extend(['--text_style', self.crossing_text_style.get()])

		if self.crossing_crossingid.get():
			crossing_args.extend(['--crossingid', self.crossing_crossingid.get()])

		crossing_filename = create_crossing_filename(
			crossing_start_date, crossing_end_date, crossing_catids, self.crossing_crossingid.get()
		)
		self.call_script(crossing_args, crossing_filename, 'find_crossings')

	def launch_find_whodunit(self):
		whodunit_date = date_string_to_objects(self.whodunit_date.get())

		whodunit_args = [sys.executable, os.path.join(basepath, 'find_whodunit.py')]
		whodunit_args.extend(['--datafile_path', self.datafile_path.get()])
		whodunit_args.extend(['--outdir_path', self.outdir_path.get()])
		whodunit_args.extend(['--radius', self.remove_units(self.whodunit_radius.get())])
		whodunit_args.extend(['--time_cutoff', self.remove_units(self.whodunit_time_cutoff.get())])
		whodunit_args.extend(['--date', self.whodunit_date.get()])
		whodunit_args.extend(['--x_coordinate', self.whodunit_x.get()])
		whodunit_args.extend(['--y_coordinate', self.whodunit_y.get()])
		whodunit_args.extend(['--text_style', self.whodunit_text_style.get()])

		whodunit_filename = create_whodunit_filename(
			whodunit_date, self.whodunit_x.get(), self.whodunit_y.get()
		)
		self.call_script(whodunit_args, whodunit_filename, 'find_whodunit')


	def launch_match_survey_to_cluster(self):
		matchsurvey_args = [sys.executable, os.path.join(basepath, 'match_survey_to_cluster.py')]
		matchsurvey_args.extend(['--datafile_path', self.datafile_path.get()])
		matchsurvey_args.extend(['--survey_file_path', self.matchsurvey_survey_file_path.get()])
		matchsurvey_args.extend(['--radius', self.remove_units(self.matchsurvey_radius.get())])
		matchsurvey_args.extend(['--time_cutoff', self.remove_units(self.matchsurvey_radius.get())])

		matchsurvey_filename = 'match_survey_to_cluster'
		self.call_script(matchsurvey_args, matchsurvey_filename, 'match_survey_to_cluster')

	def show_about_window(self):
		self.aboutwindow = tk.Toplevel()
		self.aboutwindow.title('About')

		self.aboutframe = tk.Frame(self.aboutwindow)
		self.aboutframe.grid(row=0, column=0, padx=8, pady=8)

		abouttext = '{0}\nVersion {1}\n\n{2}'.format(APP_NAME, APP_VERSION, APP_COPYRIGHT)

		self.aboutlabel = tk.Label(self.aboutframe, text=abouttext)
		self.aboutclose = tk.Button(self.aboutframe, text='Close', command=self.aboutwindow.destroy)

		self.aboutlabel.grid(row=0, column=0, padx=8, pady=8)
		self.aboutclose.grid(row=1, column=0, padx=8, pady=8)



class GraphicWindow(object):
	"""A GUI window which displays graphic output of the program."""

	def __init__(self, imagepath):
		self.imagepath = imagepath

		self.window = tk.Toplevel()
		self.window.title('Image Output: {0}'.format(os.path.basename(imagepath)))
		self.window.columnconfigure(0, weight=1)
		self.window.rowconfigure(0, weight=1)

		self.get_graphic()
		self.make_widgets()

	def get_graphic(self):
		self.image = Image.open(self.imagepath)
		self.tkimage = ImageTk.PhotoImage(self.image)

		# Grab the image sizes
		self.image_size = self.image.size
		self.initial_size = (min(self.image_size[0], 1200), min(self.image_size[1], 900))

	def make_widgets(self):
		self.uniframe = tk.Frame(self.window)
		self.uniframe.grid(row=0, column=0, padx=1, pady=1, sticky='WENS')
		self.uniframe.columnconfigure(0, weight=1)
		self.uniframe.columnconfigure(1, weight=1)
		self.uniframe.rowconfigure(0, weight=1)
		self.uniframe.rowconfigure(1, weight=0)

		# Can use the actual height here, if I can find it from the image
		self.graphic_canvas = tk.Canvas(
			self.uniframe, width=self.initial_size[0], height=self.initial_size[1]
		)
		self.vert_scrollbar = tk.Scrollbar(self.uniframe)
		self.horz_scrollbar = tk.Scrollbar(self.uniframe, orient=tk.HORIZONTAL)
		self.save_button = tk.Button(
			self.uniframe, text='Save As', command=self.save_as, cursor='hand2'
		)
		self.close_button = tk.Button(
			self.uniframe, text='Close', command=self.window.destroy, cursor='hand2'
		)

		self.graphic_canvas.grid(row=0, column=0, columnspan=2, padx=1, pady=1, sticky='WENS')
		self.vert_scrollbar.grid(row=0, column=2, padx=1, pady=1, sticky='NS')
		self.horz_scrollbar.grid(row=1, column=0, columnspan=2, padx=1, pady=1, sticky='WE')
		self.save_button.grid(row=2, column=0, padx=1, pady=1)
		self.close_button.grid(row=2, column=1, padx=1, pady=1)

		self.vert_scrollbar.config(command=self.graphic_canvas.yview)
		self.graphic_canvas.config(yscrollcommand=self.vert_scrollbar.set)

		self.horz_scrollbar.config(command=self.graphic_canvas.xview)
		self.graphic_canvas.config(xscrollcommand=self.horz_scrollbar.set)

		# Add the image to the canvas
		self.graphic_canvas.create_image((0, 0), image=self.tkimage)

		# Limit the scroll size to the size of the image
		self.graphic_canvas.config(scrollregion=self.graphic_canvas.bbox(tk.ALL))

	def save_as(self):
		dirname = os.path.dirname(self.imagepath)
		basename = os.path.basename(self.imagepath)
		fileoptions = {
			'initialdir': dirname,
			'initialfile': basename,
			'title': 'Save graphic as a new file.',
			'filetypes': [('PNG files', '.png'), ('All files', '.*')],
			'defaultextension': '.png'
		}
		filename = tkfd.asksaveasfilename(**fileoptions)
		if filename:
			self.image.save(filename)


class TextWindow(object):
	"""A GUI Window which displays text output of the program."""

	def __init__(self, text, outdir_path, initial_filename):
		self.text = text
		self.outdir_path = outdir_path
		self.initial_filename = initial_filename

		self.window = tk.Toplevel()
		self.window.title('Text Output: {0}'.format(initial_filename))
		self.window.columnconfigure(0, weight=1)
		self.window.rowconfigure(0, weight=1)
		self.window.minsize(640, 480)

		self.make_widgets()

	def make_widgets(self):
		self.uniframe = tk.Frame(self.window)
		self.uniframe.grid(row=0, column=0, padx=1, pady=1, sticky='WENS')
		self.uniframe.columnconfigure(0, weight=1)
		self.uniframe.columnconfigure(1, weight=1)
		self.uniframe.columnconfigure(2, weight=0)
		self.uniframe.rowconfigure(0, weight=1)
		self.uniframe.rowconfigure(1, weight=0)

		self.text_box = tk.Text(
			self.uniframe, width=144, height=40, padx=4, pady=4,
			font=('Courier New', 9), relief='sunken', borderwidth=1, background='#FFFFFF'
		)
		self.scrollbar = tk.Scrollbar(self.uniframe)
		self.text_box.insert(tk.END, self.text)
		self.save_button = tk.Button(
			self.uniframe, text='Save As', command=self.save_as, cursor='hand2'
		)
		self.close_button = tk.Button(
			self.uniframe, text='Close', command=self.window.destroy, cursor='hand2'
		)

		self.text_box.grid(row=0, column=0, columnspan=2, padx=1, pady=1, sticky='WENS')
		self.scrollbar.grid(row=0, column=2, padx=1, pady=1, sticky='WENS')
		self.save_button.grid(row=1, column=0, padx=1, pady=1)
		self.close_button.grid(row=1, column=1, padx=1, pady=1)

		self.scrollbar.config(command=self.text_box.yview)
		self.text_box.config(yscrollcommand=self.scrollbar.set)

	def save_as(self):
		dirname = os.path.dirname(self.outdir_path)
		fileoptions = {
			'initialdir': dirname,
			'initialfile': self.initial_filename,
			'title': 'Save text as a new file.',
			'filetypes': [('Text files', '.txt'), ('CSV files', '.csv'), ('All files', '.*')],
			'defaultextension': '.txt'
		}
		filename = tkfd.asksaveasfilename(**fileoptions)
		if filename:
			with open(filename, 'w') as file:
				file.write(self.text)


# GRAPHICS

selectfile_data = """
#define selectfile_width 24
#define selectfile_height 24
static char selectfile_bits[] = {
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xE0, 0xFF, 0x07, 0x10, 0x00, 0x08, 
  0xD0, 0xBD, 0x0B, 0x10, 0x00, 0x08, 0xD0, 0xBD, 0x0B, 0x10, 0x00, 0x08, 
  0xD0, 0xBD, 0x0B, 0x10, 0x00, 0x08, 0xD0, 0xBD, 0x0B, 0x10, 0x00, 0x08, 
  0xD0, 0xBD, 0x0B, 0x10, 0x00, 0x08, 0xD0, 0xBD, 0x0B, 0x10, 0x00, 0x08, 
  0xD0, 0xBD, 0x0B, 0x10, 0x00, 0x08, 0xD0, 0xBD, 0x0B, 0x10, 0x00, 0x08, 
  0x10, 0x00, 0x08, 0xE0, 0xFF, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  };
"""

selectdir_data = """
#define selectdir_width 24
#define selectdir_height 24
static char selectdir_bits[] = {
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF8, 0x01, 0x00, 
  0x04, 0x02, 0x00, 0x04, 0xFE, 0x0F, 0x04, 0x00, 0x10, 0xE4, 0xFF, 0x1F, 
  0x14, 0x00, 0x20, 0x14, 0x00, 0x20, 0x14, 0x00, 0x20, 0x14, 0x00, 0x20, 
  0x14, 0x00, 0x20, 0x14, 0x00, 0x20, 0x14, 0x00, 0x20, 0x14, 0x00, 0x20, 
  0x14, 0x00, 0x20, 0x14, 0x00, 0x20, 0x14, 0x00, 0x20, 0xF8, 0xFF, 0x1F, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  };
"""

large_up_arrow_data = """
#define large_up_arrow_width 17
#define large_up_arrow_height 10
static char large_up_arrow_bits[] = {
  0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x80, 0x02, 0x00, 0x40, 0x05, 0x00, 
  0xA0, 0x0A, 0x00, 0x50, 0x15, 0x00, 0xA8, 0x2A, 0x00, 0x54, 0x55, 0x00, 
  0xAA, 0xAA, 0x00, 0x00, 0x00, 0x00, };
"""

large_down_arrow_data = """
#define large_down_arrow_width 17
#define large_down_arrow_height 10
static char large_down_arrow_bits[] = {
  0x00, 0x00, 0x00, 0xAA, 0xAA, 0x00, 0x54, 0x55, 0x00, 0xA8, 0x2A, 0x00, 
  0x50, 0x15, 0x00, 0xA0, 0x0A, 0x00, 0x40, 0x05, 0x00, 0x80, 0x02, 0x00, 
  0x00, 0x01, 0x00, 0x00, 0x00, 0x00, };
"""

small_up_arrow_data = """
#define small_up_arrow_width 17
#define small_up_arrow_height 10
static char small_up_arrow_bits[] = {
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 
  0x80, 0x02, 0x00, 0x40, 0x05, 0x00, 0xA0, 0x0A, 0x00, 0x50, 0x15, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, };
"""

small_down_arrow_data = """
#define small_down_arrow_width 17
#define small_down_arrow_height 10
static char small_down_arrow_bits[] = {
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x50, 0x15, 0x00, 0xA0, 0x0A, 0x00, 
  0x40, 0x05, 0x00, 0x80, 0x02, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, };
"""

