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

from PySide import QtXml
from placemark import Placemark

class KmlHandler(QtXml.QXmlDefaultHandler):
	def __init__(self):
		QtXml.QXmlDefaultHandler.__init__(self)
		self.__parentDataName = ""
		self.currentText = ""
		self.items = []
		self.item = None

	def startElement(self, namespaceURI, localName, qName, attr):
		if localName == "Placemark":
			self.item = Placemark()
		elif localName == "Data":
			self.__parentDataName = attr.value("name")
		self.currentText = ""
		return True

	def endElement(self, namespaceURI, localName, qName):
		if localName == "value":
			if self.__parentDataName == "accuracy":
				self.item.setAccuracy(self.currentText)
			elif self.__parentDataName == "timestamp":
				self.item.setTimestamp(int(self.currentText))
		elif localName == "Point":
			self.item.setCoordinate(self.currentText)
		elif localName == "Placemark":
			self.items.append(self.item)
		return True
	
	def endDocument(self):
		self.items = sorted(self.items, key=lambda placemark: placemark.getTimestamp())
		return True

	def characters(self, ch):
		self.currentText += ch
		return True

	def fatalError(self, exception):
		print "Fatal error on line %d, column %d:%s" % (exception.lineNumber(), exception.columnNumber(), exception.message())
		return False

