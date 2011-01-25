"""
Copyright 2011 Søren Juul <zpon.dk [at] gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from datetime import datetime
from time import mktime
import time
class Placemark:
	def __init__(self):
		self.__lon = 0.0
		self.__lat = 0.0
		self.__accuracy = 0
		self.__timestamp = 0

	def setCoordinate(self, latlon):
		lonlat = latlon.split(",")
		self.__lon = float(lonlat[0])
		self.__lat = float(lonlat[1])

	def setLon(self, lon):
		self.__lon = lon
	def getLon(self):
		return self.__lon
	
	def setLat(self, lat):
		self.__lat = lat
	def getLat(self):
		return self.__lat
	
	def getLatLon(self):
		return str(self.__lat)+","+str(self.__lon)
	
	def setAccuracy(self, accuracy):
		self.__accuracy = accuracy
	
	def setTimestamp(self, timestamp):
		date = datetime.fromtimestamp(timestamp/1000)
		self.__timestamp = int(mktime(date.timetuple())+1e-6*date.microsecond-time.timezone)

	def getTimestamp(self):
		return self.__timestamp
