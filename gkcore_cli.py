#!/usr/bin/env python3

from sys import argv as args
import subprocess as cmd
import os, sys

help_text = """\t
This script helps your setup / run gkcore - GNUKhata's REST API service

USAGE: ./gkcore_cli.py [OPTION]

OPTIONS:

\tinit - Initialize the database
\tmigrate - Perform migrations on existing database
\tserve - Start the development server
\tdeploy - Start the production server
\tdump - Export a snapshot of the database to a file
"""


def check_flags(arg):
    """Validate script arguments & run appropriate action"""

    if arg == "init":
        if sys.platform.startswith("win"):
            cmd.run(["docker-compose", "up", "-d"])
            cmd.run(["pip", "install", "-r", "requirements.txt"])
            cmd.run(["python", "setup.py", "develop"])
            cmd.run(["python", "initdb.py"])
            return
        else:
            cmd.run(["docker-compose", "up", "-d"])
            cmd.run(["pip", "install", "-r", "requirements.txt"])
            cmd.run(["python3", "setup.py", "develop"])
            cmd.run(["python3", "initdb.py"])
        return

    elif arg == "migrate":
        if sys.platform.startswith("win"):
            cmd.run(["python", "db_migrate.py"])
            return
        cmd.run(["python3", "db_migrate.py"])
        return

    elif arg == "serve":
        # if sys.platform.startswith("win"):
        #     cmd.run(["docker-compose", "up", "-d"])
        #     cmd.run(["pserve", "development.ini", "--reload"])
        #     return
        cmd.run(["docker-compose", "up", "-d"])
        cmd.run(["pserve", "development.ini", "--reload"])
        return

    elif arg == "deploy":
        # if sys.platform.startswith("win"):
        #     cmd.run(["docker-compose", "up", "-d"])
        #     cmd.run(["pserve", "production.ini"])
        #     return
        cmd.run(["docker-compose", "up", "-d"])
        cmd.run(["pserve", "production.ini"])
        return

    elif arg == "dump":
        cmd.run(
            [
                "docker-compose",
                "exec",
                "db",
                "pg_dump",
                "-U",
                "gkadmin",
                "-d",
                "gkdata",
                ">",
                "gkdump.sql",
            ]
        )
        return
    else:
        print(help_text)


if len(args) == 2:
    check_flags(args[1])
else:
    print(help_text)
