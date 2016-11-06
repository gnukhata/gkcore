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
from gkcore.models.gkdb import purchaseorder, stock
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
				result = self.con.execute(select([purchaseorder.c.orderid,purchaseorder.c.orderno,purchaseorder.c.orderdate, purchaseorder.c.csid,purchaseorder.c.psflag]).order_by(purchaseorder.c.orderdate))
				allposo = []
				for row in result:
					custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["csid"]))
					custrow = custdata.fetchone()
					allposo.append({"orderid":row["orderid"],"orderno": row["orderno"], "orderdate":datetime.strftime(row["orderdate"],'%d-%m-%Y') , "custname": custrow["custname"],"psflag":row["psflag"] })
					
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
				
				psflag =int(self.request.params["psflag"])
				if(psflag==16):
					
					result=self.con.execute(select([purchaseorder.c.orderno,purchaseorder.c.orderdate,purchaseorder.c.maxdate,purchaseorder.c.deliveryplaceaddr,purchaseorder.c.datedelivery,purchaseorder.c.modeoftransport,purchaseorder.c.packaging,purchaseorder.c.payterms,purchaseorder.c.productdetails,purchaseorder.c.tax,purchaseorder.c.csid]).where(purchaseorder.c.psflag == 16))
					po =[]
					for row in result:
						custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["csid"]))
						custrow = custdata.fetchone()
						po.append({"orderno": row["orderno"], "orderdate": datetime.strftime(row["orderdate"],'%d-%m-%Y'), "maxdate": datetime.strftime(row["maxdate"],'%d-%m-%Y'),  "deliveryplaceaddr": row["deliveryplaceaddr"], "datedelivery": datetime.strftime(row["datedelivery"],'%d-%m-%Y'), "modeoftransport": row["modeoftransport"],"packaging": row["packaging"], "payterms": row["payterms"],"csid": custrow["csid"],"productdetails": row["productdetails"],"tax": row["tax"]})
						
						return {"gkstatus":enumdict["Success"],"gkresult":po}
					
				
				if(psflag==20):
					
					result=self.con.execute(select([purchaseorder.c.orderno,purchaseorder.c.orderdate,purchaseorder.c.productdetails,purchaseorder.c.csid]).where(purchaseorder.c.psflag == 20))
					so =[]
					for row in result:
						custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["csid"]))
						custrow = custdata.fetchone()

						so.append({"oredrno":row["orderno"], "orderdate": datetime.strftime(row["orderdate"],'%d-%m-%Y'),"csid": custrow["csid"],"productdetails": row["productdetails"]})
					return {"gkstatus":enumdict["Success"], "gkresult":so}
					self.con.close()
				
				return {"gkstatus":enumdict["Success"],}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()
				
	
	@view_config(request_method='GET',request_param="single",renderer='json')
	def getSingleposo(self):
		"""
		THis function is to get single purchaseorder or salesorder, By matching parameters psflag and orderno 
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
				psflag =int(self.request.params["psflag"])
				if(psflag==16):
					
					result=self.con.execute(select([purchaseorder]).where(and_(purchaseorder.c.psflag == 16,purchaseorder.c.orderno==self.request.params["orderid"])))
					po =[]
					for row in result:
						custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["csid"]))
						custrow = custdata.fetchone()

						po.append({"orderdate": datetime.strftime(row["orderdate"],'%d-%m-%Y'), "maxdate": datetime.strftime(row["maxdate"],'%d-%m-%Y'),  "deliveryplaceaddr": row["deliveryplaceaddr"], "datedelivery": datetime.strftime(row["datedelivery"],'%d-%m-%Y'),"csid":custrow["csid"],"productdetails": row["productdetails"],"tax": row["tax"]})
						return {"gkstatus":enumdict["Success"],"gkresult":po}
						self.con.close()
				
				if(psflag==20):
					
					result=self.con.execute(select([purchaseorder]).where(and_(purchaseorder.c.psflag == 20,purchaseorder.c.orderid == self.request.params["orderid"])))
					so =[]
					for row in result:
						custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["csid"]))
						custrow = custdata.fetchone()

						so.append({ "orderdate": datetime.strftime(row["orderdate"],'%d-%m-%Y'),"csid":custrow["csid"],"productdetails": row["productdetails"]})
						return {"gkstatus":enumdict["Success"], "gkresult":so}
						self.con.close()
				
				return {"gkstatus":enumdict["Success"]}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
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
				result = self.con.execute(purchaseorder.delete().where(purchaseorder.c.orderno == dataset["orderid"]))
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
