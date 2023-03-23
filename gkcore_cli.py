#!/usr/bin/env python3

from sys import argv as args
import subprocess as cmd
import os

help_text = """\t
This script helps your setup / run gkcore - GNUKhata's REST API service

USAGE: ./gkcore_cli.py [OPTION]

OPTIONS:

\tinit - Initialize the database
\tserve - Start the development server
\tdeploy - Start the production server
"""


def check_flags(arg):
    """Validate script arguments & run appropriate action"""

    # set env variable, used by gkcore to connect to db
    os.environ["GKCORE_DB_URL"] = "postgres://gkadmin:gkadmin@localhost:5432/gkdata"

    if arg == "init":
        cmd.run(["docker-compose", "up", "-d"])
        cmd.run(["python3", "initdb.py"])
        return

    elif arg == "serve":
        cmd.run(["docker-compose", "up", "-d"])
        cmd.run(["pserve", "development.ini", "--reload"])
        return

    elif arg == "deploy":
        cmd.run(["docker-compose", "up", "-d"])
        cmd.run(["pserve", "production.ini"])
        return
    else:
        print(help_text)


if len(args) > 1:
    check_flags(args[1])
else:
    print(help_text)
