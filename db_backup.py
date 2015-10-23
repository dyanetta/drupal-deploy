#!/usr/bin/python

#
# Backup database. Just a dump.
# Probably use Drush aliases?
#
# 3 Sept 2015 - dyanetta

import os
import sys
import pwd
import string
import argparse
import subprocess

#Colors for Jenkins console readability
RED='\033[1;31m'
BLUE='\033[1;34m'
GREEN='\033[1;32m'
MAGENTA='\033[1;35m'
NC='\033[0m'

# Only the Jenkins server should execute this script. This isnt foolproof
# but close enough until i figure out a better way - limiting execution to
# the Jenkins linux user account...
if (pwd.getpwuid(os.getuid()).pw_name != "jenkins"):
   print(RED + "This script should only be run by the Jenkins server. Exiting." + NC)
   exit(1)

# Handle arguments
#parser = argparse.ArgumentParser(description='Drupal Deployment Tool')
#parser.add_argument("mode", help="enable or disable maintenance mode", type=int)
#parser.add_argument("server", help="server to execute maintenance mode change on")
#args = parser.parse_args()

#if args.mode > 1 or args.mode < 0:
#   print("Argument value must be 0 or 1")
#   exit(1)

print(BLUE + "If we sync'ed databases, this is where we'd do it..." + NC) 
