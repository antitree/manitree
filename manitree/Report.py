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


import logging, sqlite3, time, os

def connectSqlite(database):
  global connection
  global cursor

  try:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
  except sqlite3.Error, e:
    print("Sqlite error: ", e.args[0])
    sys.exit()

def filterResults(name, value, data):
  filtered = []
  for row in data:
    if row[name] == value:
      filtered.append(row)
  return filtered



class Report:
  def console(self, data): 

    convert = {'high' : 0, 'medium' : 1, 'low' : 2, 'info' : 3}
    #data.sort(lambda x, y: cmp(convert[x['risk']],convert[y['risk']]))

    LOW = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDCOLOR = '\033[0m'
 
    ##TODO: you don't need the numbers anymore 
    print(LOW+'Manitree: Android Manifest Auditing tool')
    print('Author: AntiTree 10/08/2011')
    print('Intrepidus Group')
    print("*" * 50+ENDCOLOR)
    package = ''
    for row in data:
      if not package == row[3]:
        package = row[3]
        print('\nApp: '+package)
      if(row[8]) == 'high':
        print(FAIL+row[8].upper()).rjust(1),
      elif(row[8]) == 'medium':
        print(WARNING+row[8].upper()).rjust(1),
      elif(row[8]) == 'low':
        print(LOW+row[8].upper()).rjust(1),
      print(row[6]).rjust(2)
      print("\tvalue:"+row[4]+ENDCOLOR).rjust(3)
  
  def html(self, data, outputFile=False):
    print("DEVELOPMENT: html mode selected but I haven't made that")

  def text(self, data, outputFile):
    convert = {'high' : 0, 'medium' : 1, 'low' : 2}
    data.sort(lambda x, y: cmp(convert[x['risk']],convert[y['risk']]))
    deviceSet = set([])
    packageSet = set([])
    for row in data:
      deviceSet.add(row["device"])
      packageSet.add(row["package"])
    
    outputtxt = []
    ##TESTING SUMMARY
    outputtxt.append('Manitor: Android Manifest Auditing Tool')
    outputtxt.append("*" * 50)
    outputtxt.append('Devices tested:')
    for dev in deviceSet:
      if not dev == "None": outputtxt.append(dev)
    outputtxt.append("*" * 50)
    outputtxt.append('Packages tested:')
    outputtxt.extend(packageSet)
    outputtxt.append("*" * 50)
    ##DETAILS
    for dev in deviceSet:
      outputtxt.append("Device Serial: %s" % dev)
      count = 0
      for finding in data:
        if finding["device"] == dev:
          outputtxt.append("%s: %s in %s" % \
	    (finding["risk"].upper(), finding["title"], finding["package"]))
          outputtxt.append("Value: %s" % finding["vulnvalue"])
          #outputtxt.append(finding["description"]+"\n")
          count+=1
      outputtxt.append("Total items found on %s: %i" % (dev, count))
      outputtxt.append("*" * 50)

    f = open(outputFile, 'w')
    for line in outputtxt: 
      f.write("%s\n" % line)
    
   
  def devReport(self, device, package=False, risk=False, reportDate=False, database="report.db"):
    logging.debug("Starting device search for %s" % device)
    #sqlite query for a device
    connectSqlite(database)
    reportstatement = "SELECT * FROM report WHERE device='"+device+"'"
    logging.debug("Sql statement: %s" % reportstatement)
    cursor.execute(reportstatement)
    data = cursor.fetchall()
    
    if package: data = filterResults("package", package, data)
    if risk: data = filterResults("risk", risk, data)
    if reportDate: data = filterResults("time", reportDate, data)
    
    return data
  
  def packageReport(self, package=False, device=False, risk=False, reportDate=False, database="report.db"):
    connectSqlite(database)
    if package:
      reportstatement = "SELECT * FROM  report WHERE package='"+package+"'"
    else:
      reportstatement = "SELECT * FROM report WHERE package != ''"
    cursor.execute(reportstatement)
    data = cursor.fetchall()
   
    if device: data = filterResults("device", device, data)
    if risk: data = filterResults("risk", risk, data)
    if reportDate: data = filterResults("time", reportDate, data)

    return data
  
  def riskReport(self, risk, device=False, package=False, reportDate=False, database="report.db"):
    connectSqlite(database)
    reportstatement = "SELECT * FROM  report WHERE risk='"+risk+"'"  
    cursor.execute(reportstatement)
    data = cursor.fetchall()
   
    if device: data = filterResults("device", device, data)
    if package: data = filterResults("package", package, data)
    if reportDate: data = filterResults("time", reportDate, data)

    return data

  def allReport(self, device=False, package=False, risk=False, reportDate=False, database="report.db"):
    connectSqlite(database)
    reportstatement = "SELECT * FROM report group by package,risk"
    cursor.execute(reportstatement)
    data = cursor.fetchall()

    if device: data = filterResults("device", device, data)
    if package: data = filterResults("package", package, data)
    if risk: data = filterResults("risk", risk, data)
    if reportDate: data = filterResults("time", reportDate, data)

    return data

 
