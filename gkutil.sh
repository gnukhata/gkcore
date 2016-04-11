#!/bin/bash
#this file is part of GNUKhata which is a free 
#accounting software
#distributed under the terms of GNU General Public License #version 3.

#this file will create the user gkadmin  
#and add sufficient privileges
#this script will also create the database gkdata
#author Ishan Masdekar <imasdekar@openmailbox.og>
sudo useradd gkadmin
echo 'Created user gkadmin'

sudo -u postgres psql -c "create role gkadmin with login"
echo 'Role gkadmin created'

sudo -u postgres psql -c "alter role gkadmin createdb;"
echo 'Granted database creation privileges to role sttpadmin'

sudo -u postgres psql -c "grant all privileges on database template1 to gkadmin;"
echo 'Granted all privileges to role gkadmin'

sudo -u postgres psql -c "create database gkdata"
echo 'Created gkdata database '
