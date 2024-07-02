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

from gkcore.security import SecurityPolicy
from pyramid.config import Configurator
from gkcore.models.meta import eng
from wsgicors import CORS
from gkcore.enum import STATUS_CODES as enumdict


def get_secret():
    with eng.connect() as connection:
        resultset = connection.execute("select * from signature")
        if resultset.rowcount == 1:
            return resultset.fetchone()[0]
    return None

secret = get_secret() # for compatibility with old code

def main(global_config, **settings):
    config = Configurator(settings=settings)

    # Add security policy
    config.set_security_policy(
        SecurityPolicy(secret=get_secret())
    )

    config.include("pyramid_openapi3")
    config.add_route("uom", "/unitofmeasurement")
    config.include('.routes')
    config.scan()
    # include the pyramid-openapi3 plugin config
    # link: https://github.com/Pylons/pyramid_openapi3

    return CORS(
        config.make_wsgi_app(), headers="*", methods="*", maxage="180", origin="*"
    )
