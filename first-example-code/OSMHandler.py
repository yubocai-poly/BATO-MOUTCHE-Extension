#Authors: Paul-Adrien Nicole and Sarah Berkemer
#based on the example scripts here:
#https://oslandia.com/en/2017/07/03/openstreetmap-data-analysis-how-to-parse-the-data-with-python/
#
#
#the osmium classes are used to parse osm files, *.osh.pbf (history files) and *.osm.bz2 (current map)

import osmium as osm
import pandas as pd

class TimelineHandler(osm.SimpleHandler):
    def __init__(self):
        osm.SimpleHandler.__init__(self)
        self.elemtimeline = []

    def node(self, n):
        if n.tags.get('amenity') == 'restaurant' and 'name' in n.tags:
            self.elemtimeline.append(["node",
                                      n.id,
                                      n.tags['name'],
                                      n.location.lat,
                                      n.location.lon,
                                      n.version,
                                      n.visible,
                                      pd.Timestamp(n.timestamp),
                                      n.uid,
                                      n.changeset,
                                      len(n.tags)])

    def write2File(self, outfilename):
        colnames = ['type', 'id', 'name', 'lat', 'lon', 'version', 'visible', 'ts', 'uid', 'chgset', 'ntags']
        elements = pd.DataFrame(self.elemtimeline, columns=colnames)
        elements = elements.sort_values(by=['type', 'id', 'ts'])
        elements.to_csv(outfilename, date_format='%Y-%m-%d %H:%M:%S')


    def getElements(self):
        colnames = ['type', 'id', 'name', 'lat', 'lon', 'version', 'visible', 'ts', 'uid', 'chgset', 'ntags']
        elements = pd.DataFrame(self.elemtimeline, columns=colnames)
        elements = elements.sort_values(by=['type', 'id', 'ts'])
        return elements





class RestauHandler(osm.SimpleHandler):
    def __init__(self):
        super(RestauHandler, self).__init__()
        self.elements = []

    def node(self, o):
        if o.tags.get('amenity') == 'restaurant' and 'name' in o.tags:
            self.elements.append([o.tags['name'],
                                  o.id,
                                  o.location.lat,
                                  o.location.lon])

    def getElements(self):
        colnames = ['name','id', 'lat', 'lon']
        elements = pd.DataFrame(self.elements, columns=colnames)
        elements = elements.sort_values(by=['id'])
        return elements


    def write2File(self, outfilename):
        colnames = ['name','id', 'lat', 'lon']
        elements = pd.DataFrame(self.elements, columns=colnames)
        elements = elements.sort_values(by=['id'])
        elements.to_csv(outfilename, date_format='%Y-%m-%d %H:%M:%S')

