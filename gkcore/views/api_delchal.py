
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.

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
from gkcore.models.gkdb import delchal, stock, customerandsupplier, godown, product, unitofmeasurement, dcinv
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from datetime import datetime,date
import jwt
import gkcore
from gkcore.views.api_login import authCheck
from gkcore.views.api_user import getUserRole

@view_defaults(route_name='delchal')
class api_delchal(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection

	"""
	create method for delchal resource.
	stock table is also updated after delchal entry is made.
		-delchal id goes in dcinvtnid column of stock table.
		-dcinvtnflag column will be set to 4 for delivery challan entry.
	If stock table insert fails then the delchal entry will be deleted.
	"""
	@view_config(request_method='POST',renderer='json')
	def adddelchal(self):
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
				delchaldata = dataset["delchaldata"]
				stockdata = dataset["stockdata"]
				delchaldata["orgcode"] = authDetails["orgcode"]
				stockdata["orgcode"] = authDetails["orgcode"]
				if delchaldata["dcflag"]==19:
					delchaldata["issuerid"] = authDetails["userid"]
				result = self.con.execute(delchal.insert(),[delchaldata])

				if result.rowcount==1:
					dciddata = self.con.execute(select([delchal.c.dcid,delchal.c.dcdate]).where(and_(delchal.c.orgcode==authDetails["orgcode"],delchal.c.dcno==delchaldata["dcno"],delchal.c.custid==delchaldata["custid"])))
					dcidrow = dciddata.fetchone()
					stockdata["dcinvtnid"] = dcidrow["dcid"]
					stockdata["dcinvtnflag"] = 4
					stockdata["stockdate"] = dcidrow["dcdate"]
					items = stockdata.pop("items")
					try:
						for key in items.keys():
							stockdata["productcode"] = key
							stockdata["qty"] = items[key]
							result = self.con.execute(stock.insert(),[stockdata])

					except:
						result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==dcidrow["dcid"],stock.c.dcinvtnflag==4)))
						result = self.con.execute(delchal.delete().where(delchal.c.dcid==dcidrow["dcid"]))
						return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
					return {"gkstatus":enumdict["Success"]}
				else:
					return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }#
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_method='PUT', renderer='json')
	def editdelchal(self):
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
				delchaldata = dataset["delchaldata"]
				stockdata = dataset["stockdata"]
				delchaldata["orgcode"] = authDetails["orgcode"]
				stockdata["orgcode"] = authDetails["orgcode"]
				stockdata["dcinvtnid"] = delchaldata["dcid"]
				stockdata["stockdate"] = dcidrow["dcdate"]
				stockdata["dcinvtnflag"] = 4
				result = self.con.execute(delchal.update().where(delchal.c.dcid==delchaldata["dcid"]).values(delchaldata))
				if result.rowcount==1:
					result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==delchaldata["dcid"],stock.c.dcinvtnflag==4)))
					items = stockdata.pop("items")
					for key in items.keys():
						stockdata["productcode"] = key
						stockdata["qty"] = items[key]
						result = self.con.execute(stock.insert(),[stockdata])
					return {"gkstatus":enumdict["Success"]}
				else:
					return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_method='GET',request_param="delchal=all", renderer ='json')
	def getAlldelchal(self):
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
				result = self.con.execute(select([delchal.c.dcid,delchal.c.dcno,delchal.c.custid,delchal.c.dcdate, delchal.c.noofpackages, delchal.c.modeoftransport, delchal.c.attachmentcount]).where(delchal.c.orgcode==authDetails["orgcode"]).order_by(delchal.c.dcno))
				delchals = []
				for row in result:
					custdata = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==row["custid"]))
					custrow = custdata.fetchone()
					delchals.append({"dcid":row["dcid"],"dcno":row["dcno"],"custname":custrow["custname"],"csflag":custrow["csflag"],"dcdate":datetime.strftime(row["dcdate"],'%d-%m-%Y'), "attachmentcount":row["attachmentcount"]})
				return {"gkstatus": gkcore.enumdict["Success"], "gkresult":delchals }
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_method='GET',request_param="delchal=single", renderer ='json')
	def getdelchal(self):
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
				result = self.con.execute(select([delchal]).where(delchal.c.dcid==self.request.params["dcid"]))
				delchaldata = result.fetchone()
				custdata = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.state]).where(customerandsupplier.c.custid==delchaldata["custid"]))
				custname = custdata.fetchone()
				items = {}
				if delchaldata["cancelflag"]==1:
					flag = 40
				else:
					flag = 4
				stockdata = self.con.execute(select([stock.c.productcode,stock.c.qty,stock.c.inout,stock.c.goid]).where(and_(stock.c.dcinvtnflag==flag,stock.c.dcinvtnid==self.request.params["dcid"])))
				for stockrow in stockdata:
					productdata = self.con.execute(select([product.c.productdesc,product.c.uomid]).where(product.c.productcode==stockrow["productcode"]))
					productdesc = productdata.fetchone()
					uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productdesc["uomid"]))
					unitnamrrow = uomresult.fetchone()
					items[stockrow["productcode"]] = {"qty":"%.2f"%float(stockrow["qty"]),"productdesc":productdesc["productdesc"],"unitname":unitnamrrow["unitname"]}
					stockinout = stockrow["inout"]
					goiddata = stockrow["goid"]
				singledelchal = {"delchaldata":{
									"dcid":delchaldata["dcid"],
									"dcno":delchaldata["dcno"],
									"dcflag":delchaldata["dcflag"],
									"issuername":delchaldata["issuername"],
									"designation":delchaldata["designation"],
									"dcdate":datetime.strftime(delchaldata["dcdate"],'%d-%m-%Y'),
									"custid":delchaldata["custid"],"custname":custname["custname"],
									"custstate":custname["state"],
									"cancelflag":delchaldata["cancelflag"],
									"noofpackages":delchaldata["noofpackages"],
									"modeoftransport": delchaldata["modeoftransport"],
									"attachmentcount": delchaldata["attachmentcount"]
									},
								"stockdata":{
									"inout":stockinout,"items":items
									}}
				if delchaldata["cancelflag"] ==1:
					singledelchal["delchaldata"]["canceldate"] = datetime.strftime(delchaldata["canceldate"],'%d-%m-%Y')

				if goiddata!=None:
					godata = self.con.execute(select([godown.c.goname,godown.c.state]).where(godown.c.goid==goiddata))
					goname = godata.fetchone()
					singledelchal["delchaldata"]["goid"]=goiddata
					singledelchal["delchaldata"]["goname"]=goname["goname"]
					singledelchal["delchaldata"]["gostate"]=goname["state"]
				return {"gkstatus": gkcore.enumdict["Success"], "gkresult":singledelchal }
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_param="delchal=last",request_method='GET',renderer='json')
	def getLastDelChalDetails(self):
		try:
			"""
			Purpose:
			returns a last created note no. of Deliverychallan.
			Returns a json dictionary containing that Deliverychallan.
			"""
			token = self.request.headers['gktoken']
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				deliverychallandata = {"dcdate": "","dcno":""}
				dcstatus = int(self.request.params["status"])
				result = self.con.execute(select([delchal.c.dcno,delchal.c.dcdate]).where(delchal.c.dcid==(select([func.max(stock.c.dcinvtnid)]).where(and_(stock.c.inout==dcstatus,stock.c.dcinvtnflag==4,stock.c.orgcode==authDetails["orgcode"] )))) )
				row = result.fetchone()
				if row != None:
					deliverychallandata["dcdate"] = datetime.strftime((row["dcdate"]),"%d-%m-%Y")
					deliverychallandata["dcno"] = row["dcno"]
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult":deliverychallandata}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_method='GET',request_param='attach=image', renderer='json')
	def getattachment(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails['auth'] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
				dcid = self.request.params["dcid"]
				delchalData = self.con.execute(select([delchal.c.dcno, delchal.c.attachment,delchal.c.cancelflag]).where(and_(delchal.c.dcid == dcid)))
				attachment = delchalData.fetchone()
				return {"gkstatus":enumdict["Success"],"gkresult":attachment["attachment"], "dcno": attachment["dcno"], "cancelflag":attachment["cancelflag"],"userrole":urole["userrole"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	@view_config(request_method='DELETE', renderer ='json')
	def deleteDelchal(self):
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
				result = self.con.execute(delchal.update().where(delchal.c.dcid==dataset["dcid"]).values(dataset))
				stockcancel = {"dcinvtnflag":40}
				result = self.con.execute(stock.update().where(and_(stock.c.dcinvtnid==dataset["dcid"],stock.c.dcinvtnflag==4)).values(stockcancel))
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_method='GET',request_param='action=getdcinvprods', renderer='json')
	def getdcinvproducts(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails['auth'] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			#try:
				self.con = eng.connect()
				dcid = self.request.params["dcid"]
				items = {}
				stockdata = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.dcinvtnflag == 4, stock.c.dcinvtnid == dcid)))
				for stockrow in stockdata:
					productdata = self.con.execute(select([product.c.productdesc,product.c.uomid]).where(product.c.productcode==stockrow["productcode"]))
					productdesc = productdata.fetchone()
					uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productdesc["uomid"]))
					unitnamrrow = uomresult.fetchone()
					print "type of productcode"
					print type(stockrow["productcode"])
					items[stockrow["productcode"]] = {"qty":float("%.2f"%float(stockrow["qty"])),"productdesc":productdesc["productdesc"],"unitname":unitnamrrow["unitname"]}
				result = self.con.execute(select([dcinv.c.invid, dcinv.c.invprods]).where(dcinv.c.dcid == dcid))
				linkedinvoices = result.fetchall()
				#linkedinvoices refers to the invoices which are associated with the delivery challan whose id = dcid.
				for invoice in linkedinvoices:
					invprods = invoice[1]
					print type(invprods)
					try:
						for productcode in invprods.keys():
							print type(productcode)
							print type(items[int(productcode)]["qty"])
							print type(invprods[productcode])
							items[int(productcode)]["qty"] -= float(invprods[productcode])
					except:
						pass
				if len(linkedinvoices) != 0:
					for productcode in items.keys():
						if items[productcode]["qty"] == 0:
							del items[productcode]
				return {"gkstatus":enumdict["Success"], "gkresult": items}
			#except:
			#	return {"gkstatus":enumdict["ConnectionFailed"]}
			#finally:
				self.con.close()
