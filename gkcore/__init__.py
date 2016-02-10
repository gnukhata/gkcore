
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
from pyramid.authorization import ACLAuthorizationPolicy
#from pyramid_jwt import * 

eng = dbconnect()

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    config.include('pyramid_jwt')
    
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_jwt_authentication_policy("wbc@IITB~39")
    config.add_route("users",'/users/{orgcode}')
    config.add_route('user','/user/{userid}')
    config.add_route("accounts",'/accounts/{orgcode}')
    config.add_route("account",'/account/{accountcode}')
    config.add_route("login",'/login')
    config.scan("gkcore.views")
    return config.make_wsgi_app()
