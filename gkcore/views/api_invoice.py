
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
"Mohd. Talha Pawaty" <mtalha456@gmail.com>
"Vaibhav Kurhe" <vaibhav.kurhe@gmail.com>
"Bhavesh Bawadhane" <bbhavesh07@gmail.com>
"""


from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice, dcinv, delchal, stock, product, customerandsupplier, unitofmeasurement, godown, rejectionnote
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
from gkcore.views.api_user import getUserRole

@view_defaults(route_name='invoice')
class api_invoice(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
	@view_config(request_method='POST',renderer='json')
	def addInvoice(self):
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
						dcinvdataset["invprods"] = stockdataset["items"]
						result = self.con.execute(dcinv.insert(),[dcinvdataset])
						if result.rowcount ==1:
							return {"gkstatus":enumdict["Success"],"gkresult":invoiceid["invid"]}
					else:
						return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
				else:
					try:
						if invdataset.has_key('icflag'):
							result = self.con.execute(select([invoice.c.invid,invoice.c.invoicedate]).where(and_(invoice.c.invoiceno==invdataset["invoiceno"],invoice.c.orgcode==invdataset["orgcode"],invoice.c.icflag==invdataset["icflag"])))
							invoiceid = result.fetchone()
							stockdataset["dcinvtnid"] = invoiceid["invid"]
							for item in items.keys():
								stockdataset["productcode"] = item
								stockdataset["qty"] = items[item].values()[0]
								stockdataset["dcinvtnflag"] = "3"
								stockdataset["stockdate"] = invoiceid["invoicedate"]
								result = self.con.execute(stock.insert(),[stockdataset])
							return {"gkstatus":enumdict["Success"],"gkresult":invoiceid["invid"]}
						else:
							result = self.con.execute(select([invoice.c.invid,invoice.c.invoicedate]).where(and_(invoice.c.custid==invdataset["custid"], invoice.c.invoiceno==invdataset["invoiceno"],invoice.c.orgcode==invdataset["orgcode"],invoice.c.icflag==9)))
							invoiceid = result.fetchone()
							stockdataset["dcinvtnid"] = invoiceid["invid"]
							stockdataset["stockdate"] = invoiceid["invoicedate"]
							for item in items.keys():
								stockdataset["productcode"] = item
								stockdataset["qty"] = items[item].values()[0]
								stockdataset["dcinvtnflag"] = "9"
								result = self.con.execute(stock.insert(),[stockdataset])
							return {"gkstatus":enumdict["Success"],"gkresult":invoiceid["invid"]}
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
	def editInvoice(self):
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
						result = self.con.execute(select([invoice.c.invid,invoice.c.invoicedate]).where(and_(invoice.c.custid==invdataset["custid"], invoice.c.invoiceno==invdataset["invoiceno"])))
						invoiceid = result.fetchone()
						stockdataset["dcinvtnid"] = invoiceid["invid"]
						stockdataset["stockdate"] = invoiceid["invoicedate"]
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
				result = self.con.execute(invoice.delete().where(invoice.c.invid==invdataset["invid"]))
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
	@view_config(request_method='PUT',request_param='type=bwa',renderer='json')
	def updatePayment(self):
		"""
		purpose: updates the total payed amount for a certain bill or invoice or puts it on account for custommer/supplyer.
		Description:
		The function will take invid and amount received.
		The function also takes a flag called payflag.
		This flag will have the value 1:advance,2:billwise,15:on-account.
		If payflag = 2 then function will update the invoice table,
		with the given amount by incrementing paydamount for the given invoice.
		Else the amount will be added to either advamce for value 1 and onaccamt for value 15,
		Both in customer table, which implies that csid must be needed.
