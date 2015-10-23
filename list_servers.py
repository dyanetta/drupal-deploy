#!/usr/bin/python

# Sept 2015 - dyanetta
#
# This script is meant to return a list of servers to deploy
# the software to. Given a master list of ALL servers in the
# farm, the environment and the enclave - the script will
# determine the subset of servers to deploy to and write the
# list to a file to be read later by the rsync scripts.
#
# To determine the actual servers to deploy to, we need to know:
# 1) Environment - prod, test, staging or integration
# 2) Enclave - low or dmz
#
# Environment will be passed in as an argument.
# Enclave will be pulled from the config file, using the sitename
# which is passed in as an argument. PITA.
#
# Usage:
# ./build_server_list.py -f <file_containing_all_servers> -e <environment> -s <sitename>
# environment = prod | test | stage | integration
# sitename = edapt, incomm, etc... 
#
# The list is determined using the server hostnames and Platform's
# server naming standard, with a slight deviation to handle a
# type of server not accounted for - staging.
#
# Standard name:  Xlv1YdrupZZ
# where:
# X designates environment class
# 	1 = production
#	2 = test / staging
#	3 = integration
# Y designates the enclave
#	1 = infrastructure / LOW
#	2 = public / DMZ
# drup is the standard name for these servers
# 
# ZZ normally designates the server count, but
# to accomodate the additional "staging" server
# type, we'll assign "9*" to the staging servers,
# which will be a subset of the testing environment.

import re
import sys
import string
import argparse
from ConfigParser import SafeConfigParser

#Colors for Jenkins console readability
RED='\033[1;31m'
BLUE='\033[1;34m'
GREEN='\033[1;32m'
MAGENTA='\033[1;35m'
NC='\033[0m'

# This function makes it easier to pull config values
# from the config file. Instead of searching each time,
# we just call the function with the variable name we want
def ConfigSectionMap(section):
   dict1 = {}
   options = configs.options(section)
   for option in options:
      try:
         dict1[option] = configs.get(section, option)
         if dict1[option] == -1:
            DebugPrint("skip: %s" % option)
      except:
         print("Exception on %s" % option)
         dict1[option] = None
   return dict1

# RegEx to match possible hostnames. If they dont match, it wont receive
# any code updates.
p = re.compile('^[123]lv1[12]drup[0-9][0-9]$', re.IGNORECASE)
finalServerOut = "./target_server_list.txt"
finalServerList = list()

# Handle arguments
parser = argparse.ArgumentParser(description='Build target list for deploys')
parser.add_argument('-f', action="store", dest="masterFileList", required=True)
parser.add_argument('-e', action="store", dest="targetEnvironment", required=True)
parser.add_argument('-c', action="store", dest="siteConfig", required=True)
parser.add_argument('-s', action="store", dest="siteName", required=True)
args = parser.parse_args()

# Read / store the site config file. Use function to retrieve values
configs = SafeConfigParser()
configs.read(args.siteConfig)

# After we read the master server list, the servers are split into these
# lists based on their names. Then we just determine which list is where we
# want to deploy to.
prod_low_servers = list()
test_low_servers = list()
stage_low_servers = list()
integ_low_servers = list()
prod_dmz_servers = list()
test_dmz_servers = list()
stage_dmz_servers = list()
integ_dmz_servers = list()

#yah yah... no file.close(), but script is small and fast enough I dont care...
servers = [line.rstrip('\n') for line in open(args.masterFileList)]

# Character position in servername that defines server purpose/location
environChar = 0
enclaveChar = 4
stageChar = 9

# Divide master list into where they are and what purpose they serve
# Add the name to the correct list, which is what we'll eventually
# write to the file that'll be used to deploy...
for s in servers:
   if p.match(s) == None:
      print(RED + s + " is not a standard server name. Skipping." + NC)
      continue
   if s[enclaveChar] == '1':
      if s[environChar] == '1':
         prod_low_servers.append(s)
         continue
      if s[environChar] == '2':
         if s[stageChar] == '9':
            stage_low_servers.append(s)
            continue
         else:
            test_low_servers.append(s)
            continue
      if s[environChar] == '3':
         integ_low_servers.append(s)
         continue
   elif s[enclaveChar] == '2':
      if s[environChar] == '1':
         prod_dmz_servers.append(s)
         continue
      if s[environChar] == '2':
         if s[stageChar] == '9':
            stage_dmz_servers.append(s)
            continue
         else:
            test_dmz_servers.append(s)
            continue
      if s[environChar] == '3':
         integ_dmz_servers.append(s)
         continue

# Retrieves the enclave value from the site config file
# using new variable, cuz i aint typing that function name
# 8 times.
targetEnclave = ConfigSectionMap(args.siteName)['enclave']

# Assign the correct list to finalServerList, determined from
# the "environment" argument and the "enclave" value from the
# config file.
if args.targetEnvironment.lower() == "production":
   if targetEnclave.lower() == "low":
      finalServerList = prod_low_servers 
   elif targetEnclave.lower() == "dmz":
      finalServerList = prod_dmz_servers 
   else:
      print(RED + targetEnclave + " is not a valid Enclave. Exiting." + NC)
      exit(1)
elif args.targetEnvironment.lower() == "testing":
   if targetEnclave.lower() == "low":
      finalServerList = test_low_servers 
   elif targetEnclave.lower() == "dmz":
      finalServerList = test_dmz_servers 
   else:
      print(RED + targetEnclave + " is not a valid Enclave. Exiting." + NC)
      exit(1)
elif args.targetEnvironment.lower() == "staging":
   if targetEnclave.lower() == "low":
      finalServerList = stage_low_servers 
   elif targetEnclave.lower() == "dmz":
      finalServerList = stage_dmz_servers 
   else:
      print(RED + targetEnclave + " is not a valid Enclave. Exiting." + NC)
      exit(1)
elif args.targetEnvironment.lower() == "integration":
   if targetEnclave.lower() == "low":
      finalServerList = integ_low_servers 
   elif targetEnclave.lower() == "dmz":
      #finalServerList = integ_dmz_servers 
      print(RED + "There should be no integration servers in the DMZ. Exiting." + NC)
      exit(1)
   else:
      print(RED + targetEnclave + " is not a valid Enclave. Exiting." + NC)
      exit(1)
else:
   print(RED + targetEnvironment + " is not a valid Environment. Exiting." + NC)
   exit(1)

f = open (finalServerOut, 'w')
for s in finalServerList:
   f.write(s + '\n')
f.close()

exit(0)
