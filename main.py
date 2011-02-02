#!/usr/bin/env python
# -*- coding: UTF8 -*-
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

import os
import sys
from datetime import datetime
import time
from time import mktime
from PySide import QtGui, QtCore, QtNetwork, QtXml
import pyexiv2

from kmlHandler import KmlHandler

class Main(QtGui.QWidget):
	def __init__ (self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.setFixedSize(800,600)
		self.debugging = True
		self.shouldShowImage = False
		self.zoom = 15

		hlayout_main = QtGui.QHBoxLayout()
		self.setLayout(hlayout_main)
		vlayout_btn_browse = QtGui.QVBoxLayout()
		hlayout_main.addLayout(vlayout_btn_browse)
		
		self.btn_browseImages = QtGui.QPushButton("Select Images", self)
		QtCore.QObject.connect(self.btn_browseImages, QtCore.SIGNAL("clicked()"), self.browseImages)

		self.btn_browseKml = QtGui.QPushButton("Select KML", self)	
		QtCore.QObject.connect(self.btn_browseKml, QtCore.SIGNAL("clicked()"), self.browseKml)

		vlayout_btn_browse.addWidget(self.btn_browseImages)
		vlayout_btn_browse.addWidget(self.btn_browseKml)
		vlayout_btn_browse.addStretch()

		self.listModel = QtGui.QStringListModel()
		self.lst_images = QtGui.QListView(self)
		self.lst_images.clicked.connect(self.onImageClick)
		hlayout_main.addWidget(self.lst_images)

		vlayout_img_btn = QtGui.QVBoxLayout()
		hlayout_main.addLayout(vlayout_img_btn)

		self.image_viewer = QtGui.QLabel(self)
		self.image_viewer.setFixedWidth(512)
		self.image_viewer.setFixedHeight(512)
		
		vlayout_img_btn.addWidget(self.image_viewer)

		vlayout_img_btn.addStretch()
		
		hlayout_btn_switch = QtGui.QHBoxLayout()
		vlayout_img_btn.addLayout(hlayout_btn_switch)
		
		self.btn_zoomIn = QtGui.QPushButton("Zoom in", self)
		self.btn_zoomOut = QtGui.QPushButton("Zoom out", self)
		QtCore.QObject.connect(self.btn_zoomIn, QtCore.SIGNAL("clicked()"), self.zoomIn)
		QtCore.QObject.connect(self.btn_zoomOut, QtCore.SIGNAL("clicked()"), self.zoomOut)
		self.btn_showImage = QtGui.QPushButton("View Image", self)
		QtCore.QObject.connect(self.btn_showImage, QtCore.SIGNAL("clicked()"), self.showImage)
		self.btn_showMap = QtGui.QPushButton("View Map", self)
		QtCore.QObject.connect(self.btn_showMap, QtCore.SIGNAL("clicked()"), self.showMap)
		self.btn_writeGeo = QtGui.QPushButton("Write Geocoodinate", self)
		QtCore.QObject.connect(self.btn_writeGeo, QtCore.SIGNAL("clicked()"), self.tagImage)

		hlayout_btn_switch.addWidget(self.btn_zoomIn)
		hlayout_btn_switch.addWidget(self.btn_zoomOut)
		hlayout_btn_switch.addWidget(self.btn_showImage)
		hlayout_btn_switch.addWidget(self.btn_showMap)
		hlayout_btn_switch.addWidget(self.btn_writeGeo)

		self.http = QtNetwork.QHttp(self)
		self.connect(self.http, QtCore.SIGNAL('done(bool)'), self, QtCore.SLOT('updateMap(bool)'))

	def updateMap(self, error):
		if error:
			self.debug("Http error: " + self.http.errorString())
		image = QtGui.QPixmap()
		if image.loadFromData(self.http.readAll()):
			self.image_viewer.setPixmap(image)
		else:
			self.debug("Error loading image")
	
	def zoomIn(self):
		self.zoom += 1
		self.showMap()
	
	def zoomOut(self):
		self.zoom -= 1
		self.showMap()
	
	def browseImages(self):
		fileNames = QtGui.QFileDialog.getOpenFileNames(self,"Select one or more images", os.getenv("HOME"), "*.jpeg *.jpg")
		self.listModel.beginResetModel()
		self.listModel.setStringList(fileNames[0])

		self.lst_images.setModel(self.listModel)
	
	def browseKml(self):
		fileName = QtGui.QFileDialog.getOpenFileName(self,"Select one or more images", os.getenv("HOME"), "*kml")

		if not fileName:
			return

		xmlReader = QtXml.QXmlSimpleReader()
		file = QtCore.QFile(fileName[0])
		source = QtXml.QXmlInputSource(file)
		self.handler = KmlHandler()
		xmlReader.setContentHandler(self.handler)
		xmlReader.setErrorHandler(self.handler)

		ok = xmlReader.parse(source)

		if not ok:
			print "error parsing"
	
	"""
	Get geocode of current image
	Returns a array of [lat, lon, preMarkIndex]
	"""
	def getGeocode(self):
		if "Exif.Photo.DateTimeDigitized" in self.image.exifKeys():
			# get the time of photo
			imgTime = int(mktime(self.image["Exif.Photo.DateTimeDigitized"].timetuple())+1e-6*self.image["Exif.Photo.DateTimeDigitized"].microsecond-time.timezone)
			preMark = None
			postMark = None
			lat = None
			lon = None

			for index, item in enumerate(self.handler.items):
				if item.getTimestamp() > imgTime:
					if index > 1:
						preMark = self.handler.items[index-1]
						preMarkIndex = index-1
					else:
						preMark = item
						preMarkIndex = index
					postMark = item
					break

			# TODO improve position calculation, based on time between preMark and postMark 
			# contra the image time
			if preMark is not None and postMark is not None:
				lat = preMark.getLat()+(preMark.getLat()-postMark.getLat())/2
				lon = preMark.getLon()+(preMark.getLon()-postMark.getLon())/2
				return [lat, lon, preMarkIndex]
			else:
				debug("No data in KML matched the time found in image")
		else:
			# TODO handle if no tags available
			debug("Picture did not have Exif.Photo.DateTimeDigitized info")
			return [None, None, None]

	def showMap(self):
		self.shouldShowImage = False

		data = self.getGeocode()
		lat = data[0]
		lon = data[1]
		preMarkIndex = data[2]

		if lat is not None and lon is not None:
			preMark = self.handler.items[preMarkIndex]
			postMark = self.handler.items[preMarkIndex+1]

			# TODO Handle magic numbers
			if preMarkIndex - 3 < 0:
				start = 0
			else:
				start = preMarkIndex - 3
			if preMarkIndex + 4 > len(self.handler.items)-1:
				stop = len(self.handler.items)-1
			else:
				stop = preMarkIndex+4
			pathItems = self.handler.items[start:stop]
			path = []
			for item in pathItems:
				 path.append(item.getLatLon())

			strPath = "|".join(path)

			self.http.setHost("maps.google.com")
			self.http.get("/maps/api/staticmap?center="+str(lat)+","+str(lon)+"&zoom="+str(self.zoom)+"&size=512x512&maptype=roadmap&markers=color:blue|label:I|"+str(lat)+","+str(lon)+"&path="+strPath+"&sensor=false")

	def showImage(self):
		self.shouldShowImage = True
		pixmap = QtGui.QPixmap(self.listModel.stringList()[self.index]).scaled(self.image_viewer.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.FastTransformation)
		self.image_viewer.setPixmap(pixmap)

	def onImageClick(self, index):
		self.index = self.lst_images.selectedIndexes()[0].row()
		self.image = pyexiv2.Image(self.listModel.stringList()[self.index])
		self.image.readMetadata()

		if self.shouldShowImage is True:
			self.showImage()
		else:
			self.showMap()

	def tagImage(self):
		data = self.getGeocode()
		lat = data[0]
		lon = data[1]
		latref = 'S' if lat < 0 else 'N'
		lngref = 'W' if lon < 0 else 'E'
		latdeg = abs(int(lat))
		londeg = abs(int(lon))
		latmin = abs(int((lat - int(lat)) * 60 * 10000))
		lonmin = abs(int((lon - int(lon)) * 60 * 10000))
		latdeg = pyexiv2.Rational(latdeg, 1)
		latmin = pyexiv2.Rational(latmin, 10000)
		londeg = pyexiv2.Rational(londeg, 1)
		lonmin = pyexiv2.Rational(lonmin, 10000)
		bothsec = pyexiv2.Rational(0, 1)
		self.image['Exif.GPSInfo.GPSVersionID'] = '2 2 0'
		self.image['Exif.GPSInfo.GPSLatitudeRef'] = latref
		self.image['Exif.GPSInfo.GPSLatitude'] = (latdeg, latmin, bothsec)
		self.image['Exif.GPSInfo.GPSLongitudeRef'] = lngref
		self.image['Exif.GPSInfo.GPSLongitude'] = (londeg, lonmin, bothsec)
		self.image['Exif.GPSInfo.GPSMapDatum'] = 'WGS-84'
		self.image.writeMetadata()
		
	def debug(self, error):
		if self.debugging:
			print "*** DEBUG " + error

app = QtGui.QApplication(sys.argv)
widget = Main()
widget.show()
sys.exit(app.exec_())
