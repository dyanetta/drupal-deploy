#!/usr/bin/python

import os
import pwd
import sys
import mmap
import time
import glob
import string
import shutil
import logging
import argparse
import subprocess
import ConfigParser
from stat import *
from ConfigParser import SafeConfigParser

config_file = "/var/www/deployment/site-deploy.conf"
log_file = "/var/www/deployment/update.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
PIPE = subprocess.PIPE

# Print a menu of updatable sites, ask for user's choice
# Return name of the chosen, exit for any other choice
def site_selection(site_configs):
   for index, site in enumerate(site_configs):
      print(str(index) + "\t" + site)
   print("\nQ:\t" + "Quit")
   nb = raw_input("Site?  ")  

   try:
      if nb == "Q" or nb == "q":
         logging.info("Site update canceled - user's choice.")
         exit(0)
      selection = int(nb)
      if not (0 <= selection <= index):
         print("Invalid choice")
         logging.info("Site update canceled - invalid choice.")
         exit(1)
   except ValueError:
      print("Invalid choice")
      logging.info("Site update canceled - invalid choice.")
      exit(1)
   return(site_configs[selection])

# Function maps entries of the config file
# Saves a bit of work when pulling config settings
def ConfigSectionMap(section):
   dict1 = {}
   options = site_configs.options(section)
   for option in options:
      try:
         dict1[option] = site_configs.get(section, option)
         if dict1[option] == -1:
            DebugPrint("skip: %s" % option)
      except:
         print("exception on %s!" % option)
         dict1[option] = None
   return dict1

# Only apache has SSH settings configured to do git pulls
# and all files must be owned by apache, so... Only apache
# will be able to do deploys.
# #su -s /bin/bash apache -c "deploy.py"  <-- how to run as root
if (pwd.getpwuid(os.getuid()).pw_name != "apache"):
   print("This script must be run as apache - exiting")
   logging.info("Site update canceled - user must be apache.")
   exit(1)

# Parser to allow a sitename be specified as an argument or chosen thru a menu
parser = argparse.ArgumentParser(description='Drupal Deployment Tool')
parser.add_argument("input_site", nargs='?', help="Optionally add sitename to update to command line")
args = parser.parse_args()

# Read/parse config file
site_configs = SafeConfigParser()
site_configs.read(config_file)

# Validate argument or print list
updateSite = ""
if len(sys.argv) > 1:
   updateSite = args.input_site
   if updateSite not in site_configs.sections():
     print("Invalid site name - select from the following list:\n")
     updateSite = site_selection(site_configs.sections())
else:
   print("Choose a site from the following list to be updated:\n")
   updateSite = site_selection(site_configs.sections())

print("\nAttempting to update: " + updateSite)
logging.info('Site update started: ' + updateSite)

# Because ln will happily create links to nothing without giving an error
# we need to check that the source exists first. Doing this before the git pull
# to save time. Simply making sure the directories entered in the config file exist.
if os.path.isdir(ConfigSectionMap(updateSite)['files_target']) is False:
   print("This site is not configured to use the common directory. Exiting.")
   logging.info("Site update canceled. " + ConfigSectionMap(updateSite)['files_target'] + " does not exist.")
   exit(1)
if os.path.isdir(ConfigSectionMap(updateSite)['private_target']) is False:
   print("This site is not configured to use the common directory. Exiting.")
   logging.info("Site update canceled. " + ConfigSectionMap(updateSite)['private_target'] + " does not exist.")
   exit(1)
if os.path.isfile(ConfigSectionMap(updateSite)['settings_target']) is False:
   print("This site is not configured to use the common directory. Exiting.")
   logging.info("Site update canceled. " + ConfigSectionMap(updateSite)['settings_target'] + " does not exist.")
   exit(1)

# Using the SHA hash from Git as the unique identifier for this site. The Apache configs
# all point to /var/www/sites/<site> as the DocumentRoot, but that will merely be a link
# to /var/www/sites/site-hashstring. This allows us to change versions of the site simply
# by linking to whatever we want and sending a signal to apache to reread directories.

