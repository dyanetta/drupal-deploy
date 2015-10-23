#!/usr/bin/python

import sys
import string
import argparse
import subprocess
from ConfigParser import SafeConfigParser

PIPE = subprocess.PIPE

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

# Handle arguments
parser = argparse.ArgumentParser(description='Drupal Deployment Tool')
parser.add_argument('-f', action="store", dest="siteConfig")
parser.add_argument('-e', action="store", dest="targetEnvironment")
parser.add_argument('-s', action="store", dest="siteName")
args = parser.parse_args()

print(args.siteConfig)
print(args.targetEnvironment)
print(args.siteName)

# Read config file. We'll call a function when we want entries
configs = SafeConfigParser()
configs.read(args.siteConfig)

# Build the directory name we're going to clone into
# Will use the SHA hash of the git branch to make it unique
# and tell us if a version has already been deployed.
# git ls gives us the hash
try:
   process = subprocess.Popen(['git', 'ls-remote', ConfigSectionMap(args.siteName)['git_repo'],\
             ConfigSectionMap(args.siteName)['branch']], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
except subprocess.CalledProcessError:
   print("Deployment failed - issues with git repo.")
   exit(1)

print(stdoutput)
#nameHash = args.siteName + "-" + string.split(stdoutput)[0][:10]
#cloneDir = (ConfigSectionMap(args.siteName)['doc_root']).replace(args.siteName, nameHash)
#
#print("CloneDir: " + cloneDir)
#print("")







