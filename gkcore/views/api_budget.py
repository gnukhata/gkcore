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
from gkcore.models.gkdb import invoice, budget, accounts, groupsubgroups, users
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, desc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from datetime import datetime,date,timedelta
import jwt
import gkcore
from gkcore.views.api_login import authCheck
from gkcore.views.api_user import getUserRole
from gkcore.models import gkdb
from gkcore.views.api_reports import calculateBalance, calculateBalance2

@view_defaults(route_name='budget')
class api_budget(object):
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
                role = self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"]))
                userrole = role.fetchone()
                if(userrole[0] == -1 or userrole[0] == 0):
                    Bdata = self.request.json_body
                    budgetdataset = Bdata
                    budgetdataset["orgcode"] = authDetails["orgcode"]
                    result = self.con.execute(budget.insert(),[budgetdataset])
                    return {"gkstatus":enumdict["Success"]}
                else:
                    return {"gkstatus":gkcore.enumdict["ActionDisallowed"] }
            except exc.IntegrityError:
               return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET', request_param='bud=all',renderer='json')
    def getlistofbudgets(self):
        """ To get all budgets list """
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
        """ To get single budget details as per budget id 'budid' """
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
                list = result.fetchone()
                budlist={"budid":list["budid"], "budname":list["budname"],"startdate":datetime.strftime(list["startdate"],'%d-%m-%Y'),"enddate":datetime.strftime(list["enddate"],'%d-%m-%Y'),"btype":list["budtype"],"contents":list["contents"],"gaflag":list["gaflag"]}
                
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":budlist }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET', request_param='type=addtab',renderer='json')
    def getbalatbeginning(self):
        """ For clossing balances of all acounts.It  will fetch all acounts balance from financial startdate to the previous date of budget startdate with their accountcode.
        It will take financial start and budget start date as input.
        for budget type 3 which is cash. It will fetch all accounts which comes under the bank and cash subgroup.
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
                cbAccountsData = self.con.execute("select accountcode, openingbal, accountname from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Bank','Cash')) order by accountname"%(authDetails["orgcode"],authDetails["orgcode"]))
                cbAccounts = cbAccountsData.fetchall()
                d = self.request.params["uptodate"]
                calculateToDate = datetime.strptime(d,"%Y-%m-%d")
                prevday = (calculateToDate - timedelta(days=1))
                prevday = str(prevday)[0:10]
                balatbegin=0
                for bal in cbAccounts:
                    calbaldata = calculateBalance(self.con,bal["accountcode"],str(self.request.params["financialstart"]), self.request.params["financialstart"], prevday)
                    if (calbaldata["baltype"] == 'Cr'):
                        balatbegin = balatbegin - calbaldata["curbal"]
                    if (calbaldata["baltype"] == 'Dr'):
                        balatbegin = balatbegin + calbaldata["curbal"]

                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":balatbegin }
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
                role = self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"]))
                userrole = role.fetchone()
                if(userrole[0] == -1 or userrole[0] == 0):
                    dataset = self.request.json_body
                    result = self.con.execute(budget.update().where(budget.c.budid==dataset["budid"]).values(dataset))
                    return {"gkstatus":enumdict["Success"]}
                else:
                    return {"gkstatus":gkcore.enumdict["ActionDisallowed"] }
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
                role = self.con.execute(select([users.c.userrole]).where(users.c.userid==authDetails["userid"]))
                userrole=role.fetchone()
                if(userrole[0] == -1 or userrole[0] == 0):
                    result = self.con.execute(budget.delete().where(budget.c.budid==dataset["budid"]))
                    return {"gkstatus":enumdict["Success"]}
                else:
                    return {"gkstatus":gkcore.enumdict["ActionDisallowed"] }
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
                result = self.con.execute(select([budget.c.goid,budget.c.contents,budget.c.startdate,budget.c.enddate]).where(and_(budget.c.orgcode==authDetails["orgcode"],budget.c.budid== self.request.params["budid"])))
                list = result.fetchone()
                startdate = str(list["startdate"])[0:10]
                enddate = str(list["enddate"])[0:10]
                budgetIn = list["contents"]["inflow"]
                budgetOut = list["contents"]["outflow"]
                cbAccountsData = self.con.execute("select accountcode, openingbal, accountname from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Bank','Cash')) order by accountname"%(authDetails["orgcode"],authDetails["orgcode"]))
                cbAccounts = cbAccountsData.fetchall()
                # to calculate opening balance. If budget start date and financial start date are same then the opening balance for 
                # budget will becomes accounts opening balance. Else opening balance for budget will get by calculating all crs and drs up to previous date of 
                # budget start date, means add of total accounts remaining balance.
                totalopeningbal = 0
                if(startdate != financialStart):
                    d = startdate
                    calculateToDate = datetime.strptime(d,"%Y-%m-%d")
                    prevday = (calculateToDate - timedelta(days=1))
                    prevday = str(prevday)[0:10]
                    for bal in cbAccounts:
                        calculate = calculateBalance(self.con,bal["accountcode"],str(self.request.params["financialstart"]), self.request.params["financialstart"], prevday)
                        if (calculate["baltype"] == 'Cr'):
                            totalopeningbal = totalopeningbal - calculate["curbal"]
                        if (calculate["baltype"] == 'Dr'):
                            totalopeningbal = totalopeningbal + calculate["curbal"]
                else:
                    prevday = startdate
                    for bal in cbAccounts:
                        calculate = calculateBalance(self.con,bal["accountcode"],str(self.request.params["financialstart"]), self.request.params["financialstart"], prevday)
                        if (calculate["openbaltype"] == 'Cr'):
                            totalopeningbal = totalopeningbal - calculate["balbrought"]
                        if (calculate["openbaltype"] == 'Dr'):
                            totalopeningbal = totalopeningbal + calculate["balbrought"]
                calbaldata=[]
                totalCr = 0
                totalDr = 0
                totalCurbal = 0
                accData =[]
                
                for bal in cbAccounts:
                    accountcode = str(bal["accountcode"])
                    # goid is branch id . if branchid in budget then should calculate balance only for that branch.
                    if (list["goid"] != None):
                        calbaldata = calculateBalance2(self.con,accountcode, financialStart, startdate, enddate, list["goid"])
                        transactionsRecords = self.con.execute("select drs,crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s' or crs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(startdate, enddate,accountcode,accountcode, list["goid"]))
                    else:
                        calbaldata = calculateBalance(self.con,accountcode, financialStart, startdate, enddate)
                        transactionsRecords = self.con.execute("select drs,crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s' or crs ? '%s') order by voucherdate DESC,vouchercode ;"%(startdate, enddate,accountcode,accountcode))
                    transactions = transactionsRecords.fetchall()
                    accCr = 0
                    accDr = 0
                    for transaction in transactions:
                        if transaction["drs"].has_key(str(accountcode)):
                            accDr += float(transaction["drs"][accountcode])
                            totalDr += float(transaction["drs"][accountcode])
                        if transaction["crs"].has_key(accountcode):
                            accCr += float(transaction["crs"][accountcode])
                            totalCr += float(transaction["crs"][accountcode])
                    if (calbaldata["baltype"] == 'Cr'):
                        totalCurbal = totalCurbal - calbaldata["curbal"]
                        accBal = -calbaldata["curbal"]
                    if (calbaldata["baltype"] == 'Dr'):
                        totalCurbal = totalCurbal + calbaldata["curbal"]
                        accBal = calbaldata["curbal"]
                    accData.append({"accountname":bal["accountname"],"accCr":"%.2f"%float(accCr),"accDr":"%.2f"%float(accDr),"accBal":"%.2f"%float(accBal)})
                budgetBal = float(totalopeningbal) + float(budgetIn) - float(budgetOut)
                # Variance calculation
                varCr = float(budgetOut) - float(totalCr)
                varDr = float(budgetIn) - float(totalDr)
                varBal = float(budgetBal) - float(totalCurbal)
                total = {"totalCr":"%.2f"%float(totalCr),"totalDr":"%.2f"%float(totalDr),"budgetclosingbal":"%.2f"%float(totalCurbal),"totalopeningbal":"%.2f"%float(totalopeningbal),"budgetIn":"%.2f"%float(budgetIn),"budgetOut":"%.2f"%float(budgetOut),"budgetBal":"%.2f"%float(budgetBal),"varCr":"%.2f"%float(varCr),"varDr":"%.2f"%float(varDr),"varBal":"%.2f"%float(varBal),"accData":accData}
                return{"gkstatus": gkcore.enumdict["Success"], "gkresult":total}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()