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


import subprocess, logging, os, sys, shutil

def adbExecPrep(adbpath, adboptions, command):
  execute = [adbpath]
  execute.extend(adboptions.split())
  execute.extend(command)
  return execute

def setuptmpfolder(tmppath):
   if not os.path.exists(tmppath):
     os.makedirs(tmppath)


class Device:
	def apkfinder(self, adbpath, adboptions, sysFilter=False):
	#download all the apks from a device or emulator
	    commands = ['shell', 'pm', 'list', 'packages', '-f']
	    execute = adbExecPrep(adbpath, adboptions, commands)
	    p = subprocess.Popen(execute, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
	    p.wait
            logging.debug("process status: "+str(p.poll()))

	    apklist = []
	    for line in p.stdout.readlines():
	       if "error" in line:
		 print("error %s" % line)
	       a = (line.replace(':','='))
	       b = a.split('=')
	       if sysFilter and b[1][:7] == '/system':
		 logging.debug("Skipping system app: %s" % b[1])
	       else:
		 apklist.append(b[1])
		 logging.debug("Apk found: %s" % b[1])
	    apklist.sort()
	    if apklist:
	      return apklist
	    else:
	      sys.exit()

        def androidVer(self, adbpath, adboptions):
          #check which version of Android is running on the device
          #adb shell getprop ro.build.version.release
          commands = ['shell','getprop','ro.build.version.release']
          execute = adbExecPrep(adbpath, adboptions, commands)
          logging.debug("ADB options about to be executed: %s" % execute)
          p = subprocess.Popen(execute, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
          p.wait
          
          ver = p.stdout.readlines()
          logging.debug("Android Version Found: %s" % ver)
          return ver


        def adbcheck(self, adbpath, adboptions):
          #check to see how many devices are plugged in
          #if physical then not an emulatori
          ##TODO FIX so that it processes correctly
          commands = ['devices']
          execute = adbExecPrep(adbpath, adboptions, commands)
          p = subprocess.Popen(execute, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
          p.wait
	  logging.debug("process status: "+str(p.poll()))

          dl = p.stdout.readlines()
          devlist = []
          dl.remove('\n')
          for line in dl:
            dev = line.split()
            if dev[1].strip() == "device":
              logging.debug("Found device: %s", dev[0])
              if '-d' in adboptions and dev[0][:8] == 'emulator':
                logging.debug('skipping emulator device')
              elif '-e' in adboptions and not dev[0][:8] == 'emulator':
                logging.debug('skipping physical device')
              else:
                devlist.append(dev[0])
            elif dev[1] == "offline":
              print("Device %s was found but not yet online" % dev[0])

          selecteddevs = []
          if len(devlist) < 1:
            print("No devices found. Make sure the device is plugged in and in a ready state")
            sys.exit()
          else:
           if len(devlist) == 1:
            selecteddevs = devlist
           else:
            i = 1
            for line in devlist:
              print("%s: %s" % (i,line))
              i += 1
            while True:
              selected = raw_input("\nMore than one device found.\nSelect which device to use or A to test all the devices: ")
              if selected == 'A':
                logging.debug("Selected to test all devices")
                selecteddevs = devlist
                break
              elif selected.isdigit():
                if int(selected) > 0 and int(selected) <= (len(devlist)):
                  logging.debug("Device %s selected" % devlist[int(selected)-1])
                  selecteddevs.append(devlist[int(selected)-1])
                  break
              else:
                logging.debug("selection incorrect: %s" % selected)
          
          return selecteddevs




	def downloader(self, adbpath, apklist, adboptions, tmppath='/tmp/AT/'):
	    apkdl = []
	    i = 0
	    logging.debug("Number of packages to download: %s" % len(apklist))
	    setuptmpfolder(tmppath)
	    #sessioncontinue(apklist) ##finish this later
	    for apk in apklist:
	      apklocalpath = "%s%s" % (tmppath, apk.replace('/','_'))
	      commands = ['pull', apk, apklocalpath]
	      execute = adbExecPrep(adbpath, adboptions, commands)
	      p = subprocess.Popen(execute, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
              p.wait
	      logging.debug("process status: "+str(p.poll()))

	      dl = p.stdout.read().strip()
	      print(dl)
	      if "error" in dl:
		print('error')
		return
	      logging.debug("Download complete: %s" % apklocalpath)
	      apkdl.append(apklocalpath)
	      i += 1
	      print("[%i/%s]\n" % (i, len(apklist)))
	    return apkdl


        def quickdownloader(self, adbpath, apklist, adboptions, tmppath='/tmp/AT/'):
            apkdl = []
            i = 0
            logging.debug("Number of packages to download: %s" % len(apklist))
            setuptmpfolder(tmppath)

            #send binaries
            commands = ['push', 'bin/gnutar', '/tmp/']
            execute = adbExecPrep(adbpath, adboptions, commands)
            p = subprocess.Popen(execute, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
            p.wait
	    logging.debug("process status: "+str(p.poll()))

            #make executable
            logging.debug("Changing permissions")
	    commands = ['shell', 'chmod', '777', '/tmp/gnutar']
            execute = adbExecPrep(adbpath, adboptions, commands)
            p = subprocess.Popen(execute, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
            p.wait
	    logging.debug("process status: "+str(p.poll()))

            commands = ['shell', '/tmp/gnutar', '-czf', '/tmp/packages.tar.gz'] 
            commands += apklist
            execute = adbExecPrep(adbpath, adboptions, commands)
            p = subprocess.Popen(execute, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
            p.wait
	    logging.debug("process status: "+str(p.poll()))

 
            #sessioncontinue(apklist) ##finish this later
            for apk in apklist:
              apklocalpath = "%s%s" % (tmppath, apk.replace('/','_'))
              commands = ['pull', apk, apklocalpath]
              execute = adbExecPrep(adbpath, adboptions, commands)
              p = subprocess.Popen(execute, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

              dl = p.stdout.read().strip()
              print(dl)
              if "error" in dl:
                print('error')
                return
              logging.debug("Download complete: %s" % apklocalpath)
              apkdl.append(apklocalpath)
              i += 1
              print("[%i/%s]\n" % (i, len(apklist)))
            return apkdl


	def ifeelsodirty(tmppath):
  	  shutil.rmtree(tmppath)
          shutil.rmtree(report.db)


