"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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
   "Karan Kamdar" <kamdar.karan@gmail.com>
   "Prajkta Patkar" <prajkta@riseup.com>
   "Abhijith Balan" <abhijith@dff.org.in>
   "rohan khairnar" <rohankhairnar@gmail.com>
  
  This API is written for budgeting module. With this API budget add,edit,delete,list of budget and budget report calculation can be done.
  This api is related to "BUDGET TABLE".   
  """

from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice, budget, accounts, groupsubgroups
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, desc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from datetime import datetime,date
import jwt
import gkcore
from gkcore.views.api_login import authCheck
from gkcore.views.api_user import getUserRole
from gkcore.models import gkdb


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
    Then the Total Dr and Cr only for payment and receipt vouchers is calculated.
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
        tdrfrm = con.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s' and (vouchertype = 'payment' or vouchertype = 'receipt')"%(int(accountCode),financialStart,calculateFrom,))
        tcrfrm = con.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s' and (vouchertype = 'payment' or vouchertype = 'receipt')"%(int(accountCode),financialStart,calculateFrom))
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
        if ttlDrUptoFrom >  ttlCrUptoFrom:
            balanceBrought = ttlDrUptoFrom - ttlCrUptoFrom
            balType = "Dr"
            openingBalanceType = "Dr"
        if ttlCrUptoFrom >  ttlDrUptoFrom:
            balanceBrought = ttlCrUptoFrom - ttlDrUptoFrom
            balType = "Cr"
            openingBalanceType = "Cr"
    tdrfrm = con.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s'and (vouchertype = 'payment' or vouchertype = 'receipt')"%(int(accountCode),calculateFrom, calculateTo))
    tdrRow = tdrfrm.fetchone()
    tcrfrm = con.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and (vouchertype = 'payment' or vouchertype = 'receipt')"%(int(accountCode),calculateFrom, calculateTo))
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

def calculateBalance2(con,accountCode,financialStart,calculateFrom,calculateTo,goid):

    # This function is same as above but only difference is that it having extra parameter authDetails which is 
    # require for branching feature.
    # as user logged in branchwise the the goid which is branchid is send through authDetails. By checking that authDetails it 
    # decides that it logged in as branchwise or not. If logged in as branchwise then select data related to that goid. 
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
        # goid is branchid. authdetails will have branchid when logged in branchwise.
        # if branchwise logged in then should select result related to that goid.
        tdrfrm = con.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s' and goid = '%d' and (vouchertype = 'payment' or vouchertype = 'receipt')"%(int(accountCode),financialStart,calculateFrom,goid))
        tcrfrm = con.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s' and goid = '%d' and (vouchertype = 'payment' or vouchertype = 'receipt')"%(int(accountCode),financialStart,calculateFrom,goid))
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
        if ttlDrUptoFrom >  ttlCrUptoFrom:
            balanceBrought = ttlDrUptoFrom - ttlCrUptoFrom
            balType = "Dr"
            openingBalanceType = "Dr"
        if ttlCrUptoFrom >  ttlDrUptoFrom:
            balanceBrought = ttlCrUptoFrom - ttlDrUptoFrom
            balType = "Cr"
            openingBalanceType = "Cr"
    # goid is branchid. authdetails will have branchid when logged in branchwise.
    # if branchwise logged in then should select result related to that goid.
    tdrfrm = con.execute("select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and goid = '%d' and (vouchertype = 'payment' or vouchertype = 'receipt')"%(int(accountCode),calculateFrom, calculateTo,goid))
    tdrRow = tdrfrm.fetchone()
    tcrfrm = con.execute("select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and goid = '%d' and (vouchertype = 'payment' or vouchertype = 'receipt')"%(int(accountCode),calculateFrom, calculateTo,goid))
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

@view_defaults(route_name='budget')
class api_invoice(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection
    @view_config(request_method='POST',renderer='json')
    def addBudget(self):
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
                Bdata = self.request.json_body
                budgetdataset = Bdata
                budgetdataset["orgcode"] = authDetails["orgcode"]
                result = self.con.execute(budget.insert(),[budgetdataset])
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
               return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET', request_param='bud=all',renderer='json')
    def getlistofbudgets(self):
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
                if "goid" in authDetails:
                    result = self.con.execute(select([budget.c.budid,budget.c.budname,budget.c.budtype,budget.c.contents,budget.c.startdate,budget.c.enddate]).where(and_(budget.c.orgcode==authDetails["orgcode"], budget.c.goid == authDetails["goid"])))
                else:
                    result = self.con.execute(select([budget.c.budid,budget.c.budname,budget.c.budtype,budget.c.contents,budget.c.startdate,budget.c.enddate]).where(budget.c.orgcode==authDetails["orgcode"]))
                list = result.fetchall()
                budlist=[]
                for l in list:
                    budlist.append({"budid":l["budid"], "budname":l["budname"],"startdate":datetime.strftime(l["startdate"],'%d-%m-%Y'),"enddate":datetime.strftime(l["enddate"],'%d-%m-%Y'),"btype":l["budtype"]})
                
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":budlist }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET', request_param='bud=details',renderer='json')
    def getbudgetdetails(self):
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
                if "goid" in authDetails:
                    result = self.con.execute(select([budget.c.budid,budget.c.budname,budget.c.budtype,budget.c.contents,budget.c.startdate,budget.c.enddate,budget.c.gaflag]).where(and_(budget.c.orgcode==authDetails["orgcode"],budget.c.budid== self.request.params["budid"], budget.c.goid == authDetails["goid"])))
                else:
                    result = self.con.execute(select([budget.c.budid,budget.c.budname,budget.c.budtype,budget.c.contents,budget.c.startdate,budget.c.enddate,budget.c.gaflag]).where(and_(budget.c.orgcode==authDetails["orgcode"],budget.c.budid== self.request.params["budid"])))
                list = result.fetchall()
                budlist=[]
                for l in list:
                    budlist.append({"budid":l["budid"], "budname":l["budname"],"startdate":datetime.strftime(l["startdate"],'%d-%m-%Y'),"enddate":datetime.strftime(l["enddate"],'%d-%m-%Y'),"btype":l["budtype"],"contents":l["contents"],"gaflag":l["gaflag"]})
                
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":budlist }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='PUT', renderer='json')
    def editbudgets(self):
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
                result = self.con.execute(budget.update().where(budget.c.budid==dataset["budid"]).values(dataset))
                return {"gkstatus":enumdict["Success"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='DELETE', renderer='json')
    def deletebudget(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        else:
            try:
                dataset = self.request.json_body
                self.con = eng.connect()
                user = self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid==authDetails["userid"]))
                userid=user.fetchone()
                if(userid[0] == -1):
                    result = self.con.execute(budget.delete().where(budget.c.budid==dataset["budid"]))
                    return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
    
    @view_config(request_method='GET',request_param='type=budgetReport', renderer='json')
    def budgetReport(self):
        """
        Purpose:
        To calculate complete budget for given time period.
        Input from webapp: financialstartdate,budgetperiod,budgetid
        CASH Budget: ("btype" = 3)
        fetch all field data from budget table with budget Id. 
        only in cash budget the contents(JSON field) field containes "flowin" and "flowout" data.
        flowin : incoming cash budget and flowout : outgoing cash budget.
        for cash budget only that accounts which are under cash and bank subgroups are take in to consideration.
        after fetching all accounts for loop is done to calculate balance with calculatebalance function written above.
        calculatebalance fun. will gives (per account totalCr and Dr, balance remaining with its type(Cr/Dr),
        account opening balance with type )
        Calculations for cash budget:
        budget balance = (total opening balance + cash inflow) - cash ouflow
        variance(cash inflow) = inflow - total Dr
        variance(cash outflow) = outflow - total Cr
        variance(balance) = budget balance - total balance

        """
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
                financialStart = self.request.params["financialstart"]
                result = self.con.execute(select([budget.c.goid,budget.c.budid,budget.c.budname,budget.c.budtype,budget.c.contents,budget.c.startdate,budget.c.enddate,budget.c.gaflag]).where(and_(budget.c.orgcode==authDetails["orgcode"],budget.c.budid== self.request.params["budid"])))
                list = result.fetchall()
                budlist = []
                for l in list:
                    budlist.append({"goid":l["goid"],"budid":l["budid"], "budname":l["budname"],"startdate":datetime.strftime(l["startdate"],'%d-%m-%Y'),"enddate":datetime.strftime(l["enddate"],'%d-%m-%Y'),"btype":l["budtype"],"contents":l["contents"],"gaflag":l["gaflag"]})
                
                startdate = datetime.strptime(budlist[0]["startdate"],"%d-%m-%Y").strftime("%Y-%m-%d")
                enddate = datetime.strptime(budlist[0]["enddate"],"%d-%m-%Y").strftime("%Y-%m-%d")
                
                if(budlist[0]["btype"] == 3):
                    budgetIn = budlist[0]["contents"]["inflow"]
                    budgetOut = budlist[0]["contents"]["outflow"]
                    cbAccountsData = self.con.execute("select accountcode, openingbal, accountname from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Bank','Cash')) order by accountname"%(authDetails["orgcode"],authDetails["orgcode"]))
                    cbAccounts = cbAccountsData.fetchall()
                    calbaldata=[]
                    totalopeningbal = 0
                    totalCr = 0
                    totalDr = 0
                    accBal = 0
                    totalCurbal = 0
                    accData =[]
                    for bal in cbAccounts:
                        # goid is branch id . if branchid in budget then should calculate balance only for that branch.
                        if (budlist[0]["goid"] != None):
                            calbaldata = calculateBalance2(self.con,bal["accountcode"], financialStart, startdate, enddate, budlist[0]["goid"])
                        else:
                            calbaldata = calculateBalance(self.con,bal["accountcode"], financialStart, startdate, enddate)
                        if (calbaldata["openbaltype"] == 'Dr'):
                            totalopeningbal = totalopeningbal + calbaldata["balbrought"]
                        if (calbaldata["openbaltype"] == 'Cr'):
                            totalopeningbal = totalopeningbal - calbaldata["balbrought"]
                        totalCr = totalCr + calbaldata["totalcrbal"]
                        totalDr = totalDr + calbaldata["totaldrbal"]
                        if (calbaldata["baltype"] == 'Cr'):
                            totalCurbal = totalCurbal - calbaldata["curbal"]
                            accBal = -calbaldata["curbal"]
                        if (calbaldata["baltype"] == 'Dr'):
                            totalCurbal = totalCurbal + calbaldata["curbal"]
                            accBal = calbaldata["curbal"]
                        accData.append({"accountname":bal["accountname"],"accCr":calbaldata["totalcrbal"],"accDr":calbaldata["totaldrbal"],"accBal":accBal})
                    budgetBal = float(totalopeningbal) + float(budgetIn) - float(budgetOut)
                    # Variance calculation
                    varCr = float(budgetOut) - float(totalCr)
                    varDr = float(budgetIn) - float(totalDr)
                    varBal = float(budgetBal) - float(totalCurbal)
                    total = [{"totalopeningbal":totalopeningbal,"budgetIn":float(budgetIn),"budgetOut":float(budgetOut),"budgetBal":budgetBal,"varCr":varCr,"varDr":varDr,"varBal":varBal,"accData":accData}]
                    return{"gkstatus": gkcore.enumdict["Success"], "gkresult":total}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()