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
  """

from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice, budget
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
from gkcore.models.gkdb import accounts, groupsubgroups
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
                    budlist.append({"budid":l["budid"], "budname":l["budname"],"startdate":datetime.strftime(l["startdate"],'%d-%m-%Y'),"enddate":datetime.strftime(l["enddate"],'%d-%m-%Y'),"btype":l["budtype"],"totalamount":sum(l["contents"].itervalues())})
                
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

    @view_config(request_method='GET',request_param='type=cashReport', renderer='json')
    def cashBdgReport(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        else:
            # try:
                self.con = eng.connect()
                if "goid" in authDetails:
                    result = self.con.execute(select([budget.c.budid,budget.c.budname,budget.c.budtype,budget.c.contents,budget.c.startdate,budget.c.enddate,budget.c.gaflag]).where(and_(budget.c.orgcode==authDetails["orgcode"],budget.c.budid== self.request.params["budid"], budget.c.goid == authDetails["goid"])))
                else:
                    result = self.con.execute(select([budget.c.budid,budget.c.budname,budget.c.budtype,budget.c.contents,budget.c.startdate,budget.c.enddate,budget.c.gaflag]).where(and_(budget.c.orgcode==authDetails["orgcode"],budget.c.budid== self.request.params["budid"])))
                list = result.fetchall()
                budlist = []
                for l in list:
                    budlist.append({"budid":l["budid"], "budname":l["budname"],"startdate":datetime.strftime(l["startdate"],'%d-%m-%Y'),"enddate":datetime.strftime(l["enddate"],'%d-%m-%Y'),"btype":l["budtype"],"contents":l["contents"],"gaflag":l["gaflag"]})

                groupReport = []
                if(budlist[0]["btype"] == 3):
                    if(budlist[0]["gaflag"] == 1):
                        accReport = []
                        startdate = datetime.strptime(budlist[0]["startdate"],"%d-%m-%Y").strftime("%Y-%m-%d")
                        enddate = datetime.strptime(budlist[0]["enddate"],"%d-%m-%Y").strftime("%Y-%m-%d")
                        financialStart = self.request.params["financialstart"]

                        calbaldata=[]
                        budgetCr = 0
                        budgetDr = 0
                        totalBudget = 0
                        totalVariance =0
                        for account in budlist[0]["contents"].keys():
                            calbalData = calculateBalance(self.con,account, financialStart, startdate, enddate)

                            if (calbalData["baltype"] == 'Cr'):
                                variance = budlist[0]["contents"][account] - calbalData["curbal"]
                                if(variance > 0 or variance == 0):
                                    vartype = ''
                                if(variance < 0):
                                    vartype = 'Cr'
                            if (calbalData['baltype'] == 'Dr'):
                                variance = budlist[0]["contents"][account] + calbalData["curbal"]
                                if(variance > budlist[0]["contents"][account]):
                                    variance = abs(calbalData["curbal"])
                                    vartype = 'Dr'
                                elif(variance > 0 or variance == 0):
                                    vartype = ''
                                elif(variance < 0):
                                    vartype = 'Cr'
                            acc_name = self.con.execute(select([accounts.c.accountname]).where(and_(accounts.c.accountcode == account, accounts.c.orgcode == authDetails["orgcode"])))
                            acc_name = acc_name.fetchone()
                            accReport.append({"vartype":vartype,"accountname":str(acc_name[0]),"accountcode":account,"budget":budlist[0]["contents"][account], "variance":variance, "totalcr":calbalData["totalcrbal"], "totaldr":calbalData["totaldrbal"]})
                            
                        for budgett in accReport:
                            totalBudget = totalBudget + budgett["budget"]
                            totalVariance = totalVariance + budgett["variance"]
                            budgetCr = budgetCr + budgett["totalcr"]
                            budgetDr = budgetDr + budgett["totaldr"]
                        total = [{"totalBudget":totalBudget,"totalVariance":totalVariance,"budgetCr":budgetCr,"budgetDr":budgetDr}]
                        return{"gkstatus": gkcore.enumdict["Success"], "gkresult":accReport, "total":total}

                    if(budlist[0]["gaflag"] == 19):
                        budgetCr = 0
                        budgetDr = 0
                        for subgroup in budlist[0]["contents"].keys():
                            accReport = []
                            groupname = self.con.execute(select([groupsubgroups.c.groupname]).where(and_(groupsubgroups.c.groupcode == subgroup, groupsubgroups.c.orgcode == authDetails["orgcode"])))
                            groupname = groupname.fetchone()
                            startdate = datetime.strptime(budlist[0]["startdate"],"%d-%m-%Y").strftime("%Y-%m-%d")
                            enddate = datetime.strptime(budlist[0]["enddate"],"%d-%m-%Y").strftime("%Y-%m-%d")
                            financialStart = self.request.params["financialstart"]
                            total = 0
                            acc = self.con.execute(select([accounts.c.accountcode,accounts.c.accountname]).where(and_(accounts.c.groupcode == subgroup, accounts.c.orgcode == authDetails["orgcode"])))
                            acc = acc.fetchall()
                            for account in acc:
                                calbalData = calculateBalance(self.con,account["accountcode"], financialStart, startdate, enddate)
                                if (calbalData["baltype"] == 'Cr'):
                                    total = total - calbalData["curbal"]
                                if (calbalData['baltype'] == 'Dr'):
                                    total = total + calbalData["curbal"]
                                accReport.append({"accountname":account["accountname"],"accountcode":account["accountcode"], "totalcr":calbalData["totalcrbal"], "totaldr":calbalData["totaldrbal"]})

                            for crdr in accReport:
                                budgetCr = budgetCr + crdr["totalcr"]
                                budgetDr = budgetDr + crdr["totaldr"]
                            if(total < 0):
                                variance = budlist[0]["contents"][subgroup] - abs(total)
                                if(variance > 0 or variance == 0):
                                    vartype = ''
                                if(variance < 0):
                                    vartype = 'Cr'
                            if(total > 0 or total == 0):
                                variance = budlist[0]["contents"][subgroup] + abs(total)
                                if(variance > budlist[0]["contents"][subgroup]):
                                    variance = abs(total)
                                    vartype = 'Dr'
                                elif(variance > 0 or variance == 0):
                                    vartype = ''
                                elif(variance < 0):
                                    vartype = 'Cr'

                            groupReport.append({"gaflag":19,"groupname":groupname[0],"budget":budlist[0]["contents"][subgroup],"variance":variance,"vartype":vartype,"accountdata":accReport})
                        totalBudget = 0
                        totalVariance =0
                        for budgett in groupReport:
                            totalBudget = totalBudget + budgett["budget"]
                            totalVariance = totalVariance + budgett["variance"]
                        total = [{"totalBudget":totalBudget,"totalVariance":totalVariance,"budgetCr":budgetCr,"budgetDr":budgetDr}]
                        return{"gkstatus": gkcore.enumdict["Success"], "gkresult":groupReport, "total":total}
            # except:
            #     return {"gkstatus":enumdict["ConnectionFailed"] }
            # finally:
            #     self.con.close()