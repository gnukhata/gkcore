"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020 Digital Freedom Foundation & Accion Labs 
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


Contributors:
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"Prajkta Patkar"<prajakta@dff.org.in>


Main entry point:
This package initializer module is run when the application is served.
The module contains enum dict containing all gnukahta success and failure messages.
It also contains all the routes which are connected to respective resources.
To trace the link of the routes we look at the name of a route and then see where it appeares in any of the @view_defaults or @view_config decorator of any resource.
This module also scanns for the secret from the database which is then used for jwt authentication.
"""

from pyramid.config import Configurator
from sqlalchemy.engine import create_engine
from wsgicors import CORS
from gkcore.enum import STATUS_CODES as enumdict
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()


def main(global_config, **settings):
    config = Configurator(settings=settings)

    config.include("pyramid_openapi3")
    config.include('.routes')
    if settings.get('development'): # Use only when it is development mode.
        config.include('.logging')
    config.include('.renderers')
    config.scan()
    # include the pyramid-openapi3 plugin config
    # link: https://github.com/Pylons/pyramid_openapi3

    return CORS(
        config.make_wsgi_app(), headers="*", methods="*", maxage="180", origin="*"
    )

def generate_db_url():
    """ Generate database URL for engine creation. It will look for following
    environment variables, in absence, it will take the default values.

    GKCORE_DB_URL=
    GKCORE_DB_USER=
    GKCORE_DB_PASSWORD=
    GKCORE_DB_HOST=
    GKCORE_DB_PORT=
    GKCORE_DB_NAME=

    The use of dialect & driver are set to postgresql and psycopg2 until support for
    others are not tested or implemented.

    If GKCORE_DB_URL is given, it is used as database url, ignoring other variables.

    Link to SQL Alchemy documentation: https://docs.sqlalchemy.org/en/13/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2
    """
    # if env variable GKCORE_DB_URL is set, Use it
    db_url = os.environ.get("GKCORE_DB_URL")
    db_url = None

    if not db_url:
        db_name = os.environ.get("GKCORE_DB_NAME", "gkdata")
        db_user = os.environ.get("GKCORE_DB_USER", "postgres")
        db_password = os.environ.get("GKCORE_DB_PASSWORD", "gkadmin")
        db_host = os.environ.get("GKCORE_DB_HOST", '')
        db_port = os.environ.get("GKCORE_DB_PORT")
        db_url = f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?"

        custom_host = db_host + f":{db_port}" if db_port else ''
        if custom_host:
            db_url += f"host={custom_host}"
        else:
            db_url += "host=/var/run/postgresql&host=localhost"

    return db_url

eng = create_engine(generate_db_url(), echo=False, pool_size=15, max_overflow=100)
# eng can be used as an engine instance to connect to database.
# The echo parameter set to False means sql queries will not be printed to the terminal.
# Pool size is important to balance between database holding capacity in ram and speed.

def get_secret():
    with eng.connect() as connection:
        resultset = connection.execute("select * from signature")
        if resultset.rowcount == 1:
            return resultset.fetchone()[0]
    return None

secret = get_secret() # for compatibility with old code
