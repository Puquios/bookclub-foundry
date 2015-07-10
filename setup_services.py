#!/usr/bin/python

#***************************************************************************
# Copyright 2015 IBM
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#***************************************************************************

import json
import logging
import logging.handlers
import os
import os.path
import sys
import time
import argparse

from subprocess import call, Popen, PIPE

GLOBALIZATION_SERVICE='IBM Globalization'
GLOBALIZATION_SERVICE_PLAN='Experimental'
GLOBALIZATION_SERVICE_NAME='IBM Globalization'

MACHINE_TRANSLATION_SERVICE='language_translation'
MACHINE_TRANSLATION_PLAN='standard'
MACHINE_TRANSLATION_NAME='mt-watson3'

TWITTER_SERVICE='twitterinsights'
TWITTER_PLAN='Free'
TWITTER_NAME='IBM Insights for Twitter'

DEFAULT_BRIDGEAPP_NAME='pipeline_bridge_app'

Logger=None

# setup logmet logging connection if it's available
def setupLogging ():
    logger = logging.getLogger('pipeline')
    if os.environ.get('DEBUG'):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # in any case, dump logging to the screen
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    if os.environ.get('DEBUG'):
        handler.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

# find the given service in our space, get its service name, or None
# if it's not there yet
def findServiceNameInSpace (service):
    command = "cf services"
    proc = Popen([command], shell=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate();

    if proc.returncode != 0:
        Logger.info("Unable to lookup services, error was: " + out)
        return None

    foundHeader = False
    serviceStart = -1
    serviceEnd = -1
    serviceName = None
    for line in out.splitlines():
        if (foundHeader == False) and (line.startswith("name")):
            # this is the header bar, find out the spacing to parse later
            # header is of the format:
            #name          service      plan   bound apps    last operation
            # and the spacing is maintained for following lines
            serviceStart = line.find("service")
            serviceEnd = line.find("plan")-1
            foundHeader = True
        elif foundHeader:
            # have found the headers, looking for our service
            if service in line:
                # maybe found it, double check by making
                # sure the service is in the right place,
                # assuming we can check it
                if (serviceStart > 0) and (serviceEnd > 0):
                    if service in line[serviceStart:serviceEnd]:
                        # this is the correct line - find the bound app(s)
                        # if there are any
                        serviceName = line[:serviceStart]
                        serviceName = serviceName.strip()
        else:
            continue

    return serviceName

# find a service in our space, and if it's there, get the dashboard
# url for user info on it
def findServiceDashboard (service):

    serviceName = findServiceNameInSpace(service)
    if serviceName == None:
        return None

    command = "cf service \"" + serviceName + "\""
    proc = Popen([command], shell=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate();

    if proc.returncode != 0:
        return None

    serviceURL = None
    for line in out.splitlines():
        if line.startswith("Dashboard: "):
            serviceURL = line[11:]
        else:
            continue

    return serviceURL

# search cf, find an app in our space bound to the given service, and return
# the app name if found, or None if not
def findBoundAppForService (service):
    proc = Popen(["cf services"], shell=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate();

    if proc.returncode != 0:
        return None

    foundHeader = False
    serviceStart = -1
    serviceEnd = -1
    boundStart = -1
    boundEnd = -1
    boundApp = None
    for line in out.splitlines():
        if (foundHeader == False) and (line.startswith("name")):
            # this is the header bar, find out the spacing to parse later
            # header is of the format:
            #name          service      plan   bound apps    last operation
            # and the spacing is maintained for following lines
            serviceStart = line.find("service")
            serviceEnd = line.find("plan")-1
            boundStart = line.find("bound apps")
            boundEnd = line.find("last operation")
            foundHeader = True
        elif foundHeader:
            # have found the headers, looking for our service
            if service in line:
                # maybe found it, double check by making
                # sure the service is in the right place,
                # assuming we can check it
                if (serviceStart > 0) and (serviceEnd > 0) and (boundStart > 0) and (boundEnd > 0):
                    if service in line[serviceStart:serviceEnd]:
                        # this is the correct line - find the bound app(s)
                        # if there are any
                        boundApp = line[boundStart:boundEnd]
        else:
            continue

    # if we found a binding, make sure we only care about the first one
    if boundApp != None:
        if boundApp.find(",") >=0 :
            boundApp = boundApp[:boundApp.find(",")]
        boundApp = boundApp.strip()
        if boundApp=="":
            boundApp = None

    if os.environ.get('DEBUG'):
        if boundApp == None:
            Logger.debug("No existing apps found bound to service \"" + service + "\"")
        else:
            Logger.debug("Found existing service \"" + boundApp + "\" bound to service \"" + service + "\"")

    return boundApp

# look for our default bridge app.  if it's not there, create it
def checkAndCreateBridgeApp (appName=DEFAULT_BRIDGEAPP_NAME):
    # first look to see if the bridge app already exists
    command = "cf apps"
    Logger.debug("Executing command \"" + command + "\"")
    proc = Popen([command], shell=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate();

    if os.environ.get('DEBUG'):
        Logger.debug("command \"" + command + "\" returned with rc=" + str(proc.returncode))
        Logger.debug("\tstdout was " + out)
        Logger.debug("\tstderr was " + err)

    if proc.returncode != 0:
        return None

    for line in out.splitlines():
        if line.startswith(appName + " "):
            # found it!
            return True

    # our bridge app isn't around, create it
    Logger.info("Bridge app does not exist, attempting to create it")
    command = "cf push " + appName + " -i 1 -d mybluemix.net -k 1M -m 64M --no-hostname --no-manifest --no-route --no-start"
    Logger.debug("Executing command \"" + command + "\"")
    proc = Popen([command], shell=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate();

    if os.environ.get('DEBUG'):
        Logger.debug("command \"" + command + "\" returned with rc=" + str(proc.returncode))
        Logger.debug("\tstdout was " + out)
        Logger.debug("\tstderr was " + err)

    if proc.returncode != 0:
        Logger.info("Unable to create bridge app, error was: " + out)
        return False

    return True

def checkOrAddService (service, plan, serviceName):
    # look to see if we have the service in our space
    existingService = findServiceNameInSpace(service)
    if existingService == None:
        serviceName=serviceName
    print "service " + service 
    print "plan " + plan 
    print "serviceName " + serviceName 
    Logger.info("Creating service \"" + service + "\"  \"" + plan + "\"" + serviceName )

    # if we don't have the service name, means the tile isn't created in our space, so go
    # load it into our space if possible
    if existingService == None:
        Logger.info("Service \"" + service + "\" is not loaded in this space, attempting to load it")
        command = "cf create-service \"" + service + "\" \"" + plan + "\" \"" + serviceName + "\""
        Logger.debug("Executing command \"" + command + "\"")
        proc = Popen([command], 
                     shell=True, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate();

        if proc.returncode != 0:
            Logger.info("Unable to create service in this space, error was: " + out)
            return None
        return serviceName 
    return existingService 

# look for our bridge app to bind this service to.  If it's not there,
# attempt to create it.  Then bind the service to that app.  If it 
# all works, return that app name as the bound app
def createBoundAppForService (service, plan, serviceName, appName=DEFAULT_BRIDGEAPP_NAME):

    if not checkAndCreateBridgeApp(appName):
        return None
    print "service " + service 
    print "plan " + plan 
    print "serviceName " + serviceName 
    print "appName " + appName 

    serviceName=checkOrAddService(service, plan, serviceName)
    # now try to bind the service to our bridge app
    Logger.info("Binding service \"" + serviceName + "\" to app \"" + appName + "\"")
    proc = Popen(["cf bind-service " + appName + " \"" + serviceName + "\""], 
                 shell=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate();
    if proc.returncode != 0:
        Logger.info("Unable to bind service to the bridge app, error was: " + out)
        return None
    return appName

def setenvvariable(key, value, filename="setenv_globalization.sh"):
    keyvalue = 'export %s=%s\n' % (key, value)
    open(filename, 'a+').write(keyvalue)

# begin main execution sequence

try:
    Logger = setupLogging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--app")
    args=parser.parse_args()
    if args.app:
        appName=args.app
    else: 
        appName=DEFAULT_BRIDGEAPP_NAME


    createBoundAppForService(GLOBALIZATION_SERVICE, GLOBALIZATION_SERVICE_PLAN, GLOBALIZATION_SERVICE_NAME,appName)
    createBoundAppForService(MACHINE_TRANSLATION_SERVICE, MACHINE_TRANSLATION_PLAN, MACHINE_TRANSLATION_NAME,appName)
    createBoundAppForService(TWITTER_SERVICE, TWITTER_PLAN, TWITTER_NAME,appName)

    sys.exit(0)


except Exception, e:
    Logger.warning("Exception received", exc_info=e)
    sys.exit(1)

