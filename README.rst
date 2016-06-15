
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


Contributors:
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"""

Documentation
=============
gkcore is the core engine for GNUKhata <gnukhata.in> a free and open source accounting/ book keeping software.
The core engine contains the database creation and management code along with the code for implementing the logic in form of RESTful API.
To get the code running on your machine as developers, you need to create a virtual environment of Python and then create the databaes and it's dedicated users.

NOTE: PLEASE ENTER ALL COMMANDS AS THEY HAVE BEEN GIVEN INCLUDING QUOTES ("")
These are the steps to get the database initialised.
WARNING: "perform these commands with the full knowledge of what you are doing "
1, firstly we need a system user so issue the command sudo useradd gkadmin and press enter
2, create a role with same name: type sudo -u postgres psql -c "create role gkadmin with login"
3, grant all privileges for this do:
a: sudo -u postgres psql -c "alter role gkadmin createdb;"
b: sudo -u postgres psql -c "grant all privileges on database template1 to gkadmin;"
4, create the database, issue command sudo -u postgres psql -c "create database gkdata"
