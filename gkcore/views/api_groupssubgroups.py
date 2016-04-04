
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
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ , alias
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
import jwt
import gkcore
from gkcore.views.api_login import authCheck
from sqlalchemy.sql.expression import null

con = Connection
con = eng.connect()


@view_defaults(route_name='groupsubgroups')
class api_user(object):
	def __init__(self,request):
		self.request = Request
		self.request = request

	@view_config(request_method='POST',renderer='json')
	def addSubgroup(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				dataset = self.request.json_body
				dataset["orgcode"] = authDetails["orgcode"]
				result = con.execute(gkdb.groupsubgroups.insert(),[dataset])
				if result.rowcount==1:
					result = con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.orgcode==authDetails["orgcode"], gkdb.groupsubgroups.c.groupname==dataset["groupname"])))
					row = result.fetchone()
					return {"gkstatus":enumdict["Success"],"gkresult":row["groupcode"]}
				else:
					return {"gkstatus":enumdict["ConnectionFailed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
	@view_config(route_name='groupsubgroup', request_method='GET',renderer='json')
	def getGroupSubgroup(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				g = gkdb.groupsubgroups.alias("g")
				sg = gkdb.groupsubgroups.alias("sg")
				resultset = con.execute(select([(g.c.groupname).label('groupname'),(sg.c.groupname).label('subgroupname')]).where(and_(g.c.groupcode==sg.c.subgroupof,g.c.groupcode==self.request.matchdict["groupcode"])))
				grpsubs = []
				for row in resultset:
					grpsubs.append({"groupname":row["groupname"],"subgroupname":row["subgroupname"]})
				return {"gkstatus": gkcore.enumdict["Success"], "gkresult":grpsubs}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
	@view_config(request_method='PUT', renderer='json')
	def editSubgroup(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				dataset = self.request.json_body
				dataset["orgcode"]=authDetails["orgcode"]
				result = con.execute(gkdb.groupsubgroups.update().where(and_(gkdb.groupsubgroups.c.groupname==dataset["groupname"],gkdb.groupsubgroups.c.orgcode==dataset["orgcode"])).values(dataset))
				return {"gkstatus": gkcore.enumdict["Success"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
	@view_config(request_method='GET', renderer ='json')
	def getAllGroups(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			#try:
			result = con.execute(select([gkdb.groupsubgroups.c.groupname,gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.orgcode==authDetails["orgcode"], gkdb.groupsubgroups.c.subgroupof==null())))
			grps = []
			for row in result:
				grps.append({"groupname":row["groupname"], "groupcode":row["groupcode"]})
			grpbal = self.getGroupBalance(authDetails["orgcode"], grps)
			return {"gkstatus": gkcore.enumdict["Success"], "gkresult":grps, "baltbl":grpbal}
			#except:
				#return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }

	@view_config(route_name="groupDetails", request_method='GET', renderer ='json')
	def getSubgroupsByGroup(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				result = con.execute(select([gkdb.groupsubgroups.c.groupname,gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.subgroupof==self.request.matchdict["groupcode"])))
				subs = []
				for row in result:
					subs.append({"subgroupname":row["groupname"], "groupcode":row["groupcode"]})
				return {"gkstatus": gkcore.enumdict["Success"], "gkresult":subs}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }

	@view_config(request_method='DELETE', renderer ='json')
	def deleteSubgroup(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				user=con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				dataset = self.request.json_body
				if userRole[0]==-1:
					result = con.execute(gkdb.groupsubgroups.delete().where(gkdb.groupsubgroups.c.groupcode==dataset["groupcode"]))
					return {"gkstatus":enumdict["Success"]}
				else:
					{"gkstatus":  enumdict["BadPrivilege"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }

	def getGroupBalance(self,orgcode,groups):
		typeData = con.execute(select([gkdb.organisation.c.orgtype]).where(gkdb.organisation.c.orgcode ==orgcode))
		typeRow = typeData.fetchone()
		liabilityTotal = 0.00
		assetsTotal = 0.00
		difference = 0.00
		groupBalanceTable = []

		if str(typeRow["orgtype"]) == "Not For Profit":
			groupBalanceTable.append("CORPUS & LIABILITIES")
			for groupRow in groups:
				if groupRow["groupname"] == "Current Liabilities" or groupRow["groupname"] == "Reserves" or groupRow["groupname"] == "Corpus" or groupRow["groupname"] == "Loans (Liability)":
					groupBalance = eng.execute("select count(accountname) as NumberOfAccounts, sum(openingbal) as groupBalance from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s'));"%(orgcode,orgcode,groupRow["groupname"],orgcode,groupRow["groupname"]))
					balCountRow = groupBalance.fetchone()
					balCountRow = [balCountRow[0], balCountRow[1]]
					if balCountRow[1] == None:
						balCountRow[1] = 0.00
					liabilityDict = {"groupname":groupRow["groupname"],"numberofaccounts":float(balCountRow[0]),"groupbalance":float(balCountRow[1])}
					groupBalanceTable.append(liabilityDict)
					liabilityTotal = liabilityTotal + float(balCountRow[1])
			groupBalanceTable.append({"Total":liabilityTotal})
			groupBalanceTable.append("PROPERTY & ASSETS")
			for groupRow in groups:
				if groupRow["groupname"] == "Fixed Assets" or groupRow["groupname"] == "Current Assets" or groupRow["groupname"] == "Investments" or groupRow["groupname"] == "Loans (Asset)":
					groupBalance = eng.execute("select count(accountname) as NumberOfAccounts, sum(openingbal) as groupBalance from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s'));"%(orgcode,orgcode,groupRow["groupname"],orgcode,groupRow["groupname"]))
					balCountRow = groupBalance.fetchone()
					balCountRow = [balCountRow[0], balCountRow[1]]
					if balCountRow[1] == None:
						balCountRow[1] = 0.00
					AssetDict = {"groupname":groupRow["groupname"],"numberofaccounts":float(balCountRow[0]),"groupbalance":float(balCountRow[1])}
					groupBalanceTable.append(AssetDict)
					assetsTotal = assetsTotal + float(balCountRow[1])
			groupBalanceTable.append({"Total":assetsTotal})
			difference = assetsTotal - liabilityTotal
			groupBalanceTable.append({"Difference in balance": difference })
		if str(typeRow["orgtype"]) == "Profit Making":
			groupBalanceTable.append("CAPITAL & LIABILITIES")
			for groupRow in groups:
				if groupRow["groupname"] == "Capital" or groupRow["groupname"] ==  "Reserves" or groupRow["groupname"] == "Current Liabilities" or groupRow["groupname"] == "Loans (Liability)":
					groupBalance = eng.execute("select count(accountname) as NumberOfAccounts, sum(openingbal) as groupBalance from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s'));"%(orgcode,orgcode,groupRow["groupname"],orgcode,groupRow["groupname"]))
					balCountRow = groupBalance.fetchone()
					balCountRow = [balCountRow[0], balCountRow[1]]
					if balCountRow[1] == None:
						balCountRow[1] = 0.00
					liabilityDict = {"groupname":groupRow["groupname"],"numberofaccounts":float(balCountRow[0]),"groupbalance":float(balCountRow[1])}
					groupBalanceTable.append(liabilityDict)
					liabilityTotal = liabilityTotal + float(balCountRow[1])
			groupBalanceTable.append({"Total":liabilityTotal})
			groupBalanceTable.append("PROPERTY & ASSETS")
			for groupRow in groups:
				if groupRow["groupname"] == "Fixed Assets" or groupRow["groupname"] == "Current Assets" or groupRow["groupname"] == "Investments" or groupRow["groupname"] == "Loans (Asset)":
					groupBalance = eng.execute("select count(accountname) as NumberOfAccounts, sum(openingbal) as groupBalance from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s'));"%(orgcode,orgcode,groupRow["groupname"],orgcode,groupRow["groupname"]))
					balCountRow = groupBalance.fetchone()
					balCountRow = [balCountRow[0], balCountRow[1]]
					if balCountRow[1] == None:
						balCountRow[1] = 0.00
					AssetDict = {"groupname":groupRow["groupname"],"numberofaccounts":float(balCountRow[0]),"groupbalance":float(balCountRow[1])}
					groupBalanceTable.append(AssetDict)
					assetsTotal = assetsTotal + float(balCountRow[1])
			groupBalanceTable.append({"Total":assetsTotal})
			difference = assetsTotal - liabilityTotal
			groupBalanceTable.append({"Difference in balance": difference })
		return groupBalanceTable
