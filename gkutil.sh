#!/bin/bash

"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

  GNUKhata is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License along with GNUKhata (COPYING); if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,


Contributor:
"Ishan Masdekar " <imasdekar@dff.org.in>
"""
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
