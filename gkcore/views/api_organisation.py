
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
from gkcore.models import gkdb
from sqlalchemy.sql import select, distinct
from sqlalchemy import func, desc
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
import jwt
import gkcore
from gkcore.models.meta import dbconnect


@view_defaults(route_name='organisations')
class api_organisation(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
		print "Organisation initialized"

	@view_config(request_method='GET', renderer ='json')
	def getOrgs(self):
		try:
			self.con=eng.connect()
			result = self.con.execute(select([gkdb.organisation.c.orgname, gkdb.organisation.c.orgtype]).order_by(gkdb.organisation.c.orgname).distinct())
			orgs = []
			for row in result:
				orgs.append({"orgname":row["orgname"], "orgtype":row["orgtype"]})
			self.con.close()
			return {"gkstatus":enumdict["Success"], "gkdata":orgs}
		except:
			self.con.close()
			return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(route_name='orgyears', request_method='GET', renderer ='json')
	def getYears(self):
		try:
			self.con = eng.connect()
			result = self.con.execute(select([gkdb.organisation.c.yearstart, gkdb.organisation.c.yearend,gkdb.organisation.c.orgcode]).where(and_(gkdb.organisation.c.orgname==self.request.matchdict["orgname"], gkdb.organisation.c.orgtype == self.request.matchdict["orgtype"])).order_by(desc(gkdb.organisation.c.yearend)))
			years = []
			for row in result:
				years.append({"yearstart":str(row["yearstart"]), "yearend":str(row["yearend"]),"orgcode":row["orgcode"]})
			self.con.close()
			return {"gkstatus":enumdict["Success"],"gkdata":years}
		except:
			self.con.close()
			return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_method='POST',renderer='json')
	def postOrg(self):

		try:
			self.con = eng.connect()
			dataset = self.request.json_body
			orgdata = dataset["orgdetails"]
			userdata = dataset["userdetails"]
			result = self.con.execute(gkdb.organisation.insert(),[orgdata])
			if result.rowcount==1:
				code = self.con.execute(select([gkdb.organisation.c.orgcode]).where(and_(gkdb.organisation.c.orgname==orgdata["orgname"], gkdb.organisation.c.orgtype==orgdata["orgtype"], gkdb.organisation.c.yearstart==orgdata["yearstart"], gkdb.organisation.c.yearend==orgdata["yearend"])))
				orgcode = code.fetchone()
				try:
					currentassets= {"groupname":"Current Assets","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),currentassets)
					result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Current Assets",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Bank","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Cash","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Inventory","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Loans & Advance","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Sundry Debtors","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]} ])

					currentliability= {"groupname":"Current Liabilities","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),currentliability)
					result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Current Liabilities",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Provisions","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Sundry Creditors for Expense","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Sundry Creditors for Purchase","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]}])

					directexpense= {"groupname":"Direct Expense","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),directexpense)

					directincome= {"groupname":"Direct Income","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),directincome)

					fixedassets= {"groupname":"Fixed Assets","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),fixedassets)
					result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Fixed Assets",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Building","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Furniture","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Land","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Plant & Machinery","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]} ])

					indirectexpense= {"groupname":"Indirect Expense","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),indirectexpense)

					indirectincome= {"groupname":"Indirect Income","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),indirectincome)

					investment= {"groupname":"Investments","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),investment)
					result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Investments",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Investment in Bank Deposits","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Investment in Shares & Debentures","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]}, ])

					loansasset= {"groupname":"Loans(Asset)","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),loansasset)

					loansliab= {"groupname":"Loans(Liability)","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),loansliab)
					result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Loans(Liability)",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Secured","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Unsecured","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]} ])

					reserves= {"groupname":"Reserves","orgcode":orgcode["orgcode"]}
					result = self.con.execute(gkdb.groupsubgroups.insert(),reserves)

					result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Direct Income",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					if orgdata["orgtype"] == "Profit Making":
						result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Capital","orgcode":orgcode["orgcode"]},{"groupname":"Miscellaneous Expenses(Asset)","orgcode":orgcode["orgcode"]}])

						result = self.con.execute(gkdb.accounts.insert(),{"accountname":"Profit & Loss","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]})

					else:
						result = self.con.execute(gkdb.groupsubgroups.insert(),{"groupname":"Corpus","orgcode":orgcode["orgcode"]})

						result = self.con.execute(gkdb.accounts.insert(),{"accountname":"Income & Expenditure","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]})

					result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Inventory",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = self.con.execute(gkdb.accounts.insert(),[{"accountname":"Closing Stock","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Stock at the Beginning","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]}])

					result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Direct Expense",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = self.con.execute(gkdb.accounts.insert(),{"accountname":"Opening Stock","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]})



					userdata["orgcode"] = orgcode["orgcode"]
					userdata["userrole"] = -1
					result = self.con.execute(gkdb.users.insert(),[userdata])
					if result.rowcount==1:
						result = self.con.execute(select([gkdb.users.c.userid]).where(and_(gkdb.users.c.username==userdata["username"], gkdb.users.c.userpassword== userdata["userpassword"], gkdb.users.c.orgcode==userdata["orgcode"])) )
						if result.rowcount == 1:
							record = result.fetchone()

							token = jwt.encode({"orgcode":userdata["orgcode"],"userid":record["userid"]},gkcore.secret,algorithm='HS256')
							self.con.close()
							return {"gkstatus":enumdict["Success"],"token":token }
						else:
							self.con.close()
							return {"gkstatus":enumdict["ConnectionFailed"]}
					else:
							self.con.close()
							return {"gkstatus":enumdict["ConnectionFailed"]}
				except:
					result = self.con.execute(gkdb.organisation.delete().where(gkdb.organisation.c.orgcode==orgcode["orgcode"]))
					self.con.close()
					return {"gkstatus":enumdict["ConnectionFailed"]}
			else:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
		except:
			self.con.close()
			return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(route_name='organisation', request_method='GET',renderer='json')
	def getOrg(self):
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
				result = self.con.execute(select([gkdb.organisation]).where(gkdb.organisation.c.orgcode==authDetails["orgcode"]))
				row = result.fetchone()
				if(row["orgcity"]==None):
					orgcity=""
				else:
					orgcity=row["orgcity"]

				if(row["orgaddr"]==None):
					orgaddr=""
				else:
					orgaddr=row["orgaddr"]

				if(row["orgpincode"]==None):
					orgpincode=""
				else:
					orgpincode=row["orgpincode"]

				if(row["orgstate"]==None):
					orgstate=""
				else:
					orgstate=row["orgstate"]

				if(row["orgcountry"]==None):
					orgcountry=""
				else:
					orgcountry=row["orgcountry"]

				if(row["orgtelno"]==None):
					orgtelno=""
				else:
					orgtelno=row["orgtelno"]

				if(row["orgfax"]==None):
					orgfax=""
				else:
					orgfax=row["orgfax"]

				if(row["orgwebsite"]==None):
					orgwebsite=""
				else:
					orgwebsite=row["orgwebsite"]

				if(row["orgemail"]==None):
					orgemail=""
				else:
					orgemail=row["orgemail"]

				if(row["orgpan"]==None):
					orgpan=""
				else:
					orgpan=row["orgpan"]

				if(row["orgmvat"]==None):
					orgmvat=""
				else:
					orgmvat=row["orgmvat"]

				if(row["orgstax"]==None):
					orgstax=""
				else:
					orgstax=row["orgstax"]

				if(row["orgregno"]==None):
					orgregno=""
				else:
					orgregno=row["orgregno"]

				if(row["orgregdate"]==None):
					orgregdate=""
				else:
					orgregdate=row["orgregdate"]

				if(row["orgfcrano"]==None):
					orgfcrano=""
				else:
					orgfcrano=row["orgfcrano"]

				if(row["orgfcradate"]==None):
					orgfcradate=""
				else:
					orgfcradate=row["orgfcradate"]


				orgDetails={"orgname":row["orgname"], "orgtype":row["orgtype"], "yearstart":str(row["yearstart"]), "yearend":str(row["yearend"]),"orgcity":orgcity, "orgaddr":orgaddr, "orgpincode":orgpincode, "orgstate":orgstate, "orgcountry":orgcountry, "orgtelno":orgtelno, "orgfax":orgfax, "orgwebsite":orgwebsite, "orgemail":orgemail, "orgpan":orgpan, "orgmvat":orgmvat, "orgstax":orgstax, "orgregno":orgregno, "orgregdate":orgregdate, "orgfcrano":orgfcrano, "orgfcradate":orgfcradate, "roflag":row["roflag"], "booksclosedflag":row["booksclosedflag"]}
				self.con.close()
#				print orgDetails
				return {"gkstatus":enumdict["Success"],"gkdata":orgDetails}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}





	@view_config(request_method='PUT', renderer='json')
	def putOrg(self):
		token = self.request.headers['gktoken']
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				dataset = self.request.json_body
				if userRole[0]==-1:
					result = self.con.execute(gkdb.organisation.update().where(gkdb.organisation.c.orgcode==authDetails["orgcode"]).values(dataset))
					self.con.close()
					return {"gkstatus":enumdict["Success"]}
				else:
					{"gkstatus":  enumdict["BadPrivilege"]}
			except:
				self.con.close()
				return {"gkstatus":  enumdict["ConnectionFailed"]}

	@view_config(request_method='DELETE', renderer='json')
	def deleteOrg(self):
		token = self.request.headers['gktoken']
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				if userRole[0]==-1:
					result = self.con.execute(gkdb.organisation.delete().where(gkdb.organisation.c.orgcode==authDetails["orgcode"]))
					self.con.close()
					return {"gkstatus":enumdict["Success"]}
				else:
					{"gkstatus":  enumdict["BadPrivilege"]}
			except:
				self.con.close()
				return {"gkstatus":  enumdict["ConnectionFailed"]}

	@view_config(request_method='GET',request_param="type=exists",renderer='json')
	def Orgexists(self):
		try:
			self.con = eng.connect()
			orgtype = self.request.params["orgtype"]
			orgname= self.request.params["orgname"]
			finstart = self.request.params["finstart"]
			finend = self.request.params["finend"]
			orgncount = self.con.execute(select([func.count(gkdb.organisation.c.orgcode).label('orgcode')]).where(and_(gkdb.organisation.c.orgname==orgname,gkdb.organisation.c.orgtype==orgtype, gkdb.organisation.c.yearstart==finstart,gkdb.organisation.c.yearend==finend)))
			org = orgncount.fetchone()
			print org
			if org["orgcode"] !=0:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			else:
				return {"gkstatus":enumdict["Success"]}
		except:
			self.con.close()
			return {"gkstatus":  enumdict["ConnectionFailed"]}


	@view_config(request_param='orgcode', request_method='GET',renderer='json')
	def getOrgcode(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			return {"gkstatus":enumdict["Success"],"gkdata":authDetails["orgcode"]}


	@view_config(request_method='PUT', request_param="type=editorganisation", renderer='json')
	def editOrg(self):
		token = self.request.headers['gktoken']
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con =eng.connect()
				dataset = self.request.json_body
				result = self.con.execute(gkdb.organisation.update().where(gkdb.organisation.c.orgcode==dataset["orgcode"]).values(dataset))
				self.con.close()
				return {"gkstatus":enumdict["Success"]}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
