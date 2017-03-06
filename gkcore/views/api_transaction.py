
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
"Vanita Rajpurohit" <vanita.rajpurohit9819@gmail.com>
"""


from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.views.api_user import getUserRole
from gkcore.models.gkdb import vouchers, accounts, groupsubgroups, bankrecon, voucherbin, projects
from sqlalchemy.sql import select
from sqlalchemy import func
import json
from gkcore.views.api_user import getUserRole
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ , between, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result
from datetime import datetime
import base64
from PIL import Image




@view_defaults(route_name='transaction')
class api_transaction(object):
	"""
	This class is the resource to create, update, read and delete vouchers (transactions)	connection rules:
	con is used for executing sql expression language based queries,
	while eng is used for raw sql execution.
	routing mechanism:
	@view_defaults is used for setting the default route for crud on the given resource class.
	if specific route is to be attached to a certain method, overriding view_default, , or for giving get, post, put, delete methods to default route, the view_config decorator is used.
	For other predicates view_config is generally used.
	If there are more than one methods with get as the request_method, then other predicates like request_param will be used for routing request to that method.
	"""
	def __init__(self,request):
		"""
		Initialising the request object which gets the data from client.
		"""
		self.request = Request
		self.request = request
		self.con = Connection


	@view_config(request_method='POST',renderer='json')
	def addVoucher(self):
		"""
		Purpose:
		adds a new voucher for given organisation and returns success as gkstatus if adding is successful.
		Description:
		Adds a voucher into the voucher table.
		Method uses the route given in view_default while post in request_method of view_config implies create.
		The method gets request which has json_body containing:
		*voucher number
		*entry date (default as current date )
		* voucher date,
		* narration
		* Drs json object containing dr accounts as keys and their respective Dr amount as values.
		* project Drs (currently null) as well as project Crs.
		* project name if any,
		* voucher type,
		* attachment (to be implemented)
		* lockflag default False,
		* del flag default False
		After voucher is added using insert query, the vouchercount for given accounts will be incremented by 1.
		since there will be at least 2 accounts in a transaction (minimum 1 each for Dr and Cr),
		We will run a loop on the dictionary for accountcode and amounts both for Dr and Cr dicts.
		And for each account code we will fire update query.
		As usual the checking for jwt in request headers will be first done only then the code will procede.
		"""

		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dataset = self.request.json_body
				dataset["orgcode"] = authDetails["orgcode"]
				drs = dataset["drs"]
				crs = dataset["crs"]
				result = self.con.execute(vouchers.insert(),[dataset])
				for drkeys in drs.keys():
					self.con.execute("update accounts set vouchercount = vouchercount +1 where accountcode = %d"%(int(drkeys)))
					accgrpdata = self.con.execute(select([groupsubgroups.c.groupname,groupsubgroups.c.groupcode]).where(groupsubgroups.c.groupcode==(select([accounts.c.groupcode]).where(accounts.c.accountcode==int(drkeys)))))
					accgrp = accgrpdata.fetchone()
					if accgrp["groupname"] == "Bank":
						vouchercodedata = self.con.execute("select max(vouchercode) as vcode from vouchers")
						vouchercode =vouchercodedata.fetchone()
						recoresult = self.con.execute(bankrecon.insert(),[{"vouchercode":int(vouchercode["vcode"]),"accountcode":drkeys,"orgcode":authDetails["orgcode"]}])
				for crkeys in crs.keys():
					self.con.execute("update accounts set vouchercount = vouchercount +1 where accountcode = %d"%(int(crkeys)))
					accgrpdata = self.con.execute(select([groupsubgroups.c.groupname,groupsubgroups.c.groupcode]).where(groupsubgroups.c.groupcode==(select([accounts.c.groupcode]).where(accounts.c.accountcode==int(crkeys)))))
					accgrp = accgrpdata.fetchone()
					if accgrp["groupname"] == "Bank":
						vouchercodedata = self.con.execute("select max(vouchercode) as vcode from vouchers")
						vouchercode =vouchercodedata.fetchone()
						recoresult = self.con.execute(bankrecon.insert(),[{"vouchercode":int(vouchercode["vcode"]),"accountcode":crkeys,"orgcode":authDetails["orgcode"]}])
				self.con.close()
				return {"gkstatus":enumdict["Success"]}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param="details=last",request_method='GET',renderer='json')
	def getLastVoucherDetails(self):
		try:
			"""
			Purpose:
			gets a single voucher given it's voucher code.
			Returns a json dictionary containing that voucher.
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
				result = self.con.execute(select([vouchers.c.vouchernumber,vouchers.c.voucherdate]).where(vouchers.c.vouchercode==(select([func.max(vouchers.c.vouchercode)]).where(and_(vouchers.c.delflag==False, vouchers.c.vouchertype==self.request.params["type"],vouchers.c.orgcode==authDetails["orgcode"] )))) )
				row = result.fetchone()
				if row== None:
					voucher = {"vdate": "","vno":""}
				else:
					voucher = {"vdate": datetime.strftime((row["voucherdate"]),"%d-%m-%Y"),"vno":row["vouchernumber"]}
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult":voucher}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}




	@view_config(request_method='GET',renderer='json')
	def getVoucher(self):
		try:
			"""
			Purpose:
			gets a single voucher given it's voucher code.
			Returns a json dictionary containing that voucher.
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
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
				voucherCode = self.request.params["code"]
				result = self.con.execute(select([vouchers.c.vouchercode,vouchers.c.attachmentcount,vouchers.c.vouchernumber,vouchers.c.voucherdate,vouchers.c.narration,vouchers.c.drs,vouchers.c.crs,vouchers.c.prjcrs,vouchers.c.prjdrs,vouchers.c.vouchertype,vouchers.c.lockflag,vouchers.c.delflag,vouchers.c.projectcode,vouchers.c.orgcode,vouchers.c.invid]).where(and_(vouchers.c.delflag==False, vouchers.c.vouchercode==voucherCode )) )
				row = result.fetchone()
				rawDr = dict(row["drs"])
				rawCr = dict(row["crs"])
				finalDR = {}
				finalCR = {}
				for d in rawDr.keys():
					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(d)))
					account = accname.fetchone()
					finalDR[account["accountname"]] = rawDr[d]

				for c in rawCr.keys():
					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(c)))
					account = accname.fetchone()
					finalCR[account["accountname"]] = rawCr[c]

				if row["narration"]=="null":
					row["narration"] =""
				voucher = {"project":row["projectcode"],"vouchercode":row["vouchercode"],"attachmentcount":row["attachmentcount"],"vouchernumber":row["vouchernumber"],"voucherdate":datetime.strftime(row["voucherdate"],"%d-%m-%Y"),"narration":row["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":row["prjdrs"],"prjcrs":row["prjcrs"],"vouchertype":row["vouchertype"],"delflag":row["delflag"],"orgcode":row["orgcode"],"status":row["lockflag"],"invid":row["invid"]}
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult":voucher,"userrole":urole["userrole"]}
			except:
				self.con.close()
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
				self.con = eng.connect()
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
				voucherType = self.request.params["vouchertype"]
				vouchersData = self.con.execute(select([vouchers.c.vouchercode,vouchers.c.attachmentcount,vouchers.c.vouchernumber,vouchers.c.voucherdate,vouchers.c.narration,vouchers.c.drs,vouchers.c.crs,vouchers.c.prjcrs,vouchers.c.prjdrs,vouchers.c.vouchertype,vouchers.c.lockflag,vouchers.c.delflag,vouchers.c.projectcode,vouchers.c.orgcode]).where(and_(vouchers.c.orgcode == authDetails['orgcode'],func.lower(vouchers.c.vouchertype)==func.lower(voucherType),vouchers.c.delflag==False)).order_by(vouchers.c.voucherdate,vouchers.c.vouchercode))
				voucherRecords = []

				for voucher in vouchersData:
					rawDr = dict(voucher["drs"])
					rawCr = dict(voucher["crs"])
					finalDR = {}
					finalCR = {}
					tdr=0.00
					tcr=0.00
					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawDr.keys()[0])))
					account = accname.fetchone()

					if(len(rawDr)>1):
						drcount=account["accountname"]+" + "+str(len(rawDr)-1)

						for d in rawDr:

							tdr = tdr+float(rawDr[d])

						finalDR["%s"%(drcount)] = tdr
					else:
						finalDR[account["accountname"]]=rawDr[rawDr.keys()[0]]

					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawCr.keys()[0])))
					account = accname.fetchone()

					if(len(rawCr)>1):
						crcount=account["accountname"]+" + "+str(len(rawCr)-1)

						for d in rawCr:

							tcr = tcr+float(rawCr[d])
						finalCR["%s"%(crcount)] = tcr
					else:
						finalCR[account["accountname"]]=rawCr[rawCr.keys()[0]]
					if voucher["narration"]=="null":
						voucher["narration"]=""



					voucherRecords.append({"vouchercode":voucher["vouchercode"],"attachmentcount":voucher["attachmentcount"],"vouchernumber":voucher["vouchernumber"],"voucherdate":datetime.strftime(voucher["voucherdate"],"%d-%m-%Y"),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"],"status":voucher["lockflag"]})
				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords,"userrole":urole["userrole"]}
			except:
				self.con.close()
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
				self.con = eng.connect()
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
				voucherNo = self.request.params["voucherno"]
				vouchersData = self.con.execute(select([vouchers.c.vouchercode,vouchers.c.attachmentcount,vouchers.c.vouchernumber,vouchers.c.voucherdate,vouchers.c.narration,vouchers.c.drs,vouchers.c.crs,vouchers.c.prjcrs,vouchers.c.prjdrs,vouchers.c.vouchertype,vouchers.c.lockflag,vouchers.c.delflag,vouchers.c.projectcode,vouchers.c.orgcode]).where(and_(vouchers.c.orgcode == authDetails['orgcode'],func.lower(vouchers.c.vouchernumber)==func.lower(voucherNo),vouchers.c.delflag==False)).order_by(vouchers.c.voucherdate,vouchers.c.vouchercode))
				voucherRecords = []

				for voucher in vouchersData:
					rawDr = dict(voucher["drs"])
					rawCr = dict(voucher["crs"])
					finalDR = {}
					finalCR = {}
					tdr=0.00
					tcr=0.00
					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawDr.keys()[0])))
					account = accname.fetchone()

					if(len(rawDr)>1):
						drcount=account["accountname"]+" + "+str(len(rawDr)-1)

						for d in rawDr:

							tdr = tdr+float(rawDr[d])

						finalDR["%s"%(drcount)] = tdr
					else:
						finalDR[account["accountname"]]=rawDr[rawDr.keys()[0]]

					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawCr.keys()[0])))
					account = accname.fetchone()

					if(len(rawCr)>1):
						crcount=account["accountname"]+" + "+str(len(rawCr)-1)

						for d in rawCr:

							tcr = tcr+float(rawCr[d])
						finalCR["%s"%(crcount)] = tcr
					else:
						finalCR[account["accountname"]]=rawCr[rawCr.keys()[0]]
					if voucher["narration"]=="null":
						voucher["narration"]=""
					voucherRecords.append({"vouchercode":voucher["vouchercode"],"attachmentcount":voucher["attachmentcount"],"vouchernumber":voucher["vouchernumber"],"voucherdate":datetime.strftime(voucher["voucherdate"],"%d-%m-%Y"),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"],"status":voucher["lockflag"]})
				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords,"userrole":urole["userrole"]}
			except:
				self.con.close()
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
				self.con = eng.connect()
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
				voucherAmount = self.request.params["total"]
				vouchersData = self.con.execute(select([vouchers.c.vouchercode,vouchers.c.drs]).where(and_(vouchers.c.orgcode == authDetails['orgcode'],vouchers.c.delflag==False)).order_by(vouchers.c.voucherdate,vouchers.c.vouchercode))
				voucherRecords = []

				for vr in vouchersData:
					total = 0.00
					drs = dict(vr["drs"])
					for d in drs.keys():
						total = total + float(drs[d])
					if total==float(voucherAmount):
						voucherDetailsData = self.con.execute(select([vouchers.c.vouchercode,vouchers.c.attachmentcount,vouchers.c.vouchernumber,vouchers.c.voucherdate,vouchers.c.narration,vouchers.c.drs,vouchers.c.crs,vouchers.c.prjcrs,vouchers.c.prjdrs,vouchers.c.vouchertype,vouchers.c.lockflag,vouchers.c.delflag,vouchers.c.projectcode,vouchers.c.orgcode]).where(vouchers.c.vouchercode == vr["vouchercode"]))
						voucher = voucherDetailsData.fetchone()
						rawDr = dict(voucher["drs"])
						rawCr = dict(voucher["crs"])
						finalDR = {}
						finalCR = {}
						tdr=0.00
						tcr=0.00
						accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawDr.keys()[0])))
						account = accname.fetchone()

						if(len(rawDr)>1):
							drcount=account["accountname"]+" + "+str(len(rawDr)-1)

							for d in rawDr:

								tdr = tdr+float(rawDr[d])

							finalDR["%s"%(drcount)] = tdr
						else:
							finalDR[account["accountname"]]=rawDr[rawDr.keys()[0]]

						accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawCr.keys()[0])))
						account = accname.fetchone()

						if(len(rawCr)>1):
							crcount=account["accountname"]+" + "+str(len(rawCr)-1)

							for d in rawCr:

								tcr = tcr+float(rawCr[d])
							finalCR["%s"%(crcount)] = tcr
						else:
							finalCR[account["accountname"]]=rawCr[rawCr.keys()[0]]
						if voucher["narration"]=="null":
							voucher["narration"]=""
						voucherRecords.append({"vouchercode":voucher["vouchercode"],"attachmentcount":voucher["attachmentcount"],"vouchernumber":voucher["vouchernumber"],"voucherdate":datetime.strftime(voucher["voucherdate"],"%d-%m-%Y"),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"],"status":voucher["lockflag"]})

				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords,"userrole":urole["userrole"]}
			except:
				self.con.close()
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
				self.con = eng.connect()
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
				fromDate = self.request.params["from"]
				toDate = self.request.params["to"]
				vouchersData = self.con.execute(select([vouchers.c.vouchercode,vouchers.c.attachmentcount,vouchers.c.vouchernumber,vouchers.c.voucherdate,vouchers.c.narration,vouchers.c.drs,vouchers.c.crs,vouchers.c.prjcrs,vouchers.c.prjdrs,vouchers.c.vouchertype,vouchers.c.lockflag,vouchers.c.delflag,vouchers.c.projectcode,vouchers.c.orgcode]).where(and_(vouchers.c.orgcode == authDetails['orgcode'], between(vouchers.c.voucherdate,fromDate,toDate),vouchers.c.delflag==False)).order_by(vouchers.c.voucherdate,vouchers.c.vouchercode))
				voucherRecords = []

				for voucher in vouchersData:
					rawDr = dict(voucher["drs"])
					rawCr = dict(voucher["crs"])
					finalDR = {}
					finalCR = {}
					tdr=0.00
					tcr=0.00
					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawDr.keys()[0])))
					account = accname.fetchone()

					if(len(rawDr)>1):
						drcount=account["accountname"]+" + "+str(len(rawDr)-1)

						for d in rawDr:

							tdr = tdr+float(rawDr[d])

						finalDR["%s"%(drcount)] = tdr
					else:
						finalDR[account["accountname"]]=rawDr[rawDr.keys()[0]]

					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawCr.keys()[0])))
					account = accname.fetchone()

					if(len(rawCr)>1):
						crcount=account["accountname"]+" + "+str(len(rawCr)-1)

						for d in rawCr:

							tcr = tcr+float(rawCr[d])
						finalCR["%s"%(crcount)] = tcr
					else:
						finalCR[account["accountname"]]=rawCr[rawCr.keys()[0]]
					if voucher["narration"]=="null":
						voucher["narration"]=""
					voucherRecords.append({"vouchercode":voucher["vouchercode"],"attachmentcount":voucher["attachmentcount"],"vouchernumber":voucher["vouchernumber"],"voucherdate":datetime.strftime(voucher["voucherdate"],"%d-%m-%Y"),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"],"status":voucher["lockflag"]})
				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords,"userrole":urole["userrole"]}
			except:
				self.con.close()
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
				self.con = eng.connect()
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
				voucherNarration = self.request.params["nartext"]
				vouchersData = self.con.execute(select([vouchers.c.vouchercode,vouchers.c.attachmentcount,vouchers.c.vouchernumber,vouchers.c.voucherdate,vouchers.c.narration,vouchers.c.drs,vouchers.c.crs,vouchers.c.prjcrs,vouchers.c.prjdrs,vouchers.c.vouchertype,vouchers.c.lockflag,vouchers.c.delflag,vouchers.c.projectcode,vouchers.c.orgcode]).where(and_(vouchers.c.orgcode == authDetails['orgcode'],func.lower(vouchers.c.narration).like("%"+func.lower(voucherNarration)+"%"),vouchers.c.delflag==False)).order_by(vouchers.c.voucherdate,vouchers.c.vouchercode))
				voucherRecords = []

				for voucher in vouchersData:
					rawDr = dict(voucher["drs"])
					rawCr = dict(voucher["crs"])
					finalDR = {}
					finalCR = {}
					tdr=0.00
					tcr=0.00
					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawDr.keys()[0])))
					account = accname.fetchone()

					if(len(rawDr)>1):
						drcount=account["accountname"]+" + "+str(len(rawDr)-1)

						for d in rawDr:

							tdr = tdr+float(rawDr[d])

						finalDR["%s"%(drcount)] = tdr
					else:
						finalDR[account["accountname"]]=rawDr[rawDr.keys()[0]]

					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(rawCr.keys()[0])))
					account = accname.fetchone()

					if(len(rawCr)>1):
						crcount=account["accountname"]+" + "+str(len(rawCr)-1)

						for d in rawCr:

							tcr = tcr+float(rawCr[d])
						finalCR["%s"%(crcount)] = tcr
					else:
						finalCR[account["accountname"]]=rawCr[rawCr.keys()[0]]
					if voucher["narration"]=="null":
						voucher["narration"]=""
					voucherRecords.append({"vouchercode":voucher["vouchercode"],"attachmentcount":voucher["attachmentcount"],"vouchernumber":voucher["vouchernumber"],"voucherdate":datetime.strftime(voucher["voucherdate"],"%d-%m-%Y"),"narration":voucher["narration"],"drs":finalDR,"crs":finalCR,"prjdrs":voucher["prjdrs"],"prjcrs":voucher["prjcrs"],"vouchertype":voucher["vouchertype"],"delflag":voucher["delflag"],"orgcode":voucher["orgcode"],"status":voucher["lockflag"]})
				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":voucherRecords,"userrole":urole["userrole"]}
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
				voucherCode = self.request.params["vouchercode"]
				vouchersData = self.con.execute(select([vouchers.c.attachment,vouchers.c.lockflag]).where(and_(vouchers.c.vouchercode == voucherCode)))
				attachment = vouchersData.fetchone()
				return {"gkstatus":enumdict["Success"],"gkresult":attachment["attachment"],"lockflag":attachment["lockflag"],"userrole":urole["userrole"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

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
				self.con = eng.connect()
				dataset = self.request.json_body
				result = self.con.execute(vouchers.update().where(vouchers.c.vouchercode==dataset["vouchercode"]).values(dataset))
				if dataset.has_key("drs"):
					drs = dataset["drs"]
					crs = dataset["crs"]
					delrecoresult = self.con.execute("delete from bankrecon where vouchercode = %d"%(int(dataset["vouchercode"])))
					for drkeys in drs.keys():
						accgrpdata = self.con.execute(select([groupsubgroups.c.groupname,groupsubgroups.c.groupcode]).where(groupsubgroups.c.groupcode==(select([accounts.c.groupcode]).where(accounts.c.accountcode==int(drkeys)))))
						accgrp = accgrpdata.fetchone()
						if accgrp["groupname"] == "Bank":
							vouchercode =dataset["vouchercode"]
							recoresult = self.con.execute(bankrecon.insert(),[{"vouchercode":int(vouchercode),"accountcode":drkeys,"orgcode":authDetails["orgcode"]}])
					for crkeys in crs.keys():
						accgrpdata = self.con.execute(select([groupsubgroups.c.groupname,groupsubgroups.c.groupcode]).where(groupsubgroups.c.groupcode==(select([accounts.c.groupcode]).where(accounts.c.accountcode==int(crkeys)))))
						accgrp = accgrpdata.fetchone()
						if accgrp["groupname"] == "Bank":
							vouchercode =dataset["vouchercode"]
							recoresult = self.con.execute(bankrecon.insert(),[{"vouchercode":int(vouchercode),"accountcode":crkeys,"orgcode":authDetails["orgcode"]}])
				self.con.close()
				return {"gkstatus":enumdict["Success"]}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
	@view_config(request_method='DELETE',renderer='json')
	def deleteVoucher(self):
		"""
		Purpose:
		Deletes a voucher given it's voucher code.
		Returns success if deletion is successful.
		Purpose:
		This function deletes a given voucher with it's vouchercode as input.
		After deleting the voucher, the vouchercount for the involved accounts on Dr and Cr side is decremented by 1.
		"""
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dataset  = self.request.json_body
				vcode = dataset["vouchercode"]
				voucherdata = self.con.execute(select([vouchers]).where(vouchers.c.vouchercode == int(vcode)))
				voucherRow = voucherdata.fetchone()
				self.con.execute("delete from vouchers  where vouchercode = %d"%(int(vcode)))
				DrData = voucherRow["drs"]
				CrData = voucherRow["crs"]
				for drKey in DrData.keys():
					self.con.execute("update accounts set vouchercount = vouchercount -1 where accountcode = %d"%(int(drKey)))
				for crKey in CrData.keys():
					self.con.execute("update accounts set vouchercount = vouchercount -1 where accountcode = %d"%(int(crKey)))
				finalCrs = {}
				finalDrs = {}
				projectNameData = self.con.execute(select([projects.c.projectname]).where(projects.c.projectcode==voucherRow["projectcode"]))
				prjNameRow = projectNameData.fetchone()
				if prjNameRow == None:
					projectName  = ""
				else:
					projectName = prjNameRow["projectname"]
				for d in DrData.keys():
					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(d)))
					account = accname.fetchone()
					finalDrs[account["accountname"]] = DrData[d]

				for c in CrData.keys():
					accname = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(c)))
					account = accname.fetchone()
					finalCrs[account["accountname"]] = CrData[c]
				voucherBinData = {"vouchercode":voucherRow["vouchercode"],"voucherdate":voucherRow["voucherdate"],"vouchernumber":voucherRow["vouchernumber"],"narration":voucherRow["narration"],"drs":finalDrs,"crs":finalCrs,"vouchertype":voucherRow["vouchertype"],"projectname":projectName,"orgcode":authDetails["orgcode"]}
				bin = self.con.execute(voucherbin.insert(),[voucherBinData])
				self.con.close()
				return {"gkstatus":enumdict["Success"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
