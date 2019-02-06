#!/usr/bin/env python3

# SunMetrics calculates the position of the sun at a given time and place.
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

# This code was based on a reading of work done by Michel J. Anders:
# http://michelanders.blogspot.com/2010/12/calulating-sunrise-and-sunset-in-python.html
# It is also based on the spreadsheets calcs distributed by NOAA:
# http://www.srrb.noaa.gov/highlights/sunrise/calcdetails.html

# IMPORT

import math
import datetime
import pytz


# GLOBALS

# North of the equator, latitude is positive.
# West of the prime meridian, longitude is negative.
# Any dates should be datetime.datetime objects.
# "tz_local" is the local timezone where the data was taken.

# For all datetime.datetime queries, specify whether the query is in
# "local" time or "utc" time.

# Teton Cougar Project, 2012
#default_latitude = 43.725107668672
#default_longitude = -110.405046025196
#default_tz_local = 'US/Mountain'

# Mongolia, 2019
default_latitude = 47.92027778
default_longitude = 106.91722222
default_tz_local = 'Asia/Ulaanbaatar'

# CLASSES

class SunMetrics(object):
	"""Calculate sun metrics for a given longitude, latitude, and date/time.

	Based on spreadsheets from http://www.srrb.noaa.gov/highlights/sunrise/calcdetails.html

	Typical use:

	import sunrise
	sun_metrics = SunMetrics()
	print(sun_metrics.sunrise_utc)
	print(sun_metrics.solar_noon_utc)
	print(sun_metrics.sunset_utc)
	"""

	def __init__(self, latitude=default_latitude, longitude=default_longitude, tz_local=default_tz_local):
		self.latitude = latitude
		self.longitude = longitude
		self.tz_local = pytz.timezone(tz_local)
		self.tz_utc = pytz.timezone('UTC')

		# Start with "now" as the date and time
		self.datetime_utc = self.tz_utc.localize(datetime.datetime.utcnow())
		self.datetime_local = self.datetime_utc.astimezone(self.tz_local)

		self.calculate()

	def calculate(self):
		"""Calculate the sunrise, sunset, solar noon, and other things along the way."""

		# Convert the UTC time to decimal days, used in calculating Julian Date
		utc_decimal_time = self.time_to_decimal_day(self.datetime_utc.time())

		# Julian Date. Calculation from (Danby 1988, p. 207; Sinnott 1991, p. 183).
		# This equation contains an approximation making it only useful for years between 1901 and 2099
		Julian_Date = (367 * self.datetime_utc.year) - (7 * (self.datetime_utc.year + ((self.datetime_utc.month + 9) // 12)) // 4) + ((275 * self.datetime_utc.month) // 9) + self.datetime_utc.day + 1721013.5 + utc_decimal_time

		# Julian century, hundreds of years since 2000-01
		Julian_century = (Julian_Date - 2451545) / 36525

		# Geometric Mean Long Sun (degrees)
		GM_Long = (280.46646 + Julian_century * (36000.76983 + Julian_century * 0.0003032)) % 360

		# Geometric Mean Anom Sun (degrees)
		GM_Anom = 357.52911 + Julian_century * (35999.05029 - 0.0001537 * Julian_century)

		# Eccentricity of Earth's orbit
		Eccent = 0.016708634 - (Julian_century * (0.000042037 + (0.0000001267 * Julian_century)))

		# Sun Eq of Ctr
		S_Eq_Ctr = math.sin(math.radians(GM_Anom)) * (1.914602 - Julian_century * (0.004817 + 0.000014 * Julian_century)) + math.sin(math.radians(2 * GM_Anom)) * (0.019993 - 0.000101 * Julian_century) + math.sin(math.radians(3 * GM_Anom)) * 0.000289

		# Sun True Long (degrees)
		S_True_Long = GM_Long + S_Eq_Ctr

		## Sun True Anom (degrees)
		#S_True_Anom = GM_Anom + S_Eq_Ctr

		## Sun Rad Vector (Astronomical Units)
		#S_Rad_Vector = (1.000001018 * (1 - (Eccent * Eccent))) / (1 + (Eccent * math.cos(math.radians(S_True_Anom))))

		# Sun App Long (degrees)
		S_App_Long = S_True_Long - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * Julian_century))

		# Mean Obliq Ecliptic (degrees)
		M_Obliq = 23 + (26 + ((21.448 - Julian_century * (46.815 + Julian_century * (0.00059 - Julian_century * 0.001813)))) / 60) / 60

		# Obliq Corr (degrees)
		Obliq = M_Obliq + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * Julian_century))

		## Sun Rt Ascen (degrees)
		#S_Rt_Ascen = math.degrees( math.atan2( (math.cos(math.radians(Obliq)) * math.sin(math.radians(S_App_Long))), math.cos(math.radians(S_App_Long)) ) )

		# Sun Declination (degrees)
		S_Declination = math.degrees(math.asin(math.sin(math.radians(Obliq)) * math.sin(math.radians(S_App_Long))))

		# var y
		var_y = math.tan(math.radians(Obliq / 2)) * math.tan(math.radians(Obliq / 2))

		# Eq of time (minutes)
		Eq_of_time = 4 * math.degrees(var_y * math.sin(2 * math.radians(GM_Long)) - 2 * Eccent * math.sin(math.radians(GM_Anom)) + 4 * Eccent * var_y * math.sin(math.radians(GM_Anom)) * math.cos(2 * math.radians(GM_Long)) - 0.5 * var_y * var_y * math.sin(4 * math.radians(GM_Long)) - 1.25 * Eccent * Eccent * math.sin(2 * math.radians(GM_Anom)))

		# Hour Angle sunrise (degrees)
		hour_angle_sunrise = math.degrees(math.acos(math.cos(math.radians(90.833)) / (math.cos(math.radians(self.latitude)) * math.cos(math.radians(S_Declination))) - math.tan(math.radians(self.latitude)) * math.tan(math.radians(S_Declination))))

		# Solar noon (UTC decimal days)
		solar_noon = (720 - (4 * self.longitude) - Eq_of_time) / 1440

		# Sunrise (UTC decimal days)
		sunrise = solar_noon - (hour_angle_sunrise * 4 / 1440)

		# Sunset (UTC decimal days)
		sunset = solar_noon + (hour_angle_sunrise * 4 / 1440)

		## Sunlight Duration (minutes)
		#sunlight_duration = hour_angle_sunrise * 8

		## True Solar Time (minutes)
		#true_solar_time = ((utc_decimal_time * 1440) + Eq_of_time + (4 * self.longitude)) % 1440

		## Hour Angle (degrees)
		#if (true_solar_time / 4) < 0:
		# 	hour_angle = (true_solar_time / 4) + 180
		#else:
		# 	hour_angle = (true_solar_time / 4) - 180

		## Solar Zenith Angle (degrees)
		#solar_zenith_angle = math.degrees( math.acos( (math.sin(math.radians(self.latitude)) * math.sin(math.radians(S_Declination))) + (math.cos(math.radians(self.latitude)) * math.cos(math.radians(S_Declination)) * math.cos(math.radians(hour_angle))) ) )

		## Solar Elevatian Angle (degrees)
		#self.solar_elevation_angle = 90 - solar_zenith_angle

		## Approximate Atmospheric Refraction (degrees)
		#if 85 <= self.solar_elevation_angle < 180:
		# 	pre_refraction = 0
		#elif 5 <= self.solar_elevation_angle < 85:
		# 	pre_refraction = (58.1 / math.tan(math.radians(self.solar_elevation_angle))) - (0.07 / math.pow(math.tan(math.radians(self.solar_elevation_angle)), 3)) + (0.000086 / math.pow(math.tan(math.radians(self.solar_elevation_angle)), 5))
		#elif -0.575 <= self.solar_elevation_angle < 5:
		# 	# Spreadsheet equation:
		# 	#pre_refraction = 1735 + self.solar_elevation_angle * (-518.2 + self.solar_elevation_angle * (103.4 + self.solar_elevation_angle * (-12.79 + self.solar_elevation_angle * 0.711)))
		# 	# Print equation:
		# 	pre_refraction = 1735 - (518.2 * self.solar_elevation_angle) + (103.4 * math.pow(self.solar_elevation_angle, 2)) - (12.79 * math.pow(self.solar_elevation_angle, 3)) + (0.711 * math.pow(self.solar_elevation_angle, 4))
		#else:
		# 	# 20.772 in spreadsheet, 20.774 in print:
		# 	pre_refraction = -20.774 / math.tan(math.radians(self.solar_elevation_angle))
		# 
		#atmos_refraction = pre_refraction / 3600

		## Solar Elevation Angle corrected for atmospheric refraction
		#solar_elevation_refraction = self.solar_elevation_angle + atmos_refraction

		## Solar Azimuth Angle (degrees clockwise from North)
		#pre_azimuth_angle = math.degrees(math.acos(((math.sin(math.radians(self.latitude)) * math.cos(math.radians(solar_zenith_angle))) - math.sin(math.radians(S_Declination))) / (math.cos(math.radians(self.latitude)) * math.sin(math.radians(solar_zenith_angle)))))
		#if hour_angle > 0:
		# 	self.solar_azimuth_angle = (pre_azimuth_angle - 180) % 360
		#else:
		# 	self.solar_azimuth_angle = (540 - pre_azimuth_angle) % 360

		self.solar_noon_utc = self.decimal_day_to_utc_datetime(solar_noon)
		self.sunrise_utc = self.decimal_day_to_utc_datetime(sunrise)
		self.sunset_utc = self.decimal_day_to_utc_datetime(sunset)

	def new_date(self, datetime_request, utc_or_local='utc'):
		"""Take in a new date and recalculate. We need to know if the request is in utc or local time."""

		if utc_or_local == 'utc':
			self.datetime_utc = self.tz_utc.localize(datetime_request)
			self.datetime_local = self.datetime_utc.astimezone(self.tz_local)
		elif utc_or_local == 'local':
			self.datetime_local = self.tz_local.localize(datetime_request)
			self.datetime_utc = self.datetime_local.astimezone(self.tz_utc)
		else:
			print('Invalid argument for utc_or_local: {}. Should be "utc" or "local"'.format(utc_or_local))
			return False

		self.calculate()

	def time_to_decimal_day(self, time):
		"""Convert a datime.time object to a decimal day."""

		return ((time.hour * 3600) + (time.minute * 60) + time.second) / 86400.0

	def decimal_day_to_utc_datetime(self, decimal_day):
		"""Convert a decimal day to a *UTC* datetime.datetime object."""

		this_delta = datetime.timedelta(seconds=int(decimal_day * 86400))

		base_date = datetime.datetime(self.datetime_local.year, self.datetime_local.month, self.datetime_local.day)
		naive_datetime = base_date + this_delta
		return self.tz_utc.localize(naive_datetime)

	def is_daylight(self, datetime_request, utc_or_local):
		self.new_date(datetime_request, utc_or_local)

		if self.sunrise_utc <= self.datetime_utc <= self.sunset_utc:
			return True
		else:
			return False

	def output(self):
		print('Request:    {}\nSunrise:    {}\nSolar Noon: {}\nSunset:     {}\n'.format(self.datetime_utc, self.sunrise_utc, self.solar_noon_utc, self.sunset_utc))


if __name__ == "__main__":
	sun_metrics = SunMetrics()
	sun_metrics.output()

