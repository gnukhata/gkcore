#!/usr/bin/env python3

from sys import argv as args
import subprocess as cmd
import os

help_text = """\t
gkcore is gnukhata's REST API service

USAGE: ./gkcore.py [OPTION]

OPTIONS:

\tinit - Initialize the database
\tserve - Start the development server
\tdeploy - Start the production server
"""


def check_flags():
    """Validate script arguments & run appropriate action"""

    # set env variable, used by gkcore to connect to db
    os.environ["GKCORE_DB_URL"] = "postgres://gkadmin:gkadmin@localhost:5432/gkdata"

    if "init" in args:

        cmd.run(["docker-compose", "up", "-d"])
        cmd.run(["python3", "initdb.py"])
        return

    elif "serve" in args:

        cmd.run(["docker-compose", "up", "-d"])

        cmd.run(["pserve", "development.ini", "--reload"])
        # cmd.run(["gunicorn", "-b 127.0.0.1:6543", "--reload", "--paste", "development.ini"])
        return

    elif "deploy" in args:

        cmd.run(["docker-compose", "up", "-d"])
        cmd.run(["pserve", "production.ini"])
        return
    # if the user does not provide any flags
    else:
        print(help_text)


check_flags()