There will be an icFlag which will determine if it's  an incrementing or decrement.
		"""
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
				payflag = int(self.request.params["payflag"])
				pdamt = float(self.request.params["pdamt"])
				if payflag == 1:
					icFlag =int( self.request.params["icflag"])
					custid = int(self.request.params["custid"])
					if icFlag == 9:
						result = self.con.execute("update customerandsupplier set advamt = advamt + %f where custid = %d"%(pdamt,custid))
					else:
						result = self.con.execute("update customerandsupplier set advamt = advamt - %f where custid = %d"%(pdamt,custid))
				if payflag == 15:
					icFlag = int(self.request.params["icflag"])
					custid = int(self.request.params["custid"])
					if icFlag == 9:
						result = self.con.execute("update customerandsupplier set onaccamt = onaccamt + %f where custid = %d"%(pdamt,custid))
					else:
						result = self.con.execute("update customerandsupplier set onaccamt = onaccamt - %f where custid = %d"%(pdamt,custid))
				if payflag == 2:
					invid = int(self.request.params["invid"])
					result = self.con.execute("update invoice set amountpaid = amountpaid + %f where invid = %d"%(pdamt,invid))
				return {"gkstatus":enumdict["Success"]}

			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
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
				freeitems = row["freeqty"]
				if row["icflag"]==3:
					invc = {"taxstate":row["taxstate"],"cancelflag":row["cancelflag"],"invoicetotal":"%.2f"%float(row["invoicetotal"]), "attachmentcount":row["attachmentcount"]}
					if row["cancelflag"]==1:
						invc["canceldate"] = datetime.strftime(row["canceldate"],'%d-%m-%Y')
					invc["invoiceno"]=row["invoiceno"]
					invc["invid"]=row["invid"]
					invc["invoicedate"]=datetime.strftime(row["invoicedate"],'%d-%m-%Y')
				else:
					invc = {"issuername":row["issuername"],"designation":row["designation"],"taxstate":row["taxstate"],"cancelflag":row["cancelflag"],"invoicetotal":"%.2f"%float(row["invoicetotal"]), "attachmentcount":row["attachmentcount"]}
					if row["cancelflag"]==1:
						invc["canceldate"] = datetime.strftime(row["canceldate"],'%d-%m-%Y')
					result = self.con.execute(select([dcinv.c.dcid]).where(dcinv.c.invid==row["invid"]))
					dcid = result.fetchone()
					if result.rowcount>0:
						result = self.con.execute(select([delchal.c.dcno]).where(delchal.c.dcid==dcid["dcid"]))
						dcnocustid = result.fetchone()
						result = self.con.execute(select([customerandsupplier.c.custid,customerandsupplier.c.custname,customerandsupplier.c.state,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==row["custid"]))
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
					result = self.con.execute(select([product.c.productdesc,product.c.uomid]).where(product.c.productcode==item))
					productname = result.fetchone()
					uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productname["uomid"]))
					unitnamrrow = uomresult.fetchone()
					items[item]= {"priceperunit":items[item].keys()[0],"qty":items[item][items[item].keys()[0]],"productdesc":productname["productdesc"],"taxamount":row["tax"][item],"unitname":unitnamrrow["unitname"]}
				invc["contents"] = items
				invc["freeqty"] = freeitems
				return {"gkstatus": gkcore.enumdict["Success"], "gkresult":invc }
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	@view_config(request_method='GET',request_param="type=bwa", renderer ='json')
	def getCSUPBills(self):
		"""
		Purpose: gets list of unpaid bills for a given customerandsupplier or supplier.
		Takes the person's id and returns a grid containing bills.
Apart from the bills it also returns customerandsupplier or supplyer name.
		Description:
		The function will take customerandsupplier or supplier id while orgcode is  taken from token.
		The invoice table will be scanned for all the bills concerning the party.
		If the total amount is greater than amountpaid(which is 0 by default ) then the bill qualifies to be returned.
		The function will return json object with gkstatus,csName:name of the party and gkresult:grid of bills.
