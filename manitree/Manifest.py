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

import AxmlParserPY.axmlprinter as axmlprinter

def setupSqlite(database):
  global connection
  global cursor

  try:
    connection = sqlite3.connect(database)
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
  try:
    cursor.execute('INSERT INTO report values (NULL, ?, ?, ?, ?, ?, ?, ?, ?)', \
          (timestamp, device, package, vulnVal, vulnData, title, description, risk))
    connection.commit()
  except sqlite3.Error, e:
    print("Sqlite error: ", e.args[0])
    #logging.debug("Values in error: %s %s %s %s %s %s %s" % (device, package, vulnVal, vulnData, title, description, risk))
    
    pass


class Manifest:
	def binaryconverter(self, mfb):
	  bincheck = False
	  ## check to see if it's in AXML or standard xml format:
	  xmlbuff = open(mfb, 'rb')
	  xmlcheck = xmlbuff
	  try:
	    chunk = xmlcheck.read(1024)
	    if '\0' in chunk:
	      bincheck = True
	    xmlcheck.close()
	  finally:
	    logging.debug("Binary file check complete")

	  if not bincheck:
	    logging.debug("XML file is not binary. No need to convert")
	    mfxmlpath = mfb
	  else:
	    logging.debug("Binary check complete") 
	    ## convert from the binary xml format to a parseable one
	    try:
	      parse = axmlprinter.AXMLPrinter(open(mfb, 'rb').read())
	      prettyxml = xml.dom.minidom.parseString(parse.getBuff()).toxml()

	      #FIXME no need to use files any more. Send buffer directly in for processing
              logging.debug("mfb  is: %s" % mfb)
	      mfxmlpath = "%s.xml" % mfb[:-4]
	      ofile = open(mfxmlpath, 'w')
	      if os.path.isfile(mfb):
                ofile.write(prettyxml)

	        if os.path.isfile(mfxmlpath):
	          logging.debug("successfully converted %s " % mfxmlpath)
              
	      ofile.close()
	    except:
	      logging.error("Unable to convert AXML binary in %s" % mfb)
	      
          return mfxmlpath


    def manifestAudit(self, mf, device='None', database="report.db"):
      mf = self.binaryconverter(mf)
      setupSqlite(database)
      logging.debug("parsing manifest: %s ..." % mf)

      timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

      try:
          #if 1==1:##DEBUG
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
        usespermissions = mfxml.getElementsByTagName("uses-permission")
        granturipermissions = mfxml.getElementsByTagName("grant-uri-permission")
        permissions = mfxml.getElementsByTagName("permission")

      ##MANIFEST
        logging.debug("Looking at manifest section")
        for node in manifest:
          package = node.getAttribute("package")

      ##RECEIVER
        logging.debug("Looking at receiver section")
        ##process receiver example
          #<receiver android:name=".binarySMS.AdvertBinarySMSReceiver">
              #<intent-filter android:priority="2147483540">
              #  <action android:name="android.intent.action.DATA_SMS_RECEIVED" />
              #  <data android:scheme="sms" android:host="localhost" android:port="3777" />

      ##SERVICES  
        logging.debug("Looking at services section")
            ##search for services without permissions set
            #if a service is exporeted and has no permission nor an intent filter, flag it
             
        for service in services:
            if service.getAttribute("android:exported") == 'true':
                ifilter = False
                sp = False
                logging.debug("Found exported service")
                for node in service.childNodes:
                    if node.nodeName == 'intent-filter':
                        #intent filter exists
                        ifilter = True
                  
                    if service.getAttribute("android:permission"):
                        #service permission exists
                        sp = True
              
                    if not (ifilter or sp):
                        servicename = service.getAttribute("android:name")
                        insertIntoReport(timestamp, device, package, servicename, service.toxml(),
                                        'Service Not Properly Protected',
                                        'A service was found to be shared with other apps on the ' +
                                        'device without an intent filter or a permission requirement ' +
                                        'therefore leaving it accessible to any other application on ' +
                                        'the device.', 'medium')

      ##PROVIDERS
        logging.debug("Looking at providers")
            ##look for permissions being set

          
      ##GRANT-URI-PERMISSIONS    
        logging.debug("Looking at grant-uri-permissions")


        title = 'Improper Content Provider Permissions' 
        desc = ('A content provider permission was set to allows access from any other app on the ' +
                'device. Content providers may contain sensitive information about an app and therefore should not be shared.')

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
                desc = ("A secret code was found in the manifest. These codes, when entered into the dialer " + 
                        "grant access to hidden content that may contain sensitive information.")
                insertIntoReport(timestamp, device, package, xmlhost, data.toxml(), \
                                title, desc,'medium')
            elif data.getAttribute("android:port"):
                dataport = data.getAttribute("android:port")
                title = "Data SMS Receiver Set"
                desc = "A binary SMS recevier is configured to listen on a port. Binary SMS messages sent to a device are processed by the application in whichever way the developer choses. The data in this SMS should be properly validated by the application. Furthermore, the application should assume that the SMS being received is from an untrusted source."
                insertIntoReport(timestamp, device, package, dataport, data.toxml(), \
                                title, desc, 'high')

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
                                    'By setting an intent priority higher than another intent, ' +
                                    'the app effectively overrides other requests. This is commonly ' +
                                    'associated with malware.', 'medium')

        #USES-PERMISSION
        logging.debug("Looking at uses-permissions")
        for perm in usespermissions:
            value = perm.getAttribute("android:name")
            insertIntoReport(timestamp, device, package, value, perm.toxml(), "INFO Requested permission",
                            'The application has requested a permission.', 'info')

        ##ACTIONS
        logging.debug("Looking at actions")

        for action in actions:
            if action.getAttribute("android:priority").isdigit(): ##action priorities... see above
                value = action.getAttribute("android:priority")
                if int(value) > 100: 
                    logging.debug("Found priority in action")
                    insertIntoReport(timestamp, device, package, value, action.toxml(), \
                                    'High Action Priority Set', \
                                    'By setting an action priority higher than another action, the ' +
                                    'app effectively overrides other requests. This is commonly '
                                    'associated with malware.', 'medium')

            ##PERMISSIONS
            logging.debug("Looking at permission")

            #NOTE: list of built in permission groups: ACCOUNTS, COST_MONEY, DEVELOPMENT_TOOLS
            #  HARDWARE_CONTROLS, LOCATION, MESSAGES, NETWORK, PERSONAL_INFO, PHONE_CALLS, STORAGE, SYSTEM_TOOLS 


            for permission in permissions:
                pl = permission.getAttribute("android:protectionLevel")
                pn = permission.getAttribute("android:name")
                if pl == "signatureOrSystem":
                    value = pl
                    logging.debug("SignatureorSystem protection level set in custom permission")
                    insertIntoReport(timestamp, device, package, value, permission.toxml(), \
                                    'Custom Permision Uses signatureOrSystem Protection Level',
                                    'A custom permission named %s controls whether or not other ' +
                                    'applications can access the affected apps features. The use ' +
                                    'of signatureOrSystem requires that the requesting app be ' +
                                    'signed with the same signature as the one used for the system ' +
                                    'image. This value should be used only in special cases.' % pn, 'low')
                
                elif pl == "signature":
                    value = pl
                    logging.debug("Signature protection level set in custom permission")
                    insertIntoReport(timestamp, device, package, value, permission.toxml(), 
                                    'Custom Permission Uses signature Protection Level',
                                    'A custom permission named %s controls whether or not other ' +
                                    'applications can access the affected app features. The use of ' +
                                    'signature requires the requesting app to be signed the with same ' +
                                    'signature as the application that declared the permission.'% pn, 'low')
                
                elif pl == "dangerous":
                    value = pl
                    logging.debug("Dangerious protection level set in custom permission")
                    insertIntoReport(timestamp, device, package, value, permission.toxml(),
                                    'Custom Permission Uses danger Protection Level',
                                    'A custom permission named %s controls whether or not other ' +
                                    'applications can access the affected apps features. The use of ' +
                                    'the dangerous label places no restrictions on which apps can ' +
                                    'access the application declaring the permission but the user will ' +
                                    'be warned that the dangerous permission is required during installation.' %
                                    pn, 'medium')
                
                elif pl == "normal":
                    value = pl
                    logging.debug("Normal protection level set in custom permission")
                    insertIntoReport(timestamp, device, package, value, permission.toxml(),
                                    'Custom Permission Uses normal Protection Level', 
                                    'A custom permission named %s controls whether or not other applications ' +
                                    'can access the affected apps features. The use of the normal label places ' +
                                    'no restrictions on which apps can access the application declaring the ' +
                                    'permission. It is important that permission does not grant sensitive ' +
                                    'access to the application.'% pn, 'medium')
               
       
        logging.debug("Done processing %s " % mf)
        connection.commit()

      except IOError:
        logging.debug("couldn't find manifest file %s" % mf)
        pass
      except expat.ExpatError:
        logging.debug("Invalid XML file found. moving on")
        #print("XML Error code: %s" % expat.ExpatError.args)
        pass
