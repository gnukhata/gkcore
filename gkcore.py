#!/usr/bin/env python3

from sys import argv
import subprocess as cmd
import os

help = """\t
USAGE: ./gkcore.py [OPTION]

OPTIONS:

\tinit - Initialize the database
\tserve - Start the development server
\tdeploy - Start the production server
"""


def check_flags():
    """Validate script arguments & run appropriate action"""

    args = argv

    # set env variable, used by gkcore to connect to db
    os.environ["GKCORE_DB_URL"] = "postgres://gkadmin:gkadmin@localhost:5432/gkdata"

    if "init" in args:

        print("initializing the db ...")
        cmd.run(["python3", "initdb.py"])

    if "serve" in args:

        cmd.run(["docker-compose", "up", "-d"])
        cmd.run(["pserve", "development.ini"])

    if "deploy" in args:

        cmd.run(["docker-compose", "up", "-d"])
        cmd.run(["pserve", "production.ini"])

    # if the user does not provide any flags
    else:
        print(help)


check_flags()
