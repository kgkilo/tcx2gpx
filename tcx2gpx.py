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
        return ""


# pylint: disable=R0912
#Too many branches
    def __parse_trackpoint(self, trackpoint):
        '''Parse one trackpoint from the TCX file
            and write the appropriate GPX line'''


    def __parse_trackpoints(self, trackpoints):
        '''Parse all trackpoints from the TCX file'''


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
#creator="tcx2gpx" version="1.0"

        #Parse TCX file
        root = self.__root
        for node in child_elements(root):
            key = node.tagName
            if key.lower() == "globalsat_gb580":
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
tcx2gpx [--noalti] [--noext] [--nopower] [--notemp] filename
Creates a file filename.gpx in GPX format from filename in .tcx XML format.
If option --noalti is given, elevation will be not be set. Otherwise, elevation is retrieved from barometric altimeter information.
If option --noext is given, extended data (heartrate, temperature, cadence, power) will not generated. Useful for instance if size of output file matters.
If option --nopower is given, power data will not be inserted in the extended dataset.
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
            ["help", "noalti", "noext",
            "nopower", "notemp"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    if not sys.argv[1:]:
        usage()
        sys.exit(2)

    #Parse command-line options
    opts = {'noalti':False,
            'noext':False,
            'nopower':False,
            'notemp':False}

    for option, arg in ops:
        if option in ("-h", "--help"):
            usage()
            sys.exit()
        elif option in ("-n", "--noalti"):
            opts['noalti'] = True
        elif option in ("--noext"):
            opts['noext'] = True
        elif option in ("--nopower"):
            opts['nopower'] = True
        elif option in ("--notemp"):
            opts['notemp'] = True
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
