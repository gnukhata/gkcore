
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

"""
#imports contain sqlalchemy modules,
#enumdict containing status messages,
#eng for executing raw sql,
#gkdb from models for all the alchemy expressed tables.
#view_default for setting default route
#view_config for per method configurations predicates etc.
from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result
"""
purpose:
This class is the resource to create, update, read and delete accounts.

connection rules:
con is used for executing sql expression language based queries,
while eng is used for raw sql execution.
routing mechanism:
@view_defaults is used for setting the default route for crud on the given resource class.
if specific route is to be attached to a certain method, or for giving get, post, put, delete methods to default route, the view_config decorator is used.
For other predicates view_config is generally used.
"""
con = Connection
con = eng.connect()
"""
default route to be attached to this resource.
refer to the __init__.py of main gkcore package for details on routing url
"""
@view_defaults(route_name='bankrecon')
class bankreconciliation(object):
	#constructor will initialise request.
	def __init__(self,request):
		self.request = Request
		self.request = request

	@view_config(request_method='GET',renderer='json')
	def banklist(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				result = con.execute(select([gkdb.accounts.c.accountname,gkdb.accounts.c.accountcode]).where(and_(gkdb.accounts.c.orgcode==authDetails["orgcode"],gkdb.accounts.c.groupcode ==(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.orgcode==authDetails["orgcode"],gkdb.groupsubgroups.c.groupname=='Bank'))))).order_by(gkdb.accounts.c.accountname))
				accs = []
				for row in result:
					accs.append({"accountcode":row["accountcode"], "accountname":row["accountname"]})
				return {"gkstatus": enumdict["Success"], "gkresult":accs}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
