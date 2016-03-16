


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


from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models.gkdb import vouchers
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


@view_defaults(route_name='transaction')
class api_transaction(object):
	def __init__(self,request):
		self.request = Request
		self.request = request

	@view_config(request_method='POST',renderer='json')
	def addvoucher(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				dataset = self.request.json_body
				print dataset
				dataset["orgcode"] = authDetails["orgcode"]
				result = con.execute(vouchers.insert(),[dataset])
				return {"gkstatus":enumdict["Success"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_method='GET',renderer='json')
	def getVoucher(self):
		try:
			token = self.request.headers['gktoken']
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				voucherCode = self.request.params["code"]
				result = con.execute(select([vouchers]).where(and_(vouchers.c.orgcode==authDetails["orgcode"], vouchers.c.vouchercode==voucherCode )) )
				row = result.fetchone()
				
				voucher = {"vouchercode":row["vouchercode"],"vouchernumber":row["vouchernumber"],"voucherdate":str(row["voucherdate"]),"entrydate":str(row["entrydate"]),"narration":row["narration"],"drs":row["drs"],"crs":row["crs"],"prjdrs":row["prjdrs"],"prjcrs":row["prjcrs"],"vouchertype":row["vouchertype"],"delflag":row["delflag"],"orgcode":row["orgcode"]}
				return {"gkstatus":enumdict["Success"], "gkresult":voucher}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}