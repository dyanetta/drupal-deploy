# drupal-deploy

These are a series of scripts written to be called from a Jenkins project.
The series of scripts are incomplete, as the project and my contract were
canceled. The basic process was:

1) Git pull code to the Jenkins workspace
2) Create links to dynamic content
3) Rsync the code to prod/test server (as specified from Jenkins parameters)
4) Optionally backup the dynamic content
5) Optionally backup the database
6) Update the database
7) Restart httpd services

The "old-deploy.py" script was the 1st iteration, before we decided to
run everything through Jenkins.

