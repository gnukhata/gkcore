
"""
Copyright (C) 2014 2015 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

  GNUKhata is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public
  License along with GNUKhata (COPYING); if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,


Contributor: 
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>



Main entry point"""

from pyramid.config import Configurator
from gkcore.models.meta import dbconnect
from pyramid.events import NewRequest

eng = dbconnect()
resultset = eng.execute("select * from signature")
row = resultset.fetchone()
secret = row[0]
#print secret
enumdict = {"Success":0,"DuplicateEntry":1,"UnauthorisedAccess":2,"ConnectionFailed":3}
def add_cors_headers_response_callback(event):
    def cors_headers(request, response):
        response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '1728000',
        })
    event.request.add_response_callback(cors_headers)

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.add_route("orgid","/organisation/{orgname}/{orgtype}/{yearstart}/{yearend}")
    config.add_route("organisation","/organisation/{orgcode}")
    config.add_route("organisations","/organisations")
    config.add_route("orgyears","/orgyears/{orgname}/{orgtype}")
    config.add_route("users",'/users/{orgcode}')
    config.add_route('user','/user/{userid}')
    config.add_route("accounts",'/accounts/{orgcode}')
    config.add_route("account",'/account/{accountcode}')
    config.add_route("login",'/login')
    config.add_route("groupsubgroup","/groupsubgroup/{groupcode}")
    config.add_route("groupsubgroups","/groupsubgroups")
    config.add_route("groupDetails","/groupDetails/{groupcode}")
    config.scan("gkcore.views")
    config.add_subscriber(add_cors_headers_response_callback, NewRequest)
    return config.make_wsgi_app()
