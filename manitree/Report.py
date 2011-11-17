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

def connectSqlite():
  global connection
  global cursor

  try:
    connection = sqlite3.connect("report.db")
    cursor = connection.cursor()
  except sqlite3.Error, e:
    print("Sqlite error: ", e.args[0])
    sys.exit()


class Report:
  def console(self, mode="text",device=False,package=False,risk=False):
    connectSqlite()
    logging.debug("Starting report generation")
    if device:
      reportstatement = "SELECT * from report where device='"+device+"'"
    else:
      reportstatement = "SELECT * from report"

    logging.debug("Sql statement: %s" % reportstatement) 
    cursor.execute(reportstatement)

    #god. This could be so much better...
    LOW = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDCOLOR = '\033[0m'

    print(LOW+'Manitor: Android Manifest Auditing tool')
    print('Author: AntiTree 10/08/2011')
    print('Intrepidus Group')
    print("*" * 50+ENDCOLOR)
    for row in cursor.fetchall():
      #logging.debug(row)
      if(row[8]) == 'high':
        print(FAIL+row[8].upper()+ENDCOLOR).rjust(1),
      elif(row[8]) == 'medium':
        print(WARNING+row[8].upper()+ENDCOLOR).rjust(1),
      elif(row[8]) == 'low':
        print(LOW+row[8].upper()+ENDCOLOR).rjust(1),
      print(row[6]).rjust(2),
      print("value:"+row[4]).rjust(3)
      print(row[7].strip())
    
    
