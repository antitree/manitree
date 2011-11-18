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



import subprocess, logging, sqlite3, time, os
import xml.parsers.expat as expat
import xml.dom.minidom

def setupSqlite():
  global connection
  global cursor

  try:
    connection = sqlite3.connect("report.db")
    cursor = connection.cursor()
    ## id, timestamp, device, vulnerable value, vulndata, summary, description, risk value
    cursor.execute('CREATE TABLE IF NOT EXISTS report \
      (id INTEGER PRIMARY KEY, time DATETIME, \
      device VARCHAR, package VARCHAR, vulnvalue VARCHAR, vulndata VARCHAR, title VARCHAR, \
      description VARCHAR, risk VARCHAR)')
  except sqlite3.Error, e:
    print("Sqlite error: ", e.args[0])
    sys.exit()

def insertIntoReport(timestamp, device, package, vulnVal, vulnData, title, description, risk):
  reportstatement = "INSERT INTO report values(NULL, '"+timestamp+"','"+device+ \
          "', '"+package+"', '"+vulnVal+"','"+vulnData+"','"+title+"','"+description+"', '"+risk+"')"
  cursor.execute(reportstatement)
  connection.commit()


class Manifest:
	def binaryconverter(self, axmlppath, mfb):
	  ## convert from the binary xml format to a parseable one
          logging.debug("mfb  is: %s" % mfb)
	  mfxmlpath = "%s.xml" % mfb[:-4]
	  ofile = open(mfxmlpath, 'w')
	  if os.path.isfile(mfb):
	    ##use AXMLPrinter2.jar to convert
	    p = subprocess.Popen(['java', '-jar', str(axmlppath), str(mfb)],
	      stdin=subprocess.PIPE, stdout=ofile, close_fds=True)
            logging.debug("process status: "+str(p.poll()))

	    if os.path.isfile(mfxmlpath):
	      logging.debug("successfully converted %s " % mfxmlpath)
              
            time.sleep(.5)##workaround due to xml processing speeds
	  ofile.close()
          return mfxmlpath


	def manifestAudit(self, mf, device='None'):
	  setupSqlite()
	  logging.debug("parsing manifest: %s ..." % mf)

	  timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

	  try:
	    mfxml = xml.dom.minidom.parse(mf)

	    node = mfxml.documentElement
	    manifest = mfxml.getElementsByTagName("manifest")
	    services = mfxml.getElementsByTagName("service")
	    providers = mfxml.getElementsByTagName("provider")
	    receivers = mfxml.getElementsByTagName("receiver")
	    applications = mfxml.getElementsByTagName("application")
	    datas = mfxml.getElementsByTagName("data")
	    intents = mfxml.getElementsByTagName("intent-filter")
	    actions = mfxml.getElementsByTagName("action")
	    granturipermissions = mfxml.getElementsByTagName("grant-uri-permission")

	  ##MANIFEST
	    logging.debug("Looking at manifest section")
	    for node in manifest:
	      package = node.getAttribute("package")

	  ##SERVICES  
	    logging.debug("Looking at services section")
	    #for service in services:
	      #search for illegally exported services
            #Disabled for now
	    #     if service.getAttribute("android:exported"):
	    #     	insertIntoReport(timestamp, device, package, 'Null', service.toxml(),  \
	    #	  'Exported Service',  \
	    #	  'A service is being exported. Make sure that sensitive information is \
	    #	  not accessible and that proper restrictions are used.', \
	    #	  'info')

	  ##PROVIDERS
	    logging.debug("Looking at providers")

	    #for provider in providers:
	      #print(provider.attributes["android:name"].value)
	      
	  ##GRANT-URI-PERMISSIONS	
	    logging.debug("Looking at grant-uri-permissions")


	    title = 'Improper Content Provider Permissions' 
            desc = 'A content provider permission was set to allows access from any other app on the device. Content providers may contain sensitive information about an app and therefore should not be shared.'

	    for granturi in granturipermissions:
	      if granturi.getAttribute("android:pathPrefix") == '/':
                insertIntoReport(timestamp, device, package, 'pathPrefix=/', granturi.toxml(), title, desc, 'high')
	      elif granturi.getAttribute("android:path") == '/':
		insertIntoReport(timestamp, device, package, 'path=/', granturi.toxml(), title, desc, 'high')
              elif granturi.getAttribute("android:pathPattern") == '*':
		insertIntoReport(timestamp, device, package, 'path=/', granturi.toxml(), title, desc, 'high')

	  ##APPLICATIONS
	    logging.debug("Looking at applications")
            for application in applications:
              if application.getAttribute("android:debuggable") == "true":
                insertIntoReport(timestamp, device, package, 'debuggable', application.toxml(), \
			'Debug Enabled For App', \
			'Debugging was enabled on the app which makes it easier for reverse engineers to hook a debugger to it. This allows dumping a stack trace and accessing debugging helper classes.', 'low') 

	  ##DATA
	    logging.debug("Looking at data")

	    for data in datas:
	      if data.getAttribute("android:scheme") == "android_secret_code":
		xmlhost = data.getAttribute("android:host")
                title = "Hidden Dialer Code Found"
                desc = "A secret code was found in the manifest. These codes, when entered into the dialeri grant access to hidden content that may contain sensitive information."
		insertIntoReport(timestamp, device, package, xmlhost, data.toxml(), \
		    title, desc,'medium') 

	  ##HOST

	  ##INTENTS
	    logging.debug("Looking at intents")

	    for intent in intents:
	      if intent.getAttribute("android:priority").isdigit(): 
                value = intent.getAttribute("android:priority")
                if int(value) > 100:
                  logging.debug("Found priority in intent")
		  insertIntoReport(timestamp, device, package, value, intent.toxml(), \
		    'High Intent Priority Set', \
		      'By setting an intent priority higher than another intent, the app effectively overrides other requests. This is commonly associated with malware.', 'medium')

	  ##ACTIONS
	    logging.debug("Looking at actions")

	    for action in actions:
	      if intent.getAttribute("android:priority").isdigit(): ##action priorities... see above
                value = intent.getAttribute("android:priority")
                if int(value) > 100: 
                  logging.debug("Found priority in action")
		  insertIntoReport(timestamp, device, package, value, action.toxml(), \
		    'High Action Priority Set', \
		    'By setting an action priority higher than another action, the app effectively overrides other requests. This is commonly associated with malware.', 'medium')
	   
	    logging.debug("Done processing %s " % mf)
	    connection.commit()

	  except IOError:
	      print("couldn't find manifest file %s" % mf)
	      pass
	  except expat.ExpatError:
	      print("Invalid XML file found. This sometimes happens if the hard drive lags")
	      #print("XML Error code: %s" % expat.ExpatError.args)
	      time.sleep(3)
	      pass
