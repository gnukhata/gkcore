
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


from gkcore import eng
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json 
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
import jwt

con = Connection
con = eng.connect()


@view_defaults(route_name='users')
class api_user(object):
	def __init__(self,request):
		self.request = Request
		self.request = request

	@view_config(request_method='POST',renderer='json')
	def addUser(self):
		try:
			dataset = self.request.json_body
			print dataset
			result = con.execute(gkdb.users.insert(),[dataset])
			return result.rowcount
		except:
			return False
	@view_config(route_name='user', request_method='GET',renderer='json')
	def getUser(self):
		result = con.execute(select([gkdb.users]).where(gkdb.users.c.userid == self.request.matchdict["userid"] ))
		row = result.fetchone()
		User = {"userid":row["userid"], "username":row["username"], "userrole":row["userrole"], "userquestion":row["userquestion"], "useranswer":row["useranswer"], "userpassword":row["userpassword"]}
		print User
		return User
	@view_config(request_method='PUT', renderer='json')
	def editUser(self):
		try:
			dataset = self.request.json_body
			result = con.execute(gkdb.users.update().where(gkdb.users.c.userid==dataset["userid"]).values(dataset))
			print result.rowcount
			return result.rowcount
		except:
			return False
	@view_config(request_method='GET', renderer ='json')
	def getAllUsers(self):
		token = self.request.headers["nav"]
		print token
		print jwt.decode(token, 'wbc@IITB~39', algorithms=['HS256'])
		result = con.execute(select([gkdb.users.c.username,gkdb.users.c.userid]).where(gkdb.users.c.orgcode==self.request.matchdict["orgcode"]))
		accs = []
		for row in result:
			accs.append({"userid":row["userid"], "username":row["username"]})
		print accs
		return accs
