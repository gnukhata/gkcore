
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
from gkcore.models.gkdb import invoice, dcinv, delchal, stock
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
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
				items = invdataset["items"]
				invdataset["orgcode"] = authDetails["orgcode"]
				stockdataset["orgcode"] = authDetails["orgcode"]
				result = self.con.execute(invoice.insert(),[invdataset])
				if invdataset.has_key("dcid"):
					if result.rowcount == 1:
						result = self.con.execute(select([invoice.c.invid]).where(and_(invoice.c.custid==invdataset["custid"], invoice.c.invoiceno==invdataset["invoiceno"])))
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
						for item in items.keys():
							stockdataset["productcode"] = item
							stockdataset["qty"] = items[item].values()[0]
							stockdataset["stockflag"] = "9"
							result = self.con.execute(stock.insert(),[stockdataset])
						return {"gkstatus":enumdict["Success"]}
					except:
						result = self.con.execute(stock.delete().where(and_(stock.c.dcinvid==invdataset["invid"],stock.c.stockflag==9)))
						result = self.con.execute(invoice.delete().where(invoice.c.invid==invdataset["invid"]))

			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				result = self.con.execute(invoice.delete().where(invoice.c.invid==dataset["invid"]))
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
				dataset = self.request.json_body
				result = self.con.execute(invoice.update().where(invoice.c.invid==dataset["invid"]).values(dataset))
				return {"gkstatus":enumdict["Success"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_method='GET', renderer ='json')
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
                        result = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==custid["custid"]))
                        custname = result.fetchone()
                        invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"], "invoicedate":row["invoicedate"],"custname":custid["custname"]})
                    else:
                        result = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["custid"]))
                        custname = result.fetchone()
                        invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"], "invoicedate":row["invoicedate"],"custname":custid["custname"]})
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
				result = self.con.execute(invoice.delete().where(invoice.c.invid==dataset["invid"]))
				result = self.con.execute(stock.delete().where(and_(stock.c.dcinvid==dataset["invid"],stock.c.stockflag==9)))
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
