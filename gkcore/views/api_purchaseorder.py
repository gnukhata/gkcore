
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
"Pornima Kolte <pornima@openmailbox.org>"
"Prajkta Patkar<prajkta.patkar007@gmail.com>"
"""


from pyramid.view import view_defaults,  view_config
from gkcore.views.api_login import authCheck
from gkcore import eng, enumdict
from pyramid.request import Request
from gkcore.models.gkdb import purchaseorder, customerandsupplier,product
from sqlalchemy.sql import select, distinct
from sqlalchemy import func, desc
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ ,exc
from datetime import datetime,date
import jwt
import gkcore
from gkcore.models.meta import dbconnect

from datetime import datetime,date



@view_defaults(route_name='purchaseorder')
class api_purchaseorder(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
		print "Purchase order initialized"

	@view_config(request_method='POST',renderer='json')
	def addPoSo(self):
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
	def getAllPoSoData(self):
		""" This function returns all existing PO and SO """
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

				result = self.con.execute(select([purchaseorder]).where(purchaseorder.c.orgcode==authDetails["orgcode"]).order_by(purchaseorder.c.orderdate))
				allposo = []
				for row in result:


					custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["csid"]))
					custrow = custdata.fetchone()
					allposo.append({"orderid":row["orderid"],"orderno": row["orderno"], "orderdate": datetime.strftime(row["orderdate"],'%d-%m-%Y'),"creditperiod": custrow["creditperiod"],"payterms": row["payterms"],"modeoftransport":row["modeoftransport"],"designation":["designation"],
										"schedule":row["schedule"],"taxstate":row["taxstate"],"taxrate":row["taxrate"],"psflag":row["psflag"]})
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult":allposo}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	@view_config(request_method='GET',request_param='psflag',renderer='json')
	def getposo(self):

		"""
		This function gives all purchaseorder or salesorder by matching parameter psflag
		"""
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
				psflagdata =int(self.request.params["psflag"])
				result=self.con.execute(select([purchaseorder.c.orderid,purchaseorder.c.orderno,purchaseorder.c.orderdate,purchaseorder.c.csid]).where(and_(purchaseorder.c.psflag == psflagdata,purchaseorder.c.orgcode==authDetails["orgcode"])))
				po =[]
				for row in result:
					custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["csid"]))
					custrow = custdata.fetchone()
					po.append({"orderid":row["orderid"],"orderno": row["orderno"], "orderdate":datetime.strftime(row["orderdate"],'%d-%m-%Y') ,"custname": custrow["custname"]})
				return {"gkstatus":enumdict["Success"],"gkresult":po}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()


	@view_config(request_method='GET',request_param="poso=single", renderer ='json')
	def getSingleposo(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		else:
			self.con = eng.connect()
			result = self.con.execute(select([purchaseorder]).where(purchaseorder.c.orderid==self.request.params["orderid"]))
			podata = result.fetchone()
			schedule = podata["schedule"]
			details={}
			for key in schedule:
				details[key] = {"productname":schedule[key]["productname"],"packages":schedule[key]["packages"],"rateperunit":schedule[key]["rateperunit"],"quantity":schedule[key]["quantity"]}
			po = {
				"orderno":podata["orderno"],
				"orderdate": datetime.strftime(podata["orderdate"],'%d-%m-%Y'),
				"creditperiod":podata["creditperiod"],
				"payterms":podata["payterms"],
				"modeoftransport":podata["modeoftransport"],
				"designation":podata["designation"],
				"schedule":details,
				"taxstate":podata["taxstate"],
				"taxrate":"%.2f"%float(podata["taxrate"]),
				"psflag":podata["psflag"],
				"csid":podata["csid"]
				}
			return {"gkstatus":enumdict["Success"],"gkresult":po}
			self.con.close()


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
				result = self.con.execute(purchaseorder.update().where(purchaseorder.c.orderid == dataset["orderid"]).values(dataset))
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
				result = self.con.execute(purchaseorder.delete().where(purchaseorder.c.orderid == dataset["orderid"]))
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
