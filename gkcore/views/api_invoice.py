
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


from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice, dcinv, delchal, stock, product, customerandsupplier
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from datetime import datetime,date
import jwt
import gkcore
from gkcore.views.api_login import authCheck

@view_defaults(route_name='invoice')
class api_invoice(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection

	@view_config(request_method='POST',renderer='json')
	def addinvoice(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dtset = self.request.json_body
				dcinvdataset={}
				invdataset = dtset["invoice"]
				stockdataset = dtset["stock"]
				items = invdataset["contents"]
				invdataset["orgcode"] = authDetails["orgcode"]
				stockdataset["orgcode"] = authDetails["orgcode"]
				result = self.con.execute(invoice.insert(),[invdataset])
				if invdataset.has_key("dcid"):
					if result.rowcount == 1:
						result = self.con.execute(select([invoice.c.invid]).where(and_(invoice.c.custid==invdataset["custid"], invoice.c.invoiceno==invdataset["invoiceno"],invoice.c.orgcode==invdataset["orgcode"],invoice.c.icflag==9)))
						invoiceid = result.fetchone()
						dcinvdataset["dcid"]=invdataset["dcid"]
						dcinvdataset["invid"]=invoiceid["invid"]
						dcinvdataset["orgcode"]=invdataset["orgcode"]
						result = self.con.execute(dcinv.insert(),[dcinvdataset])
						if result.rowcount ==1:
							return {"gkstatus":enumdict["Success"]}
					else:
						return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
				else:
					try:
						if invdataset.has_key('icflag'):
							result = self.con.execute(select([invoice.c.invid]).where(and_(invoice.c.invoiceno==invdataset["invoiceno"],invoice.c.orgcode==invdataset["orgcode"],invoice.c.icflag==invdataset["icflag"])))
							invoiceid = result.fetchone()
							stockdataset["dcinvtnid"] = invoiceid["invid"]
							for item in items.keys():
								stockdataset["productcode"] = item
								stockdataset["qty"] = items[item].values()[0]
								stockdataset["dcinvtnflag"] = "3"
								result = self.con.execute(stock.insert(),[stockdataset])
							return {"gkstatus":enumdict["Success"]}
						else:
							result = self.con.execute(select([invoice.c.invid]).where(and_(invoice.c.custid==invdataset["custid"], invoice.c.invoiceno==invdataset["invoiceno"],invoice.c.orgcode==invdataset["orgcode"],invoice.c.icflag==9)))
							invoiceid = result.fetchone()
							stockdataset["dcinvtnid"] = invoiceid["invid"]
							for item in items.keys():
								stockdataset["productcode"] = item
								stockdataset["qty"] = items[item].values()[0]
								stockdataset["dcinvtnflag"] = "9"
								result = self.con.execute(stock.insert(),[stockdataset])
							return {"gkstatus":enumdict["Success"]}
					except:
						result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==invoiceid["invid"],stock.c.dcinvtnflag==9)))
						result = self.con.execute(invoice.delete().where(invoice.c.invid==invoiceid["invid"]))
						return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_method='PUT', renderer='json')
	def editinvoice(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dtset = self.request.json_body
				dcinvdataset={}
				invdataset = dtset["invoice"]
				stockdataset = dtset["stock"]
				items = invdataset["contents"]
				invdataset["orgcode"] = authDetails["orgcode"]
				stockdataset["orgcode"] = authDetails["orgcode"]
				result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==invdataset["invid"],stock.c.dcinvtnflag==9)))
				result = self.con.execute(dcinv.delete().where(dcinv.c.invid==invdataset["invid"]))
				if invdataset.has_key("dcid"):
					dcid = invdataset.pop("dcid")
					result = self.con.execute(invoice.update().where(invoice.c.invid==invdataset["invid"]).values(invdataset))
					invdataset["dcid"] = dcid
					if result.rowcount == 1:
						dcinvdataset["dcid"]=invdataset["dcid"]
						dcinvdataset["orgcode"]=invdataset["orgcode"]
						dcinvdataset["invid"]=invdataset["invid"]
						result = self.con.execute(dcinv.insert(),[dcinvdataset])
						return {"gkstatus":enumdict["Success"]}
					else:
						return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
				else:
					try:
						result = self.con.execute(invoice.update().where(invoice.c.invid==invdataset["invid"]).values(invdataset))
						result = self.con.execute(select([invoice.c.invid]).where(and_(invoice.c.custid==invdataset["custid"], invoice.c.invoiceno==invdataset["invoiceno"])))
						invoiceid = result.fetchone()
						stockdataset["dcinvtnid"] = invoiceid["invid"]
						for item in items.keys():
							stockdataset["productcode"] = item
							stockdataset["qty"] = items[item].values()[0]
							stockdataset["dcinvtnflag"] = "9"
							result = self.con.execute(stock.insert(),[stockdataset])
						return {"gkstatus":enumdict["Success"]}
					except:
						result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==invoiceid["invid"],stock.c.dcinvtnflag==9)))
						result = self.con.execute(invoice.delete().where(invoice.c.invid==invoiceid["invid"]))
						return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				result = self.con.execute(invoice.delete().where(invoice.c.invid==dataset["invid"]))
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()


	@view_config(request_method='GET',request_param="inv=single", renderer ='json')
	def getInvoiceDetails(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dataset = self.request.params["invid"]
				result = self.con.execute(select([invoice]).where(invoice.c.invid==dataset))
				row = result.fetchone()
				items = row["contents"]
				if row["icflag"]==3:
					invc = {"taxstate":row["taxstate"],"cancelflag":row["cancelflag"]}
					if row["cancelflag"]==1:
						invc["canceldate"] = datetime.strftime(row["canceldate"],'%d-%m-%Y')
					invc["invoiceno"]=row["invoiceno"]
					invc["invid"]=row["invid"]
					invc["invoicedate"]=datetime.strftime(row["invoicedate"],'%d-%m-%Y')
				else:
					invc = {"issuername":row["issuername"],"designation":row["designation"],"taxstate":row["taxstate"],"cancelflag":row["cancelflag"]}
					if row["cancelflag"]==1:
						invc["canceldate"] = datetime.strftime(row["canceldate"],'%d-%m-%Y')
					if row["custid"] == None:
						result = self.con.execute(select([dcinv.c.dcid]).where(dcinv.c.invid==row["invid"]))
						dcid = result.fetchone()
						result = self.con.execute(select([delchal.c.custid,delchal.c.dcno]).where(delchal.c.dcid==dcid["dcid"]))
						dcnocustid = result.fetchone()
						result = self.con.execute(select([customerandsupplier.c.custid,customerandsupplier.c.custname,customerandsupplier.c.state,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==dcnocustid["custid"]))
						custname = result.fetchone()
						invc["invoiceno"]=row["invoiceno"]
						invc["invid"]=row["invid"]
						invc["dcid"]=dcid["dcid"]
						invc["dcno"]=dcnocustid["dcno"]
						invc["invoicedate"]=datetime.strftime(row["invoicedate"],'%d-%m-%Y')
						invc["custname"]=custname["custname"]
						invc["custid"]=custname["custid"]
						invc["state"]=custname["state"]
						invc["csflag"]=custname["csflag"]
					else:
						result = self.con.execute(select([customerandsupplier.c.custid,customerandsupplier.c.custname,customerandsupplier.c.state,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==row["custid"]))
						custname = result.fetchone()
						invc["invoiceno"]=row["invoiceno"]
						invc["invid"]=row["invid"]
						invc["orderid"]=row["orderid"]
						invc["invoicedate"]=datetime.strftime(row["invoicedate"],'%d-%m-%Y')
						invc["custname"]=custname["custname"]
						invc["custid"]=custname["custid"]
						invc["state"]=custname["state"]
						invc["csflag"]=custname["csflag"]
				for item in items.keys():
					result = self.con.execute(select([product.c.productdesc]).where(product.c.productcode==item))
					productname = result.fetchone()
					items[item]= {"priceperunit":items[item].keys()[0],"qty":items[item][items[item].keys()[0]],"productdesc":productname["productdesc"],"taxamount":row["tax"][item]}
				invc["contents"] = items
				return {"gkstatus": gkcore.enumdict["Success"], "gkresult":invc }
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			finally:
				self.con.close()



	@view_config(request_method='GET',request_param="inv=all", renderer ='json')
	def getAllinvoices(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				result = self.con.execute(select([invoice.c.invoiceno,invoice.c.invid,invoice.c.invoicedate,invoice.c.custid]).where(invoice.c.orgcode==authDetails["orgcode"]).order_by(invoice.c.invoicedate))
				invoices = []
				for row in result:
					if row["custid"] == None:
						result = self.con.execute(select([dcinv.c.dcid]).where(dcinv.c.invid==row["invid"]))
						dcid = result.fetchone()
						result = self.con.execute(select([delchal.c.custid]).where(delchal.c.dcid==dcid["dcid"]))
						custid = result.fetchone()
						result = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==custid["custid"]))
						custname = result.fetchone()
						invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"],"custname":custname["custname"],"csflag":custname["csflag"],"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y')})
					else:
						result = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==row["custid"]))
						custname = result.fetchone()
						invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"],"custname":custname["custname"],"csflag":custname["csflag"],"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y')})
				return {"gkstatus": gkcore.enumdict["Success"], "gkresult":invoices }
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	@view_config(request_method='GET',request_param="cash=all", renderer ='json')
	def getAllcashmemos(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				result = self.con.execute(select([invoice.c.invoiceno,invoice.c.invid,invoice.c.invoicedate]).where(and_(invoice.c.orgcode==authDetails["orgcode"],invoice.c.icflag==3)).order_by(invoice.c.invoicedate))
				invoices = []
				for row in result:
					invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"],"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y')})
				return {"gkstatus": gkcore.enumdict["Success"], "gkresult":invoices }
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	@view_config(request_method='DELETE', renderer ='json')
	def deleteinvoice(self):
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
				dataset["canceldate"]=datetime.now().date()
				result = self.con.execute(invoice.update().where(invoice.c.invid==dataset["invid"]).values(dataset))
				if dataset["icflag"]==9:
					stockcancel = {"dcinvtnflag":90}
				else:
					stockcancel = {"dcinvtnflag":30}
				result = self.con.execute(stock.update().where(and_(stock.c.dcinvtnid==dataset["invid"],stock.c.dcinvtnflag==dataset["icflag"])).values(stockcancel))
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
