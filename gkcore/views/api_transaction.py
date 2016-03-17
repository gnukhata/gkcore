


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
from gkcore.models.gkdb import vouchers, accounts
from sqlalchemy.sql import select
import json 
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ , between
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
	def addVoucher(self):
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
				result = con.execute(select([vouchers]).where(and_(vouchers.c.delflag==False, vouchers.c.vouchercode==voucherCode )) )
				row = result.fetchone()
				rawDr = dict(row["drs"])
				rawCr = dict(row["crs"])
				finalDR = {}
				finalCR = {}
				for d in rawDr.keys():
					accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(d)))
					account = accname.fetchone()
					finalDR[account["accountname"]] = rawDr[d]
				print finalDR
				
				for c in rawCr.keys():
					accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(c)))
					account = accname.fetchone()
					finalCR[account["accountname"]] = rawCr[c]
				print finalCR
				
				voucher = {"vouchercode":row["vouchercode"],"vouchernumber":row["vouchernumber"],"voucherdate":str(row["voucherdate"]),"entrydate":str(row["entrydate"]),"narration":row["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":row["prjdrs"],"prjcrs":row["prjcrs"],"vouchertype":row["vouchertype"],"delflag":row["delflag"],"orgcode":row["orgcode"]}
				return {"gkstatus":enumdict["Success"], "gkresult":voucher}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
			
	@view_config(request_method='GET',request_param='searchby=type', renderer='json')
	def searchByType(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails['auth'] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				voucherType = self.request.params["vouchertype"]
				vouchersData = con.execute(select([vouchers]).where(and_(vouchers.c.orgcode == authDetails['orgcode'],vouchers.c.vouchertype==voucherType,vouchers.c.delflag==False)))
				voucherRecords = []
				
				for voucher in vouchersData:
					rawDr = dict(voucher["drs"])
					rawCr = dict(voucher["crs"])
					finalDR = {}
					finalCR = {}	
					for d in rawDr.keys():
						accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(d)))
						account = accname.fetchone()
						finalDR[account["accountname"]] = rawDr[d]
					print finalDR
					
					for c in rawCr.keys():
						accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(c)))
						account = accname.fetchone()
						finalCR[account["accountname"]] = rawCr[c]
					print finalCR
					
					voucherRecords.append({"vouchercode":voucher["vouchercode"],"vouchernumber":voucher["vouchernumber"],"voucherdate":str(voucher["voucherdate"]),"entrydate":str(voucher["entrydate"]),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"]})
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

				
	@view_config(request_method='GET',request_param='searchby=vnum', renderer='json')
	def searchByVoucherNumber(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails['auth'] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				voucherNo = self.request.params["voucherno"]
				vouchersData = con.execute(select([vouchers]).where(and_(vouchers.c.orgcode == authDetails['orgcode'],vouchers.c.vouchernumber==voucherNo,vouchers.c.delflag==False)))
				voucherRecords = []
				
				for voucher in vouchersData:
					rawDr = dict(voucher["drs"])
					rawCr = dict(voucher["crs"])
					finalDR = {}
					finalCR = {}	
					for d in rawDr.keys():
						accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(d)))
						account = accname.fetchone()
						finalDR[account["accountname"]] = rawDr[d]
					print finalDR
					
					for c in rawCr.keys():
						accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(c)))
						account = accname.fetchone()
						finalCR[account["accountname"]] = rawCr[c]
					print finalCR
					
					voucherRecords.append({"vouchercode":voucher["vouchercode"],"vouchernumber":voucher["vouchernumber"],"voucherdate":str(voucher["voucherdate"]),"entrydate":str(voucher["entrydate"]),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"]})
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_method='GET',request_param='searchby=amount', renderer='json')
	def searchByAmount(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails['auth'] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				voucherAmount = self.request.params["total"]
				print voucherAmount
				vouchersData = con.execute(select([vouchers.c.vouchercode,vouchers.c.drs]).where(and_(vouchers.c.orgcode == authDetails['orgcode'],vouchers.c.delflag==False)))
				voucherRecords = []
				
				for vr in vouchersData:
					total = 0.00
					drs = dict(vr["drs"])
					for d in drs.keys():
						total = total + float(drs[d])
					print total
					if total==float(voucherAmount):
						voucherDetailsData = con.execute(select([vouchers]).where(vouchers.c.vouchercode == vr["vouchercode"]))
						voucher = voucherDetailsData.fetchone()
						rawDr = dict(voucher["drs"])
						rawCr = dict(voucher["crs"])
						finalDR = {}
						finalCR = {}	
						for d in rawDr.keys():
							accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(d)))
							account = accname.fetchone()
							finalDR[account["accountname"]] = rawDr[d]
						print finalDR
						
						for c in rawCr.keys():
							accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(c)))
							account = accname.fetchone()
							finalCR[account["accountname"]] = rawCr[c]
						print finalCR
						voucherRecords.append({"vouchercode":voucher["vouchercode"],"vouchernumber":voucher["vouchernumber"],"voucherdate":str(voucher["voucherdate"]),"entrydate":str(voucher["entrydate"]),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"]})
				
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_method='GET',request_param='searchby=date', renderer='json')
	def searchByDate(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails['auth'] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				fromDate = self.request.params["from"]
				toDate = self.request.params["to"]
				vouchersData = con.execute(select([vouchers]).where(and_(vouchers.c.orgcode == authDetails['orgcode'], between(vouchers.c.voucherdate,fromDate,toDate),vouchers.c.delflag==False)))
				voucherRecords = []
				
				for voucher in vouchersData:
					rawDr = dict(voucher["drs"])
					rawCr = dict(voucher["crs"])
					finalDR = {}
					finalCR = {}	
					for d in rawDr.keys():
						accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(d)))
						account = accname.fetchone()
						finalDR[account["accountname"]] = rawDr[d]
					print finalDR
					
					for c in rawCr.keys():
						accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(c)))
						account = accname.fetchone()
						finalCR[account["accountname"]] = rawCr[c]
					print finalCR
					
					voucherRecords.append({"vouchercode":voucher["vouchercode"],"vouchernumber":voucher["vouchernumber"],"voucherdate":str(voucher["voucherdate"]),"entrydate":str(voucher["entrydate"]),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"]})
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

				
	@view_config(request_method='GET',request_param='searchby=narration', renderer='json')
	def searchByNarration(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails['auth'] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				voucherNarration = self.request.params["nartext"]
				vouchersData = con.execute(select([vouchers]).where(and_(vouchers.c.orgcode == authDetails['orgcode'],vouchers.c.narration.like("%"+voucherNarration+"%"),vouchers.c.delflag==False)))
				voucherRecords = []
				
				for voucher in vouchersData:
					rawDr = dict(voucher["drs"])
					rawCr = dict(voucher["crs"])
					finalDR = {}
					finalCR = {}	
					for d in rawDr.keys():
						accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(d)))
						account = accname.fetchone()
						finalDR[account["accountname"]] = rawDr[d]
					print finalDR
					
					for c in rawCr.keys():
						accname = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(c)))
						account = accname.fetchone()
						finalCR[account["accountname"]] = rawCr[c]
					print finalCR
					
					voucherRecords.append({"vouchercode":voucher["vouchercode"],"vouchernumber":voucher["vouchernumber"],"voucherdate":str(voucher["voucherdate"]),"entrydate":str(voucher["entrydate"]),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"]})
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}


	@view_config(request_method='PUT', renderer='json')
	def updateVoucher(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				dataset = self.request.json_body()
				result = con.execute(vouchers.update().where(vouchers.c.vouchercode==dataset["vouchercode"]).values(dataset))
				return {"gkstatus":enumdict["Success"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
	@view_config(request_method='DELETE',renderer='json')
	def deleteVoucher(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				eng.execute("update vouchers set delflag= true where vouchercode = %d"%(int(self.request.params["vouchercode"])))
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}