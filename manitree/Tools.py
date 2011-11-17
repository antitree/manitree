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



import subprocess, logging, os, sys

class Tools:
	def istoolinpath(self, bin):
	##Search for the tool in the path otherwise look in the local folder
	  logging.debug("Looking for %s " % bin)
	  p = subprocess.Popen(('which', '%s' % bin), stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
	  path = p.stdout.read().strip()
	  if not path == '':
	    logging.debug('Found %s in the environment path' % path)
	    return path
	  else:
	    if os.path.exists('./%s' % bin):
	      path = './%s' % bin
	      logging.debug("Found %s in the local path: %s" % (bin,path))
	      return path
	    else:
	      print("Could not find %s in path. Make sure it's installed or in the local path" % bin)
	      sys.exit()
