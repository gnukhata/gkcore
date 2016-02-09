
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
from sqlalchemy.ext.baked import Result

con = Connection
con = eng.connect()


@view_defaults(route_name='accounts')
class api_account(object):
	def __init__(self,request):
		self.request = Request
		self.request = request

	@view_config(request_method='POST',renderer='json')
	def addAccount(self):
		try:
			dataset = self.request.json_body
			print dataset
			result = con.execute(gkdb.accounts.insert(),[dataset])
			return result.rowcount
		except:
			return False
	@view_config(route_name='account', request_method='GET',renderer='json')
	def getAccount(self):
		result = con.execute(select([gkdb.accounts]).where(gkdb.accounts.c.accountcode==self.request.matchdict["accountcode"]))
		row = result.fetchone()
		accs={"accountcode":row["accountcode"], "accountname":row["accountname"], "openingbal":row["openingbal"],"groupcode":row["groupcode"]}
		print accs
		return accs
	@view_config(request_method='GET', renderer ='json')
	def getAllAccounts(self):
		result = con.execute(select([gkdb.accounts.c.accountname,gkdb.accounts.c.accountcode]).where(gkdb.accounts.c.orgcode==self.request.matchdict["orgcode"]))
		accs = []
		for row in result:
			accs.append({"accountcode":row["accountcode"], "accountname":row["accountname"]})
		print accs
		return accs
	@view_config(request_method='PUT', renderer='json')
	def editAccount(self):
		try:
			dataset = self.request.json_body
			result = con.execute(gkdb.accounts.update().where(gkdb.accounts.c.accountcode==dataset["accountcode"]).values(dataset))
			print result.rowcount
			return result.rowcount
		except:
			return False