# this segment grabs that unique sha hash code
try:
   process = subprocess.Popen(['git', 'ls-remote', ConfigSectionMap(updateSite)['git_repo'], \
             ConfigSectionMap(updateSite)['branch']], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()

except subprocess.CalledProcessError:
   logging.info('Site update failed - Issue reading git repo.')
   logging.info(stderroutput)
   print("Deployment failed - issues with access to git repo.")
   exit(1)

# creates the directory name via site's nickname + first 10 characters of the SHA hash
# if the directory already exists, someone has already tried to deploy this version. If it wasnt
# successful - you'll need to delete the directory and try again. We're not ready to script cleanup
# attempts yet.
nameHash = updateSite + "-" + string.split(stdoutput)[0][:10]
str = ConfigSectionMap(updateSite)['doc_root']
cloneDir = str.replace(updateSite, nameHash)
try:
   os.mkdir(cloneDir, 0755) 
except OSError:
   print("Directory already exists: " + cloneDir)
   print("This typically means the most current code is already deployed.")
   logging.info('Site update failed - code is already updated.')
   exit(1)
logging.info('\tUpdated master branch detected - deploying to: ' + cloneDir)
try:
   process = subprocess.Popen(['git', 'clone', ConfigSectionMap(updateSite)['git_repo'], '-b', \
             ConfigSectionMap(updateSite)['branch'], '--single-branch', '--recursive', cloneDir], \
             stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
except subprocess.CalledProcessError:
   logging.info('Site update failed - Issue reading git repo.')
   logging.info(stderroutput)
   print("Site update failed - issues with access to git repo.")
   exit(1)

print("Git Clone successful for: " + updateSite)
logging.info('\tGit Clone successful: ' + updateSite)

# Dynamic content is saved in a separate location and links are created
# to it. Links are not saved in git for reasons.
# doing: ln -s common/site/files files
# doing: ln -s common/site/private private
# doing: ln -s common/site/settings.local.php settings.local.php
try:
   str = ConfigSectionMap(updateSite)['files_link']
   hashDir = str.replace(updateSite, nameHash)
   process = subprocess.Popen(['ln', '-s', ConfigSectionMap(updateSite)['files_target'], hashDir], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
   sys.stdout.write(stderroutput)
except subprocess.CalledProcessError:
   logging.info('Site update failed - Issues creating symlinks.')
   logging.info(stderroutput)
   print("Site update failed - Issues creating symlinks.")
   exit(1)

try:
   str = ConfigSectionMap(updateSite)['private_link']
   hashDir = str.replace(updateSite, nameHash)
   process = subprocess.Popen(['ln', '-s', ConfigSectionMap(updateSite)['private_target'], hashDir], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
   sys.stdout.write(stderroutput)
except subprocess.CalledProcessError:
   logging.info('Site update failed - Issues creating symlinks.')
   logging.info(stderroutput)
   print("Site update failed - Issues creating symlinks.")
   exit(1)

try:
   str = ConfigSectionMap(updateSite)['settings_link']
   hashDir = str.replace(updateSite, nameHash)
   process = subprocess.Popen(['ln', '-s', ConfigSectionMap(updateSite)['settings_target'], hashDir], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
   sys.stdout.write(stderroutput)
except subprocess.CalledProcessError:
   logging.info('Site update failed - Issues creating symlinks.')
   logging.info(stderroutput)
   print("Site update failed - Issues creating symlinks.")
   exit(1)

#Database updates
#dump db, run drush updb, etc...
try:
   process = subprocess.Popen(['/usr/bin/drush', '-r', cloneDir, 'updatedb', '-y'], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
except subprocess.CalledProcessError:
   logging.info('Site update failed - db update issues.')
   logging.info(stderroutput)
   print('Site update failed - db update failed.')
   exit(1)

logging.info('\tLinks to content created: ' + updateSite)
print("Links to content created: " + updateSite)

###############################################
# Code's been deployed - Starting Cleanup Now #
###############################################

# Remove .git subdirectory & files. Shouldn't contain anything sensitive info, but...
os.remove(cloneDir + "/" + '.gitignore')
os.remove(cloneDir + "/" + '.gitmodules')
gitdir = (cloneDir + "/" + '.git')
shutil.rmtree(gitdir)

# Link the doc_root to the newly deployed directory.
# Create a new link, then rename that link to remain atomic.
tm = time.strftime("%Y%m%d%H%M%S")
tmplink = (ConfigSectionMap(updateSite)['doc_root'] + "-" + tm)
os.symlink(cloneDir, tmplink)
os.rename(tmplink, ConfigSectionMap(updateSite)['doc_root'])

if (os.path.realpath(ConfigSectionMap(updateSite)['doc_root']) + "/") != cloneDir:
   logging.info('Site update failed - Issue creating links.')
   print('Site update failed - Issue creating links.')

logging.info('\tDocumentRoot link changed: ' + updateSite)
print("DocumentRoot link changed: " + updateSite)

# Restart Apache since we've changed the the entire site. Using the graceful option will let it finish serving open
# connections so we arent killing sessions for other sites. The apache user will require a sudoer entry to restart httpd:
# apache ALL= "service httpd graceful"
try:
   process = subprocess.Popen(['sudo', '/sbin/service', 'httpd', 'graceful'], stdout=PIPE, stderr=PIPE)
   stdoutput, stderroutput = process.communicate()
   sys.stdout.write(stderroutput)
except subprocess.CalledProcessError:
   logging.info('Site update failed - Could not restart httpd.')
   logging.info(stderroutput)
   print("Site update failed - Could not restart httpd.")
   exit(1)

# Cleanup old git clone directories. On test we want to leave 5 revisions (per devs) and prod will just be 1.
# 1) Determine if prod/test
#    -WWW_NREL variable in /etc/httpd/conf/httpd.conf is TEST or PROD
# 2) Use time stamps to determine last 5/1 (pulling list from git would be better, maybe if time allows...)
# 3) Remove the older directories

# Probably will move this to top of the script - may introduce features later that will need to know prod/test
# determing if prod/test is useful. maybe eventually use hostname if the naming standard sticks.
prodEnv = False
f = open("/etc/httpd/conf/httpd.conf")
s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
if s.find('WWW_NREL "PROD"') != -1:
   prodEnv = True

versions_to_keep = 5
if (prodEnv):
   versions_to_keep = 2

doc_root_parent = os.path.dirname(ConfigSectionMap(updateSite)['doc_root'])
print(ConfigSectionMap(updateSite)['doc_root'])
print(doc_root_parent)

fileString = (doc_root_parent + "/" + updateSite + "*")
files = glob.glob(fileString)
files.remove(cloneDir)
files.sort(key=os.path.getmtime)

try:
   for f in files[:-versions_to_keep]:
      print("Removing: " + f)
      shutil.rmtree(f)
except Exception as e:
   print(e)

# ToDo 
#backup database before drush updb
#add config field - backup db each time? Some db's are huge, probably need some
#way to limit it...
#if test : sync from prod?
