
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


#login function
from gkcore import eng
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json 
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result
import jwt
import gkcore
con= Connection
con= eng.connect()

@view_config(route_name='login',request_method='POST',renderer='json')
def gkLogin(request):
	dataset = request.json_body
	result = con.execute(select([gkdb.users.c.userid,gkdb.users.c.userrole]).where(gkdb.users.c.username==dataset["username"] and gkdb.users.c.userpassword== dataset["userpassword"] and gkdb.users.c.orgcode==dataset["orgcode"]) )
	if result.rowcount == 1:
		record = result.fetchone()
		
		token = jwt.encode({"orgcode":dataset["orgcode"],"userid":record["userid"]},gkcore.secret,algorithm='HS256')
		return {"status":"ok","token":token }
	else:
		return {"status":"invalid"}

def authCheck(token):
	try:
		tokendict = jwt.decode(token,gkcore.secret,algorithms=['HS256'])
		return True
	except:
		return False