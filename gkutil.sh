#!/bin/bash

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
