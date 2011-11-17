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


import os
import shutil
import xml.dom.minidom
from optparse import OptionParser, OptionGroup
import time
import logging

import manitree.Apk as Apk
import manitree.Device as Device
import manitree.Manifest as Manifest
import manitree.Tools as Tools
import manitree.Report as Report

def main():
  #options parser

  MODE = ''
  parser = OptionParser(usage="%prog -f [MANIFESTFILE | APKFILE] | -D", version="%prog 0.5")
  parser.set_defaults(
    inputFile = "",
  )
  parser.add_option("-f", dest="inputFile", action="store", help='path to AndroidManifest.xml or APK (e.g. /home/user/com.something.apk, ./')

  group = OptionGroup(parser, "Device Mode Options")
  group.add_option("-D", dest="device", action="store_true", help="Device Mode: Perform a full test on a device")
  group.add_option("-d", action="store_true", dest="physical", help="Download from a physical device.(Device mode only)")
  group.add_option("-e", action="store_true", dest="emulator",help="Download from an emulated device.(Device mode only)")
  group.add_option("--path", action="store", dest="tmppath", help="Set path of where files are temporarily downloaded. (Default /tmp/AT)")
  group.add_option("-u", action="store_true", dest="userapps", help="Test only user apps")
  parser.add_option_group(group)
#  group.add_option("-k", action="store_true", dest="keep", help="Keep APKs downloaded from a a device")

  group = OptionGroup(parser, "Debug Options")
  group.add_option("-v", action="store_true", dest="verbose", help="Display verbose output")
  group.add_option("-q", action="store_true", dest="quiet",help="Quiet mode")
  group.add_option("-t", action="store_true", dest="test", help="Test mode. Check to see that environment has been setup")
  parser.add_option_group(group)

  (options, args) = parser.parse_args()
  ##VALIDATE OPTIONS HERE
  if options.quiet:
    logging.getLogger().setLevel(logging.ERROR)
  elif options.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
  else:
    logging.getLogger().setLevel(logging.INFO)

  if options.inputFile:
    if os.path.isdir(options.inputFile):
      MODE = 'dir'
    elif options.inputFile.endswith('apk'):
      MODE = 'apk'
    elif options.inputFile.endswith('xml'):
      MODE = 'xml'
    elif options.test == True:
      MODE = 'test'
    else:
      parser.error("Invalid input file")

  adboptions = ''
  if options.device == True:
    MODE = 'dev'
    if options.physical:
      adboptions += '-d'
    elif options.emulator:
      adboptions += '-e'

  if options.userapps:
    sysFilter = True
  else:
    sysFilter = False

  if MODE == 'dev':
    dev = Device.Device()
    tool = Tools.Tools()
    adbpath = tool.istoolinpath('adb')
    devlist = dev.adbcheck(adbpath, adboptions)
    if not options.tmppath:
      tmppath = '/tmp/AT'
    else:
      tmppath = options.tmppath

    for device in devlist:
      logging.debug("Starting device test on %s" % device)
      adboptions = "-s " + device
      devicetesting(adboptions, sysFilter, tmppath)
  elif MODE == 'apk':
    apktesting(options.inputFile)
  elif MODE == 'xml':
    manifesttesting(options.inputFile)
  elif MODE == 'dir':
    if not options.inputFile.endswith('/'):
      dirtesting(options.inputFile+'/')
    else:
      dirtesting(options.inputFile)
  elif MODE == 'test':
    testtesting()
  else:
    parser.error("What mode are you looking for? See -h for usage.")
    sys.exit()

  report = Report.Report()
  report.console()##update this with more options


def manifesttesting(file):
  man = Manifest.Manifest()
  logging.debug("Starting manifest audit")
  man.manifestAudit(file)  

def dirtesting(dir):
  logging.debug("Starting directory audit")
  dirlist = os.listdir(dir)
  for file in dirlist:
    ext = file[-3:]
    if ext == 'apk':
      apk = Apk.Apk()
      absfile = dir + file
      logging.debug("Found apk: %s" % absfile)
      apktesting(absfile)
      #time.sleep(1)
    elif ext == 'xml':
      absfile = dir + file
      logging.debug("Found manifest: %s" % absfile)
      #TODO check to see if it's an axml file
      manifesttesting(absfile)
      #time.sleep(0.5)
    else:
      logging.debug("Not a file of interest: %s " % file)
  
def testtesting():
  tool = Tools.Tools()
  adb = tool.istoolinpath('adb')
  print adb
  #check to see if axml2print is installed
  axmlppath = tool.istoolinpath('AXMLPrinter2.jar')
  print axmlppath

def apktesting(file):
  apk = Apk.Apk()
  logging.debug("Starting apk audit")
  tool = Tools.Tools()
  adb = tool.istoolinpath("adb")
  axmlppath = tool.istoolinpath("AXMLPrinter2.jar")
  logging.debug("input file is %s" % file)
  manifest = apk.manifestextractor(file)
  logging.debug("manifest is %s" % manifest)

  man = Manifest.Manifest()
  mfxml = man.binaryconverter(axmlppath,manifest) 
  #time.sleep(1)##workaround so the processes die
  man.manifestAudit(mfxml)

def devicetesting(adboptions, sysFilter=False, tmppath='/tmp/AT'):
##performs functions related to device testing: Downloading, extracting, processing
  manifests = []
  apklist = []
  dllist = []

  tool = Tools.Tools()
  axmlppath = tool.istoolinpath('AXMLPrinter2.jar')
  adbpath = tool.istoolinpath('adb')

  dev = Device.Device()

  logging.debug("Looking for installed apps")
  apklist = dev.apkfinder(adbpath, adboptions, sysFilter)        ##/system/app/appname

  logging.debug("Beginning download...")
  dllist = dev.downloader(adbpath, apklist,adboptions, tmppath) ##(/tmp/AT/appname.apk)

  apk = Apk.Apk()
  logging.debug("Extracting manifest files")
  for apkfile in dllist:
    logging.debug("dllist apk: %s" % apk)
    manifests.append(apk.manifestextractor(apkfile)) ##/tmp/AT/manifest1.bin

  mfxmls = []

  man = Manifest.Manifest()

  logging.debug("Starting binary conversion")
  for mfb in manifests:
    if mfb: ##FIX THIS. There shouldn't be blanks in the list
      mfxmls.append(man.binaryconverter(axmlppath,mfb))    ##/tmp/at/manifest1.xml
  
  logging.debug("Unloading processes...")
  #time.sleep(15)##WORKAROUND: Needs at least 5 seconds otherwise xml expat error occus

  logging.debug("Starting manifest audit")
  for mf in mfxmls:
    man.manifestAudit(mf, adboptions.split()[1])                       

  dev.ifeelsodirty()  ##TODO fix this. it doesn't work right now


if __name__ == "__main__":
  main()
