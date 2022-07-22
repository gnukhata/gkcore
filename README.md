# GKCORE

The REST API server of GNUKhata

- [API Docs](https://gnukhata.gitlab.io/gkcore/api-docs/)
- License: `APGPLv3`

# Installation

## Docker

Requirements:

- [docker-compose](https://docs.docker.com/compose/)
- [virtualenv](https://pypi.org/project/virtualenv/)

- Create a virtal environment named `gkenv`: `virtualenv gkenv`
- `cd` into the cloned gkcore repository
- activate the gkcore virtual environment
- run `pip install -r requirements.txt` to install gkcore dependencies
- set environment variable `export GKCORE_DB_URL="postgres://gkadmin:gkadmin@localhost:5432/gkdata"`
- Run the command `docker-compose up -d` to start the containers on which gkcore depends
- If you are running gkcore for the first time, run `python3 initdb.py` which initializes the database schema
- For development purpose, run `pserve development.ini --reload`
- For production, run `pserve production.ini`

gkcore now can be accessed via `localhost:6543` from your web browser or at `0.0.0.0:6543` incase of production

> The gkcore's data is stored under `gkdir` folder in the user's home directory.

## Manual

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

# Credits

- Razorpay: IFSC validation server is used as a docker service [source](https://github.com/razorpay/ifsc)
- pgadmin: Helps visualizing gnukhata's database locally
- GST Portal: For providing HSN/SAC codes spreadsheet

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
