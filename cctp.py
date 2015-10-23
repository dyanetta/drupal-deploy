#!/usr/bin/python

#
# Changes a drupal site's maintenance_mode setting.
# 0 = maintenance_mode disabled (normal operation)
# 1 = maintenance_mode enabled (website down)
#
# 1 Sept 2015 - dyanetta

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
#parser = argparse.ArgumentParser(description='Drupal Deployment Project')
#parser.add_argument("input_site", nargs='?', help="Optionally add sitename to update to command line")
#args = parser.parse_args()

print(BLUE + "Copying cloned directory to some environment somewhere..." + NC)