The bills grid calld gkresult will return a list as it's value.
		The columns will be as follows:
		Bill no., Bill date, Customer/ supplier name,total amount and outstanding.
		the outstanding is calculated as total - amountpaid.
		"""
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
				unpaidBillsRecords = self.con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.custid,invoice.c.invoicetotal,invoice.c.amountpaid]).where(and_(invoice.c.custid == self.request.params["custid"],invoice.c.invoicetotal > invoice.c.amountpaid)))

				unpaidBills = unpaidBillsRecords.fetchall()
				bills = []
				for bill in unpaidBills:
					upb = {}
					upb["invid"] = bill["invid"]
					upb["invoiceno"] = bill["invoiceno"]
					upb["invoicedate"]=datetime.strftime(bill["invoicedate"],'%d-%m-%Y')
					upb["invoicetotal"] ="%.2f"%float(bill["invoicetotal"])
					upb["pendingamount"] = "%.2f"% (float(bill["invoicetotal"]) -  float(bill["amountpaid"]))
					bills.append(upb)
				custNameData = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid == self.request.params["custid"]))
				custnameRecord = custNameData.fetchone()
				csName = custnameRecord["custname"]
				gkresult = {"csname":csName,"unpaidbills":bills}
				return{"gkstatus":enumdict["Success"],"gkresult":gkresult}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
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
				result = self.con.execute(select([invoice.c.invoiceno,invoice.c.invid,invoice.c.invoicedate,invoice.c.custid,invoice.c.invoicetotal,invoice.c.attachmentcount]).where(and_(invoice.c.orgcode==authDetails["orgcode"],invoice.c.icflag==9)).order_by(invoice.c.invoicedate))
				invoices = []
				for row in result:
					result = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==row["custid"]))
					custname = result.fetchone()
					invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"],"custname":custname["custname"],"csflag":custname["csflag"],"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y'),"invoicetotal":"%.2f"%float(row["invoicetotal"]), "attachmentcount":row["attachmentcount"]})
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
				invid = self.request.params["invid"]
				invoiceData = self.con.execute(select([invoice.c.invoiceno, invoice.c.attachment,invoice.c.cancelflag]).where(and_(invoice.c.invid == invid)))
				attachment = invoiceData.fetchone()
				return {"gkstatus":enumdict["Success"],"gkresult":attachment["attachment"],"invoiceno":attachment["invoiceno"], "cancelflag":attachment["cancelflag"],"userrole":urole["userrole"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
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

	@view_config(request_method='GET', request_param="unbilled_delnotes", renderer ='json')
	def unbilled_delnotes(self):
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
				orgcode = authDetails["orgcode"]
				dataset = self.request.json_body
				inputdate = dataset["inputdate"]
				new_inputdate = dataset["inputdate"]
				new_inputdate = datetime.strptime(new_inputdate, "%Y-%m-%d")
				dc_unbilled = []
				alldcids = self.con.execute(select([delchal.c.dcid, delchal.c.dcdate]).distinct().where(and_(delchal.c.orgcode == orgcode, delchal.c.dcdate <= new_inputdate, stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 4, delchal.c.dcid == stock.c.dcinvtnid)).order_by(delchal.c.dcdate))
				alldcids = alldcids.fetchall()
				dcResult = []
				i = 0
				while(i < len(alldcids)):
					dcid = alldcids[i]
					invidresult = self.con.execute(select([dcinv.c.invid]).where(and_(dcid[0] == dcinv.c.dcid, dcinv.c.orgcode == orgcode, invoice.c.orgcode == orgcode, invoice.c.invid == dcinv.c.invid, invoice.c.invoicedate <= new_inputdate)))
					invidresult = invidresult.fetchall()
					if len(invidresult) == 0:
						dcprodresult = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 4, dcid[0] == stock.c.dcinvtnid)))
						dcprodresult = dcprodresult.fetchall()
						#This code is for rejection note
						#even if an invoice is not prepared and rejection note prepared for whole delivery note then it should not come into unbilled delivery note.
						allrnidres = self.con.execute(select([rejectionnote.c.rnid]).distinct().where(and_(rejectionnote.c.orgcode == orgcode, rejectionnote.c.rndate <= new_inputdate, rejectionnote.c.dcid == dcid[0])))
						allrnidres = allrnidres.fetchall()
						rnprodresult = []
						#get stock respected to all rejection notes
						for rnid in allrnidres:
							temp = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 18, stock.c.dcinvtnid == rnid[0])))
							temp = temp.fetchall()
							rnprodresult.append(temp)
						matchedproducts = []
						remainingproducts = {}
						totalqtyofdcprod = {}
						for eachitem in dcprodresult:
							totalqtyofdcprod.update({eachitem[0]:eachitem[1]})
						for row in rnprodresult:
							for prodc, qty in row:
								if prodc in remainingproducts:
									remainingproducts[prodc] = float(remainingproducts[prodc]) + float(qty)
									if float(remainingproducts[prodc]) >= float(totalqtyofdcprod[prodc]):
										matchedproducts.append(prodc)
										del remainingproducts[prodc]
								elif float(qty) >= float(totalqtyofdcprod[prodc]):
									matchedproducts.append(prodc)
								else:
									remainingproducts.update({prodc:float(qty)})
						if len(matchedproducts) == len(dcprodresult):
							#Now we have got the delchals, for which invoices are also sent completely.
							alldcids.remove(dcid)
							i-=1
					else:
						#invid's will be distinct only. So no problem to explicitly applying distinct clause.
						dcprodresult = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 4, dcid[0] == stock.c.dcinvtnid)))
						dcprodresult = dcprodresult.fetchall()
						#I am assuming :productcode must be distinct. So, I haven't applied distinct construct.
						#what if dcprodresult or invprodresult is empty?
						invprodresult = []
						for invid in invidresult:
							temp = self.con.execute(select([invoice.c.contents]).where(and_(invoice.c.orgcode == orgcode, invid == invoice.c.invid)))
							temp = temp.fetchall()
							#Below two lines are intentionally repeated. It's not a mistake.
							temp = temp[0]
							temp = temp[0]
							invprodresult.append(temp)
						#Now we have to compare the two results: dcprodresult and invprodresult
						#I assume that the delchal must have at most only one entry for a particular product. If not, then it's a bug and needs to be rectified.
						#But, in case of invprodresult, there can be more than one productcodes mentioned. This is because, with one delchal, there can be many invoices linked.
						matchedproducts = []
						remainingproducts = {}
						totalqtyofdcprod = {}
						for eachitem in dcprodresult:
						#dcprodresult is a list of tuples. eachitem is one such tuple.
							totalqtyofdcprod.update({eachitem[0]:eachitem[1]})
							for eachinvoice in invprodresult:
							#invprodresult is a list of dictionaries. eachinvoice is one such dictionary.
								for eachproductcode in eachinvoice.keys():
									#eachitem[0] is unique. It's not repeated.
									dcprodcode = eachitem[0]
									if int(dcprodcode) == int(eachproductcode):
										#this means that the product in delchal matches with the product in invoice
										#now we will check its quantity
										invqty = eachinvoice[eachproductcode].values()[0]
										dcqty = eachitem[1]
										if float(dcqty) == float(invqty):#conversion of datatypes to compatible ones is very important when comparing them.
											#this means the quantity of current individual product is matched exactly
											matchedproducts.append(int(eachproductcode))
										elif float(dcqty) > float(invqty):
											#this means current invoice has not billed the whole product quantity.
											if dcprodcode in remainingproducts.keys():
												if float(dcqty) == (float(remainingproducts[dcprodcode]) + float(invqty)):
													matchedproducts.append(int(eachproductcode))
													#whether we use eachproductcode or dcprodcode, doesn't matter. Because, both values are the same here.
													del remainingproducts[int(eachproductcode)]
												else:
													#It must not be the case that below addition is greater than dcqty.
													remainingproducts[dcprodcode] = (float(remainingproducts[dcprodcode]) + float(invqty))
											else:
												remainingproducts.update({dcprodcode:float(invqty)})
										else:
											#"dcqty < invqty" should never happen.
											# It could happen when multiple delivery chalans have only one invoice.
											pass

						#This code is for rejection note
						allrnidres = self.con.execute(select([rejectionnote.c.rnid]).distinct().where(and_(rejectionnote.c.orgcode == orgcode, rejectionnote.c.rndate <= new_inputdate, rejectionnote.c.dcid == dcid[0])))
						allrnidres = allrnidres.fetchall()
						rnprodresult = []
						#get stock respected to all rejection notes
						for rnid in allrnidres:
							temp = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 18, stock.c.dcinvtnid == rnid[0])))
							temp = temp.fetchall()
							rnprodresult.append(temp)
						for row in rnprodresult:
							for prodc, qty in row:
								if prodc in remainingproducts:
									remainingproducts[prodc] = float(remainingproducts[prodc]) + float(qty)
									if float(remainingproducts[prodc]) >= float(totalqtyofdcprod[prodc]):
										matchedproducts.append(prodc)
										del remainingproducts[prodc]

						if len(matchedproducts) == len(dcprodresult):
							#Now we have got the delchals, for which invoices are also sent completely.
							alldcids.remove(dcid)
							i-=1
					i+=1
					pass

				for eachdcid in alldcids:
					singledcResult = self.con.execute(select([delchal.c.dcid, delchal.c.dcno, delchal.c.dcdate, delchal.c.dcflag, customerandsupplier.c.custname, customerandsupplier.c.csflag, delchal.c.attachmentcount]).distinct().where(and_(delchal.c.orgcode == orgcode, customerandsupplier.c.orgcode == orgcode, eachdcid[0] == delchal.c.dcid, delchal.c.custid == customerandsupplier.c.custid, stock.c.dcinvtnflag == 4, eachdcid[0] == stock.c.dcinvtnid)))
					singledcResult = singledcResult.fetchone()
					dcResult.append(singledcResult)

				temp_dict = {}
				srno = 1
				if dataset["type"] == "invoice":
					for row in dcResult:
						temp_dict = {"dcid": row["dcid"], "srno": srno, "dcno":row["dcno"], "dcdate": datetime.strftime(row["dcdate"],"%d-%m-%Y"), "dcflag": row["dcflag"], "csflag": row["csflag"], "custname": row["custname"], "attachmentcount": row["attachmentcount"]}
						if temp_dict["dcflag"] == 19:
							#We don't have to consider sample.
							temp_dict["dcflag"] = "Sample"
						elif temp_dict["dcflag"]== 6:
							#we ignore this as well
							temp_dict["dcflag"] = "Free Replacement"
						if temp_dict["dcflag"] != "Sample" and temp_dict["dcflag"] !="Free Replacement":
							dc_unbilled.append(temp_dict)
							srno += 1
				else:
					#type=rejection note
					#Here even delivery type sample and free Replacement can also be rejected.
					for row in dcResult:
						temp_dict = {"dcid": row["dcid"], "srno": srno, "dcno":row["dcno"], "dcdate": datetime.strftime(row["dcdate"],"%d-%m-%Y"), "dcflag": row["dcflag"], "csflag": row["csflag"], "custname": row["custname"], "attachmentcount": row["attachmentcount"]}
						dc_unbilled.append(temp_dict)
						srno += 1
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult": dc_unbilled}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	'''This mehtod gives all invoices which are not fully rejected yet. It is used in rejection note, to prepare rejection note against these invoices'''
	@view_config(request_method='GET', request_param="type=nonrejected", renderer ='json')
	def nonRejected(self):
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
				orgcode = authDetails["orgcode"]
				dataset = self.request.json_body
				new_inputdate = dataset["inputdate"]
				new_inputdate = datetime.strptime(new_inputdate, "%Y-%m-%d")
				inv_nonrejected = []
				allinvids = self.con.execute(select([invoice.c.invid]).distinct().where(and_(invoice.c.orgcode == orgcode, invoice.c.invoicedate <= new_inputdate)))
				allinvids = allinvids.fetchall()
				i = 0
				while(i < len(allinvids)):
					invid = allinvids[i]
					invprodresult = []
					temp = self.con.execute(select([invoice.c.contents]).where(and_(invoice.c.orgcode == orgcode, invoice.c.invid == invid[0])))
					temp = temp.fetchall()
					invprodresult.append(temp[0][0])
					allrnidres = self.con.execute(select([rejectionnote.c.rnid]).distinct().where(and_(rejectionnote.c.orgcode == orgcode, rejectionnote.c.invid == invid[0])))
					allrnidres = allrnidres.fetchall()
					rnprodresult = []
					#get stock respected to all rejection notes
					for rnid in allrnidres:
						temp = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 18, stock.c.dcinvtnid == rnid[0])))
						temp = temp.fetchall()
						rnprodresult.append(temp)
					totalqtyofinvprod = {}
					for eachitem in invprodresult:
						for prodc in eachitem:
							totalqtyofinvprod.update({int(prodc):eachitem[prodc].values()[0]})
					for row in rnprodresult:
						for prodc, qty in row:
							if prodc in totalqtyofinvprod:
								totalqtyofinvprod[prodc] = float(totalqtyofinvprod[prodc]) - float(qty)
								if float(totalqtyofinvprod[prodc]) <= 0.00:
									del totalqtyofinvprod[prodc]
							else:
								pass
					if len(totalqtyofinvprod) == 0:
						allinvids.remove(invid)
						i-=1
					i+=1
				srno = 1
				for eachinvid in allinvids:
					singleinvResult = self.con.execute(select([invoice.c.invid, invoice.c.invoiceno, invoice.c.invoicedate, customerandsupplier.c.custname, customerandsupplier.c.csflag]).distinct().where(and_(invoice.c.orgcode == orgcode, customerandsupplier.c.orgcode == orgcode, eachinvid[0] == invoice.c.invid, invoice.c.custid == customerandsupplier.c.custid)))
					singleinvResult = singleinvResult.fetchone()
					temp_dict = {"invid": singleinvResult["invid"], "srno": srno, "invoiceno":singleinvResult["invoiceno"], "invoicedate": datetime.strftime(singleinvResult["invoicedate"],"%d-%m-%Y"), "csflag": singleinvResult["csflag"], "custname": singleinvResult["custname"]}
					inv_nonrejected.append(temp_dict)
					srno += 1
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult": inv_nonrejected}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_method='GET',request_param='type=nonrejectedinvprods', renderer='json')
	def nonRejectedInvProds(self):
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
				dataset = self.request.json_body
				invid = dataset["invid"]
				invprodresult = []
				orgcode = authDetails["orgcode"]
				temp = self.con.execute(select([invoice.c.contents]).where(and_(invoice.c.orgcode == orgcode, invoice.c.invid == invid)))
				temp = temp.fetchall()
				invprodresult.append(temp[0][0])
				items = {}
				for eachitem in invprodresult:
					for prodc in eachitem:
						productdata = self.con.execute(select([product.c.productdesc,product.c.uomid]).where(product.c.productcode==int(prodc)))
						productdesc = productdata.fetchone()
						uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productdesc["uomid"]))
						unitnamrrow = uomresult.fetchone()
						items[int(prodc)] = {"qty":float("%.2f"%float(eachitem[prodc].values()[0])),"productdesc":productdesc["productdesc"],"unitname":unitnamrrow["unitname"]}
				allrnidres = self.con.execute(select([rejectionnote.c.rnid]).distinct().where(and_(rejectionnote.c.orgcode == orgcode, rejectionnote.c.invid == invid)))
				allrnidres = allrnidres.fetchall()
				rnprodresult = []
				#get stock respected to all rejection notes
				for rnid in allrnidres:
					temp = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 18, stock.c.dcinvtnid == rnid[0])))
					temp = temp.fetchall()
					rnprodresult.append(temp)
				for row in rnprodresult:
					try:
						for prodc, qty in row:
							items[int(prodc)]["qty"] -= float(qty)
					except:
						pass
				for productcode in items.keys():
					if items[productcode]["qty"] == 0:
						del items[productcode]
				temp = self.con.execute(select([dcinv.c.dcid]).where(and_(dcinv.c.orgcode == orgcode, dcinv.c.invid == invid)))
				temp = temp.fetchone()
				dcdetails = {}
				custdata = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.custaddr, customerandsupplier.c.custtan]).where(customerandsupplier.c.custid.in_(select([invoice.c.custid]).where(invoice.c.invid==invid))))
				custname = custdata.fetchone()
				dcdetails = {"custname":custname["custname"], "custaddr": custname["custaddr"], "custtin":custname["custtan"]}
				if temp:
					result = self.con.execute(select([delchal]).where(delchal.c.dcid==temp[0]))
					delchaldata = result.fetchone()
					stockdata = self.con.execute(select([stock.c.goid]).where(and_(stock.c.dcinvtnflag==4,stock.c.dcinvtnid==temp[0])))
					stockdata = stockdata.fetchone()
					dcdetails = {"dcid":temp[0], "custname":custname["custname"], "custaddr": custname["custaddr"], "custtin":custname["custtan"], "goid":"", "goname":"", "gostate":"", "dcflag":delchaldata["dcflag"]}
					godata = self.con.execute(select([godown.c.goname,godown.c.state, godown.c.goaddr]).where(godown.c.goid==stockdata[0]))
					goname = godata.fetchone()
					dcdetails["goid"] = stockdata[0]
					dcdetails["goname"] = goname["goname"]
					dcdetails["gostate"] = goname["state"]
					dcdetails["goaddr"] = goname["goaddr"]
				return {"gkstatus":enumdict["Success"], "gkresult": items, "delchal": dcdetails}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()
