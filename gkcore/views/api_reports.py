
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
from gkcore.models.gkdb import accounts, vouchers, groupsubgroups, projects, organisation
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ , alias, or_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from gkcore.views.api_user import getUserRole
from datetime import datetime,date
import calendar
from monthdelta import monthdelta
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
		financialStart = str(financialStart)
		calculateFrom= str(calculateFrom)
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

	@view_config(request_param='type=monthlyledger', renderer='json')
	def monthlyLedger(self):
		"""
		Purpose:
		Gets the list of all months with their respective closing balance for the given account.
		takes accountcode as input parameter.
		description:
		This function is used to produce a monthly ledger report for a given account.
		This is a useful report from which the accountant can choose
		a month for which the entire ledger can be displayed.
		In this report just the closing balance at end of every month is displayed.
		Takes accountcode as input parameter.
		This function is called when type=monthlyledger is passed to the /reports url.
		accountcode is extracted from json_body from request.
		Orgcode is procured from the jwt header.
		The list returned is a grid containing set of dictionaries.
		For each month calculatebalance will be called to get the closing balnace for that range.
		each dictionary will have 2 keys with their respective values,
		month and balance will be the 2 key value pares.
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
				orgcode = authDetails["orgcode"]
				accountCode = self.request.params["accountcode"]
				accNameData= con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode== accountCode))
				row = accNameData.fetchone()
				accname = row["accountname"]
				finStartData = con.execute(select([organisation.c.yearstart]).where(organisation.c.orgcode==orgcode))
				finRow = finStartData.fetchone()
				financialStart = finRow['yearstart']
				finEndData = con.execute(select([organisation.c.yearend]).where(organisation.c.orgcode == orgcode))
				finEndrow = finEndData.fetchone()
				financialEnd = finEndrow['yearend']
				monthCounter = 1
				startMonthDate = financialStart
				endMonthDate = date(startMonthDate.year, startMonthDate.month, (calendar.monthrange(startMonthDate.year, startMonthDate.month)[1]))
				monthlyBal = []
				while endMonthDate <= financialEnd:
					monthClBal =  self.calculateBalance(accountCode, str(financialStart), str(financialStart), str(endMonthDate))
					if (monthClBal["baltype"] == "Dr"):
						clBal = {"month": calendar.month_name[startMonthDate.month], "Dr": "%.2f"%float(monthClBal["curbal"]), "Cr":"", "period":str(startMonthDate)+":"+str(endMonthDate)}
						monthlyBal.append(clBal)
					if (monthClBal["baltype"] == "Cr"):
						clBal = {"month": calendar.month_name[startMonthDate.month], "Dr": "", "Cr":"%.2f"%float(monthClBal["curbal"]), "period":str(startMonthDate)+":"+str(endMonthDate)}
						monthlyBal.append(clBal)
					startMonthDate = date(financialStart.year,financialStart.month,financialStart.day) + monthdelta(monthCounter)
					endMonthDate = date(startMonthDate.year, startMonthDate.month, calendar.monthrange(startMonthDate.year, startMonthDate.month)[1])
					monthCounter  +=1
				return {"gkstatus":enumdict["Success"], "gkresult": monthlyBal, "accountcode":accountCode}

			except Exception as E:
				print E
				return {"gkstatus":enumdict["ConnectionFailed"]}


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
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
  				orgcode = authDetails["orgcode"]
  				accountCode = self.request.params["accountcode"]
  				calculateFrom = self.request.params["calculatefrom"]
  				calculateTo = self.request.params["calculateto"]
  				projectCode =self.request.params["projectcode"]
  				financialStart = self.request.params["financialstart"]
  				calbalDict = self.calculateBalance(accountCode,financialStart,calculateFrom,calculateTo)
  				vouchergrid = []
  				bal=0.00
				accnamerow = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(accountCode)))
				accname = accnamerow.fetchone()
				headerrow = {"accountname":''.join(accname),"projectname":"","calculateto":datetime.strftime(datetime.strptime(str(calculateTo),"%Y-%m-%d").date(),'%d-%m-%Y'),"calculatefrom":datetime.strftime(datetime.strptime(str(calculateFrom),"%Y-%m-%d").date(),'%d-%m-%Y')}
				if projectCode!="":
					prjnamerow = con.execute(select([projects.c.projectname]).where(projects.c.projectcode==int(projectCode)))
					prjname = prjnamerow.fetchone()
					headerrow["projectname"]=''.join(prjname)

  				if projectCode == "" and calbalDict["balbrought"]>0:
  					openingrow={"vouchercode":"","vouchernumber":"","voucherdate":datetime.strftime(datetime.strptime(str(calculateFrom),"%Y-%m-%d").date(),'%d-%m-%Y'),"particulars":["Opening Balance"],"balance":"","narration":"","status":""}
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
  					transactionsRecords = eng.execute("select * from vouchers where voucherdate >= '%s'  and voucherdate < '%s' and projectcode=%d and (drs ? '%s' or crs ? '%s');"%(calculateFrom, calculateTo,int(projectCode),accountCode,accountCode))

  				transactions = transactionsRecords.fetchall()

  				crtotal = 0.00
  				drtotal = 0.00
  				for transaction in transactions:
  					ledgerRecord = {"vouchercode":transaction["vouchercode"],"vouchernumber":transaction["vouchernumber"],"voucherdate":str(transaction["voucherdate"].date().strftime('%d-%m-%Y')),"narration":transaction["narration"],"status":transaction["lockflag"]}
  					if transaction["drs"].has_key(accountCode):
  						ledgerRecord["Dr"] = "%.2f"%float(transaction["drs"][accountCode])
  						ledgerRecord["Cr"] = ""
  						drtotal += float(transaction["drs"][accountCode])
  						par=[]
  						for cr in transaction["crs"].keys():
  							accountnameRow = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(cr)))
  							accountname = accountnameRow.fetchone()
  							par.append(''.join(accountname))
  						ledgerRecord["particulars"] = par
  						bal = bal + float(transaction["drs"][accountCode])

  					if transaction["crs"].has_key(accountCode):
  						ledgerRecord["Cr"] = "%.2f"%float(transaction["crs"][accountCode])
  						ledgerRecord["Dr"] = ""
  						crtotal += float(transaction["crs"][accountCode])
  						par=[]
  						for dr in transaction["drs"].keys():
  							accountnameRow = con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(dr)))
  							accountname = accountnameRow.fetchone()
  							par.append(''.join(accountname))

  						ledgerRecord["particulars"] = par
  						bal = bal - float(transaction["crs"][accountCode])
  					if bal>0:
  						ledgerRecord["balance"] = "%.2f(Dr)"%(bal)
  					elif bal<0:
  						ledgerRecord["balance"] = "%.2f(Cr)"%(abs(bal))
  					else :
  						ledgerRecord["balance"] = "%.2f"%(0.00)
  					vouchergrid.append(ledgerRecord)
  				if projectCode=="":
  					if calbalDict["openbaltype"] == "Cr":
  						calbalDict["totalcrbal"] -= calbalDict["balbrought"]
  					if calbalDict["openbaltype"] == "Dr":
  						calbalDict["totaldrbal"] -= calbalDict["balbrought"]
  					ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":"","narration":"","Dr":"%.2f"%(calbalDict["totaldrbal"]),"Cr":"%.2f"%(calbalDict["totalcrbal"]),"particulars":["Total of Transactions"],"balance":"","status":""}
  					vouchergrid.append(ledgerRecord)
  					ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":datetime.strftime(datetime.strptime(str(calculateTo),"%Y-%m-%d").date(),'%d-%m-%Y'),"narration":"", "particulars":["Closing Balance C/F"],"balance":"","status":""}
  					if calbalDict["baltype"] == "Cr":
  						ledgerRecord["Dr"] = "%.2f"%(calbalDict["curbal"])
  						ledgerRecord["Cr"] = ""

  					if calbalDict["baltype"] == "Dr":
  						ledgerRecord["Cr"] = "%.2f"%(calbalDict["curbal"])
  						ledgerRecord["Dr"] = ""
  					vouchergrid.append(ledgerRecord)

  					ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":"","narration":"", "particulars":["Grand Total"],"balance":"","status":""}
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
  				else:
  					ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":"","narration":"","Dr":"%.2f"%(drtotal),"Cr":"%.2f"%(crtotal),"particulars":["Total of Transactions"],"balance":"","status":""}
  					vouchergrid.append(ledgerRecord)
  				return {"gkstatus":enumdict["Success"],"gkresult":vouchergrid,"userrole":urole["userrole"],"ledgerheader":headerrow}
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
					ntbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr": "%.2f"%(totalDr),"Dr":"%.2f"%(totalDr) })
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
				gtbGrid.append({"accountcode":"","accountname":"Total Balance","groupname":"","Dr balance":"%.2f"%(totalDr),"Cr balance":"%.2f"%(totalCr),"srno":"" })
				if totalDr > totalCr:
					baldiff = totalDr - totalCr
					gtbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Cr balance": "%.2f"%(baldiff),"Dr balance":"" })
					gtbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr balance": "%.2f"%(totalDr),"Dr balance":"%.2f"%(totalDr) })
				if totalDr < totalCr:
					baldiff = totalCr - totalDr
					gtbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Dr balance": "%.2f"%(baldiff),"Cr balance":"" })
					gtbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr balance": "%.2f"%(totalCr),"Dr balance":"%.2f"%(totalCr) })
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
					if calbalData["openbaltype"] == "Cr":
						calbalData["totalcrbal"] -= calbalData["balbrought"]
					if calbalData["openbaltype"] == "Dr":
						calbalData["totaldrbal"] -= calbalData["balbrought"]
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
				extbrow = {"accountcode": "","accountname":"","groupname":"","openingbalance":"Total", "totaldr":"%.2f"%(totalDr),"totalcr":"%.2f"%(totalCr),"curbaldr":"%.2f"%(totalDrBal),"curbalcr":"%.2f"%(totalCrBal),"srno":""}
				extbGrid.append(extbrow)

				if totalDrBal>totalCrBal:
					extbGrid.append({"accountcode": "","accountname":"Difference in Trial Balance","groupname":"","openingbalance":"", "totaldr":"","totalcr":"","srno":"","curbalcr":"%.2f"%(totalDrBal - totalCrBal),"curbaldr":""})
					extbGrid.append({"accountcode": "","accountname":"","groupname":"","openingbalance":"", "totaldr":"","totalcr":"","curbaldr":"%.2f"%(totalDrBal),"curbalcr":"%.2f"%(totalDrBal),"srno":""})
				if totalCrBal>totalDrBal:
					extbGrid.append({"accountcode": "","accountname":"Difference in Trial Balance","groupname":"","openingbalance":"", "totaldr":"","totalcr":"","srno":"","curbaldr":"%.2f"%(totalCrBal - totalDrBal),"curbalcr":""})
					extbGrid.append({"accountcode": "","accountname":"","groupname":"","openingbalance":"", "totaldr":"","totalcr":"","curbaldr":"%.2f"%(totalCrBal),"curbalcr":"%.2f"%(totalCrBal),"srno":""})
				return {"gkstatus":enumdict["Success"],"gkresult":extbGrid}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}




	@view_config(request_param='type=cashflow', renderer='json')
	def cashflow(self):
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
				calculateFrom = self.request.params["calculatefrom"]
				calculateTo = self.request.params["calculateto"]
				financialStart = self.request.params["financialstart"]
				cbAccountsData = eng.execute("select accountcode, openingbal, accountname from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Bank','Cash'))"%(authDetails["orgcode"],authDetails["orgcode"]))
				cbAccounts = cbAccountsData.fetchall()
				receiptcf = []
				paymentcf = []
				rctransactionsgrid = []
				closinggrid = []
				rcaccountcodes = []
				pyaccountcodes = []
				rctotal = 0.00
				pytotal = 0.00
				receiptcf.append({"toby":"To","particulars":"Opening balance","amount":"","accountcode":""})
				closinggrid.append({"toby":"By","particulars":"Closing balance","amount":"","accountcode":""})
				for cbAccount in cbAccounts:
					opacc = self.calculateBalance(cbAccount["accountcode"], financialStart, calculateFrom, calculateTo)
					if opacc["balbrought"]!=0.00:
						receiptcf.append({"toby":"","particulars":''.join(cbAccount["accountname"]),"amount":"%.2f"%float(opacc["balbrought"])+"(%s)"%(opacc["openbaltype"]),"accountcode":cbAccount["accountcode"]})
						if opacc["openbaltype"]=="Dr":
							rctotal += float(opacc["balbrought"])
						if opacc["openbaltype"]=="Cr":
							rctotal -= float(opacc["balbrought"])
					if opacc["curbal"]!=0.00:
						closinggrid.append({"toby":"","particulars":''.join(cbAccount["accountname"]),"amount":"%.2f"%float(opacc["curbal"])+"(%s)"%(opacc["baltype"]),"accountcode":cbAccount["accountcode"]})
						if opacc["baltype"]=="Dr":
							pytotal += float(opacc["curbal"])
						if opacc["baltype"]=="Cr":
							pytotal -= float(opacc["curbal"])
					transactionsRecords = eng.execute("select crs,drs from vouchers where voucherdate >= '%s'  and voucherdate < '%s' and vouchertype != 'contra' and (drs ? '%s' or crs ? '%s');"%(calculateFrom, calculateTo, cbAccount["accountcode"],cbAccount["accountcode"]))
					transactions = transactionsRecords.fetchall()
					for transaction in transactions:
						for cr in transaction["crs"]:
							if cr not in rcaccountcodes and int(cr) != int(cbAccount["accountcode"]):
								rcaccountcodes.append(cr)
								rccalbaldata = self.calculateBalance(cr, financialStart, calculateFrom, calculateTo)
								rcaccountname = eng.execute("select accountname from accounts where accountcode=%d"%(int(cr)))
								rcacc= ''.join(rcaccountname.fetchone())
								rctransactionsgrid.append({"toby":"To","particulars":rcacc,"amount":"%.2f"%float(rccalbaldata["totalcrbal"]),"accountcode":int(cr)})
								rctotal += float(rccalbaldata["totalcrbal"])
						for dr in transaction["drs"]:
							if dr not in pyaccountcodes and int(dr) != int(cbAccount["accountcode"]):
								pyaccountcodes.append(dr)
								pycalbaldata = self.calculateBalance(dr, financialStart, calculateFrom, calculateTo)
								pyaccountname = eng.execute("select accountname from accounts where accountcode=%d"%(int(dr)))
								pyacc= ''.join(pyaccountname.fetchone())
								paymentcf.append({"toby":"By","particulars":pyacc,"amount":"%.2f"%float(pycalbaldata["totaldrbal"]),"accountcode":int(dr)})
								pytotal += float(pycalbaldata["totaldrbal"])
				receiptcf.extend(rctransactionsgrid)
				receiptcf.append({"toby":"","particulars":"Total","amount":"%.2f"%float(rctotal),"accountcode":""})
				paymentcf.extend(closinggrid)
				paymentcf.append({"toby":"","particulars":"Total","amount":"%.2f"%float(pytotal),"accountcode":""})
				return {"gkstatus":enumdict["Success"],"rcgkresult":receiptcf,"pygkresult":paymentcf}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param='type=projectstatement', renderer='json')
	def projectStatement(self):
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
				calculateTo = self.request.params["calculateto"]
				financialStart = self.request.params["financialstart"]
				projectCode= self.request.params["projectcode"]
				totalDr = 0.00
				totalCr = 0.00
				grpaccsdata = eng.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Direct Income','Indirect Expense','Indirect Income'))"%(authDetails["orgcode"],authDetails["orgcode"]))
				grpaccs = grpaccsdata.fetchall()
				srno = 1
				projectStatement = []
				for accountRow in grpaccs:
					group = eng.execute("select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"%(int(accountRow["accountcode"]),int(accountRow["accountcode"])))
					groupRow = group.fetchone()
					drresult = eng.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s' and projectcode=%d"%(int(accountRow["accountcode"]),financialStart, calculateTo, int(projectCode)))
					drresultRow = drresult.fetchone()
					crresult = eng.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s' and projectcode=%d"%(int(accountRow["accountcode"]),financialStart, calculateTo, int(projectCode)))
					crresultRow = crresult.fetchone()
					statementRow ={"srno":srno,"accountcode":accountRow["accountcode"],"accountname":accountRow["accountname"],"groupname":groupRow["groupname"],"totalout":'%.2f'%float(totalDr),"totalin":'%.2f'%float(totalCr)}
					if drresultRow["total"]==None:
						statementRow["totalout"] = '%.2f'%float(0.00)
					else:
						statementRow["totalout"] = '%.2f'%float(drresultRow["total"])
						totalDr = totalDr + drresultRow["total"]
					if crresultRow["total"]==None:
						statementRow["totalin"] = '%.2f'%float(0.00)
					else:
						statementRow["totalin"] = '%.2f'%float(crresultRow["total"])
						totalCr = totalCr + crresultRow["total"]
					if float(statementRow["totalout"]) == 0 and float(statementRow["totalin"]) == 0:
						continue
					srno = srno +1
					projectStatement.append(statementRow)
				projectStatement.append({"srno":"","accountcode":"","accountname":"","groupname":"Total","totalout":'%.2f'%float(totalDr),"totalin":'%.2f'%float(totalCr)})
				return {"gkstatus":enumdict["Success"],"gkresult":projectStatement}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param="type=verticalbalancesheet",renderer="json")
	def balanceSheet(self):
		"""
		Purpose:
		Gets the list of groups and their respective balances
		takes organisation code and end date as input parameter
		Description:
		This function is used to generate balance sheet for a given organisation and the given time period.
		This function takes orgcode and end date as the input parameters
		This function is called when the type=balaancesheet is passed to the /report url.
		orgcode is extracted from the header
		end date is extracted from the request_params
		The accountcode is extracted from the database under  groupcode for groups relevent to balance sheet (meaning all groups except income and expence groups).
		the  groupbalance will be initialized to 0.0 for each group.
		this accountcode is sent to the calculateBalance function along with financialstart, calculateTo
		the function will return the closing balance related to each account which will be later added or subtracted according to the accounting rules from the group balance
		the above statements will be running in a loop for each group.
		Later all the group balances for sources and application will be added
		the difference in the amounts of sourcetotal and applicationtotal will be found
		the function will return the gkstatus and gkresult which contains a list of dictionaries where every dictionary represents a row with two key-value pairs each representing columns

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
				orgcode = authDetails["orgcode"]
				financialstart = con.execute("select yearstart, orgtype from organisation where orgcode = %d"%int(orgcode))
				financialstartRow = financialstart.fetchone()
				financialStart = financialstartRow["yearstart"]
				orgtype = financialstartRow["orgtype"]
				calculateTo = self.request.params["calculateto"]
				calculateTo = calculateTo
				balanceSheet=[]
				sourcesTotal = 0.00
				applicationsTotal = 0.00
				difference = 0.00
				balanceSheet.append({"groupname":"Sources:","amount":""})
				capital_Corpus = ""
				if orgtype == "Profit Making":
					capital_Corpus = "Capital"
				if orgtype == "Not For Profit":
					capital_Corpus = "Corpus"
				groupWiseTotal = 0.00


				#Calculate grouptotal for group Capital/Corpus
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = '%s' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s'));"%(orgcode, orgcode, capital_Corpus, orgcode, capital_Corpus))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						print accountDetails
						groupWiseTotal += accountDetails["balbrought"]
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal -= accountDetails["balbrought"]
				sourcesTotal += groupWiseTotal
				balanceSheet.append({"groupname":capital_Corpus, "amount":"%.2f"%(groupWiseTotal)})


				#Calculate grouptotal for group Loans(Liability)
				groupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Liability)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Loans(Liability)'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal -= accountDetails["curbal"]
				sourcesTotal += groupWiseTotal
				balanceSheet.append({"groupname": "Loans(Liability)", "amount":"%.2f"%(groupWiseTotal)})


				print "Current Liabilities"
				#Calculate grouptotal for group Current Liabilities
				groupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Liabilities' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Current Liabilities'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal -= accountDetails["curbal"]
				sourcesTotal += groupWiseTotal
				balanceSheet.append({"groupname":"Current Liabilities", "amount":"%.2f"%(groupWiseTotal)})


				print "Reserves"
				#Calculate grouptotal for group "Reserves"
				groupWiseTotal = 0.00
				incomeTotal = 0.00
				expenseTotal = 0.00

				#Calculate all income(Direct and Indirect Income)
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Income','Indirect Income') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Income','Indirect Income')));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						incomeTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						incomeTotal -= accountDetails["curbal"]

				#Calculate all expense(Direct and Indirect Expense)
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Expense','Indirect Expense') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Indirect Expense')));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						expenseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						expenseTotal -= accountDetails["curbal"]


				#Calculate total of all accounts in Reserves except(Direct and Indirect Income, Expense)
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Reserves' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Reserves'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal -= accountDetails["curbal"]


				#Calculate Profit/Loss for the year
				profit = 0.00
				if (expenseTotal > incomeTotal):
					profit = expenseTotal - incomeTotal
					groupWiseTotal -= profit
					balanceSheet.append({"groupname":"Reserves", "amount":"%.2f"%(groupWiseTotal)})
					balanceSheet.append({"groupname":"Loss for the Year:","amount":"%.2f"%(profit)})
				if (expenseTotal < incomeTotal):
					profit = incomeTotal - expenseTotal
					groupWiseTotal += profit
					balanceSheet.append({"groupname":"Reserves", "amount":"%.2f"%(groupWiseTotal)})
					balanceSheet.append({"groupname":"Profit for the Year:","amount":"%.2f"%(profit)})
				if (expenseTotal == incomeTotal):
					balanceSheet.append({"groupname":"Reserves", "amount":"%.2f"%(groupWiseTotal)})


				sourcesTotal += groupWiseTotal
				balanceSheet.append({"groupname":"Total", "amount":"%.2f"%(sourcesTotal)})

				#Applications:
				balanceSheet.append({"groupname":"Applications:","amount":""})


				#Calculate grouptotal for group "Fixed Assets"
				groupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Fixed Assets' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Fixed Assets'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += groupWiseTotal
				balanceSheet.append({"groupname":"Fixed Assets", "amount":"%.2f"%(groupWiseTotal)})


				print "Investments"
				#Calculate grouptotal for group "Investments"
				groupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Investments' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Investments'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += groupWiseTotal
				balanceSheet.append({"groupname": "Investments", "amount":"%.2f"%(groupWiseTotal)})


				print "Current Assets"
				#Calculate grouptotal for group "Current Assets"
				groupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Assets' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Current Assets'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += groupWiseTotal
				balanceSheet.append({"groupname":"Current Assets", "amount":"%.2f"%(groupWiseTotal)})


				print "Loans(Asset)"
				#Calculate grouptotal for group Loans(Asset)
				groupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Asset)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Loans(Asset)'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += groupWiseTotal
				balanceSheet.append({"groupname":"Loans(Asset)", "amount":"%.2f"%(groupWiseTotal)})


				print "Miscellaneous"
				#Calculate grouptotal for group "Miscellaneous Expenses(Asset)"
				groupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Miscellaneous Expenses(Asset)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Miscellaneous Expenses(Asset)'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += groupWiseTotal
				balanceSheet.append({"groupname":"Miscellaneous Expenses(Asset)", "amount":"%.2f"%(groupWiseTotal)})

				balanceSheet.append({"groupname":"Total", "amount":"%.2f"%(applicationsTotal)})

				difference = abs(sourcesTotal - applicationsTotal)
				balanceSheet.append({"groupname":"Difference", "amount":"%.2f"%(difference)})

				return {"gkstatus":enumdict["Success"],"gkresult":balanceSheet}


			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}



	@view_config(request_param="type=conventionalbalancesheet",renderer="json")
	def conventionalbalanceSheet(self):
		"""
		Purpose:
		Gets the list of groups and their respective balances
		takes organisation code and end date as input parameter
		Description:
		This function is used to generate balance sheet for a given organisation and the given time period.
		This function takes orgcode and end date as the input parameters
		This function is called when the type=conventionalbalancesheet is passed to the /report url.
		orgcode is extracted from the header
		end date is extracted from the request_params
		The accountcode is extracted from the database under  groupcode for groups relevent to balance sheet (meaning all groups except income and expence groups).
		the  groupbalance will be initialized to 0.0 for each group.
		this accountcode is sent to the calculateBalance function along with financialstart, calculateTo
		the function will return the closing balance related to each account which will be later added or subtracted according to the accounting rules from the group balance
		the above statements will be running in a loop for each group.
		Later all the group balances for sources and application will be added
		the difference in the amounts of sourcetotal and applicationtotal will be found
		the function will return the gkstatus and gkresult which contains a list of dictionaries where every dictionary represents a row with two key-value pairs each representing columns
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
				orgcode = authDetails["orgcode"]
				financialstart = con.execute("select yearstart, orgtype from organisation where orgcode = %d"%int(orgcode))
				financialstartRow = financialstart.fetchone()
				financialStart = financialstartRow["yearstart"]
				orgtype = financialstartRow["orgtype"]
				calculateTo = self.request.params["calculateto"]
				calculateTo = calculateTo
				balanceSheet=[]
				sourcegroupWiseTotal = 0.00
				applicationgroupWiseTotal = 0.00
				sourcesTotal = 0.00
				applicationsTotal = 0.00
				difference = 0.00
				balanceSheet.append({"sourcesgroupname":"Sources:","sourceamount":"","appgroupname":"Applications:","applicationamount":""})
				capital_Corpus = ""
				if orgtype == "Profit Making":
					capital_Corpus = "Capital"
				if orgtype == "Not For Profit":
					capital_Corpus = "Corpus"


				#Calculate grouptotal for group Capital/Corpus
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = '%s' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s'));"%(orgcode, orgcode, capital_Corpus, orgcode, capital_Corpus))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						sourcegroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						sourcegroupWiseTotal -= accountDetails["curbal"]
				sourcesTotal += sourcegroupWiseTotal

				#Calculate grouptotal for group "Fixed Assets"
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Fixed Assets' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Fixed Assets'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						applicationgroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						applicationgroupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += applicationgroupWiseTotal
				balanceSheet.append({"sourcesgroupname":capital_Corpus,"sourceamount":"%.2f"%(sourcegroupWiseTotal),"appgroupname":"Fixed Assets","applicationamount":"%.2f"%(applicationgroupWiseTotal)})


				#Calculate grouptotal for group Loans(Liability)
				sourcegroupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Liability)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Loans(Liability)'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						sourcegroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						sourcegroupWiseTotal -= accountDetails["curbal"]
				sourcesTotal += sourcegroupWiseTotal


				#Calculate grouptotal for group "Investments"
				applicationgroupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Investments' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Investments'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						applicationgroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						applicationgroupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += applicationgroupWiseTotal
				balanceSheet.append({"sourcesgroupname":"Loans(Liability)","sourceamount":"%.2f"%(sourcegroupWiseTotal),"appgroupname":"Investments","applicationamount":"%.2f"%(applicationgroupWiseTotal)})


				#Calculate grouptotal for group Current Liabilities
				sourcegroupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Liabilities' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Current Liabilities'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						sourcegroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						sourcegroupWiseTotal -= accountDetails["curbal"]
				sourcesTotal += sourcegroupWiseTotal


				#Calculate grouptotal for group "Current Assets"
				applicationgroupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Assets' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Current Assets'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						applicationgroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						applicationgroupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += applicationgroupWiseTotal
				balanceSheet.append({"sourcesgroupname":"Current Liabilities","sourceamount":"%.2f"%(sourcegroupWiseTotal),"appgroupname":"Current Assets","applicationamount":"%.2f"%(applicationgroupWiseTotal)})


				#Calculate grouptotal for group "Reserves"
				sourcegroupWiseTotal = 0.00
				incomeTotal = 0.00
				expenseTotal = 0.00
				#Calculate all income(Direct and Indirect Income)
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Income','Indirect Income') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Income','Indirect Income')));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						incomeTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						incomeTotal -= accountDetails["curbal"]

				#Calculate all expense(Direct and Indirect Expense)
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Expense','Indirect Expense') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Indirect Expense')));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						expenseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						expenseTotal -= accountDetails["curbal"]

				#Calculate total of all accounts in Reserves (except Direct and Indirect Income, Expense)
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Reserves' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Reserves'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						sourcegroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						sourcegroupWiseTotal -= accountDetails["curbal"]

				#Calculate Profit/Loss for the year
				profit = 0.00
				if (expenseTotal > incomeTotal):
					profit = expenseTotal - incomeTotal
					sourcegroupWiseTotal -= profit
				if (expenseTotal < incomeTotal):
					profit = incomeTotal - expenseTotal
					sourcegroupWiseTotal += profit

				sourcesTotal += sourcegroupWiseTotal

				#Calculate grouptotal for group Loans(Asset)
				applicationgroupWiseTotall = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Asset)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Loans(Asset)'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						applicationgroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						applicationgroupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += applicationgroupWiseTotal
				balanceSheet.append({"sourcesgroupname":"Reserves","sourceamount":"%.2f"%(sourcegroupWiseTotal),"appgroupname":"Loans(Asset)","applicationamount":"%.2f"%(applicationgroupWiseTotal)})


				#Calculate grouptotal for group "Miscellaneous Expenses(Asset)"
				applicationgroupWiseTotal = 0.00
				accountcodeData = eng.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Miscellaneous Expenses(Asset)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Miscellaneous Expenses(Asset)'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = self.calculateBalance(accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						applicationgroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						applicationgroupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += applicationgroupWiseTotal

				if (expenseTotal > incomeTotal):
					balanceSheet.append({"sourcesgroupname":"Loss for the Year","sourceamount":"%.2f"%(profit),"appgroupname":"Miscellaneous Expenses(Asset)","applicationamount":"%.2f"%(applicationgroupWiseTotal)})
				if (expenseTotal < incomeTotal):
					balanceSheet.append({"sourcesgroupname":"Profit for the Year","sourceamount":"%.2f"%(profit),"appgroupname":"Miscellaneous Expenses(Asset)","applicationamount":"%.2f"%(applicationgroupWiseTotal)})
				if (expenseTotal == incomeTotal):
					balanceSheet.append({"sourcesgroupname":"","sourceamount":"","appgroupname":"Miscellaneous Expenses(Asset)","applicationamount":"%.2f"%(applicationgroupWiseTotal)})

				#Total of Sources and Applications
				balanceSheet.append({"sourcesgroupname":"Total","sourceamount":"%.2f"%(sourcesTotal),"appgroupname":"Total","applicationamount":"%.2f"%(applicationsTotal)})

				#Difference
				difference = abs(sourcesTotal - applicationsTotal)
				balanceSheet.append({"sourcesgroupname":"Difference","sourceamount":"%.2f"%(difference),"appgroupname":"","applicationamount":""})

				return {"gkstatus":enumdict["Success"],"gkresult":balanceSheet}


			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
