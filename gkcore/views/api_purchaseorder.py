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
"""


from pyramid.view import view_defaults,  view_config
from gkcore.views.api_login import authCheck
from gkcore import eng, enumdict
from pyramid.request import Request

from gkcore.models.gkdb import purchaseorder
from sqlalchemy.sql import select, distinct
from sqlalchemy import func, desc
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
import jwt
import gkcore
from datetime import datetime,date
from gkcore.models.meta import dbconnect


@view_defaults(route_name='purchaseorder')
class api_purchaseorder(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
		print "Purchase order initialized"

	@view_config(request_method='POST',renderer='json')
	def addPurchaseorder(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dataset = self.request.json_body
				dataset["orgcode"] = authDetails["orgcode"]
				result = self.con.execute(purchaseorder.insert(),[dataset])
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()


	@view_config(request_method='GET',renderer='json')
	def getAllPurchaseorders(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				result = self.con.execute(select([purchaseorder.c.orderno, gkdb.purchaseorder.c.orderdate, gkdb.purchaseorder.c.csid]).order_by(gkdb.purchaseorder.c.orderdate))
				purchaseorders = []
				for row in result:
					custdata = self.con.execute(select([gkdb.customerandsupplier.c.custname]).where(gkdb.customerandsupplier.c.custid==row["csid"]))
					custrow = custdata.fetchone()
					purchaseorders.append({"orderid":row["orderid"],"orderno": row["orderno"], "orderdate":datetime.strftime(row["podate"],'%d-%m-%Y') , "custname": custrow["custname"],"psflag":["psflag"] })
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult":purchaseorders}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param='po=single',request_method='GET',renderer='json')
	def getPurchaseorder(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				result = self.con.execute(select([gkdb.purchaseorder]).where(gkdb.purchaseorder.c.orderno == self.request.params["orderno"]))
				row = result.fetchone()
				purchaseOrderDetails = {"orderno": row["orderno"], "podate": datetime.strftime(row["podate"],'%d-%m-%Y'), "maxdate": datetime.strftime(row["maxdate"],'%d-%m-%Y'),  "deliveryplaceaddr": row["deliveryplaceaddr"], "datedelivery": datetime.strftime(row["datedelivery"],'%d-%m-%Y'), "modeoftransport": row["modeoftransport"],"packaging": row["packaging"], "payterms": row["payterms"],"csid": row["csid"],"productdetails": row["productdetails"],"tax": row["tax"]}
				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":purchaseOrderDetails}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}


	@view_config(request_method='PUT',renderer='json')
	def editPurchaseOrder(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dataset = self.request.json_body
				result = self.con.execute(gkdb.purchaseorder.update().where(gkdb.purchaseorder.c.orderno == dataset["orderno"]).values(dataset))
				return {"gkstatus":enumdict["Success"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()


	@view_config(request_method='DELETE',renderer='json')
	def deletePurchaseOrder(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dataset = self.request.json_body
				result = self.con.execute(gkdb.purchaseorder.delete().where(gkdb.purchaseorder.c.orderno == dataset["orderno"]))
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
