#!/usr/bin/python
#
# Copyright 2011 Intrepidus Group
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import logging, time, os
from optparse import OptionParser, OptionGroup

import manitree.Report as Report

def main():
  parser = OptionParser(usage="%prog ([-T outputfile.txt] | [-H output.html] | |) [-r report.db]", \
    version ="%prog 0.1")
  parser.set_defaults( \
    databaseFile="report.db",
    device=False, package=False, risk=False, 
  )
  parser.add_option("-T", dest="txtFile", action="store",  \
   help='path to text output')
  parser.add_option("-H", dest="htmlFile", action="store", \
   help='path to html output')
  parser.add_option("-f", dest="databaseFile", action="store", \
   help='path to report database (Default report.db')

  reportGroup = OptionGroup(parser, "Report Options")
  reportGroup.add_option("-D", dest="devicereport", action="store", \
   help='run a report on a specific device. Supply the device serial number or use "None" if testing was done on individual files')
  reportGroup.add_option("-P", dest="packagereport", action="store", \
   help='run a report on a specific package. (ex. com.intrepidusgroup.app)')
  reportGroup.add_option("-R", dest="riskreport", action="store", \
   help='run a report on matching risk levels. (high, medium, or low)')
  parser.add_option_group(reportGroup)

  filterGroup = OptionGroup(parser, "Filter Options")
  filterGroup.add_option("-d", dest="device", action="store")
  filterGroup.add_option("-p", dest="package", action="store")
  filterGroup.add_option("-r", dest="risk", action="store")
  
  parser.add_option_group(filterGroup)

  group = OptionGroup(parser, "Debug Options")
  group.add_option("-v", action="store_true", dest="verbose", help="Display verbose output")
  parser.add_option_group(group)

  (options, args) = parser.parse_args()

  if options.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
  else:
    logging.getLogger().setLevel(logging.INFO)

  if not os.path.exists(options.databaseFile):
    parser.error("%s report database not found." % options.databaseFile)

  report = Report.Report()

  if options.devicereport:
    logging.debug("Running device report")
    output = report.devReport(options.devicereport, options.package, options.risk)
  elif options.packagereport:
    logging.debug("Running package report")
    output = report.packageReport(options.packagereport, options.device, options.risk)
  elif options.riskreport:
    logging.debug("Running risk report")
    output = report.riskReport(options.riskreport, options.device, options.package)
  else:
    logging.debug("Running all device report")
    output = report.allReport(options.device, options.package, options.risk)
  
  if options.txtFile:
    #run report to text file
    report.text(output, options.txtFile)
  elif options.htmlFile:
    #run report to html file
    report.html(output, options.htmlFile)
  else:
    #run report to the console
    report.console(output)

if __name__ == "__main__":
  main()

