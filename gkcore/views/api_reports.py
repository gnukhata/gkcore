
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
"Vanita Rajpurohit" <vanita.rajpurohit9819@gmail.com>
"Prajkta Patkar" <prajkta.patkar007@gmail.com>
"""


from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models.gkdb import accounts, vouchers, groupsubgroups, projects, organisation, users, voucherbin,delchal,invoice,customerandsupplier,stock,product,transfernote,goprod, dcinv
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
from gkcore.models.meta import dbconnect
from sqlalchemy.sql.functions import func
from time import strftime, strptime


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

def calculateBalance(con,accountCode,financialStart,calculateFrom,calculateTo):
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
	groupData = con.execute("select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"%(int(accountCode),int(accountCode)))
	groupRecord = groupData.fetchone()
	groupName = groupRecord["groupname"]
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
		tdrfrm = con.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s'"%(int(accountCode),financialStart,calculateFrom))
		tcrfrm = con.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s'"%(int(accountCode),financialStart,calculateFrom))
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
	tdrfrm = con.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s'"%(int(accountCode),calculateFrom, calculateTo))
	tdrRow = tdrfrm.fetchone()
	tcrfrm = con.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s'"%(int(accountCode),calculateFrom, calculateTo))
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

@view_defaults(route_name='report' , request_method='GET')
class api_reports(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection

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
				self.con = eng.connect()
				orgcode = authDetails["orgcode"]
				accountCode = self.request.params["accountcode"]
				accNameData= self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode== accountCode))
				row = accNameData.fetchone()
				accname = row["accountname"]
				finStartData = self.con.execute(select([organisation.c.yearstart]).where(organisation.c.orgcode==orgcode))
				finRow = finStartData.fetchone()
				financialStart = finRow['yearstart']
				finEndData = self.con.execute(select([organisation.c.yearend]).where(organisation.c.orgcode == orgcode))
				finEndrow = finEndData.fetchone()
				financialEnd = finEndrow['yearend']
				monthCounter = 1
				startMonthDate = financialStart
				endMonthDate = date(startMonthDate.year, startMonthDate.month, (calendar.monthrange(startMonthDate.year, startMonthDate.month)[1]))
				monthlyBal = []
				while endMonthDate <= financialEnd:
					count = self.con.execute("select count(vouchercode) as vcount from vouchers where voucherdate<='%s' and voucherdate>='%s' and orgcode='%d' and (drs ? '%s' or crs ? '%s') "%(endMonthDate, startMonthDate, orgcode, accountCode, accountCode))
					count = count.fetchone()
					countDr = self.con.execute("select count(vouchercode) as vcount from vouchers where voucherdate<='%s' and voucherdate>='%s' and orgcode='%d' and (drs ? '%s') "%(endMonthDate, startMonthDate, orgcode, accountCode))
					countDr = countDr.fetchone()
					countCr = self.con.execute("select count(vouchercode) as vcount from vouchers where voucherdate<='%s' and voucherdate>='%s' and orgcode='%d' and (crs ? '%s') "%(endMonthDate, startMonthDate, orgcode, accountCode))
					countCr = countCr.fetchone()
					countLock = self.con.execute("select count(vouchercode) as vcount from vouchers where voucherdate<='%s' and voucherdate>='%s' and orgcode='%d' and lockflag='t' and (drs ? '%s' or crs ? '%s') "%(endMonthDate, startMonthDate, orgcode, accountCode, accountCode))
					countLock = countLock.fetchone()
					adverseflag = 0
					monthClBal =  calculateBalance(self.con,accountCode, str(financialStart), str(financialStart), str(endMonthDate))
					if (monthClBal["baltype"] == "Dr"):
						if ((monthClBal["grpname"] == 'Corpus' or monthClBal["grpname"] == 'Capital' or monthClBal["grpname"] == 'Current Liabilities' or monthClBal["grpname"] == 'Loans(Liability)' or monthClBal["grpname"] == 'Reserves' or monthClBal["grpname"] == 'Indirect Income' or monthClBal["grpname"] == 'Direct Income') and monthClBal["curbal"]!=0) :
							adverseflag = 1
						clBal = {"month": calendar.month_name[startMonthDate.month], "Dr": "%.2f"%float(monthClBal["curbal"]), "Cr":"", "period":str(startMonthDate)+":"+str(endMonthDate), "vcount":count["vcount"], "vcountDr":countDr["vcount"], "vcountCr":countCr["vcount"], "vcountLock":countLock["vcount"], "advflag":adverseflag}
						monthlyBal.append(clBal)
					if (monthClBal["baltype"] == "Cr"):
						if ((monthClBal["grpname"] == 'Current Assets' or monthClBal["grpname"] == 'Fixed Assets'or monthClBal["grpname"] == 'Investments' or monthClBal["grpname"] == 'Loans(Asset)' or monthClBal["grpname"] == 'Miscellaneous Expenses(Asset)' or monthClBal["grpname"] == 'Indirect Expense' or monthClBal["grpname"] == 'Direct Expense') and monthClBal["curbal"]!=0):
							adverseflag = 1
						clBal = {"month": calendar.month_name[startMonthDate.month], "Dr": "", "Cr":"%.2f"%float(monthClBal["curbal"]), "period":str(startMonthDate)+":"+str(endMonthDate), "vcount":count["vcount"], "vcountDr":countDr["vcount"], "vcountCr":countCr["vcount"], "vcountLock":countLock["vcount"], "advflag":adverseflag}
						monthlyBal.append(clBal)
					if (monthClBal["baltype"] == ""):
						if ((monthClBal["grpname"] == 'Corpus' or monthClBal["grpname"] == 'Capital' or monthClBal["grpname"] == 'Current Liabilities' or monthClBal["grpname"] == 'Loans(Liability)' or monthClBal["grpname"] == 'Reserves' or monthClBal["grpname"] == 'Indirect Income' or monthClBal["grpname"] == 'Direct Income') and count["vcount"]!=0):
							clBal = {"month": calendar.month_name[startMonthDate.month], "Dr": "", "Cr":"%.2f"%float(monthClBal["curbal"]), "period":str(startMonthDate)+":"+str(endMonthDate), "vcount":count["vcount"], "vcountDr":countDr["vcount"], "vcountCr":countCr["vcount"], "vcountLock":countLock["vcount"], "advflag":adverseflag}
						if ((monthClBal["grpname"] == 'Current Assets' or monthClBal["grpname"] == 'Fixed Assets'or monthClBal["grpname"] == 'Investments' or monthClBal["grpname"] == 'Loans(Asset)' or monthClBal["grpname"] == 'Miscellaneous Expenses(Asset)' or monthClBal["grpname"] == 'Indirect Expense' or monthClBal["grpname"] == 'Direct Expense') and count["vcount"]!=0):
							clBal = {"month": calendar.month_name[startMonthDate.month], "Dr":"%.2f"%float(monthClBal["curbal"]), "Cr":"", "period":str(startMonthDate)+":"+str(endMonthDate), "vcount":count["vcount"], "vcountDr":countDr["vcount"], "vcountCr":countCr["vcount"], "vcountLock":countLock["vcount"], "advflag":adverseflag}
						if (count["vcount"]==0):
							clBal = {"month": calendar.month_name[startMonthDate.month], "Dr":"", "Cr":"", "period":str(startMonthDate)+":"+str(endMonthDate), "vcount":count["vcount"], "vcountDr":countDr["vcount"], "vcountCr":countCr["vcount"], "vcountLock":countLock["vcount"], "advflag":adverseflag}
						monthlyBal.append(clBal)
					startMonthDate = date(financialStart.year,financialStart.month,financialStart.day) + monthdelta(monthCounter)
					endMonthDate = date(startMonthDate.year, startMonthDate.month, calendar.monthrange(startMonthDate.year, startMonthDate.month)[1])
					monthCounter  +=1
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult": monthlyBal, "accountcode":accountCode,"accountname":accname}

			except Exception as E:
				print E
				self.con.close()
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
		in addition it also provides a flag to indicate if the balance is adverce.
		In addition to all this, there are 2 other columns containing running total Dr and Cr,
		this is used in Printing.
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
				self.con = eng.connect()
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
				orgcode = authDetails["orgcode"]
				accountCode = self.request.params["accountcode"]
				calculateFrom = self.request.params["calculatefrom"]
				calculateTo = self.request.params["calculateto"]
				projectCode =self.request.params["projectcode"]
				financialStart = self.request.params["financialstart"]
				calbalDict = calculateBalance(self.con,accountCode,financialStart,calculateFrom,calculateTo)
				vouchergrid = []
				bal = 0.00
				adverseflag = 0
				accnamerow = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(accountCode)))
				accname = accnamerow.fetchone()
				headerrow = {"accountname":''.join(accname),"projectname":"","calculateto":datetime.strftime(datetime.strptime(str(calculateTo),"%Y-%m-%d").date(),'%d-%m-%Y'),"calculatefrom":datetime.strftime(datetime.strptime(str(calculateFrom),"%Y-%m-%d").date(),'%d-%m-%Y')}
				if projectCode!="":
					prjnamerow = self.con.execute(select([projects.c.projectname]).where(projects.c.projectcode==int(projectCode)))
					prjname = prjnamerow.fetchone()
					headerrow["projectname"]=''.join(prjname)

				if projectCode == "" and calbalDict["balbrought"]>0:
					openingrow={"vouchercode":"","vouchernumber":"","voucherdate":datetime.strftime(datetime.strptime(str(calculateFrom),"%Y-%m-%d").date(),'%d-%m-%Y'),"balance":"","narration":"","status":"", "vouchertype":"", "advflag":""}
					vfrom = datetime.strptime(str(calculateFrom),"%Y-%m-%d")
					fstart = datetime.strptime(str(financialStart),"%Y-%m-%d")
					if vfrom==fstart:
						openingrow["particulars"]=[{'accountname':"Opening Balance"}]
					if vfrom>fstart:
						openingrow["particulars"]=[{'accountname':"Balance B/F"}]
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
					transactionsRecords = self.con.execute("select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s' or crs ? '%s') order by voucherdate,vouchercode ;"%(calculateFrom, calculateTo, accountCode,accountCode))
				else:
					transactionsRecords = self.con.execute("select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and projectcode=%d and (drs ? '%s' or crs ? '%s') order by voucherdate, vouchercode;"%(calculateFrom, calculateTo,int(projectCode),accountCode,accountCode))

				transactions = transactionsRecords.fetchall()

				crtotal = 0.00
				drtotal = 0.00
				for transaction in transactions:
					ledgerRecord = {"vouchercode":transaction["vouchercode"],"vouchernumber":transaction["vouchernumber"],"voucherdate":str(transaction["voucherdate"].date().strftime('%d-%m-%Y')),"narration":transaction["narration"],"status":transaction["lockflag"], "vouchertype":transaction["vouchertype"], "advflag":""}
					if transaction["drs"].has_key(accountCode):
						ledgerRecord["Dr"] = "%.2f"%float(transaction["drs"][accountCode])
						ledgerRecord["Cr"] = ""
						drtotal += float(transaction["drs"][accountCode])
						par=[]
						for cr in transaction["crs"].keys():
							accountnameRow = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(cr)))
							accountname = accountnameRow.fetchone()
							if len(transaction['crs'])>1:
								par.append({'accountname':accountname['accountname'],'amount':transaction['crs'][cr]})
							else:
								par.append({'accountname':accountname['accountname']})
						ledgerRecord["particulars"] = par
						bal = bal + float(transaction["drs"][accountCode])

					if transaction["crs"].has_key(accountCode):
						ledgerRecord["Cr"] = "%.2f"%float(transaction["crs"][accountCode])
						ledgerRecord["Dr"] = ""
						crtotal += float(transaction["crs"][accountCode])
						par=[]
						for dr in transaction["drs"].keys():
							accountnameRow = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(dr)))
							accountname = accountnameRow.fetchone()
							if len(transaction['drs'])>1:
								par.append({'accountname':accountname['accountname'],'amount':transaction['drs'][dr]})
							else:
								par.append({'accountname':accountname['accountname']})
						ledgerRecord["particulars"] = par
						bal = bal - float(transaction["crs"][accountCode])
					if bal>0:
						ledgerRecord["balance"] = "%.2f(Dr)"%(bal)
					elif bal<0:
						ledgerRecord["balance"] = "%.2f(Cr)"%(abs(bal))
					else :
						ledgerRecord["balance"] = "%.2f"%(0.00)
					ledgerRecord["ttlRunDr"] = "%.2f"%(drtotal)
					ledgerRecord["ttlRunCr"] = "%.2f"%(crtotal)
					vouchergrid.append(ledgerRecord)
				if projectCode=="":
					if calbalDict["openbaltype"] == "Cr":
						calbalDict["totalcrbal"] -= calbalDict["balbrought"]
					if calbalDict["openbaltype"] == "Dr":
						calbalDict["totaldrbal"] -= calbalDict["balbrought"]
					ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":"","narration":"","Dr":"%.2f"%(calbalDict["totaldrbal"]),"Cr":"%.2f"%(calbalDict["totalcrbal"]),"particulars":[{'accountname':"Total of Transactions"}],"balance":"","status":"", "vouchertype":"", "advflag":""}
					vouchergrid.append(ledgerRecord)

					if calbalDict["curbal"]!=0:
						ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":datetime.strftime(datetime.strptime(str(calculateTo),"%Y-%m-%d").date(),'%d-%m-%Y'),"narration":"", "particulars":[{'accountname':"Closing Balance C/F"}],"balance":"","status":"", "vouchertype":""}
						if calbalDict["baltype"] == "Cr":
							if (calbalDict["grpname"] == 'Current Assets' or calbalDict["grpname"] == 'Fixed Assets'or calbalDict["grpname"] == 'Investments' or calbalDict["grpname"] == 'Loans(Asset)' or calbalDict["grpname"] == 'Miscellaneous Expenses(Asset)') and calbalDict["curbal"]!=0:
								adverseflag = 1
							ledgerRecord["Dr"] = "%.2f"%(calbalDict["curbal"])
							ledgerRecord["Cr"] = ""

						if calbalDict["baltype"] == "Dr":
							if (calbalDict["grpname"] == 'Corpus' or calbalDict["grpname"] == 'Capital'or calbalDict["grpname"] == 'Current Liabilities' or calbalDict["grpname"] == 'Loans(Liability)' or calbalDict["grpname"] == 'Reserves') and calbalDict["curbal"]!=0:
								adverseflag = 1
							ledgerRecord["Cr"] = "%.2f"%(calbalDict["curbal"])
							ledgerRecord["Dr"] = ""
						ledgerRecord["advflag"] = adverseflag
						vouchergrid.append(ledgerRecord)

					if (calbalDict["curbal"]==0 and calbalDict["balbrought"]!=0) or calbalDict["curbal"]!=0 or calbalDict["balbrought"]!=0:
						ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":"","narration":"", "particulars":[{'accountname':"Grand Total"}],"balance":"","status":"", "vouchertype":"", "advflag":""}
						if projectCode == "" and calbalDict["balbrought"]>0:
							if calbalDict["openbaltype"] =="Dr":
								calbalDict["totaldrbal"] +=  float(calbalDict["balbrought"])

							if calbalDict["openbaltype"] =="Cr":
								calbalDict["totalcrbal"] +=  float(calbalDict["balbrought"])
							if calbalDict["baltype"] == "Cr":
								calbalDict["totaldrbal"] += float(calbalDict["curbal"])

							if calbalDict["baltype"] == "Dr":
								calbalDict["totalcrbal"] += float(calbalDict["curbal"])
							ledgerRecord["Dr"] = "%.2f"%(calbalDict["totaldrbal"])
							ledgerRecord["Cr"] = "%.2f"%(calbalDict["totaldrbal"])
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
					ledgerRecord = {"vouchercode":"","vouchernumber":"","voucherdate":"","narration":"","Dr":"%.2f"%(drtotal),"Cr":"%.2f"%(crtotal),"particulars":[{'accountname':"Total of Transactions"}],"balance":"","status":"", "vouchertype":"", "advflag":""}
					vouchergrid.append(ledgerRecord)
				self.con.close()


				return {"gkstatus":enumdict["Success"],"gkresult":vouchergrid,"userrole":urole["userrole"],"ledgerheader":headerrow}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}


	@view_config(request_param='type=crdrledger', renderer='json')
	def crdrledger(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus": enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				ur = getUserRole(authDetails["userid"])
				urole = ur["gkresult"]
				orgcode = authDetails["orgcode"]
				accountCode = self.request.params["accountcode"]
				side = self.request.params["side"]
				calculateFrom = self.request.params["calculatefrom"]
				calculateTo = self.request.params["calculateto"]
				projectCode =self.request.params["projectcode"]
				financialStart = self.request.params["financialstart"]
				vouchergrid = []
				bal=0.00
				accnamerow = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(accountCode)))
				accname = accnamerow.fetchone()
				headerrow = {"accountname":accname["accountname"],"projectname":"","calculateto":datetime.strftime(datetime.strptime(str(calculateTo),"%Y-%m-%d").date(),'%d-%m-%Y'),"calculatefrom":datetime.strftime(datetime.strptime(str(calculateFrom),"%Y-%m-%d").date(),'%d-%m-%Y')}
				if projectCode!="":
					prjnamerow = self.con.execute(select([projects.c.projectname]).where(projects.c.projectcode==int(projectCode)))
					prjname = prjnamerow.fetchone()
					headerrow["projectname"]=prjname["projectname"]
				if side=="dr":
					if projectCode == "":
						transactionsRecords = self.con.execute("select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') order by voucherdate;"%(calculateFrom, calculateTo, accountCode))
					else:
						transactionsRecords = self.con.execute("select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and projectcode=%d and (drs ? '%s') order by voucherdate;"%(calculateFrom, calculateTo,int(projectCode),accountCode))
					transactions = transactionsRecords.fetchall()
					for transaction in transactions:
						ledgerRecord = {"vouchercode":transaction["vouchercode"],"vouchernumber":transaction["vouchernumber"],"voucherdate":str(transaction["voucherdate"].date().strftime('%d-%m-%Y')),"narration":transaction["narration"],"status":transaction["lockflag"], "vouchertype":transaction["vouchertype"]}
						ledgerRecord["Dr"] = "%.2f"%float(transaction["drs"][accountCode])
						ledgerRecord["Cr"] = ""
						par=[]
						for cr in transaction["crs"].keys():
							accountnameRow = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(cr)))
							accountname = accountnameRow.fetchone()
							if len(transaction['crs'])>1:
								par.append({'accountname':accountname['accountname'],'amount':transaction['crs'][cr]})
							else:
								par.append({'accountname':accountname['accountname']})
						ledgerRecord["particulars"] = par
						vouchergrid.append(ledgerRecord)
					self.con.close()
					return {"gkstatus":enumdict["Success"],"gkresult":vouchergrid,"userrole":urole["userrole"],"ledgerheader":headerrow}

				if side=="cr":
					if projectCode == "":
						transactionsRecords = self.con.execute("select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') order by voucherdate;"%(calculateFrom, calculateTo, accountCode))
					else:
						transactionsRecords = self.con.execute("select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and projectcode=%d and (crs ? '%s') order by voucherdate;"%(calculateFrom, calculateTo,int(projectCode),accountCode))
					transactions = transactionsRecords.fetchall()
					for transaction in transactions:
						ledgerRecord = {"vouchercode":transaction["vouchercode"],"vouchernumber":transaction["vouchernumber"],"voucherdate":str(transaction["voucherdate"].date().strftime('%d-%m-%Y')),"narration":transaction["narration"],"status":transaction["lockflag"], "vouchertype":transaction["vouchertype"]}
						ledgerRecord["Cr"] = "%.2f"%float(transaction["crs"][accountCode])
						ledgerRecord["Dr"] = ""
						par=[]
						for dr in transaction["drs"].keys():
							accountnameRow = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(dr)))
							accountname = accountnameRow.fetchone()
							if len(transaction['drs'])>1:
								par.append({'accountname':accountname['accountname'],'amount':transaction['drs'][dr]})
							else:
								par.append({'accountname':accountname['accountname']})
						ledgerRecord["particulars"] = par
						vouchergrid.append(ledgerRecord)
					self.con.close()
					return {"gkstatus":enumdict["Success"],"gkresult":vouchergrid,"userrole":urole["userrole"],"ledgerheader":headerrow}
			except:
				self.con.close()
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
		In addition to this data we have 2 other columns,
		Total Running total for Dr and Cr useful for printing.
		Same applies to the following methods in this class for gross and extended trial balances.
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
				self.con = eng.connect()
				accountData = self.con.execute(select([accounts.c.accountcode,accounts.c.accountname]).where(accounts.c.orgcode==authDetails["orgcode"] ).order_by(accounts.c.accountname) )
				accountRecords = accountData.fetchall()
				ntbGrid = []
				financialStart = self.request.params["financialstart"]
				calculateTo =  self.request.params["calculateto"]
				srno = 0
				totalDr = 0.00
				totalCr = 0.00
				for account in accountRecords:
					adverseflag = 0
					calbalData = calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
					if calbalData["baltype"]=="":
						continue
					srno += 1
					ntbRow = {"accountcode": account["accountcode"],"accountname":account["accountname"],"groupname": calbalData["grpname"],"srno":srno}
					if calbalData["baltype"] == "Dr":
						if (calbalData["grpname"] == 'Corpus' or calbalData["grpname"] == 'Capital' or calbalData["grpname"] == 'Current Liabilities' or calbalData["grpname"] == 'Loans(Liability)' or calbalData["grpname"] == 'Reserves') and calbalData["curbal"]!=0:
							adverseflag = 1
						ntbRow["Dr"] = "%.2f"%(calbalData["curbal"])
						ntbRow["Cr"] = ""
						ntbRow["advflag"] = adverseflag
						totalDr = totalDr + calbalData["curbal"]
					if calbalData["baltype"] == "Cr":
						if (calbalData["grpname"] == 'Current Assets' or calbalData["grpname"] == 'Fixed Assets'or calbalData["grpname"] == 'Investments' or calbalData["grpname"] == 'Loans(Asset)' or calbalData["grpname"] == 'Miscellaneous Expenses(Asset)') and calbalData["curbal"]!=0:
							adverseflag = 1
						ntbRow["Dr"] = ""
						ntbRow["Cr"] = "%.2f"%(calbalData["curbal"])
						ntbRow["advflag"] = adverseflag
						totalCr = totalCr + calbalData["curbal"]
					ntbRow["ttlRunDr"] = "%.2f"%(totalDr)
					ntbRow["ttlRunCr"] = "%.2f"%(totalCr)
					ntbGrid.append(ntbRow)
				ntbGrid.append({"accountcode":"","accountname":"Total","groupname":"","srno":"","Dr": "%.2f"%(totalDr),"Cr":"%.2f"%(totalCr), "advflag":"" })
				if totalDr > totalCr:
					baldiff = totalDr - totalCr
					ntbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Cr": "%.2f"%(baldiff),"Dr":"", "advflag":"" })
					ntbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr": "%.2f"%(totalDr),"Dr":"%.2f"%(totalDr), "advflag":""  })
				if totalDr < totalCr:
					baldiff = totalCr - totalDr
					ntbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Dr": "%.2f"%(baldiff),"Cr":"", "advflag":"" })
					ntbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr": "%.2f"%(totalCr),"Dr":"%.2f"%(totalCr), "advflag":"" })
				self.con.close()


				return {"gkstatus":enumdict["Success"],"gkresult":ntbGrid}
			except:
				self.con.close()
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
				self.con = eng.connect()
				accountData = self.con.execute(select([accounts.c.accountcode,accounts.c.accountname]).where(accounts.c.orgcode==authDetails["orgcode"] ).order_by(accounts.c.accountname) )
				accountRecords = accountData.fetchall()
				gtbGrid = []
				financialStart = self.request.params["financialstart"]
				calculateTo =  self.request.params["calculateto"]
				srno = 0
				totalDr = 0.00
				totalCr = 0.00
				for account in accountRecords:
					adverseflag = 0
					calbalData = calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
					if float(calbalData["totaldrbal"])==0 and float(calbalData["totalcrbal"]) == 0:
						continue
					srno += 1
					if (calbalData["baltype"] == "Dr") and (calbalData["grpname"] == 'Corpus' or calbalData["grpname"] == 'Capital' or calbalData["grpname"] == 'Current Liabilities' or calbalData["grpname"] == 'Loans(Liability)' or calbalData["grpname"] == 'Reserves') and calbalData["curbal"]!=0:
						adverseflag = 1
					if (calbalData["baltype"] == "Cr") and (calbalData["grpname"] == 'Current Assets' or calbalData["grpname"] == 'Fixed Assets'or calbalData["grpname"] == 'Investments' or calbalData["grpname"] == 'Loans(Asset)' or calbalData["grpname"] == 'Miscellaneous Expenses(Asset)') and calbalData["curbal"]!=0:
						adverseflag = 1
					gtbRow = {"accountcode": account["accountcode"],"accountname":account["accountname"],"groupname": calbalData["grpname"],"Dr balance":"%.2f"%(calbalData["totaldrbal"]),"Cr balance":"%.2f"%(calbalData["totalcrbal"]),"srno":srno, "advflag":adverseflag }
					totalDr += calbalData["totaldrbal"]
					totalCr += calbalData["totalcrbal"]
					gtbRow["ttlRunDr"] = "%.2f"%(totalDr)
					gtbRow["ttlRunCr"] = "%.2f"%(totalCr)
					gtbGrid.append(gtbRow)
				gtbGrid.append({"accountcode":"","accountname":"Total","groupname":"","Dr balance":"%.2f"%(totalDr),"Cr balance":"%.2f"%(totalCr),"srno":"", "advflag":"" })
				if totalDr > totalCr:
					baldiff = totalDr - totalCr
					gtbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Cr balance": "%.2f"%(baldiff),"Dr balance":"", "advflag":"" })
					gtbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr balance": "%.2f"%(totalDr),"Dr balance":"%.2f"%(totalDr), "advflag":"" })
				if totalDr < totalCr:
					baldiff = totalCr - totalDr
					gtbGrid.append({"accountcode":"","accountname":"Difference in Trial balance","groupname":"","srno":"","Dr balance": "%.2f"%(baldiff),"Cr balance":"", "advflag":"" })
					gtbGrid.append({"accountcode":"","accountname":"","groupname":"","srno":"","Cr balance": "%.2f"%(totalCr),"Dr balance":"%.2f"%(totalCr), "advflag":"" })
				self.con.close()


				return {"gkstatus":enumdict["Success"],"gkresult":gtbGrid}
			except:
				self.con.close()
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

				self.con = eng.connect()
				accountData = self.con.execute(select([accounts.c.accountcode,accounts.c.accountname]).where(accounts.c.orgcode==authDetails["orgcode"] ).order_by(accounts.c.accountname) )
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
					adverseflag = 0
					calbalData = calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
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
						if (calbalData["grpname"] == 'Corpus' or calbalData["grpname"] == 'Capital' or calbalData["grpname"] == 'Current Liabilities' or calbalData["grpname"] == 'Loans(Liability)' or calbalData["grpname"] == 'Reserves') and calbalData["curbal"]!=0:
							adverseflag = 1
						extbrow["curbaldr"] = "%.2f"%(calbalData["curbal"])
						extbrow["curbalcr"] = ""
						totalDrBal += calbalData["curbal"]
					if calbalData["baltype"]=="Cr":
						if (calbalData["grpname"] == 'Current Assets' or calbalData["grpname"] == 'Fixed Assets'or calbalData["grpname"] == 'Investments' or calbalData["grpname"] == 'Loans(Asset)' or calbalData["grpname"] == 'Miscellaneous Expenses(Asset)') and calbalData["curbal"]!=0:
							adverseflag = 1
						extbrow["curbaldr"] = ""
						extbrow["curbalcr"] = "%.2f"%(calbalData["curbal"])
						totalCrBal += calbalData["curbal"]
					if calbalData["baltype"]=="":
						extbrow["curbaldr"]=""
						extbrow["curbalcr"]=""
					extbrow["ttlRunDr"] = "%.2f"%(totalDrBal)
					extbrow["ttlRunCr"] = "%.2f"%(totalCrBal)
					extbrow["advflag"] = adverseflag
					extbGrid.append(extbrow)
				extbrow = {"accountcode": "","accountname":"Total","groupname":"","openingbalance":"", "totaldr":"%.2f"%(totalDr),"totalcr":"%.2f"%(totalCr),"curbaldr":"%.2f"%(totalDrBal),"curbalcr":"%.2f"%(totalCrBal),"srno":"", "advflag":""}
				extbGrid.append(extbrow)

				if totalDrBal>totalCrBal:
					extbGrid.append({"accountcode": "","accountname":"Difference in Trial Balance","groupname":"","openingbalance":"", "totaldr":"","totalcr":"","srno":"","curbalcr":"%.2f"%(totalDrBal - totalCrBal),"curbaldr":"", "advflag":""})
					extbGrid.append({"accountcode": "","accountname":"","groupname":"","openingbalance":"", "totaldr":"","totalcr":"","curbaldr":"%.2f"%(totalDrBal),"curbalcr":"%.2f"%(totalDrBal),"srno":"", "advflag":""})
				if totalCrBal>totalDrBal:
					extbGrid.append({"accountcode": "","accountname":"Difference in Trial Balance","groupname":"","openingbalance":"", "totaldr":"","totalcr":"","srno":"","curbaldr":"%.2f"%(totalCrBal - totalDrBal),"curbalcr":"", "advflag":""})
					extbGrid.append({"accountcode": "","accountname":"","groupname":"","openingbalance":"", "totaldr":"","totalcr":"","curbaldr":"%.2f"%(totalCrBal),"curbalcr":"%.2f"%(totalCrBal),"srno":"", "advflag":""})
				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":extbGrid}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}




	@view_config(request_param='type=cashflow', renderer='json')
	def cashflow(self):
		"""
		Purpose:
		Returns a grid containing opening and closing balances of those accounts under the group of Cash or Bank
		and also the total receipt and total payment (Cr and Dr) for the time period of theses accounts
		Description:
		This method has type=cashflow as request_param in view_config.
		the method takes financial start, calculatefrom and calculateto as parameters.
		then it fetches all the accountcodes, their opening balances and accountnames from the database which are under the group of Cash or Bank
		then a loop is ran for all these accounts and in the loop, the calculateBalance function is caaled for all these accounts
		if the balbrought!=0 (balbrought returned from calculateBalance, this also becomes the opening balance for the period) then the dictionary containing accountdetails and balbrought amount is appended to the "receiptcf" list.
		the balbrought amount is added or subtracted from the "rctotal" depending upon its openbaltype
		if the curbal!=0 (curbal returned from calculateBalance, this also becomes the closing balance for the period) then a dictionary containing the accountdetails and curbal amount is appended to the "closinggrid" list
		the curbal amount is added or subtracted from the "pytotal" depending upon its baltype
		then, all the vouchers (Except contra and journal) are fetched from the database which contain these accountcodes in either their crs or drs
		then a loop is ran for the accountcodes of the above fetched voucher crs to find the total receipts in the particular account. the same is done with drs to find the total payment done from that account.
		then the dictionary containing the accountdetails along total receipts is appended in the "rctransactionsgrid" list and the dictionary containing accountdetails along with the total payments are appended in the "paymentcf" list
		totalrunningreceipt (ttlRunDr) and totalrunningpayments(ttlRunCr) are calculated and added in the list for printing purpose.
		then these lists are joined to receiptcf & closing grid accordingly and returned as rcgkresult & pygkresult
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

				self.con = eng.connect()
				calculateFrom = self.request.params["calculatefrom"]
				calculateTo = self.request.params["calculateto"]
				financialStart = self.request.params["financialstart"]
				cbAccountsData = self.con.execute("select accountcode, openingbal, accountname from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Bank','Cash')) order by accountname"%(authDetails["orgcode"],authDetails["orgcode"]))
				cbAccounts = cbAccountsData.fetchall()
				receiptcf = []
				paymentcf = []
				rctransactionsgrid = []
				closinggrid = []
				rcaccountcodes = []
				pyaccountcodes = []
				bankcodes = []
				rctotal = 0.00
				pytotal = 0.00
				ttlRunDr = 0.00
				ttlRunCr = 0.00
				vfrom = datetime.strptime(str(calculateFrom),"%Y-%m-%d")
				fstart = datetime.strptime(str(financialStart),"%Y-%m-%d")
				if vfrom==fstart:
					receiptcf.append({"toby":"To","particulars":"Opening balance","amount":"","accountcode":"", "ttlRunDr":""})
				if vfrom>fstart:
					receiptcf.append({"toby":"To","particulars":"Balance B/F","amount":"","accountcode":"", "ttlRunDr":""})
				for cbAccount in cbAccounts:
					bankcodes.append(str(cbAccount["accountcode"]))
				closinggrid.append({"toby":"By","particulars":"Closing balance","amount":"","accountcode":"", "ttlRunCr":""})
				for cbAccount in cbAccounts:
					opacc = calculateBalance(self.con,cbAccount["accountcode"], financialStart, calculateFrom, calculateTo)
					if opacc["balbrought"]!=0.00:
						if opacc["openbaltype"]=="Dr":
							receiptcf.append({"toby":"","particulars":''.join(cbAccount["accountname"]),"amount":"%.2f"%float(opacc["balbrought"]),"accountcode":cbAccount["accountcode"], "ttlRunDr":""})
							rctotal += float(opacc["balbrought"])
						if opacc["openbaltype"]=="Cr":
							receiptcf.append({"toby":"","particulars":''.join(cbAccount["accountname"]),"amount":"-"+"%.2f"%float(opacc["balbrought"]),"accountcode":cbAccount["accountcode"], "ttlRunDr":""})
							rctotal -= float(opacc["balbrought"])
					if opacc["curbal"]!=0.00:
						if opacc["baltype"]=="Dr":
							closinggrid.append({"toby":"","particulars":''.join(cbAccount["accountname"]),"amount":"%.2f"%float(opacc["curbal"]),"accountcode":cbAccount["accountcode"], "ttlRunCr":""})
							pytotal += float(opacc["curbal"])
						if opacc["baltype"]=="Cr":
							closinggrid.append({"toby":"","particulars":''.join(cbAccount["accountname"]),"amount":"-"+"%.2f"%float(opacc["curbal"]),"accountcode":cbAccount["accountcode"], "ttlRunCr":""})
							pytotal -= float(opacc["curbal"])
					transactionsRecords = self.con.execute("select crs,drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and vouchertype not in ('contra','journal') and (drs ? '%s' or crs ? '%s');"%(calculateFrom, calculateTo, cbAccount["accountcode"],cbAccount["accountcode"]))
					transactions = transactionsRecords.fetchall()
					for transaction in transactions:
						for cr in transaction["crs"]:
							if cr not in rcaccountcodes and int(cr) != int(cbAccount["accountcode"]):
								rcaccountcodes.append(cr)
								crresult = self.con.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and vouchertype not in ('contra','journal') and (drs ?| array%s);"%(int(cr),financialStart, calculateTo, str(bankcodes)))
								crresultRow = crresult.fetchone()
								rcaccountname = self.con.execute("select accountname from accounts where accountcode=%d"%(int(cr)))
								rcacc= ''.join(rcaccountname.fetchone())
								ttlRunDr += float(crresultRow["total"])
								rctransactionsgrid.append({"toby":"To","particulars":rcacc,"amount":"%.2f"%float(crresultRow["total"]),"accountcode":int(cr), "ttlRunDr": ttlRunDr})
								rctotal += float(crresultRow["total"])
						for dr in transaction["drs"]:
							if dr not in pyaccountcodes and int(dr) != int(cbAccount["accountcode"]):
								pyaccountcodes.append(dr)
								drresult = self.con.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and vouchertype not in ('contra','journal') and (crs ?| array%s)"%(int(dr),financialStart, calculateTo,str(bankcodes)))
								drresultRow = drresult.fetchone()
								pyaccountname = self.con.execute("select accountname from accounts where accountcode=%d"%(int(dr)))
								pyacc= ''.join(pyaccountname.fetchone())
								ttlRunCr += float(drresultRow["total"])
								paymentcf.append({"toby":"By","particulars":pyacc,"amount":"%.2f"%float(drresultRow["total"]),"accountcode":int(dr), "ttlRunCr":ttlRunCr})
								pytotal += float(drresultRow["total"])
				receiptcf.extend(rctransactionsgrid)
				paymentcf.extend(closinggrid)
				if len(receiptcf)>len(paymentcf):
					emptyno = len(receiptcf)-len(paymentcf)
					for i in range(0,emptyno):
						paymentcf.append({"toby":"","particulars":"","amount":".","accountcode":"", "ttlRunCr":""})
				if len(receiptcf)<len(paymentcf):
					emptyno = len(paymentcf)-len(receiptcf)
					for i in range(0,emptyno):
						receiptcf.append({"toby":"","particulars":"","amount":".","accountcode":"", "ttlRunDr":""})
				receiptcf.append({"toby":"","particulars":"Total","amount":"%.2f"%float(rctotal),"accountcode":"", "ttlRunDr":""})
				paymentcf.append({"toby":"","particulars":"Total","amount":"%.2f"%float(pytotal),"accountcode":"", "ttlRunCr":""})
				self.con.close()


				return {"gkstatus":enumdict["Success"],"rcgkresult":receiptcf,"pygkresult":paymentcf}
			except:
				self.con.close()
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
		In addition there will be running Cr and Dr totals for printing purpose.
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
				self.con = eng.connect()
				calculateTo = self.request.params["calculateto"]
				financialStart = self.request.params["financialstart"]
				projectCode= self.request.params["projectcode"]
				totalDr = 0.00
				totalCr = 0.00
				grpaccsdata = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Direct Income','Indirect Expense','Indirect Income')) order by accountname"%(authDetails["orgcode"],authDetails["orgcode"]))
				grpaccs = grpaccsdata.fetchall()
				srno = 1
				projectStatement = []
				for accountRow in grpaccs:
					group = self.con.execute("select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"%(int(accountRow["accountcode"]),int(accountRow["accountcode"])))
					groupRow = group.fetchone()
					drresult = self.con.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and projectcode=%d"%(int(accountRow["accountcode"]),financialStart, calculateTo, int(projectCode)))
					drresultRow = drresult.fetchone()
					crresult = self.con.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and projectcode=%d"%(int(accountRow["accountcode"]),financialStart, calculateTo, int(projectCode)))
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
					statementRow["ttlRunDr"] = "%.2f"%(totalDr)
					statementRow["ttlRunCr"] = "%.2f"%(totalCr)
					projectStatement.append(statementRow)
				projectStatement.append({"srno":"","accountcode":"","accountname":"","groupname":"Total","totalout":'%.2f'%float(totalDr),"totalin":'%.2f'%float(totalCr)})
				self.con.close()


				return {"gkstatus":enumdict["Success"],"gkresult":projectStatement}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param="type=balancesheet",renderer="json")
	def balanceSheet(self):
		"""
		Purpose:
		Gets the list of groups and their respective balances
		takes organisation code and end date as input parameter
		Description:
		This function is used to generate balance sheet for a given organisation and the given time period.
		This function takes orgcode and end date as the input parameters
		This function is called when the type=balancesheet is passed to the /report url.
		orgcode is extracted from the header
		end date is extracted from the request_params
		The accountcode is extracted from the database under  groupcode for groups relevent to balance sheet
		the  groupbalance will be initialized to 0.0 for each group.
		this accountcode is sent to the calculateBalance function along with financialstart, calculateTo
		the function will return the closing balance related to each account which will be later added or subtracted according to the accounting rules from the group balance
		Then the subgroups and their respective accounts will be fetched from the database and the detail will be sent to the calculatBalance function which will return the curbal.
		the amount will be added or subtracted from the subgroup balance accordingly.
		the above steps will be executed in loop to calculate balances of all subgroups.
		these balances will be added/subtracted from the group balance accordingly.
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
				self.con = eng.connect()
				orgcode = authDetails["orgcode"]
				financialstart = self.con.execute("select yearstart, orgtype from organisation where orgcode = %d"%int(orgcode))
				financialstartRow = financialstart.fetchone()
				financialStart = financialstartRow["yearstart"]
				orgtype = financialstartRow["orgtype"]
				calculateTo = self.request.params["calculateto"]
				balancetype = int(self.request.params["baltype"])
				sbalanceSheet=[]
				abalanceSheet=[]
				sourcesTotal = 0.00
				applicationsTotal = 0.00
				difference = 0.00
				sbalanceSheet.append({"groupAccname":"Sources:","amount":"", "groupAcccode":"","subgroupof":"" , "accountof":"", "groupAccflag":"", "advflag":""})
				capital_Corpus = ""
				if orgtype == "Profit Making":
					capital_Corpus = "Capital"
				if orgtype == "Not For Profit":
					capital_Corpus = "Corpus"
				groupWiseTotal = 0.00

				#Calculate grouptotal for group Capital/Corpus
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = '%s') order by accountname;"%(orgcode, orgcode, capital_Corpus))
				accountCodes = accountcodeData.fetchall()
				subgroupDataRow = self.con.execute("select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='%s');"%(orgcode, orgcode, capital_Corpus))
				subgroupData = subgroupDataRow.fetchall()
				groupCode = self.con.execute("select groupcode from groupsubgroups where (orgcode=%d and groupname='%s');"%(orgcode,capital_Corpus))
				groupcode = groupCode.fetchone()["groupcode"];
				groupAccSubgroup = []

				for accountRow in accountCodes:
					accountTotal = 0.00
					adverseflag = 0
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal += accountDetails["curbal"]
						accountTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr" and accountDetails["curbal"]!=0):
						adverseflag = 1
						accountTotal -= accountDetails["curbal"]
						groupWiseTotal -= accountDetails["curbal"]
					groupAccSubgroup.append({"groupAccname":accountRow["accountname"], "amount":"%.2f"%(accountTotal), "groupAcccode":accountRow["accountcode"], "subgroupof":"", "accountof":groupcode, "groupAccflag":1, "advflag":adverseflag})

				for subgroup in subgroupData:
					subgroupTotal = 0.00
					accounts = []
					subgroupAccDataRow = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"%(orgcode, subgroup["groupcode"]))
					subgroupAccData = subgroupAccDataRow.fetchall()
					for account in subgroupAccData:
						accountTotal = 0.00
						adverseflag = 0
						accountDetails =  calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
						if (accountDetails["baltype"]=="Cr"):
							subgroupTotal += accountDetails["curbal"]
							accountTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Dr" and accountDetails["curbal"]!=0):
							adverseflag = 1
							subgroupTotal -= accountDetails["curbal"]
							accountTotal -= accountDetails["curbal"]
						if (accountDetails["curbal"]!=0):
							accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
					groupWiseTotal += subgroupTotal
					groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
					groupAccSubgroup += accounts
				sourcesTotal += groupWiseTotal
				sbalanceSheet.append({"groupAccname":capital_Corpus,"amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"", "advflag":""})
				sbalanceSheet += groupAccSubgroup


				#Calculate grouptotal for group Loans(Liability)
				groupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Liability)') order by accountname;"%(orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				subgroupDataRow = self.con.execute("select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Loans(Liability)');"%(orgcode, orgcode))
				subgroupData = subgroupDataRow.fetchall()
				groupCode = self.con.execute("select groupcode from groupsubgroups where (orgcode=%d and groupname='Loans(Liability)');"%(orgcode))
				groupcode = groupCode.fetchone()["groupcode"];
				groupAccSubgroup = []

				for accountRow in accountCodes:
					accountTotal = 0.00
					adverseflag = 0
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal += accountDetails["curbal"]
						accountTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr" and accountDetails["curbal"]!=0):
						adverseflag = 1
						accountTotal -= accountDetails["curbal"]
						groupWiseTotal -= accountDetails["curbal"]
					groupAccSubgroup.append({"groupAccname":accountRow["accountname"], "amount":"%.2f"%(accountTotal), "groupAcccode":accountRow["accountcode"], "subgroupof":"", "accountof":groupcode, "groupAccflag":1, "advflag":adverseflag})

				for subgroup in subgroupData:
					subgroupTotal = 0.00
					accounts = []
					subgroupAccDataRow = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"%(orgcode, subgroup["groupcode"]))
					subgroupAccData = subgroupAccDataRow.fetchall()
					for account in subgroupAccData:
						accountTotal = 0.00
						adverseflag = 0
						accountDetails =  calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
						if (accountDetails["baltype"]=="Cr"):
							subgroupTotal += accountDetails["curbal"]
							accountTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Dr" and accountDetails["curbal"]!=0):
							adverseflag = 1
							subgroupTotal -= accountDetails["curbal"]
							accountTotal -= accountDetails["curbal"]
						if (accountDetails["curbal"]!=0):
							accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
					groupWiseTotal += subgroupTotal
					groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
					groupAccSubgroup += accounts

				sourcesTotal += groupWiseTotal
				sbalanceSheet.append({"groupAccname":"Loans(Liability)","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"", "advflag":""})
				sbalanceSheet += groupAccSubgroup


				#Calculate grouptotal for group Current Liabilities
				groupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Liabilities') order by accountname;"%(orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				subgroupDataRow = self.con.execute("select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Current Liabilities');"%(orgcode, orgcode))
				subgroupData = subgroupDataRow.fetchall()
				groupCode = self.con.execute("select groupcode from groupsubgroups where (orgcode=%d and groupname='Current Liabilities');"%(orgcode))
				groupcode = groupCode.fetchone()["groupcode"];
				groupAccSubgroup = []

				for accountRow in accountCodes:
					accountTotal = 0.00
					adverseflag = 0
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal += accountDetails["curbal"]
						accountTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr" and accountDetails["curbal"]!=0):
						adverseflag =1
						accountTotal -= accountDetails["curbal"]
						groupWiseTotal -= accountDetails["curbal"]
					groupAccSubgroup.append({"groupAccname":accountRow["accountname"], "amount":"%.2f"%(accountTotal), "groupAcccode":accountRow["accountcode"], "subgroupof":"", "accountof":groupcode, "groupAccflag":1, "advflag":adverseflag})

				for subgroup in subgroupData:
					subgroupTotal = 0.00
					accounts = []
					subgroupAccDataRow = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"%(orgcode, subgroup["groupcode"]))
					subgroupAccData = subgroupAccDataRow.fetchall()
					for account in subgroupAccData:
						accountTotal = 0.00
						adverseflag = 0
						accountDetails =  calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
						if (accountDetails["baltype"]=="Cr"):
							subgroupTotal += accountDetails["curbal"]
							accountTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Dr" and accountDetails["curbal"]!=0):
							adverseflag = 1
							subgroupTotal -= accountDetails["curbal"]
							accountTotal -= accountDetails["curbal"]
						if (accountDetails["curbal"]!=0):
							accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
					groupWiseTotal += subgroupTotal
					groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
					groupAccSubgroup += accounts

				sourcesTotal += groupWiseTotal
				sbalanceSheet.append({"groupAccname":"Current Liabilities","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"", "advflag":""})
				sbalanceSheet += groupAccSubgroup


				#Calculate grouptotal for group "Reserves"
				groupWiseTotal = 0.00
				incomeTotal = 0.00
				expenseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Reserves') order by accountname;"%(orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				subgroupDataRow = self.con.execute("select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Reserves');"%(orgcode, orgcode))
				subgroupData = subgroupDataRow.fetchall()
				groupCode = self.con.execute("select groupcode from groupsubgroups where (orgcode=%d and groupname='Reserves');"%(orgcode))
				groupcode = groupCode.fetchone()["groupcode"];
				groupAccSubgroup = []

				for accountRow in accountCodes:
					accountTotal = 0.00
					adverseflag = 0
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						groupWiseTotal += accountDetails["curbal"]
						accountTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr" and accountDetails["curbal"]!=0):
						adverseflag = 1
						accountTotal -= accountDetails["curbal"]
						groupWiseTotal -= accountDetails["curbal"]
					groupAccSubgroup.append({"groupAccname":accountRow["accountname"], "amount":"%.2f"%(accountTotal), "groupAcccode":accountRow["accountcode"], "subgroupof":"", "accountof":groupcode, "groupAccflag":1, "advflag":adverseflag})

				for subgroup in subgroupData:
					subgroupTotal = 0.00
					accounts = []
					subgroupAccDataRow = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"%(orgcode, subgroup["groupcode"]))
					subgroupAccData = subgroupAccDataRow.fetchall()
					for account in subgroupAccData:
						accountTotal = 0.00
						adverseflag = 0
						accountDetails =  calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
						if (accountDetails["baltype"]=="Cr"):
							subgroupTotal += accountDetails["curbal"]
							accountTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Dr" and accountDetails["curbal"]!=0):
							adverseflag = 1
							subgroupTotal -= accountDetails["curbal"]
							accountTotal -= accountDetails["curbal"]
						if (accountDetails["curbal"]!=0):
							accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
					groupWiseTotal += subgroupTotal
					groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
					groupAccSubgroup += accounts

				#Calculate all income(Direct and Indirect Income)
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Income','Indirect Income') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Income','Indirect Income')));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						incomeTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						incomeTotal -= accountDetails["curbal"]

				#Calculate all expense(Direct and Indirect Expense)
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Expense','Indirect Expense') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Indirect Expense')));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						expenseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						expenseTotal -= accountDetails["curbal"]

				#Calculate Profit/Loss for the year
				profit = 0
				if (expenseTotal > incomeTotal):
					profit = expenseTotal - incomeTotal
					groupWiseTotal -= profit
					sbalanceSheet.append({"groupAccname":"Reserves","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"", "advflag":""})
					if orgtype == "Profit Making":
						sbalanceSheet.append({"groupAccname":"Loss for the Year:","amount":"%.2f"%(profit), "groupAcccode":"","subgroupof":groupcode , "accountof":"", "groupAccflag":2, "advflag":""})
					else:
						sbalanceSheet.append({"groupAccname":"Deficit for the Year:","amount":"%.2f"%(profit), "groupAcccode":"","subgroupof":groupcode , "accountof":"", "groupAccflag":2, "advflag":""})

				if (expenseTotal < incomeTotal):
					profit = incomeTotal - expenseTotal
					groupWiseTotal += profit
					sbalanceSheet.append({"groupAccname":"Reserves","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})
					if orgtype == "Profit Making":
						sbalanceSheet.append({"groupAccname":"Profit for the Year:","amount":"%.2f"%(profit), "groupAcccode":"","subgroupof":groupcode , "accountof":"", "groupAccflag":2,"advflag":""})
					else:
						sbalanceSheet.append({"groupAccname":"Surplus for the Year:","amount":"%.2f"%(profit), "groupAcccode":"","subgroupof":groupcode , "accountof":"", "groupAccflag":2,"advflag":""})
				if (expenseTotal == incomeTotal):
					sbalanceSheet.append({"groupAccname":"Reserves","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})

				sbalanceSheet += groupAccSubgroup
				sourcesTotal += groupWiseTotal
				sbalanceSheet.append({"groupAccname":"Total","amount":"%.2f"%(sourcesTotal), "groupAcccode":"","subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})

				#Applications:
				abalanceSheet.append({"groupAccname":"Applications:","amount":"", "groupAcccode":"","subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})


				#Calculate grouptotal for group "Fixed Assets"
				groupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Fixed Assets') order by accountname;"%(orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				subgroupDataRow = self.con.execute("select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Fixed Assets');"%(orgcode, orgcode))
				subgroupData = subgroupDataRow.fetchall()
				groupCode = self.con.execute("select groupcode from groupsubgroups where (orgcode=%d and groupname='Fixed Assets');"%(orgcode))
				groupcode = groupCode.fetchone()["groupcode"];
				groupAccSubgroup = []

				for accountRow in accountCodes:
					accountTotal = 0.00
					adverseflag = 0
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal += accountDetails["curbal"]
						accountTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
						adverseflag = 1
						accountTotal -= accountDetails["curbal"]
						groupWiseTotal -= accountDetails["curbal"]
					groupAccSubgroup.append({"groupAccname":accountRow["accountname"], "amount":"%.2f"%(accountTotal), "groupAcccode":accountRow["accountcode"], "subgroupof":"", "accountof":groupcode, "groupAccflag":1,"advflag":adverseflag})

				for subgroup in subgroupData:
					subgroupTotal = 0.00
					accounts = []
					subgroupAccDataRow = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"%(orgcode, subgroup["groupcode"]))
					subgroupAccData = subgroupAccDataRow.fetchall()

					for account in subgroupAccData:
						accountTotal = 0.00
						adverseflag = 0
						accountDetails = calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
						if (accountDetails["baltype"]=="Dr"):
							subgroupTotal += accountDetails["curbal"]
							accountTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
							adverseflag =1
							subgroupTotal -= accountDetails["curbal"]
							accountTotal -= accountDetails["curbal"]
						if (accountDetails["curbal"]!=0):
							accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2,"advflag":adverseflag})
					groupWiseTotal += subgroupTotal
					groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"","advflag":""})
					groupAccSubgroup += accounts

				applicationsTotal += groupWiseTotal
				abalanceSheet.append({"groupAccname":"Fixed Assets","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})
				abalanceSheet += groupAccSubgroup



				#Calculate grouptotal for group "Investments"
				groupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Investments') order by accountname;"%(orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				subgroupDataRow = self.con.execute("select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Investments');"%(orgcode, orgcode))
				subgroupData = subgroupDataRow.fetchall()
				groupCode = self.con.execute("select groupcode from groupsubgroups where (orgcode=%d and groupname='Investments');"%(orgcode))
				groupcode = groupCode.fetchone()["groupcode"];
				groupAccSubgroup = []

				for accountRow in accountCodes:
					accountTotal = 0.00
					adverseflag = 0
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal += accountDetails["curbal"]
						accountTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
						adverseflag = 1
						accountTotal -= accountDetails["curbal"]
						groupWiseTotal -= accountDetails["curbal"]
					groupAccSubgroup.append({"groupAccname":accountRow["accountname"], "amount":"%.2f"%(accountTotal), "groupAcccode":accountRow["accountcode"], "subgroupof":"", "accountof":groupcode, "groupAccflag":1, "advflag":adverseflag})

				for subgroup in subgroupData:
					subgroupTotal = 0.00
					accounts = []
					subgroupAccDataRow = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"%(orgcode, subgroup["groupcode"]))
					subgroupAccData = subgroupAccDataRow.fetchall()
					for account in subgroupAccData:
						accountTotal = 0.00
						adverseflag = 0
						accountDetails =  calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
						if (accountDetails["baltype"]=="Dr"):
							subgroupTotal += accountDetails["curbal"]
							accountTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
							adverseflag = 1
							subgroupTotal -= accountDetails["curbal"]
							accountTotal -= accountDetails["curbal"]
						if (accountDetails["curbal"]!=0):
							accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
					groupWiseTotal += subgroupTotal
					groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"","advflag":""})
					groupAccSubgroup += accounts

				applicationsTotal += groupWiseTotal
				abalanceSheet.append({"groupAccname":"Investments","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})
				abalanceSheet += groupAccSubgroup


				#Calculate grouptotal for group "Current Assets"
				groupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Assets') order by accountname;"%(orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				subgroupDataRow = self.con.execute("select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Current Assets');"%(orgcode, orgcode))
				subgroupData = subgroupDataRow.fetchall()
				groupCode = self.con.execute("select groupcode from groupsubgroups where (orgcode=%d and groupname='Current Assets');"%(orgcode))
				groupcode = groupCode.fetchone()["groupcode"];
				groupAccSubgroup = []

				for accountRow in accountCodes:
					accountTotal = 0.00
					adverseflag  = 0
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal += accountDetails["curbal"]
						accountTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
						adverseflag = 1
						accountTotal -= accountDetails["curbal"]
						groupWiseTotal -= accountDetails["curbal"]
					groupAccSubgroup.append({"groupAccname":accountRow["accountname"], "amount":"%.2f"%(accountTotal), "groupAcccode":accountRow["accountcode"], "subgroupof":"", "accountof":groupcode, "groupAccflag":1, "advflag":adverseflag})

				for subgroup in subgroupData:
					subgroupTotal = 0.00
					accounts = []
					subgroupAccDataRow = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"%(orgcode, subgroup["groupcode"]))
					subgroupAccData = subgroupAccDataRow.fetchall()
					for account in subgroupAccData:
						accountTotal = 0.00
						adverseflag = 0
						accountDetails =  calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
						if (accountDetails["baltype"]=="Dr"):
							subgroupTotal += accountDetails["curbal"]
							accountTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
							adverseflag = 1
							subgroupTotal -= accountDetails["curbal"]
							accountTotal -= accountDetails["curbal"]
						if (accountDetails["curbal"]!=0):
							accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
					groupWiseTotal += subgroupTotal
					groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"","advflag":""})
					groupAccSubgroup += accounts

				applicationsTotal += groupWiseTotal
				abalanceSheet.append({"groupAccname": "Current Assets","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"", "advflag":""})
				abalanceSheet += groupAccSubgroup


				#Calculate grouptotal for group Loans(Asset)
				groupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Asset)') order by accountname;"%(orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				subgroupDataRow = self.con.execute("select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Loans(Asset)');"%(orgcode, orgcode))
				subgroupData = subgroupDataRow.fetchall()
				groupCode = self.con.execute("select groupcode from groupsubgroups where (orgcode=%d and groupname='Loans(Asset)');"%(orgcode))
				groupcode = groupCode.fetchone()["groupcode"];
				groupAccSubgroup = []

				for accountRow in accountCodes:
					accountTotal = 0.00
					adverseflag = 0
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						groupWiseTotal += accountDetails["curbal"]
						accountTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
						adverseflag = 1
						accountTotal -= accountDetails["curbal"]
						groupWiseTotal -= accountDetails["curbal"]
					groupAccSubgroup.append({"groupAccname":accountRow["accountname"], "amount":"%.2f"%(accountTotal), "groupAcccode":accountRow["accountcode"], "subgroupof":"", "accountof":groupcode, "groupAccflag":1, "advflag":adverseflag})

				for subgroup in subgroupData:
					subgroupTotal = 0.00
					accounts = []
					subgroupAccDataRow = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"%(orgcode, subgroup["groupcode"]))
					subgroupAccData = subgroupAccDataRow.fetchall()
					for account in subgroupAccData:
						accountTotal = 0.00
						adverseflag  = 0
						accountDetails =  calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
						if (accountDetails["baltype"]=="Dr"):
							subgroupTotal += accountDetails["curbal"]
							accountTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
							adverseflag = 1
							subgroupTotal -= accountDetails["curbal"]
							accountTotal -= accountDetails["curbal"]
						if (accountDetails["curbal"]!=0):
							accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
					groupWiseTotal += subgroupTotal
					groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
					groupAccSubgroup += accounts

				applicationsTotal += groupWiseTotal
				abalanceSheet.append({"groupAccname":"Loans(Asset)","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})
				abalanceSheet += groupAccSubgroup


				if orgtype=="Profit Making":
					#Calculate grouptotal for group "Miscellaneous Expenses(Asset)"
					groupWiseTotal = 0.00
					accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Miscellaneous Expenses(Asset)') order by accountname;"%(orgcode, orgcode))
					accountCodes = accountcodeData.fetchall()
					subgroupDataRow = self.con.execute("select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Miscellaneous Expenses(Asset)');"%(orgcode, orgcode))
					subgroupData = subgroupDataRow.fetchall()
					groupCode = self.con.execute("select groupcode from groupsubgroups where (orgcode=%d and groupname='Miscellaneous Expenses(Asset)');"%(orgcode))
					groupcode = groupCode.fetchone()["groupcode"];
					groupAccSubgroup = []

					for accountRow in accountCodes:
						accountTotal = 0.00
						adverseflag = 0
						accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
						if (accountDetails["baltype"]=="Dr"):
							groupWiseTotal += accountDetails["curbal"]
							accountTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
							adverseflag = 1
							accountTotal -= accountDetails["curbal"]
							groupWiseTotal -= accountDetails["curbal"]
						groupAccSubgroup.append({"groupAccname":accountRow["accountname"], "amount":"%.2f"%(accountTotal), "groupAcccode":accountRow["accountcode"], "subgroupof":"", "accountof":groupcode, "groupAccflag":1, "advflag":adverseflag})

					for subgroup in subgroupData:
						subgroupTotal = 0.00
						accounts = []
						subgroupAccDataRow = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"%(orgcode, subgroup["groupcode"]))
						subgroupAccData = subgroupAccDataRow.fetchall()
						for account in subgroupAccData:
							accountTotal = 0.00
							adverseflag = 0
							accountDetails =  calculateBalance(self.con,account["accountcode"], financialStart, financialStart, calculateTo)
							if (accountDetails["baltype"]=="Dr"):
								subgroupTotal += accountDetails["curbal"]
								accountTotal += accountDetails["curbal"]
							if (accountDetails["baltype"]=="Cr" and accountDetails["curbal"]!=0):
								adverseflag = 1
								subgroupTotal -= accountDetails["curbal"]
								accountTotal -= accountDetails["curbal"]
							if (accountDetails["curbal"]!=0):
								accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag": adverseflag})
						groupWiseTotal += subgroupTotal
						groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"","advflag":""})
						groupAccSubgroup += accounts

					applicationsTotal += groupWiseTotal
					abalanceSheet.append({"groupAccname": "Miscellaneous Expenses(Asset)","amount":"%.2f"%(groupWiseTotal), "groupAcccode":groupcode,"subgroupof":"" , "accountof":"", "groupAccflag":"", "advflag":""})
					abalanceSheet += groupAccSubgroup

				abalanceSheet.append({"groupAccname": "Total","amount":"%.2f"%(applicationsTotal), "groupAcccode":"","subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})
				sourcesTotal = round(sourcesTotal,2)
				applicationsTotal = round(applicationsTotal,2)
				difference = abs(sourcesTotal - applicationsTotal)

				if sourcesTotal>applicationsTotal:
					abalanceSheet.append({"groupAccname": "Difference","amount":"%.2f"%(difference), "groupAcccode":"","subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})
					abalanceSheet.append({"groupAccname": "Total","amount":"%.2f"%(sourcesTotal), "groupAcccode":"","subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})
				if applicationsTotal>sourcesTotal:
					sbalanceSheet.append({"groupAccname": "Difference","amount":"%.2f"%(difference), "groupAcccode":"","subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})
					sbalanceSheet.append({"groupAccname": "Total","amount":"%.2f"%(applicationsTotal), "groupAcccode":"","subgroupof":"" , "accountof":"", "groupAccflag":"","advflag":""})


				if balancetype == 1:
					if orgtype=="Profit Making":
						if applicationsTotal>sourcesTotal and profit==0:
							abalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
						if sourcesTotal>applicationsTotal and profit==0:
							sbalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
							sbalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
							sbalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
						if applicationsTotal>sourcesTotal and profit!=0:
							abalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
							abalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
						if sourcesTotal>applicationsTotal and profit!=0:
							sbalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
							sbalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
						if difference==0 and profit==0:
							sbalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
						if difference==0 and profit!=0:
							emptyno=0
					if orgtype=="Not For Profit":
						if applicationsTotal>sourcesTotal and profit==0:
							abalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
							abalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
						if sourcesTotal>applicationsTotal and profit==0:
							sbalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
							sbalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
						if applicationsTotal>sourcesTotal and profit!=0:
							abalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
							abalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
							abalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
						if sourcesTotal>applicationsTotal and profit!=0:
							sbalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})
						if difference==0 and profit==0:
							emptyno=0
						if difference==0 and profit!=0:
							abalanceSheet.insert(-1,{"groupAccname": "","amount":"", "groupAcccode":"","subgroupof":"","accountof":"", "groupAccflag":"","advflag":""})


				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult":{"leftlist":sbalanceSheet, "rightlist":abalanceSheet}}


			except:
				self.con.close()
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
				self.con = eng.connect()
				orgcode = authDetails["orgcode"]
				financialstart = self.con.execute("select yearstart, orgtype from organisation where orgcode = %d"%int(orgcode))
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
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = '%s' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s'));"%(orgcode, orgcode, capital_Corpus, orgcode, capital_Corpus))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						sourcegroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						sourcegroupWiseTotal -= accountDetails["curbal"]
				sourcesTotal += sourcegroupWiseTotal

				#Calculate grouptotal for group "Fixed Assets"
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Fixed Assets' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Fixed Assets'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						applicationgroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						applicationgroupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += applicationgroupWiseTotal
				balanceSheet.append({"sourcesgroupname":capital_Corpus,"sourceamount":"%.2f"%(sourcegroupWiseTotal),"appgroupname":"Fixed Assets","applicationamount":"%.2f"%(applicationgroupWiseTotal)})


				#Calculate grouptotal for group Loans(Liability)
				sourcegroupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Liability)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Loans(Liability)'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						sourcegroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						sourcegroupWiseTotal -= accountDetails["curbal"]
				sourcesTotal += sourcegroupWiseTotal


				#Calculate grouptotal for group "Investments"
				applicationgroupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Investments' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Investments'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						applicationgroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						applicationgroupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += applicationgroupWiseTotal
				balanceSheet.append({"sourcesgroupname":"Loans(Liability)","sourceamount":"%.2f"%(sourcegroupWiseTotal),"appgroupname":"Investments","applicationamount":"%.2f"%(applicationgroupWiseTotal)})


				#Calculate grouptotal for group Current Liabilities
				sourcegroupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Liabilities' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Current Liabilities'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						sourcegroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						sourcegroupWiseTotal -= accountDetails["curbal"]
				sourcesTotal += sourcegroupWiseTotal


				#Calculate grouptotal for group "Current Assets"
				applicationgroupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Assets' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Current Assets'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
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
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Income','Indirect Income') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Income','Indirect Income')));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Cr"):
						incomeTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						incomeTotal -= accountDetails["curbal"]

				#Calculate all expense(Direct and Indirect Expense)
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Expense','Indirect Expense') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Indirect Expense')));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						expenseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						expenseTotal -= accountDetails["curbal"]

				#Calculate total of all accounts in Reserves (except Direct and Indirect Income, Expense)
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Reserves' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Reserves'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
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
				applicationgroupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Asset)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Loans(Asset)'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						applicationgroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						applicationgroupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += applicationgroupWiseTotal
				balanceSheet.append({"sourcesgroupname":"Reserves","sourceamount":"%.2f"%(sourcegroupWiseTotal),"appgroupname":"Loans(Asset)","applicationamount":"%.2f"%(applicationgroupWiseTotal)})


				#Calculate grouptotal for group "Miscellaneous Expenses(Asset)"
				applicationgroupWiseTotal = 0.00
				accountcodeData = self.con.execute("select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Miscellaneous Expenses(Asset)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Miscellaneous Expenses(Asset)'));"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if (accountDetails["baltype"]=="Dr"):
						applicationgroupWiseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						applicationgroupWiseTotal -= accountDetails["curbal"]
				applicationsTotal += applicationgroupWiseTotal


				if (expenseTotal > incomeTotal):
					balanceSheet.append({"sourcesgroupname":"Loss for the Year:","sourceamount":"%.2f"%(profit),"appgroupname":"Miscellaneous Expenses(Asset)","applicationamount":"%.2f"%(applicationgroupWiseTotal)})
				if (expenseTotal < incomeTotal):
					balanceSheet.append({"sourcesgroupname":"Profit for the Year","sourceamount":"%.2f"%(profit),"appgroupname":"Miscellaneous Expenses(Asset)","applicationamount":"%.2f"%(applicationgroupWiseTotal)})
				if (expenseTotal == incomeTotal):
					balanceSheet.append({"sourcesgroupname":"","sourceamount":"","appgroupname":"Miscellaneous Expenses(Asset)","applicationamount":"%.2f"%(applicationgroupWiseTotal)})

				#Total of Sources and Applications
				balanceSheet.append({"sourcesgroupname":"Total","sourceamount":"%.2f"%(sourcesTotal),"appgroupname":"Total","applicationamount":"%.2f"%(applicationsTotal)})

				#Difference
				difference = abs(sourcesTotal - applicationsTotal)
				balanceSheet.append({"sourcesgroupname":"Difference","sourceamount":"%.2f"%(difference),"appgroupname":"","applicationamount":""})
				self.con.close()


				return {"gkstatus":enumdict["Success"],"gkresult":balanceSheet}


			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}



	@view_config(request_param="type=profitloss", renderer = "json")
	def profitLoss(self):
		"""
		This method returns a grid containing the profit and loss statement of the organisation.
		The profit and loss statement has all the direct and indirect expenses and the direct and indirect incomes.
		If the incomes are greater than the expenses, the organisation is in profit
		Purpose:
		the method takes the orgcode and the calculateto as the input parameters and returns a grid containing the list of all accounts under the group of direct and indirect income and, direct and indirect expenses along with their respective balances. It also return the gross and net profit/loss made by the company.
		Description:
		the function generates the profit and loss statement of the organisation.
		this function is called when the type=profitloss is passed to the /report url.
		the orgcode is extracted from the header
		calculateTo date is extracted from the request_params
		the accountcodes under the groups direct income and direct expense are extracted from the database.
		then these codes are sent to the calculateBalance function which returns their current balances.
		the total of these balances give the gross profit/loss of the organisation.
		then the accountcodes under the indirect income and indirect expense are extracted from the database.
		and sent to the calculateBalance function along with the financial start and the calculateto date.
		the total of balances of these accounts along with the gross profit/loss gives the net profit/loss of the organisation
		this list of two dictionaries conatining each account, its respective balance as one dictionary and  gross profit/loss along with the amount and net profit/loss along with the amount also as dictionary is returned.
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

				self.con = eng.connect()
				orgcode = authDetails["orgcode"]
				financialstart = self.con.execute("select yearstart, orgtype from organisation where orgcode = %d"%int(orgcode))
				financialstartRow = financialstart.fetchone()
				financialStart = financialstartRow["yearstart"]
				orgtype = financialstartRow["orgtype"]
				calculateTo = self.request.params["calculateto"]
				calculateTo = calculateTo
				expense = []
				income = []
				incomeTotal = 0.00
				expenseTotal = 0.00
				difference = 0.00
				profit = ""
				loss = ""
				if (orgtype == "Profit Making"):
					profit = "Profit"
					loss = "Loss"
					pnlAccountname = "Profit & Loss"
				if (orgtype == "Not For Profit"):
					profit = "Surplus"
					loss = "Deficit"
					pnlAccountname = "Income & Expenditure"

				expense.append({"toby":"","accountname":"DIRECT EXPENSE", "amount":"", "accountcode":""})
				income.append({"toby":"","accountname":"DIRECT INCOME","amount":"", "accountcode":""})

				#Calculate all expense(Direct Expense)
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Direct Expense' or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Direct Expense')) order by accountname;"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if accountDetails["curbal"]==0:
						continue
					if (accountDetails["baltype"]=="Dr"):
						expenseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						expenseTotal -= accountDetails["curbal"]
					expense.append({"toby":"To,","accountname":accountRow["accountname"], "amount":"%.2f"%(accountDetails["curbal"]), "accountcode":accountRow["accountcode"]})

				#Calculate all income(Direct Income)
				accountcodeData = self.con.execute("select accountcode,accountname from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Direct Income' or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Direct Income')) order by accountname;"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					if accountRow["accountname"]==pnlAccountname:
						csAccountcode = self.con.execute("select accountcode from accounts where orgcode=%d and accountname='Closing Stock'"%(orgcode))
						csAccountcodeRow = csAccountcode.fetchone()
						crresult = self.con.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and (drs ? '%s') and (crs ? '%s');"%(int(csAccountcodeRow["accountcode"]),str(financialStart), str(calculateTo), int(accountRow["accountcode"]), int(csAccountcodeRow["accountcode"])))
						crresultRow = crresult.fetchone()
						drresult = self.con.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and (drs ? '%s') and (crs ? '%s');"%(int(csAccountcodeRow["accountcode"]),str(financialStart), str(calculateTo), int(csAccountcodeRow["accountcode"]), int(accountRow["accountcode"])))
						drresultRow = drresult.fetchone()
						if crresultRow["total"]==None and drresultRow["total"]!=None:
							crResult = 0.00
							drResult = drresultRow["total"]
						elif drresultRow["total"]==None and crresultRow["total"]!=None:
							drResult = 0.00
							crResult = crresultRow["total"]
						elif drresultRow["total"]==None and crresultRow["total"]==None:
							drResult = 0.00
							crResult = 0.00
						else:
							drResult = drresultRow["total"]
							crResult = crresultRow["total"]
						totalCsAmt = drResult -  crResult
						incomeTotal += totalCsAmt
						if totalCsAmt!=0:
							income.append({"toby":"By", "accountname":"Closing Stock", "amount":"%.2f"%float(totalCsAmt), "accountcode":csAccountcodeRow["accountcode"]})
					else:
						accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
						if accountDetails["curbal"]==0:
							continue
						if (accountDetails["baltype"]=="Cr"):
							incomeTotal += accountDetails["curbal"]
						if (accountDetails["baltype"]=="Dr"):
							incomeTotal -= accountDetails["curbal"]
						income.append({"toby":"By,","accountname":accountRow["accountname"], "amount":"%.2f"%float(accountDetails["curbal"]), "accountcode":accountRow["accountcode"]})

				if(expenseTotal > incomeTotal):
					difference = expenseTotal - incomeTotal
					income.append({"toby":"By,","accountname":"Gross "+loss+" C/F","amount":"%.2f"%float(difference), "accountcode":""})
					if len(income)>len(expense):
						emptyno = len(income)-len(expense)
						for i in range(0,emptyno):
							expense.append({"toby":"","accountname":"","amount":".", "accountcode":""})
					if len(income)<len(expense):
						emptyno = len(expense)-len(income)
						for i in range(0,emptyno):
							income.append({"toby":"","accountname":"","amount":".", "accountcode":""})
					expense.append({"toby":"","accountname":"TOTAL","amount":"%.2f"%(expenseTotal), "accountcode":""})
					income.append({"toby":"","accountname":"TOTAL","amount":"%.2f"%(expenseTotal), "accountcode":""})
					expenseTotal = 0.00
					expenseTotal = difference
					incomeTotal = 0.00

				if(expenseTotal < incomeTotal):
					difference = incomeTotal - expenseTotal
					expense.append({"toby":"To,","accountname":"Gross "+profit+" C/F","amount":"%.2f"%float(difference), "accountcode":""})
					if len(income)>len(expense):
						emptyno = len(income)-len(expense)
						for i in range(0,emptyno):
							expense.append({"toby":"","accountname":"","amount":".", "accountcode":""})
					if len(income)<len(expense):
						emptyno = len(expense)-len(income)
						for i in range(0,emptyno):
							income.append({"toby":"","accountname":"","amount":".", "accountcode":""})
					expense.append({"toby":"","accountname":"TOTAL","amount":"%.2f"%(incomeTotal), "accountcode":""})
					income.append({"toby":"","accountname":"TOTAL","amount":"%.2f"%(incomeTotal), "accountcode":""})
					incomeTotal = 0.00
					incomeTotal = difference
					expenseTotal = 0.00


				expense.append({"toby":"","accountname":"INDIRECT EXPENSE", "amount":"", "accountcode":""})
				income.append({"toby":"","accountname":"INDIRECT INCOME","amount":"", "accountcode":""})
				if(expenseTotal > incomeTotal):
					expense.append({"toby":"To,","accountname":"Gross "+loss+" B/F","amount":"%.2f"%float(difference), "accountcode":""})
				if(expenseTotal < incomeTotal):
					income.append({"toby":"By,","accountname":"Gross "+profit+" B/F","amount":"%.2f"%float(difference), "accountcode":""})
				difference = 0.00
				#Calculate all expense(Indirect Expense)
				accountcodeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Indirect Expense' or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Indirect Expense')) order by accountname;"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if accountDetails["curbal"]==0:
						continue
					if (accountDetails["baltype"]=="Dr"):
						expenseTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Cr"):
						expenseTotal -= accountDetails["curbal"]
					expense.append({"toby":"To,","accountname":accountRow["accountname"],"amount":"%.2f"%(accountDetails["curbal"]),"accountcode":accountRow["accountcode"]})

				#Calculate all income(Indirect Income)
				accountcodeData = self.con.execute("select accountcode,accountname from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Indirect Income' or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Indirect Income')) order by accountname;"%(orgcode, orgcode, orgcode))
				accountCodes = accountcodeData.fetchall()
				for accountRow in accountCodes:
					accountDetails = calculateBalance(self.con,accountRow["accountcode"], financialStart, financialStart, calculateTo)
					if accountDetails["curbal"]==0:
						continue
					if (accountDetails["baltype"]=="Cr"):
						incomeTotal += accountDetails["curbal"]
					if (accountDetails["baltype"]=="Dr"):
						incomeTotal -= accountDetails["curbal"]
					income.append({"toby":"By,","accountname":accountRow["accountname"],"amount":"%.2f"%(accountDetails["curbal"]), "accountcode":accountRow["accountcode"]})

				if(expenseTotal > incomeTotal):
					difference = expenseTotal - incomeTotal
					income.append({"toby":"By,","accountname":"Net "+loss+" Carried to B/S","amount":"%.2f"%(difference), "accountcode":""})
					if len(income)>len(expense):
						emptyno = len(income)-len(expense)
						for i in range(0,emptyno):
							expense.append({"toby":"","accountname":"","amount":".", "accountcode":""})
					if len(income)<len(expense):
						emptyno = len(expense)-len(income)
						for i in range(0,emptyno):
							income.append({"toby":"","accountname":"","amount":".", "accountcode":""})
					expense.append({"toby":"","accountname":"TOTAL","amount":"%.2f"%(expenseTotal), "accountcode":""})
					income.append({"toby":"","accountname":"TOTAL","amount":"%.2f"%(expenseTotal), "accountcode":""})

				if(expenseTotal < incomeTotal):
					difference = incomeTotal - expenseTotal
					expense.append({"toby":"To,","accountname":"Net "+profit+" Carried to B/S","amount":"%.2f"%(difference), "accountcode":""})
					if len(income)>len(expense):
						emptyno = len(income)-len(expense)
						for i in range(0,emptyno):
							expense.append({"toby":"","accountname":"","amount":".", "accountcode":""})
					if len(income)<len(expense):
						emptyno = len(expense)-len(income)
						for i in range(0,emptyno):
							income.append({"toby":"","accountname":"","amount":".", "accountcode":""})
					expense.append({"toby":"","accountname":"TOTAL","amount":"%.2f"%(incomeTotal), "accountcode":""})
					income.append({"toby":"","accountname":"TOTAL","amount":"%.2f"%(incomeTotal), "accountcode":""})
				self.con.close()


				return {"gkstatus":enumdict["Success"],"expense":expense,"income":income}


			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param='type=deletedvoucher', renderer='json')
	def getdeletedVoucher(self):
		"""
		this function is called when type=deletedvoucher is passed to the url /report
		it returns a grid containing details of all the deleted vouchers
		it first checks the userrole then fetches the data from voucherbin puts into a list.
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
				self.con = eng.connect()
				orgcode = authDetails["orgcode"]
				orgcode = int(orgcode)
				user = self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"]))
				userrole = user.fetchone()
				vouchers = []
				if userrole[0] == -1:
					voucherRow = self.con.execute(select([voucherbin]).where(voucherbin.c.orgcode == orgcode).order_by(voucherbin.c.voucherdate,voucherbin.c.vouchercode))
					voucherData = voucherRow.fetchall()
					for voucher in voucherData:
						vouchers.append({"vouchercode": voucher["vouchercode"], "vouchernumber":voucher["vouchernumber"], "voucherdate": datetime.strftime(voucher["voucherdate"],"%d-%m-%Y"), "narration": voucher["narration"], "drs":voucher["drs"] , "crs":voucher["crs"], "vouchertype": voucher["vouchertype"], "projectname": voucher["projectname"]})
					self.con.close()
					return {"gkstatus":enumdict["Success"], "gkresult": vouchers}
				else:
					self.con.close()
					return {"gkstatus":enumdict["BadPrivilege"]}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
	@view_config(request_param="type=stockreport",renderer="json")
	def stockReport(self):
		"""
		Purpose:
		Return the structured data grid of stock report for given product.
		Input will be productcode,startdate,enddate.
		orgcode will be taken from header and startdate and enddate of fianancial year taken from organisation table .
		returns a list of dictionaries where every dictionary will be one row.
		description:
		This function returns the complete stock report,
		including opening stock every inward and outward quantity and running balance for every transaction along with transaction type.
		at the end we get total inward and outward quantity.
		This report will be on the basis of productcode, startdate and enddate given from the client.
		The orgcode is taken from the header.
		The report will query database to get all in and out records for the given product where the dcinvtn flag is not 20.
		For every iteration of this list with a for loop we will find out the date of transaction from the delchal or invoice table depending on the flag being 4 or 9.
		Cash memo is in the invoice table so even 3 will qualify.
		Then we wil find the customer or supplyer name on the basis of given data.
		Note that if the startdate is same as the yearstart of the organisation then opening stock can be directly taken from the product table.
		if it is later than the startyear then we will have to come to the closing balance of the day before startdate given by client and use it as the opening balance.
		The row will be represented in this grid with every key denoting a column.
		The columns (keys) will be,
		date,particulars,invoice/dcno, transaction type (invoice /delchal),inward quantity,outward quantity ,total inward quantity , total outwrd quanity and balance.
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
				self.con = eng.connect()
				orgcode = authDetails["orgcode"]
				productCode = self.request.params["productcode"]
				startDate =datetime.strptime(str(self.request.params["startdate"]),"%Y-%m-%d")
				endDate =datetime.strptime(str(self.request.params["enddate"]),"%Y-%m-%d")
				stockReport = []
				totalinward = 0.00
				totaloutward = 0.00
				openingStockResult = self.con.execute(select([product.c.openingstock]).where(and_(product.c.productcode == productCode, product.c.orgcode == orgcode)))
				osRow =openingStockResult.fetchone()
				openingStock = osRow["openingstock"]
				stockRecords = self.con.execute(select([stock]).where(and_(stock.c.productcode == productCode,stock.c.orgcode == orgcode, or_(stock.c.dcinvtnflag != 20,stock.c.dcinvtnflag != 40, stock.c.dcinvtnflag != 30,stock.c.dcinvtnflag != 90))))
				stockData = stockRecords.fetchall()
				ysData = self.con.execute(select([organisation.c.yearstart]).where(organisation.c.orgcode == orgcode) )
				ysRow = ysData.fetchone()
				yearStart = datetime.strptime(str(ysRow["yearstart"]),"%Y-%m-%d")
				enData = self.con.execute(select([organisation.c.yearend]).where(organisation.c.orgcode == orgcode) )
				enRow = enData.fetchone()
				yearend = datetime.strptime(str(enRow["yearend"]),"%Y-%m-%d")
				if startDate > yearStart:
					for stockRow in stockData:
						if stockRow["dcinvtnflag"] == 3 or  stockRow["dcinvtnflag"] ==  9:
							countresult = self.con.execute(select([func.count(invoice.c.invid).label('inv')]).where(and_(invoice.c.invoicedate >= yearStart, invoice.c.invoicedate < startDate, invoice.c.invid == stockRow["dcinvtnid"])))
							countrow = countresult.fetchone()
							if countrow["inv"] == 1:
								if  stockRow["inout"] == 9:
									openingStock = float(openingStock) + float(stockRow["qty"])
								if  stockRow["inout"] == 15:
									openingStock = float(openingStock) - float(stockRow["qty"])
						if stockRow["dcinvtnflag"] == 4:
							countresult = self.con.execute(select([func.count(delchal.c.dcid).label('dc')]).where(and_(delchal.c.dcdate >= yearStart, delchal.c.dcdate < startDate, delchal.c.dcid == stockRow["dcinvtnid"])))
							countrow = countresult.fetchone()
							if countrow["dc"] == 1:
								if  stockRow["inout"] == 9:
									openingStock = float(openingStock) + float(stockRow["qty"])
								if  stockRow["inout"] == 15:
									openingStock = float(openingStock) - float(stockRow["qty"])
				stockReport.append({"date":"","particulars":"opening stock","trntype":"","dcid":"","dcno":"","invid":"","invno":"","inward":"%.2f"%float(openingStock)})
				totalinward = totalinward + float(openingStock)
				for finalRow in stockData:
					if finalRow["dcinvtnflag"] == 3 or  finalRow["dcinvtnflag"] ==  9:
						countresult = self.con.execute(select([invoice.c.invoicedate,invoice.c.invoiceno,invoice.c.custid]).where(and_(invoice.c.invoicedate >= startDate, invoice.c.invoicedate <= endDate, invoice.c.invid == finalRow["dcinvtnid"])))
						if countresult.rowcount == 1:
							countrow = countresult.fetchone()
							custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid == countrow["custid"]))
							custrow = custdata.fetchone()
							if custrow!=None:
								custnamedata = custrow["custname"]
							else:
								custnamedata = "Cash Memo"
							if  finalRow["inout"] == 9:
								openingStock = float(openingStock) + float(finalRow["qty"])
								totalinward = float(totalinward) + float(finalRow["qty"])
								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["invoicedate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":custnamedata,"trntype":"invoice","dcid":"","dcno":"","invid":finalRow["dcinvtnid"],"invno":countrow["invoiceno"],"inwardqty":"%.2f"%float(finalRow["qty"]),"outwardqty":"","balance":"%.2f"%float(openingStock)  })
							if  finalRow["inout"] == 15:
								openingStock = float(openingStock) - float(finalRow["qty"])
								totaloutward = float(totaloutward) + float(finalRow["qty"])
								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["invoicedate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":custnamedata,"trntype":"invoice","dcid":"","dcno":"","invid":finalRow["dcinvtnid"],"invno":countrow["invoiceno"],"inwardqty":"","outwardqty":"%.2f"%float(finalRow["qty"]),"balance":"%.2f"%float(openingStock)  })
					if finalRow["dcinvtnflag"] == 4:
						countresult = self.con.execute(select([delchal.c.dcdate,delchal.c.dcno,delchal.c.custid]).where(and_(delchal.c.dcdate >= startDate, delchal.c.dcdate <= endDate, delchal.c.dcid == finalRow["dcinvtnid"])))
						if countresult.rowcount == 1:
							countrow = countresult.fetchone()
							custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid == countrow["custid"]))
							custrow = custdata.fetchone()
							dcinvresult = self.con.execute(select([dcinv.c.invid]).where(dcinv.c.dcid == finalRow["dcinvtnid"]))
							if dcinvresult.rowcount == 1:
								dcinvrow = dcinvresult.fetchone()
								invresult = self.con.execute(select([invoice.c.invoiceno]).where(invoice.c.invid == dcinvrow["invid"]))
								""" No need to check if invresult has rowcount 1 since it must be 1 """
								invrow = invresult.fetchone()
								trntype = "delchal&invoice"
							else:
								dcinvrow = {"invid": ""}
								invrow = {"invoiceno": ""}
								trntype = "delchal"

							if  finalRow["inout"] == 9:
								openingStock = float(openingStock) + float(finalRow["qty"])
								totalinward = float(totalinward) + float(finalRow["qty"])

								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["dcdate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":custrow["custname"],"trntype":trntype,"dcid":finalRow["dcinvtnid"],"dcno":countrow["dcno"],"invid":dcinvrow["invid"],"invno":invrow["invoiceno"],"inwardqty":"%.2f"%float(finalRow["qty"]),"outwardqty":"","balance":"%.2f"%float(openingStock)  })
							if  finalRow["inout"] == 15:
								openingStock = float(openingStock) - float(finalRow["qty"])
								totaloutward = float(totaloutward) + float(finalRow["qty"])

								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["dcdate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":custrow["custname"],"trntype":trntype,"dcid":finalRow["dcinvtnid"],"dcno":countrow["dcno"],"invid":dcinvrow["invid"],"invno":invrow["invoiceno"],"inwardqty":"","outwardqty":"%.2f"%float(finalRow["qty"]),"balance":"%.2f"%float(openingStock)  })

				stockReport.append({"date":"","particulars":"Total","dcid":"","dcno":"","invid":"","invno":"","trntype":"","totalinwardqty":"%.2f"%float(totalinward),"totaloutwardqty":"%.2f"%float(totaloutward)})

				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":stockReport }
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
	@view_config(request_param="type=godownstockreport",renderer="json")
	def godownStockReport(self):
		"""
		Purpose:
		Return the structured data grid of stock report for given product.
		Input will be productcode,startdate,enddate and goid.
		orgcode will be taken from header and startdate and enddate of fianancial year taken from organisation table .
		returns a list of dictionaries where every dictionary will be one row.
		description:
		This function returns the complete stock report,
		including opening stock every inward and outward quantity and running balance for every transaction along with transaction type for a selected product and godown.
		at the end we get total inward and outward quantity.
		This report will be on the basis of productcode, startdate and enddate given from the client.
		The orgcode is taken from the header.
		The report will query database to get all in and out records for the given product where the dcinvtn flag is not 20.
		For every iteration of this list with a for loop we will find out the date of transaction from the delchal or invoice table depending on the flag being 4 or 9.
		Cash memo is in the invoice table so even 3 will qualify.
		Then we wil find the customer or supplyer name on the basis of given data.
		Note that if the startdate is same as the yearstart of the organisation then opening stock can be directly taken from the product table.
		if it is later than the startyear then we will have to come to the closing balance of the day before startdate given by client and use it as the opening balance.
		The row will be represented in this grid with every key denoting a column.
		The columns (keys) will be,
		date,particulars,invoice/dcno, transaction type (invoice /delchal),inward quantity,outward quantity ,total inward quantity , total outwrd quanity and balance.
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
				self.con = eng.connect()
				orgcode = authDetails["orgcode"]
				productCode = self.request.params["productcode"]
				godownCode = self.request.params["goid"]
				startDate =datetime.strptime(str(self.request.params["startdate"]),"%Y-%m-%d")
				endDate =datetime.strptime(str(self.request.params["enddate"]),"%Y-%m-%d")
				stockReport = []
				totalinward = 0.00
				totaloutward = 0.00
				openingStock = 0.00
				goopeningStockResult = self.con.execute(select([goprod.c.goopeningstock]).where(and_(goprod.c.productcode == productCode,goprod.c.goid == godownCode, goprod.c.orgcode == orgcode)))
				gosRow =goopeningStockResult.fetchone()
				if gosRow!=None:
					gopeningStock = gosRow["goopeningstock"]
				else:
					gopeningStock = 0.00
				stockRecords = self.con.execute(select([stock]).where(and_(stock.c.productcode == productCode,stock.c.goid == godownCode,stock.c.orgcode == orgcode, or_(stock.c.dcinvtnflag != 40, stock.c.dcinvtnflag != 30,stock.c.dcinvtnflag != 90))))
				stockData = stockRecords.fetchall()
				ysData = self.con.execute(select([organisation.c.yearstart]).where(organisation.c.orgcode == orgcode) )
				ysRow = ysData.fetchone()
				yearStart = datetime.strptime(str(ysRow["yearstart"]),"%Y-%m-%d")
				enData = self.con.execute(select([organisation.c.yearend]).where(organisation.c.orgcode == orgcode) )
				enRow = enData.fetchone()
				yearend = datetime.strptime(str(enRow["yearend"]),"%Y-%m-%d")
				if startDate > yearStart:
					for stockRow in stockData:
						if stockRow["dcinvtnflag"] == 3 or  stockRow["dcinvtnflag"] ==  9:
							countresult = self.con.execute(select([func.count(invoice.c.invid).label('inv')]).where(and_(invoice.c.invoicedate >= yearStart, invoice.c.invoicedate < startDate, invoice.c.invid == stockRow["dcinvtnid"])))
							countrow = countresult.fetchone()
							if countrow["inv"] == 1:
								if  stockRow["inout"] == 9:
									gopeningStock = float(gopeningStock) + float(stockRow["qty"])
								if  stockRow["inout"] == 15:
									gopeningStock = float(gopeningStock) - float(stockRow["qty"])
						if stockRow["dcinvtnflag"] == 4:
							countresult = self.con.execute(select([func.count(delchal.c.dcid).label('dc')]).where(and_(delchal.c.dcdate >= yearStart, delchal.c.dcdate < startDate, delchal.c.dcid == stockRow["dcinvtnid"])))
							countrow = countresult.fetchone()
							if countrow["dc"] == 1:
								if  stockRow["inout"] == 9:
									gopeningStock = float(gopeningStock) + float(stockRow["qty"])
								if  stockRow["inout"] == 15:
									gopeningStock = float(gopeningStock) - float(stockRow["qty"])
						if stockRow["dcinvtnflag"] == 20:
							countresult = self.con.execute(select([func.count(transfernote.c.transfernoteid).label('tn')]).where(and_(transfernote.c.transfernotedate >= yearStart,transfernote.c.transfernotedate  < startDate,transfernote.c.transfernoteid  == stockRow["dcinvtnid"])))
							countrow = countresult.fetchone()
							if countrow["tn"] == 1:
								if  stockRow["inout"] == 9:
									gopeningStock = float(gopeningStock) + float(stockRow["qty"])
								if  stockRow["inout"] == 15:
									gopeningStock = float(gopeningStock) - float(stockRow["qty"])
				stockReport.append({"date":"","particulars":"opening stock","trntype":"","dcid":"","dcno":"","invid":"","invno":"","tnid":"","tnno":"","inward":"%.2f"%float(gopeningStock)})
				totalinward = totalinward + float(gopeningStock)

				for finalRow in stockData:
					if finalRow["dcinvtnflag"] == 3 or  finalRow["dcinvtnflag"] ==  9:
						countresult = self.con.execute(select([invoice.c.invoicedate,invoice.c.invoiceno,invoice.c.custid]).where(and_(invoice.c.invoicedate >= startDate, invoice.c.invoicedate <= endDate, invoice.c.invid == finalRow["dcinvtnid"])))
						if countresult.rowcount == 1:
							countrow = countresult.fetchone()
							custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid == countrow["custid"]))
							custrow = custdata.fetchone()
							if custrow!=None:
								custnamedata = custrow["custname"]
							else:
								custnamedata = "Cash Memo"
							if  finalRow["inout"] == 9:
								gopeningStock = float(gopeningStock) + float(finalRow["qty"])
								totalinward = float(totalinward) + float(finalRow["qty"])
								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["invoicedate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":custnamedata,"trntype":"invoice","dcid":"","dcno":"","invid":finalRow["dcinvtnid"],"invno":countrow["invoiceno"],"tnid":"","tnno":"","inwardqty":"%.2f"%float(finalRow["qty"]),"outwardqty":"","balance":"%.2f"%float(gopeningStock)  })
							if  finalRow["inout"] == 15:
								gopeningStock = float(gopeningStock) - float(finalRow["qty"])
								totaloutward = float(totaloutward) + float(finalRow["qty"])
								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["invoicedate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":custnamedata,"trntype":"invoice","dcid":"","dcno":"","invid":finalRow["dcinvtnid"],"invno":countrow["invoiceno"],"tnid":"","tnno":"","inwardqty":"","outwardqty":"%.2f"%float(finalRow["qty"]),"balance":"%.2f"%float(gopeningStock)  })
					if finalRow["dcinvtnflag"] == 4:
						countresult = self.con.execute(select([delchal.c.dcdate,delchal.c.dcno,delchal.c.custid]).where(and_(delchal.c.dcdate >= startDate, delchal.c.dcdate <= endDate, delchal.c.dcid == finalRow["dcinvtnid"])))
						if countresult.rowcount == 1:
							countrow = countresult.fetchone()
							custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid == countrow["custid"]))
							custrow = custdata.fetchone()
							dcinvresult = self.con.execute(select([dcinv.c.invid]).where(dcinv.c.dcid == finalRow["dcinvtnid"]))
							if dcinvresult.rowcount == 1:
								dcinvrow = dcinvresult.fetchone()
								invresult = self.con.execute(select([invoice.c.invoiceno]).where(invoice.c.invid == dcinvrow["invid"]))
								""" No need to check if invresult has rowcount 1 since it must be 1 """
								invrow = invresult.fetchone()
								trntype = "delchal&invoice"
							else:
								dcinvrow = {"invid": ""}
								invrow = {"invoiceno": ""}
								trntype = "delchal"

							if  finalRow["inout"] == 9:
								gopeningStock = float(gopeningStock) + float(finalRow["qty"])
								totalinward = float(totalinward) + float(finalRow["qty"])

								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["dcdate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":custrow["custname"],"trntype":trntype,"dcid":finalRow["dcinvtnid"],"dcno":countrow["dcno"],"invid":dcinvrow["invid"],"invno":invrow["invoiceno"],"tnid":"","tnno":"","inwardqty":"%.2f"%float(finalRow["qty"]),"outwardqty":"","balance":"%.2f"%float(gopeningStock)  })
							if  finalRow["inout"] == 15:
								gopeningStock = float(gopeningStock) - float(finalRow["qty"])
								totaloutward = float(totaloutward) + float(finalRow["qty"])

								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["dcdate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":custrow["custname"],"trntype":trntype,"dcid":finalRow["dcinvtnid"],"dcno":countrow["dcno"],"invid":dcinvrow["invid"],"invno":invrow["invoiceno"],"tnid":"","tnno":"","inwardqty":"","outwardqty":"%.2f"%float(finalRow["qty"]),"balance":"%.2f"%float(gopeningStock)  })
					if finalRow["dcinvtnflag"] == 20:
						countresult = self.con.execute(select([transfernote.c.transfernotedate,transfernote.c.transfernoteno]).where(and_(transfernote.c.transfernotedate >= startDate, transfernote.c.transfernotedate <= endDate, transfernote.c.transfernoteid == finalRow["dcinvtnid"])))
						if countresult.rowcount == 1:
							countrow = countresult.fetchone()
							if  finalRow["inout"] == 9:
								gopeningStock = float(gopeningStock) + float(finalRow["qty"])
								totalinward = float(totalinward) + float(finalRow["qty"])
								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["transfernotedate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":"","trntype":"transfer note","dcid":"","dcno":"","invid":"","invno":"","tnid":finalRow["dcinvtnid"],"tnno":countrow["transfernoteno"],"inwardqty":"%.2f"%float(finalRow["qty"]),"outwardqty":"","balance":"%.2f"%float(gopeningStock)  })
							if  finalRow["inout"] == 15:
								gopeningStock = float(gopeningStock) - float(finalRow["qty"])
								totaloutward = float(totaloutward) + float(finalRow["qty"])
								stockReport.append({"date":datetime.strftime(datetime.strptime(str(countrow["transfernotedate"].date()),"%Y-%m-%d").date(),"%d-%m-%Y"),"particulars":"","trntype":"transfer note","dcid":"","dcno":"","invid":"","invno":"","tnid":finalRow["dcinvtnid"],"tnno":countrow["transfernoteno"],"inwardqty":"","outwardqty":"%.2f"%float(finalRow["qty"]),"balance":"%.2f"%float(gopeningStock)  })


				stockReport.append({"date":"","particulars":"Total","dcid":"","dcno":"","invid":"","invno":"","tnid":"","tnno":"","trntype":"","totalinwardqty":"%.2f"%float(totalinward),"totaloutwardqty":"%.2f"%float(totaloutward)})
				return {"gkstatus":enumdict["Success"],"gkresult":stockReport }

				self.con.close()
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
	@view_config(request_param='type=closingbalance', renderer='json')
	def closingBalance(self):
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
				accountCode=self.request.params["accountcode"]
				financialStart = self.request.params["financialstart"]
				calculateTo =  self.request.params["calculateto"]
				calbalData = calculateBalance(self.con,accountCode, financialStart, financialStart, calculateTo)
				currentBalance=calbalData["curbal"]
				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":currentBalance}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
