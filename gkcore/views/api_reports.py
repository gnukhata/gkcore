
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
from gkcore.models.gkdb import accounts, vouchers, groupsubgroups
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ , alias, or_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config

from datetime import datetime
con = Connection
con = eng.connect()

"""
purpose:
This class is the resource to generate reports,
Such as Trial Balance, Ledger, Cash flowe, Balance sheet etc.

connection rules:
con is used for executing sql expression language based queries,
while eng is used for raw sql execution.
routing mechanism:
@view_defaults is used for setting the default route for crud on the given resource class.
if specific route is to be attached to a certain method, or for giving get, post, put, delete methods to default route, the view_config decorator is used.
For other predicates view_config is generally used.
This class has single route with only get as method.
Depending on the request_param, different methods will be called on the route given in view_default.

"""

@view_defaults(route_name='report' , request_method='GET')
class api_reports(object):
	def __init__(self,request):
		self.request = Request
		self.request = request

	def calculateBalance(self,accountCode,financialStart,calculateFrom,calculateTo):
		"""
		purpose:
		This is a private method which will return
		*groupname for the provided account
		*opening balance for the range
		*opening balance type
		*closing balance for the selected range
		*closing balance type
		*Total Dr for the range
		* total Cr for the range.
		Input parameters are:
		*Orgcode
		*accountname
		*financialfrom
		*calculatefrom
		*calculateto

		first we will get the groupname for the provided account.
		note that the given account may be associated with a subgroup for which we must get the group.
		Then we get the opening balance and if it is not 0 then decide if it is a Dr or Cr balance based on the group.
		Then the Total Dr and Cr is calculated.
		If the calculate from is ahead of financial start, then the entire process is repeated.
		This function is called by all reports in this resource.
		we will be initializing all function level variables here.
		"""
		groupName = ""
		openingBalance = 0.00
		balanceBrought = 0.00
		currentBalance = 0.00
		ttlCrBalance = 0.00
		ttlDrBalance = 0.00
		openingBalanceType = ""
		ttlDrUptoFrom = 0.00
		ttlCrUptoFrom = 0.00
		balType = ""
		groupData = eng.execute("select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"%(int(accountCode),int(accountCode)))
		groupRecord = groupData.fetchone()
		groupName = groupRecord["groupname"]
		print "group is %s"%(groupName)
		#now similarly we will get the opening balance for this account.

		obData = con.execute(select([accounts.c.openingbal]).where(accounts.c.accountcode == accountCode) )
		ob = obData.fetchone()
		openingBalance = float(ob["openingbal"])
		financialYearStartDate = datetime.strptime(financialStart,"%Y-%m-%d")
		calculateFromDate = datetime.strptime(calculateFrom,"%Y-%m-%d")
		calculateToDate = datetime.strptime(calculateTo,"%Y-%m-%d")
		if financialYearStartDate == calculateFromDate:
			if openingBalance == 0:
				balanceBrought = 0

			if openingBalance < 0 and (groupName == 'Current Assets' or groupName == 'Fixed Assets'or groupName == 'Investments' or groupName == 'Loans(Asset)' or groupName == 'Miscellaneous Expenses(Asset)'):
				balanceBrought = abs(openingBalance)
				openingBalanceType = "Cr"
				balType = "Cr"

			if openingBalance > 0 and (groupName == 'Current Assets' or groupName == 'Fixed Assets'or groupName == 'Investments' or groupName == 'Loans(Asset)' or groupName == 'Miscellaneous Expenses(Asset)'):
				balanceBrought = openingBalance
				openingBalanceType = "Dr"
				balType = "Dr"

			if openingBalance < 0 and (groupName == 'Corpus' or groupName == 'Capital'or groupName == 'Current Liabilities' or groupName == 'Loans(Liability)' or groupName == 'Reserves'):
				balanceBrought = abs(openingBalance)
				openingBalanceType = "Dr"
				balType = "Dr"

			if openingBalance > 0 and (groupName == 'Corpus' or groupName == 'Capital'or groupName == 'Current Liabilities' or groupName == 'Loans(Liability)' or groupName == 'Reserves'):
				balanceBrought = openingBalance
				openingBalanceType = "Cr"
				balType = "Cr"
		else:
			tdrfrm = eng.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s'"%(int(accountCode),financialStart,calculateFrom))
			tcrfrm = eng.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s'"%(int(accountCode),financialStart,calculateFrom))
			tdrRow = tdrfrm.fetchone()
			tcrRow= tcrfrm.fetchone()
			ttlCrUptoFrom = tcrRow['total']
			ttlDrUptoFrom = tdrRow['total']
			if ttlCrUptoFrom == None:
				ttlCrUptoFrom = 0.00
			if ttlDrUptoFrom == None:
				ttlDrUptoFrom = 0.00

			if openingBalance == 0:
				balanceBrought = 0.00
			if openingBalance < 0 and (groupName == 'Current Assets' or groupName == 'Fixed Assets'or groupName == 'Investments' or groupName == 'Loans(Asset)' or groupName == 'Miscellaneous Expenses(Asset)'):
				ttlCrUptoFrom = ttlCrUptoFrom +abs(openingBalance)
			if openingBalance > 0 and (groupName == 'Current Assets' or groupName == 'Fixed Assets'or groupName == 'Investments' or groupName == 'Loans(Asset)' or groupName == 'Miscellaneous Expenses(Asset)'):
				ttlDrUptoFrom = ttlDrUptoFrom +openingBalance
			if openingBalance < 0 and (groupName == 'Corpus' or groupName == 'Capital'or groupName == 'Current Liabilities' or groupName == 'Loans(Liability)' or groupName == 'Reserves'):
				ttlDrUptoFrom = ttlDrUptoFrom+ abs(openingBalance)
			if openingBalance > 0 and (groupName == 'Corpus' or groupName == 'Capital'or groupName == 'Current Liabilities' or groupName == 'Loans(Liability)' or groupName == 'Reserves'):
				ttlCrUptoFrom = ttlCrUptoFrom + openingBalance
			if ttlDrUptoFrom >	ttlCrUptoFrom:
				balanceBrought = ttlDrUptoFrom - ttlCrUptoFrom
				balType = "Dr"
				openingBalanceType = "Dr"
			if ttlCrUptoFrom >	ttlDrUptoFrom:
				balanceBrought = ttlCrUptoFrom - ttlDrUptoFrom
				balType = "Cr"
				openingBalanceType = "Cr"
		tdrfrm = eng.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s'"%(int(accountCode),calculateFrom, calculateTo))
		tcrfrm = eng.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s'"%(int(accountCode),calculateFrom, calculateTo))
		tdrRow = tdrfrm.fetchone()
		tcrRow= tcrfrm.fetchone()
		ttlDrBalance = tdrRow['total']
		ttlCrBalance = tcrRow['total']
		if ttlCrBalance == None:
			ttlCrBalance = 0.00
		if ttlDrBalance == None:
			ttlDrBalance = 0.00
		if balType =="Dr":
			ttlDrBalance = ttlDrBalance + float(balanceBrought)
		if balType =="Cr":
			ttlCrBalance = ttlCrBalance + float(balanceBrought)
		if ttlDrBalance > ttlCrBalance :
			currentBalance = ttlDrBalance - ttlCrBalance
			balType = "Dr"
		if ttlCrBalance > ttlDrBalance :
			currentBalance = ttlCrBalance - ttlDrBalance
			balType = "Cr"
		return {"balbrought":float(balanceBrought),"curbal":float(currentBalance),"totalcrbal":float(ttlCrBalance),"totaldrbal":float(ttlDrBalance),"baltype":balType,"openbaltype":openingBalanceType,"grpname":groupName}

	@view_config(request_param='type=ledger', renderer='json')
	def ledger(self):
		"""
		Purpose:
		Creates a grid containing complete ledger.
		Takes calculatefrom,calculateto and accountcode.
		Returns success as status and the grid containing ledger.
		description:
		this function returns a grid containing ledger.
		The first row contains opening balance of the account.
		subsequent rows contain all the transactions for an account given it's account code.
		Further, it gives the closing balance at the end of all cr and dr transactions.
		If the closing balance is Dr then the amount will be shown at the cr side and other way round.
		Then finally grand total is displayed.
		This method is called when the report url is called with type=ledger request_param.
		The columns  in the grid include:
		*Date,Particular,voucher Number, Dr,Cr and balance at end of transaction.
		"""

		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		else:
			try:
				orgcode = authDetails["orgcode"]
				accountCode = self.request.params["accountcode"]
				calculateFrom = self.request.params["calculatefrom"]
				calculateTo = self.request.params["calculateto"]
				projectCode =self.request.params["projectcode"]
				financialStart = self.request.params["financialstart"]
				calbalDict = self.calculateBalance(accountCode,financialStart,calculateFrom,calculateTo)
				vouchergrid = []
				bal=0.00
				if projectCode == "" and calbalDict["balbrought"]>0:
					openingrow={"vouchercode":"","vouchernumber":"","voucherdate":"","particulars":"Opening Balance","balance":"","narration":""}
					if calbalDict["openbaltype"] =="Dr":
						openingrow["Dr"] = "%.2f"%float(calbalDict["balbrought"])
						openingrow["Cr"] = ""
						bal = float(calbalDict["balbrought"])
					if calbalDict["openbaltype"] =="Cr":
						openingrow["Dr"] = ""
						openingrow["Cr"] = "%.2f"%float(calbalDict["balbrought"])
						bal = float(-calbalDict["balbrought"])
					vouchergrid.append(openingrow)
				if projectCode == "":
					transactionsRecords = eng.execute("select * from vouchers where voucherdate >= '%s'  and voucherdate < '%s' and (drs ? '%s' or crs ? '%s');"%(calculateFrom, calculateTo, accountCode,accountCode))
				else:
					transactionsRecords = eng.execute("select * from vouchers where voucherdate >= '%s'  and voucherdate < '%s' and projectcode=%d and (drs ? '%s' or crs ? '%s');"%(calculateFrom, calculateTo,projectCode,accountCode,accountCode))

				transactions = transactionsRecords.fetchall()


				for transaction in transactions:
					ledgerRecord = {"vouchercode":transaction["vouchercode"],"vouchernumber":transaction["vouchernumber"],"voucherdate":str(transaction["voucherdate"]),"narration":transaction["narration"]}
					if transaction["drs"].has_key(accountCode):
						ledgerRecord["Dr"] = "%.2f"%float(transaction["drs"][accountCode])
						ledgerRecord["Cr"] = ""
						par=[]
						for cr in transaction["crs"].keys():
							accountnameRow = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(cr)))
							accountname = accountnameRow.fetchone()
							par.append(str(accountname))

						ledgerRecord["particulars"] = format("\n".join(par))
						bal = bal + float(transaction["drs"][accountCode])

					if transaction["crs"].has_key(accountCode):
						ledgerRecord["Cr"] = "%.2f"%float(transaction["crs"][accountCode])
						ledgerRecord["Dr"] = ""
						par=[]
						for dr in transaction["drs"].keys():
							accountnameRow = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(dr)))
							accountname = accountnameRow.fetchone()
							par.append(str(accountname))

						ledgerRecord["particulars"] = format("\n".join(par))
						bal = bal - float(transaction["crs"][accountCode])
					if bal>0:
						ledgerRecord["balance"] = "%.2f(Dr)"%(bal)
					elif bal<0:
						ledgerRecord["balance"] = "%.2f(Cr)"%(abs(bal))
					else :
						ledgerRecord["balance"] = "%.2f"%(0.00)
					vouchergrid.append(ledgerRecord)
				if calbalDict["openbaltype"] == "Cr":
					calbalDict["totalcrbal"] -= calbalDict["balbrought"]
				if calbalDict["openbaltype"] == "Dr":
					calbalDict["totaldrbal"] -= calbalDict["balbrought"]
				ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":"","narration":"","Dr":"%.2f"%(calbalDict["totaldrbal"]),"Cr":"%.2f"%(calbalDict["totalcrbal"]),"particulars":"Total of Transactions","balance":""}
				vouchergrid.append(ledgerRecord)
				ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":str(calculateTo),"narration":"", "particulars":"Closing Balance C/F","balance":""}
				print calbalDict["baltype"]
				if calbalDict["baltype"] == "Cr":
					ledgerRecord["Dr"] = "%.2f"%(calbalDict["curbal"])
					ledgerRecord["Cr"] = ""

				if calbalDict["baltype"] == "Dr":
					ledgerRecord["Cr"] = "%.2f"%(calbalDict["curbal"])
					ledgerRecord["Dr"] = ""
				vouchergrid.append(ledgerRecord)

				ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":"","narration":"", "particulars":"Grand Total","balance":""}
				if projectCode == "" and calbalDict["balbrought"]>0:
					if calbalDict["openbaltype"] =="Dr":
						calbalDict["totaldrbal"] +=  float(calbalDict["balbrought"])

					if calbalDict["openbaltype"] =="Cr":
						calbalDict["totalcrbal"] +=  float(calbalDict["balbrought"])

					if calbalDict["totaldrbal"]>calbalDict["totalcrbal"]:
						ledgerRecord["Dr"] = "%.2f"%(calbalDict["totaldrbal"])
						ledgerRecord["Cr"] = "%.2f"%(calbalDict["totaldrbal"])

					if calbalDict["totaldrbal"]<calbalDict["totalcrbal"]:
						ledgerRecord["Dr"] = "%.2f"%(calbalDict["totalcrbal"])
						ledgerRecord["Cr"] = "%.2f"%(calbalDict["totalcrbal"])
					vouchergrid.append(ledgerRecord)
				else:
					if calbalDict["totaldrbal"]>calbalDict["totalcrbal"]:
						ledgerRecord["Dr"] = "%.2f"%(calbalDict["totaldrbal"])
						ledgerRecord["Cr"] = "%.2f"%(calbalDict["totaldrbal"])

					if calbalDict["totaldrbal"]<calbalDict["totalcrbal"]:
						ledgerRecord["Dr"] = "%.2f"%(calbalDict["totalcrbal"])
						ledgerRecord["Cr"] = "%.2f"%(calbalDict["totalcrbal"])
					vouchergrid.append(ledgerRecord)
				return {"gkstatus":enumdict["Success"],"gkresult":vouchergrid}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param='type=nettrialbalance', renderer='json')
	def netTrialBalance(self):
		"""
		Purpose:
		Returns a grid containing net trial balance for all accounts started from financial start till the end date provided by the user.
		Description:
		This method has type=nettrialbalance as request_param in view_config.
		the method takes financial start and calculateto as parameters.
		Then it calls calculateBalance in a loop after retriving list of accountcode and account names.
		For every iteration financialstart is passed twice to calculateBalance because in trial balance start date is always the financial start.
		Then all dR balances and all Cr balances are added to get total balance for each side.
		Finally if balances are different then that difference is calculated and shown on the lower side followed by a row containing grand total.
		All rows in the ntbGrid are dictionaries.
		"""

		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				accountData = con.execute(select([accounts.c.accountcode,accounts.c.accountname]).where(accounts.c.orgcode==authDetails["orgcode"] ) )
				accountRecords = accountData.fetchall()
				ntbGrid = []
				financialStart = self.request.params["financialstart"]
				calculateTo =  self.request.params["calculateto"]
				srno = 0
				totalDr = 0.00
				totalCr = 0.00
				for account in accountRecords:
					calbalData = self.calculateBalance(account["accountcode"], financialStart, financialStart, calculateTo)
					if calbalData["baltype"]=="":
						continue
					srno += 1
					ntbRow = {"accountcode": account["accountcode"],"accountname":account["accountname"],"groupname": calbalData["grpname"],"srno":srno}
					if calbalData["baltype"] == "Dr":
						ntbRow["Dr"] = "%.2f"%(calbalData["curbal"])
						ntbRow["Cr"] = ""
						totalDr = totalDr + calbalData["curbal"]
					if calbalData["baltype"] == "Cr":
						ntbRow["Dr"] = ""
						ntbRow["Cr"] = "%.2f"%(calbalData["curbal"])
						totalCr = totalCr + calbalData["curbal"]
					ntbGrid.append(ntbRow)
				ntbGrid.append({"accountcode":"","accountname":"Total","groupname":"","srno":"","Dr": "%.2f"%(totalDr),"Cr":"%.2f"%(totalCr) })
				if totalDr > totalCr:
					baldiff = totalDr - totalCr
					ntbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Cr": "%.2f"%(baldiff),"Dr":"" })
					ntbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","TotalCr": "%.2f"%(totalDr),"TotalDr":"%.2f"%(totalDr) })
				if totalDr < totalCr:
					baldiff = totalCr - totalDr
					ntbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Dr": "%.2f"%(baldiff),"Cr":"" })
					ntbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr": "%.2f"%(totalCr),"Dr":"%.2f"%(totalCr) })
				return {"gkstatus":enumdict["Success"],"gkresult":ntbGrid}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param='type=grosstrialbalance', renderer='json')
	def grossTrialBalance(self):
		"""
		Purpose:
		Returns a grid containing gross trial balance for all accounts started from financial start till the end date provided by the user.
		Description:
		This method has type=nettrialbalance as request_param in view_config.
		the method takes financial start and calculateto as parameters.
		Then it calls calculateBalance in a loop after retriving list of accountcode and account names.
		For every iteration financialstart is passed twice to calculateBalance because in trial balance start date is always the financial start.
		Then all dR balances and all Cr balances are added to get total balance for each side.
		Finally if balances are different then that difference is calculated and shown on the lower side followed by a row containing grand total.
		All rows in the ntbGrid are dictionaries.
		"""

		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				accountData = con.execute(select([accounts.c.accountcode,accounts.c.accountname]).where(accounts.c.orgcode==authDetails["orgcode"] ) )
				accountRecords = accountData.fetchall()
				gtbGrid = []
				financialStart = self.request.params["financialstart"]
				calculateTo =  self.request.params["calculateto"]
				srno = 0
				totalDr = 0.00
				totalCr = 0.00
				for account in accountRecords:
					calbalData = self.calculateBalance(account["accountcode"], financialStart, financialStart, calculateTo)
					if float(calbalData["totaldrbal"])==0 and float(calbalData["totalcrbal"]) == 0:
						continue
					srno += 1
					gtbRow = {"accountcode": account["accountcode"],"accountname":account["accountname"],"groupname": calbalData["grpname"],"Dr balance":"%.2f"%(calbalData["totaldrbal"]),"Cr balance":"%.2f"%(calbalData["totalcrbal"]),"srno":srno }
					totalDr += calbalData["totaldrbal"]
					totalCr += calbalData["totalcrbal"]
					gtbGrid.append(gtbRow)
				gtbGrid.append({"accountcode":"","accountname":"Total Balance","groupname":"","Dr Balance":"%.2f"%(totalDr),"Cr balance":"%.2f"%(totalCr),"srno":"" })
				if totalDr > totalCr:
					baldiff = totalDr - totalCr
					gtbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Cr Balance": "%.2f"%(baldiff),"Dr Balance":"" })
					gtbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr Balance": "%.2f"%(totalDr),"Dr Balance":"%.2f"%(totalDr) })
				if totalDr < totalCr:
					baldiff = totalCr - totalDr
					gtbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Dr Balance": "%.2f"%(baldiff),"Cr Balance":"" })
					gtbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr Balance": "%.2f"%(totalCr),"Dr Balance":"%.2f"%(totalCr) })
				return {"gkstatus":enumdict["Success"],"gkresult":gtbGrid}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param='type=extendedtrialbalance', renderer='json')
	def extendedTrialBalance(self):
		"""
		Purpose:
		Returns a grid containing extended trial balance for all accounts started from financial start till the end date provided by the user.
		Description:
		This method has type=nettrialbalance as request_param in view_config.
		the method takes financial start and calculateto as parameters.
		Then it calls calculateBalance in a loop after retriving list of accountcode and account names.
		For every iteration financialstart is passed twice to calculateBalance because in trial balance start date is always the financial start.
		Then all dR balances and all Cr balances are added to get total balance for each side.
		After this all closing balances are added either on Dr or Cr side depending on the baltype.
		Finally if balances are different then that difference is calculated and shown on the lower side followed by a row containing grand total.
		All rows in the extbGrid are dictionaries.
		"""

		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				accountData = con.execute(select([accounts.c.accountcode,accounts.c.accountname]).where(accounts.c.orgcode==authDetails["orgcode"] ) )
				accountRecords = accountData.fetchall()
				extbGrid = []
				financialStart = self.request.params["financialstart"]
				calculateTo =  self.request.params["calculateto"]
				srno = 0
				totalDr = 0.00
				totalCr = 0.00
				totalDrBal = 0.00
				totalCrBal = 0.00
				difftb = 0.00
				for account in accountRecords:
					calbalData = self.calculateBalance(account["accountcode"], financialStart, financialStart, calculateTo)
					if float(calbalData["balbrought"]) == 0  and float(calbalData["totaldrbal"])==0 and float(calbalData["totalcrbal"]) == 0:
						continue
					srno += 1
					extbrow = {"accountcode": account["accountcode"],"accountname":account["accountname"],"groupname": calbalData["grpname"],"totaldr":"%.2f"%(calbalData["totaldrbal"]),"totalcr":"%.2f"%(calbalData["totalcrbal"]),"srno":srno}
					if calbalData["balbrought"] > 0:
						extbrow["openingbalance"]="%.2f(%s)"% (calbalData["balbrought"],calbalData["openbaltype"])
					else:
						extbrow["openingbalance"] = "0.00"
					totalDr += calbalData["totaldrbal"]
					totalCr +=  calbalData["totalcrbal"]
					if calbalData["baltype"]=="Dr":
						extbrow["curbaldr"] = "%.2f"%(calbalData["curbal"])
						extbrow["curbalcr"] = ""
						totalDrBal += calbalData["curbal"]
					if calbalData["baltype"]=="Cr":
						extbrow["curbaldr"] = ""
						extbrow["curbalcr"] = "%.2f"%(calbalData["curbal"])
						totalCrBal += calbalData["curbal"]
					extbGrid.append(extbrow)
				extbrow = {"accountcode": "","accountname":"","groupname":"","openingbalance":"Total", "totaldr":"%.2f"%(totalDr),"totalcr":"%.2f"%(totalCr),"curbaldr":"%.2f"%(totalDrBal),"curbalcr":"%.2f"%(totalCrBal)}
				extbGrid.append(extbrow)

				if totalDrBal>totalCrBal:
					extbrow = {"accountcode": "","accountname":"Difference in Trial Balance","groupname":"","openingbalance":"", "totaldr":"","totalcr":""}
					extbrow["curbalcr"] = "%.2f"%(totalDrBal - totalCrBal)
					extbrow["curbaldr"] =""
					extbGrid.append(extbrow)
				if totalCrBal>totalDrBal:
					extbrow = {"accountcode": "","accountname":"Difference in Trial Balance","groupname":"","openingbalance":"", "totaldr":"","totalcr":""}
					extbrow["curbaldr"] = "%.2f"%(totalDrBal - totalCrBal)
					extbrow["curbalcr"] =""
					extbGrid.append(extbrow)
				return {"gkstatus":enumdict["Success"],"gkresult":extbGrid}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
