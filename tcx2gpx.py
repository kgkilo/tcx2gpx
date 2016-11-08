'''
Convert a TCX file to a GPX file, including extensions.

Original idea from:
    https://code.google.com/p/ambit2gpx/source/browse/src/ambit2gpx.py
'''

import os
import xml.dom.minidom
import getopt
import sys
from dateutil import parser #needs python-dateutil on Ubuntu
from datetime import timedelta


def child_elements(parent):
    '''Returns a list of child elements of a node of an XML structure'''
    elements = []
    for child in parent.childNodes:
        if child.nodeType != child.ELEMENT_NODE:
            continue
        elements.append(child)
    return elements


class TcxXMLParser(object):
    '''The main converter class'''

    def __init__(self, xml_node, opts, output_file):
        assert isinstance(xml_node, xml.dom.Node)
        assert xml_node.nodeType == xml_node.ELEMENT_NODE
        self.__root = xml_node
        self.__outputfile = output_file
        self.__time =  None
        self.__opts = opts
        self.__nb_trackpoints_parsed = 0


    def extension(self, heartrate, temperature, cadence, power):
        '''Compiles the GPX extension part of a trackpoint'''
        extension_found = False

        hr_ext = ""
        if (heartrate is not None):
            extension_found = True
            hr_ext = "<gpxtpx:hr>{hr}</gpxtpx:hr>".format(hr=heartrate)

        tmp_ext = ""
        if (temperature is not None):
            extension_found = True
            tmp_ext = "<gpxtpx:atemp>{temp}</gpxtpx:atemp>".format(
                                                    temp=temperature)

        cad_ext = ""
        if (cadence is not None):
            extension_found = True
            cad_ext = "<gpxtpx:cad>{cadence}</gpxtpx:cad>".format(
                                                    cadence=cadence)

        pow_ext = ""
        if (power is not None):
            extension_found = True
            pow_ext = "<gpxtpx:power>{power}</gpxtpx:power>".format(
                                                    power=power)

        if not extension_found:
            return ""

        #Compose return string
        ret = """<extensions>
        <gpxtpx:TrackPointExtension>
            {hrext}""".format(hrext=hr_ext)

        if tmp_ext != "":
            ret += """
            {tmpext}""".format(tmpext=tmp_ext)

        if pow_ext != "":
            ret += """
            {powext}""".format(powext=pow_ext)

        if cad_ext != "":
            ret += """
            {cadext}""".format(cadext=cad_ext)

        ret += """
        </gpxtpx:TrackPointExtension>
    </extensions>"""

        return ret


