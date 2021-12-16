```
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.

  GNUKhata is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License along with GNUKhata (COPYING); if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,
```

Contributors:
"Krishnakant Mane" <kk@gmail.com>

### Installation

> Note: you have to press enter after completely typing every command.

- On debian/Ubuntu distributions Install python-virtualenv postgresql and dependencies using following command

> ` sudo apt-get install python3-virtualenv postgresql python3-dev libpq-dev git python3-setuptools build-essential`

- Create a python virtualenv in a directory(NOT IN gkwebapp or gkcore. If using emacs please do so in '.virtualenvs' directory in home.) using:

> `virtualenv gkenv `

- change directory to gkenv:

> `cd gkenv`

- Activate your virtualenv using:

> `source bin/activate`

- Fork gkcore from https://gitlab.com/gnukhata/gkcore

- Create and add your SSH key to gitlab by following this guide - https://gitlab.com/help/gitlab-basics/create-your-ssh-keys.md

- Clone gkcore in your workspace using:

> `git clone git@gitlab.com:<username>/gkcore.git`

- Change permission of gkcore to gain write acess.

> `sudo chmod 775 gkcore`

- Change to gkcore directory. Look inside the directory. You must find files like `gkutil.sh`, `setup.py`, `initdb.py`

- Give permission to gkutil.sh file to execute and execute the same using:

> `chmod 755 gkutil.sh`

> `./gkutil.sh`

- Activate your virtual environment and run setup.py using:

> `python3 setup.py develop`

- Your environment will be checked for all the required libraries and the missing ones will be downloaded.

- Now we have to run initdb.py script. This will create tables in our database. To run this script we need to switch to a user 'gkadmin' which was created when we ran 'gkutil.sh' script.

> `sudo su gkadmin`

Activate your virtualenv and then run initdb.py

> `python initdb.py`

- To run gkcore server in development mode use:

> `pserve development.ini --reload`

gkcore is now accessible at `http://localhost:6543`🎉

### Credits

- Razorpay: IFSC validation server is used as a docker service [source](https://github.com/razorpay/ifsc)
- pgadmin: Helps visualizing gnukhata's database locally

<!--

* Open another terminal and change directory to gkwebapp
* Activate virtualenv and run setup.py using

> `python setup.py develop`

- To run gkwebapp server in development mode use:

> `pserve development.ini`

# Documentation

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
-->
