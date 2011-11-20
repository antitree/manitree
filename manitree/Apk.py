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


import subprocess, logging, os

class Apk:
	def manifestextractor(self, apk):
	  #extract just the manifest and put them into a nice location

	  ##FIX: fucking python zip does a verification on whether or not
	  ### the comment lenth in the header matches the comments actual
	  ### length in the zip file. Waiting for patch:
	  # http://bugs.python.org/issue1757072

	  #Until then, work around with subprocess  

	  apkpath = "%s" % apk
	  logging.debug("manifestextractor apkpath is: %s" % apkpath)
	  apkxmlpath = "%s.bin" % apkpath
	  try:
	    ofile = open(apkxmlpath, 'w')
	    if os.path.isfile(apkpath):
	      logging.debug("APK file found: %s" % apkpath)
	      ## unzip with -p for stdout so we can rename it
	      p = subprocess.Popen(['unzip', '-p', '%s' % apkpath, 'AndroidManifest.xml'],
		stdin=subprocess.PIPE, stdout=ofile, close_fds=True)
	      logging.debug("Done extracting manifest from %s" % apk)
	      return apkxmlpath
	    else:
	      logging.error("APK %s was not found. Are you sure it wasn't deleted?" % apkxmlpath)
	      return
	  except Exception, e:
	    logging.error("Problem extracting %s %s" % (apk, e))
	    return
	    pass


