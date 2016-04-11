


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


from pyramid.view import view_defaults,  view_config
from gkcore import eng, enumdict
from gkcore.models import gkdb
from sqlalchemy.sql import select, distinct
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
import jwt
import gkcore
con = Connection
con = eng.connect()

@view_defaults(route_name='organisations')
class api_organisation(object):
	def __init__(self,request):
		self.request = request

	@view_config(request_method='GET', renderer ='json')
	def getOrgs(self):
		try:
			result = con.execute(select([gkdb.organisation.c.orgname, gkdb.organisation.c.orgtype]).distinct())
			orgs = []
			for row in result:
				orgs.append({"orgname":row["orgname"], "orgtype":row["orgtype"]})
			return {"gkstatus":enumdict["Success"], "gkdata":orgs}
		except:
			return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(route_name='orgyears', request_method='GET', renderer ='json')
	def getYears(self):
		try:
			result = con.execute(select([gkdb.organisation.c.yearstart, gkdb.organisation.c.yearend,gkdb.organisation.c.orgcode]).where(and_(gkdb.organisation.c.orgname==self.request.matchdict["orgname"], gkdb.organisation.c.orgtype == self.request.matchdict["orgtype"])))
			years = []
			for row in result:
				years.append({"yearstart":str(row["yearstart"]), "yearend":str(row["yearend"]),"orgcode":row["orgcode"]})
			return {"gkstatus":enumdict["Success"],"gkdata":years}
		except:
			return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_method='POST',renderer='json')
	def postOrg(self):

		try:
			dataset = self.request.json_body
			orgdata = dataset["orgdetails"]
			userdata = dataset["userdetails"]
			result = con.execute(gkdb.organisation.insert(),[orgdata])
			if result.rowcount==1:
				code = con.execute(select([gkdb.organisation.c.orgcode]).where(and_(gkdb.organisation.c.orgname==orgdata["orgname"], gkdb.organisation.c.orgtype==orgdata["orgtype"], gkdb.organisation.c.yearstart==orgdata["yearstart"], gkdb.organisation.c.yearend==orgdata["yearend"])))
				orgcode = code.fetchone()
				try:

					currentassets= {"groupname":"Current Assets","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),currentassets)
					result = con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Current Assets",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Bank","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Cash","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Inventory","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Loans & Advance","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Sundry Debtors","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]} ])

					currentliability= {"groupname":"Current Liabilities","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),currentliability)
					result = con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Current Liabilities",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Provisions","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Sundry Creditors for Expense","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Sundry Creditors for Purchase","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]}])

					directexpense= {"groupname":"Direct Expense","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),directexpense)

					directincome= {"groupname":"Direct Income","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),directincome)

					fixedassets= {"groupname":"Fixed Assets","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),fixedassets)
					result = con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Fixed Assets",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Building","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Furniture","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Land","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Plant & Machinery","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]} ])

					indirectexpense= {"groupname":"Indirect Expense","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),indirectexpense)

					indirectincome= {"groupname":"Indirect Income","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),indirectincome)

					investment= {"groupname":"Investments","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),investment)
					result = con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Investments",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Investment in Bank Deposits","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Investment in Shares & Debentures","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]}, ])

					loansasset= {"groupname":"Loans(Asset)","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),loansasset)

					loansliab= {"groupname":"Loans(Liability)","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),loansliab)
					result = con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Loans(Liability)",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Secured","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Unsecured","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]} ])

					reserves= {"groupname":"Reserves","orgcode":orgcode["orgcode"]}
					result = con.execute(gkdb.groupsubgroups.insert(),reserves)

					result = con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Direct Income",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					if orgdata["orgtype"] == "Profit Making":
						result = con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Capital","orgcode":orgcode["orgcode"]},{"groupname":"Miscellaneous Expenses(Asset)","orgcode":orgcode["orgcode"]}])

						result = con.execute(gkdb.accounts.insert(),{"accountname":"Profit & Loss","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]})

					else:
						result = con.execute(gkdb.groupsubgroups.insert(),{"groupname":"Corpus","orgcode":orgcode["orgcode"]})

						result = con.execute(gkdb.accounts.insert(),{"accountname":"Income & Expenditure","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]})

					result = con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Inventory",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = con.execute(gkdb.accounts.insert(),[{"accountname":"Closing Stock","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Stock at the Beginning","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]}])

					result = con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Direct Expense",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
					grpcode = result.fetchone()
					result = con.execute(gkdb.accounts.insert(),{"accountname":"Opening Stock","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]})



					userdata["orgcode"] = orgcode["orgcode"]
					userdata["userrole"] = -1
					result = con.execute(gkdb.users.insert(),[userdata])
					if result.rowcount==1:
						result = con.execute(select([gkdb.users.c.userid]).where(and_(gkdb.users.c.username==userdata["username"], gkdb.users.c.userpassword== userdata["userpassword"], gkdb.users.c.orgcode==userdata["orgcode"])) )
						if result.rowcount == 1:
							record = result.fetchone()

							token = jwt.encode({"orgcode":userdata["orgcode"],"userid":record["userid"]},gkcore.secret,algorithm='HS256')
							return {"gkstatus":enumdict["Success"],"token":token }
						else:
							return {"gkstatus":enumdict["ConnectionFailed"]}
					else:
							return {"gkstatus":enumdict["ConnectionFailed"]}
				except:
					result = con.execute(gkdb.organisation.delete().where(gkdb.organisation.c.orgcode==orgcode["orgcode"]))
					return {"gkstatus":enumdict["ConnectionFailed"]}
			else:
				return {"gkstatus":enumdict["ConnectionFailed"]}
		except:
			return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(route_name='organisation', request_method='GET',renderer='json')
	def getOrg(self):
		try:
			result = con.execute(select([gkdb.organisation]).where(gkdb.organisation.c.orgcode==self.request.matchdict["orgcode"]))
			row = result.fetchone()
			orgDetails={"orgname":row["orgname"], "orgtype":row["orgtype"], "yearstart":str(row["yearstart"]), "yearend":str(row["yearend"]),"orgcity":row["orgcity"], "orgaddr":row["orgaddr"], "orgpincode":row["orgpincode"], "orgstate":row["orgstate"], "orgcountry":row["orgcountry"], "orgtelno":row["orgtelno"], "orgfax":row["orgfax"], "orgwebsite":row["orgwebsite"], "orgemail":row["orgemail"], "orgpan":row["orgpan"], "orgmvat":row["orgmvat"], "orgstax":row["orgstax"], "orgregno":row["orgregno"], "orgregdate":row["orgregdate"], "orgfcrano":row["orgfcrano"], "orgfcradate":row["orgfcradate"], "roflag":row["roflag"], "booksclosedflag":row["booksclosedflag"]	}
			return {"gkstatus":enumdict["Success"],"gkdata":orgDetails}
		except:
			return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_method='PUT', renderer='json')
	def putOrg(self):
		token = self.request.headers['gktoken']
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				user=con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				dataset = self.request.json_body
				if userRole[0]==-1:
					result = con.execute(gkdb.organisation.update().where(gkdb.organisation.c.orgcode==authDetails["orgcode"]).values(dataset))
					return {"gkstatus":enumdict["Success"]}
				else:
					{"gkstatus":  enumdict["BadPrivilege"]}
			except:
				return {"gkstatus":  enumdict["ConnectionFailed"]}

	@view_config(request_method='DELETE', renderer='json')
	def deleteOrg(self):
		token = self.request.headers['gktoken']
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				user=con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				if userRole[0]==-1:
					result = con.execute(gkdb.organisation.delete().where(gkdb.organisation.c.orgcode==authDetails["orgcode"]))
					return {"gkstatus":enumdict["Success"]}
				else:
					{"gkstatus":  enumdict["BadPrivilege"]}
			except:
				return {"gkstatus":  enumdict["ConnectionFailed"]}

	@view_config(route_name='orgid', request_method='GET',renderer='json')
	def getOrgCode(self):
		try:
			result = con.execute(select([gkdb.organisation.c.orgcode]).where(and_(gkdb.organisation.c.orgname==self.request.matchdict["orgname"], gkdb.organisation.c.orgtype==self.request.matchdict["orgtype"], gkdb.organisation.c.yearstart==self.request.matchdict["yearstart"], gkdb.organisation.c.yearend==self.request.matchdict["yearend"])))
			row = result.fetchone()
			orgcode={"orgcode":row["orgcode"]}
			return {"gkstatus":enumdict["Success"],"gkdata":orgcode}
		except:
			return {"gkstatus":enumdict["ConnectionFailed"]}
