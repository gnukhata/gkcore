
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

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



Main entry point:
This package initializer module is run when the application is served.
The module contains enum dict containing all gnukahta success and failure messages.
It also contains all the routes which are connected to respective resources.
To trace the link of the routes we look at the name of a route and then see where it appeares in any of the @view_defaults or @view_config decorator of any resource.
This module also scanns for the secret from the database which is then used for jwt authentication.
"""

from pyramid.config import Configurator
from gkcore.models.meta import dbconnect
from gkcore.views import *
from webob import request
from webob.request import Request
from wsgicors import CORS
try:
	eng = dbconnect()
	resultset = eng.execute("select * from signature")
	row = resultset.fetchone()
	secret = row[0]
	#print secret
except:
	secret = ""

enumdict = {"Success":0,"DuplicateEntry":1,"UnauthorisedAccess":2,"ConnectionFailed":3,"BadPrivilege":4, "ActionDisallowed":5}

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.add_route("organisation","/organisation")
    config.add_route("invoice","/invoice")
    config.add_route("organisations","/organisations")
    config.add_route("categoryspecs","/categoryspecs")
    config.add_route("orgyears","/orgyears/{orgname}/{orgtype}")
    config.add_route("transaction","/transaction")
    config.add_route("users",'/users')
    config.add_route('user','/user')
    config.add_route('bankrecon','/bankrecon')
    config.add_route("accounts",'/accounts')
    config.add_route("account",'/account/{accountcode}')
    config.add_route("projects",'/projects')
    config.add_route("project",'/project/{projectcode}')
    config.add_route("customersupplier",'/customersupplier')
    config.add_route("unitofmeasurement","/unitofmeasurement")
    config.add_route("accountsbyrule",'/accountsbyrule')
    config.add_route("login",'/login')
    config.add_route("groupallsubgroup","/groupallsubgroup/{groupcode}")
    config.add_route("groupsubgroup","/groupsubgroup/{groupcode}")
    config.add_route("groupsubgroups","/groupsubgroups")
    config.add_route("groupDetails","/groupDetails/{groupcode}")
    config.add_route("report","/report")
    config.add_route("rollclose","/rollclose")
    config.add_route("forgotpassword","/forgotpassword")
    config.add_route("categories","/categories")
    config.add_route("products","/products")
    config.add_route("godown","/godown")
    config.add_route("delchal","/delchal")
    config.add_route("purchaseorder","/purchaseorder")    
    config.add_route("transfernote","/transfernote")
    config.add_route("discrepancynote","/discrepancynote")
    config.add_route("tax","/tax")
    config.add_route("backuprestore","/backuprestore")
    config.add_route("groupflatlist","/groupflatlist")
    config.scan("gkcore.views")

    return CORS(config.make_wsgi_app(),headers="*",methods="*",maxage="180",origin="*")