# pylint: disable=R0912
#Too many branches
    def __parse_trackpoint(self, trackpoint):
        '''Parse one trackpoint from the TCX file
            and write the appropriate GPX line'''
        latitude = None
        longitude = None
        altitude = None
        speed = None
        heartrate = None
        cadence = None
        power = None
        temperature = None
        inttime = None

        self.__nb_trackpoints_parsed += 1   #One more trackpoint parsed
        #Progress bar: print a dot for every 100 trackpoint
        if self.__nb_trackpoints_parsed % 100 == 0:
            sys.stdout.write(".")
            if self.__nb_trackpoints_parsed % (80*100) == 0:
                sys.stdout.write("\n")

        #Analyse trackpoint data
        '''
        Sample data

        <Trackpoint>
          <Time>2016-10-07T08:01:12Z</Time>
          <Position>
            <LatitudeDegrees>46.291537</LatitudeDegrees>
            <LongitudeDegrees>11.244808</LongitudeDegrees>
          </Position>
          <AltitudeMeters>245.2</AltitudeMeters>
          <DistanceMeters>0.0</DistanceMeters>
          <HeartRateBpm>
            <Value>98</Value>
          </HeartRateBpm>
          <Cadence>70</Cadence>
          <Extensions>
            <TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">
              <Watts>81</Watts>
              <Speed>19.09785839292334</Speed>
            </TPX>
          </Extensions>
        </Trackpoint>
        '''
        for node in child_elements(trackpoint):
            key = node.tagName

            if key.lower() == "time":
                val = node.firstChild.nodeValue
                inttime = val

            elif key.lower() == "position":
                for subNode in child_elements(node):
                  subKey = subNode.tagName
                  if subKey.lower() == "latitudedegrees":
                    subVal = subNode.firstChild.nodeValue
                    latitude = float(subVal)

                  elif subKey.lower() == "longitudedegrees":
                    subVal = subNode.firstChild.nodeValue
                    longitude = float(subVal)
                  #print subKey, subVal

            elif key.lower() == "altitudemeters":
                val = node.firstChild.nodeValue
                if self.__opts['noalti']:
                    altitude = 0
                else:
                    altitude = float(val)

            elif key.lower() == "distancemeters":
                val = node.firstChild.nodeValue
                cadence = int(float(val))

            elif key.lower() == "heartratebpm":
                val = node.firstChild.firstChild.nodeValue.replace(',', '.')
                heartrate = int(val)

            elif key.lower() == "cadence":
                val = node.firstChild.nodeValue
                cadence = int(val)

            elif key.lower() == "temperature":
                temperature = float(val)

            elif key.lower() == "extensions":
                for subNode in child_elements(child_elements(node)[0]):
                  subKey = subNode.tagName
                  if subKey.lower() == "watts":
                    subVal = subNode.firstChild.nodeValue
                    power = float(subVal)
                  elif subKey.lower() == "speed":
                    subVal = subNode.firstChild.nodeValue
                    speed = float(subVal)
                  #print subKey, subVal

        #Format output
        if latitude is not None and longitude is not None:
            if self.__opts['noalti']:
                print >> self.__outputfile, """
<trkpt lat="{latitude}" lon="{longitude}"><time>{time}</time><speed>{speed}</speed>
    {extension}
</trkpt>
""".format(latitude=latitude, longitude=longitude,
           time=inttime, speed=speed,
           extension=self.extension(heartrate, temperature,
                                    cadence, power))
            else:
                print >> self.__outputfile, """
<trkpt lat="{latitude}" lon="{longitude}"><ele>{altitude}</ele><time>{time}</time><speed>{speed}</speed>
    {extension}
</trkpt>
""".format(latitude=latitude, longitude=longitude, altitude=altitude,
           time=inttime, speed=speed,
           extension=self.extension(heartrate, temperature,
                                    cadence, power))



    def __parse_trackpoints(self, trackpoints):
        '''Parse all trackpoints from the TCX file'''
        for node in child_elements(trackpoints):
            if node.tagName == "Activities":
                self.__parse_trackpoints(node)
            elif node.tagName == "Activity":
                self.__parse_trackpoints(node)
            elif node.tagName == "Lap":
                self.__parse_trackpoints(node)
            elif node.tagName == "Track":
                self.__parse_trackpoints(node)
            key = node.tagName

            #Now let's get those trackpoints
            if key.lower() == "trackpoint":
                self.__parse_trackpoint(node)


    def execute(self):
        '''Compile the contents of the GPX file'''
        #Write GPX header
        #Creator set to Garmin Edge 800 so that Strava accepts
        # barometric altitude datae
        print >> self.__outputfile, \
            '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>'
        print >> self.__outputfile, """
<gpx version="1.1"
creator="Garmin Edge 800"
xmlns="http://www.topografix.com/GPX/1/1"
xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">

  <metadata>
    <link href="https://github.com/kgkilo/tcx2gpx">
      <text>Tcx2Gpx</text>
    </link>
  </metadata>

  <trk>
    <trkseg>
"""

        #Parse TCX file
        root = self.__root
        for node in child_elements(root):
            key = node.tagName

            if key.lower() == "trainingcenterdatabase":
                self.__parse_trackpoints(node)

        #Finish writing GPX file
        print >> self.__outputfile,"""
    </trkseg>
  </trk>
</gpx>
"""


def usage():
    '''Prints default usage help'''
    print """
tcx2gpx [--noalti] filename
Creates a file filename.gpx in GPX format from filename in .tcx XML format.
If option --noalti is given, elevation will be not be set. Otherwise, elevation is retrieved from barometric altimeter information.
"""


def read_input_file(filename):
    '''Reads the contents of the input file'''
    input_file = open(filename)
    input_file.readline() # Skip first line
    file_contents = input_file.read()
    input_file.close()
    return file_contents


def write_output_file(root_filename, top_node, opts):
    '''Writes the top_node tree into a GPX file'''
    output_filename = root_filename + '.gpx'
    output_file = open(output_filename, 'w')
    print "Creating file {0}".format(output_filename)
    TcxXMLParser(top_node[0], opts, output_file).execute()
    output_file.close()


def parse_tcx_file(file_contents):
    '''Parses the contents of the TCX file and returns it'''
    doc = xml.dom.minidom.parseString(
                        '<?xml version="1.0" encoding="utf-8"?><top>'
                        + file_contents + '</top>')
    assert doc is not None
    top = doc.getElementsByTagName('top')
    assert len(top) == 1
    return top


# pylint: disable=W0612
#Unused variable (arg)
def main():
    '''Erm.. main...'''

    try:
        ops, args = getopt.getopt(sys.argv[1:],
            "ha",
            ["help", "noalti"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    if not sys.argv[1:]:
        usage()
        sys.exit(2)

    #Parse command-line options
    opts = {'noalti':False}

    for option, arg in ops:
        if option in ("-h", "--help"):
            usage()
            sys.exit()
        elif option in ("-n", "--noalti"):
            opts['noalti'] = True
        else:
            assert False, "unhandled option"

    #Read input TCX file
    filename = args[0]
    (root_filename, ext) = os.path.splitext(filename)
    if (ext == ""):
        filename += ".tcx"
    if (not os.path.exists(filename)):
        print >> sys.stderr, "File {0} doesn't exist".format(filename)
        sys.exit()
    file_contents = read_input_file(filename)

    #Parse TCX file contents
    print "Parsing file {0}".format(filename)
    top = parse_tcx_file(file_contents)
    print "Done."

    #Write output GPX file
    write_output_file(root_filename, top, opts)
    print "\nDone."

if __name__ == "__main__":
    main()
