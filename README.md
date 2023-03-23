# GKCORE

The REST API server of GNUKhata

- [API Docs](https://gnukhata.gitlab.io/gkcore/api-docs/)
- License: `APGPLv3`

# Installation

## Via Docker (Easier)

Requirements:

- [docker](https://www.docker.com/)
- [docker-compose](https://docs.docker.com/compose/)
- [virtualenv](https://pypi.org/project/virtualenv/)

- Install dependencies `libpq-dev` and `build-essential`. On debian/Ubuntu distro's `sudo apt install libpq-dev build-essential`
- Create a virtal environment named gkenv: `virtualenv gkenv`
- activate the gkcore virtual environment: `source gkenv/bin/activate`
- `cd` into the cloned gkcore repository
- run `pip install -r requirements.txt` to install gkcore dependencies
- set environment variable `export GKCORE_DB_URL="postgres://gkadmin:gkadmin@localhost:5432/gkdata"`
- Run the command `docker-compose up -d` to start the containers on which gkcore depends
- If you are running gkcore for the first time, run `python3 setup.py develop` to setup the app and `python3 initdb.py` which initializes the database schema
- For development purpose, run `pserve development.ini --reload`
- For production, run `pserve production.ini`

gkcore can be accessed at `localhost:6543` from your web browser or `0.0.0.0:6543` incase of production

> gkcore API docs (swagger UI) can be accessed via `localhost:6543/docs` from your web browser

## Manual Way

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

# Environment Variables:

- `GKCORE_DB_URL`: Provide a custom database URL
- `GKCORE_IFSC_SERVER`: Provide custom IFSC api endpoint.
- `GKCORE_DISABLE_REGISTRATION`: set to "yes" to disable registrations.

# After Installation

- When gkcore is installed on VPS, make sure to change the timezone to India with command `timedatectl set-timezone Asia/Kolkata` as organization logs pickup the default timezone.

# Public instances

| API endpoint                 | Info                                                       |
| ---------------------------- | ---------------------------------------------------------- |
| https://api-dev.gnukhata.org | Hosted by GNUKhata team. this api is based on devel branch |

# Credits

- [Razorpay IFSC](https://github.com/razorpay/ifsc): IFSC validation server is used as a docker service
- pgadmin: Helps visualizing gnukhata's database locally
- GST Portal: For providing HSN/SAC codes spreadsheet
