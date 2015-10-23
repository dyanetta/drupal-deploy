#!/usr/bin/python

import os
import sys
import string
import argparse
import subprocess
from ConfigParser import SafeConfigParser

#Colors for Jenkins console readability
RED='\033[1;31m'
BLUE='\033[1;34m'
GREEN='\033[1;32m'
MAGENTA='\033[1;35m'
NC='\033[0m'

PIPE = subprocess.PIPE
targetServerList = "./target_server_list.txt"

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
parser.add_argument('-f', action="store", dest="siteConfig", required=True)
parser.add_argument('-s', action="store", dest="siteName", required=True)
args = parser.parse_args()

# Read config file. We'll call a function when we want entries
configs = SafeConfigParser()
configs.read(args.siteConfig)

# Build the directory name we're going to clone into.
# Will use the SHA hash of the git branch to make it unique
# and tell us if a version has already been deployed.
# Jenkins user will need sudo permissions to become the "repo_user" (from config files)
# to pull git info.
try:
   process = subprocess.Popen(['/usr/bin/sudo', '-u', ConfigSectionMap(args.siteName)['repo_user'], \
                               '/usr/bin/git', 'ls-remote', ConfigSectionMap(args.siteName)['site_git_repo'], 'master'], \
                               stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
except subprocess.CalledProcessError:
   print(RED + "Deployment failed - issues querying the git repo." + NC)
   print(RED + stderroutput + NC)
   exit(1)

# Creates the "hashname" from the sitename + the 1st 10 chars of the UUID of the git branch
# unique AND readable!
nameHash = args.siteName + "-" + string.split(stdoutput)[0][:10]
cloneDir = (ConfigSectionMap(args.siteName)['doc_root']).replace(args.siteName, nameHash)
print(BLUE + "New directory will be: " + cloneDir + NC)

# jenkins runs as the user jenkins. Need permissions to create the directory we're cloning into. Making the directory as jenkins
# then using sudo to change the ownership to the repo_user is easier then muddling through an embedded sudo... "sudo cisrv sudo mdkir"
try:
   process = subprocess.Popen(['/usr/bin/sudo', '/bin/mkdir', '-p', nameHash], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
   process = subprocess.Popen(['/usr/bin/sudo', '/bin/chown', ConfigSectionMap(args.siteName)['repo_user'], nameHash], stdout=PIPE, stderr=PIPE)
   stdoutput2, stderroutput2 = process.communicate()
except subprocess.CalledProcessError:
   print(RED + "Deployment failed - issue creating clone directory in jenkins workspace" + NC)
   print(RED + stderroutput + NC)
   print(RED + stderroutput2 + NC)
   exit(1)

try:
   process = subprocess.Popen(['/usr/bin/sudo', '-u', ConfigSectionMap(args.siteName)['repo_user'], \
                               '/usr/bin/git', 'clone', ConfigSectionMap(args.siteName)['site_git_repo'], '-b', 'master', \
                               '--single-branch', '--recursive', nameHash], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
except subprocess.CalledProcessError:
   print(RED + "Deployment failed - issues cloning the git repo." + NC)
   print(RED + stderroutput + NC)
   exit(1) 

# Making links to the common, private and local settings files.
# Because of how symlinks work, we can happily create our links now
# even though their target doesnt exist on this server. Some script run
# after the copy to target server will have to check that the links are valid.
try:
   tmpstr = ConfigSectionMap(args.siteName)['files_link']
   substr = tmpstr.split(args.siteName, 1)[1]
   hashDir = tmpstr.replace(args.siteName, nameHash)
   subDir = nameHash + substr.replace(args.siteName, nameHash)

   print("ln -s " + ConfigSectionMap(args.siteName)['files_target'] + " " + subDir)
   process = subprocess.Popen(['/usr/bin/sudo', '-u', ConfigSectionMap(args.siteName)['repo_user'], 'ln', '-s', \
                              ConfigSectionMap(args.siteName)['files_target'], subDir], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
except subprocess.CalledProcessError:
   print(RED + "Deployment failed - Issues creating common symlinks." + NC)
   print(RED + stderroutput + NC)
   exit(1)














