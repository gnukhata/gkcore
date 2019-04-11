"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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
                    budgetdataset = self.request.json_body
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
                btype = self.request.params["btype"]
                if "goid" in authDetails:
                    result = self.con.execute(select([budget.c.budid,budget.c.budname,budget.c.budtype,budget.c.contents,budget.c.startdate,budget.c.enddate]).where(and_(budget.c.budtype==btype,budget.c.orgcode==authDetails["orgcode"], budget.c.goid == authDetails["goid"])))
                else:
                    result = self.con.execute(select([budget.c.budid,budget.c.budname,budget.c.budtype,budget.c.contents,budget.c.startdate,budget.c.enddate]).where(and_(budget.c.budtype==btype,budget.c.orgcode==authDetails["orgcode"])))
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
        Budget type = 3: (Cash Budget)
        It will fetch all accounts except accounts under Bank and Cash subgroups.
        Accounts under Direct,Indirect Expense and Current Liabilities are consider in Outflow
        Accounts under Direct,Indirect Income and Current Assets are consider in Inflow.
        Budget type = 5:(Expense Budget)
        It will fetch all accounts under Direct and Indirect Expense group and their subgroups.
        Budget type = 19: (Sales Budget)
        It will fetch all accounts under Direct Expense and Income group and their subgroup.
        Income accounts will consider in Sales or Income and Expense accounts will consider in Purchases or Expense.

        """
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
                uptodate = self.request.params["uptodate"]
                financialStart = self.request.params["financialstart"]
                btype = self.request.params["btype"]
                # budget type 3: cash budget
                if btype == '3':
                    result = self.con.execute("select accountcode, openingbal, accountname from accounts where orgcode = %d"%(authDetails["orgcode"]))
                    accounts = result.fetchall()

                    if(uptodate != financialStart):
                        calculateToDate = datetime.strptime(uptodate,"%Y-%m-%d")
                        prevday = (calculateToDate - timedelta(days=1))
                        prevday = str(prevday)[0:10]
                        inAccountdata=[]
                        outAccountdata=[]
                        openingBal=0.00

                        for bal in accounts:
                            groupData = self.con.execute("select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"%(int(bal["accountcode"]),int(bal["accountcode"])))
                            groupRecord = groupData.fetchone()

                            # Outflow accounts
                            if(groupRecord[0] == 'Direct Expense' or groupRecord[0] == 'Indirect Expense' or groupRecord[0] == 'Current Liabilities' ):
                                outAccountdata.append({"accountname":bal["accountname"],"accountcode":bal["accountcode"]})

                            # Inflow accounts 
                            if(groupRecord[0] == 'Direct Income' or groupRecord[0] == 'Indirect Income' or groupRecord[0] == 'Current Assets' ):
                                
                                subgroupname = self.con.execute("select groupname from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d)"%int(bal["accountcode"]))
                                subgroup = subgroupname.fetchone()
                                # bank and cash accounts balance as opening balance of budget
                                if(subgroup[0] == 'Bank' or subgroup[0] == 'Cash'):
                                    if "goid" in authDetails:
                                        calbaldata = calculateBalance2(self.con,bal["accountcode"],str(financialStart), str(financialStart), prevday, authDetails["goid"])
                                    else:
                                        calbaldata = calculateBalance(self.con,bal["accountcode"],str(financialStart), str(financialStart), prevday)
                                    
                                    if (calbaldata["baltype"] == 'Cr'):
                                        openingBal = float(openingBal) - float(calbaldata["curbal"])
                                    if (calbaldata["baltype"] == 'Dr'):
                                        openingBal = float(openingBal) + float(calbaldata["curbal"])
                                else:
                                    inAccountdata.append({"accountname":bal["accountname"],"accountcode":bal["accountcode"]})
                        
                        data={"inflow":inAccountdata,"outflow":outAccountdata,"openingbal":"%.2f"%float(openingBal)}
                        return {"gkstatus": gkcore.enumdict["Success"], "gkresult":data }
                    else:
                        inAccountdata=[]
                        outAccountdata=[]
                        openingBal=0.00
                        for bal in accounts:
                            groupData = self.con.execute("select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"%(int(bal["accountcode"]),int(bal["accountcode"])))
                            groupRecord = groupData.fetchone()
                            # Outflow accounts
                            if(groupRecord[0] == 'Direct Expense' or groupRecord[0] == 'Indirect Expense' or groupRecord[0] == 'Current Liabilities' ):
                                outAccountdata.append({"accountname":bal["accountname"],"accountcode":bal["accountcode"]})
                            # Inflow accounts
                            if(groupRecord[0] == 'Direct Income' or groupRecord[0] == 'Indirect Income' or groupRecord[0] == 'Current Assets' ):
                                subgroupname = self.con.execute("select groupname from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d)"%int(bal["accountcode"]))
                                subgroup = subgroupname.fetchone()
                                # cash and bank accounts balance as opening balance of budget
                                if(subgroup[0] == 'Bank' or subgroup[0] == 'Cash'):
                                    openingBal= float(openingBal) + float(bal["openingbal"])
                                else:
                                    inAccountdata.append({"accountname":bal["accountname"],"accountcode":bal["accountcode"]})

                        data={"inflow":inAccountdata,"outflow":outAccountdata,"openingbal":"%.2f"%float(openingBal)}
                        return {"gkstatus": gkcore.enumdict["Success"], "gkresult":data }
                    

                # budget type 16: pnl budget
                if btype == '16':
                    
                    




                    
                # if btype == '19':
                #     directExpense = self.con.execute("select accountcode,accountname from accounts where orgcode = %d and (groupcode in (select groupcode from groupsubgroups where orgcode=%d and (groupname = 'Direct Expense' or subgroupof in (select groupcode from groupsubgroups where orgcode= %d and (groupname='Direct Expense')))))"%(authDetails["orgcode"],authDetails["orgcode"],authDetails["orgcode"]))                    
                #     accounts = directExpense.fetchall();
                    
                #     expense=[]
                #     totalBalAtBegin=0.00
                #     if(uptodate != financialStart):
                #         calculateToDate = datetime.strptime(uptodate,"%Y-%m-%d")
                #         prevday = (calculateToDate - timedelta(days=1))
                #         prevday = str(prevday)[0:10]
                #         for account in accounts:
                #             if "goid" in authDetails:
                #                 data = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(str(financialStart), prevday,account["accountcode"], authDetails["goid"]))
                #             else:
                #                 data = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') order by voucherdate DESC,vouchercode ;"%(str(financialStart), prevday,account["accountcode"]))
                #             data = data.fetchall()
                #             accountbal=0.00
                #             for transaction in data:
                #                 accountbal += float(transaction["drs"][str(account["accountcode"])])
                #             totalBalAtBegin = float(totalBalAtBegin) + float(accountbal)
                #             expense.append({"accountname":account["accountname"],"accountcode":account["accountcode"],"accountbal":"%.2f"%float(accountbal)})
                #     else:
                #         for account in accounts:
                #             expense.append({"accountname":account["accountname"],"accountcode":account["accountcode"],"accountbal":"%.2f"%float(0)})

                #     directIncome = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and (groupcode in (select groupcode from groupsubgroups where orgcode=%d and (groupname = 'Direct Income' or subgroupof in (select groupcode from groupsubgroups where orgcode= %d and (groupname ='Direct Income')))))"%(authDetails["orgcode"],authDetails["orgcode"],authDetails["orgcode"]))
                #     accounts = directIncome.fetchall();
                #     income=[]
                #     totalBalAtBegin=0.00
                #     if(uptodate != financialStart):
                #         calculateToDate = datetime.strptime(uptodate,"%Y-%m-%d")
                #         prevday = (calculateToDate - timedelta(days=1))
                #         prevday = str(prevday)[0:10]
                #         for account in accounts:
                #             if "goid" in authDetails:
                #                 data = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(str(financialStart), prevday,account["accountcode"], authDetails["goid"]))
                #             else:
                #                 data = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') order by voucherdate DESC,vouchercode ;"%(str(financialStart), prevday,account["accountcode"]))
                #             data = data.fetchall()
                #             accountbal=0.00
                #             for transaction in data:
                #                 accountbal += float(transaction["crs"][str(account["accountcode"])])
                #             totalBalAtBegin = float(totalBalAtBegin) + float(accountbal)
                #             income.append({"accountname":account["accountname"],"accountcode":account["accountcode"],"accountbal":"%.2f"%float(accountbal)})
                #     else:
                #         for account in accounts:
                #             income.append({"accountname":account["accountname"],"accountcode":account["accountcode"],"accountbal":"%.2f"%float(0)})
                #     total = {"totalbal":"%.2f"%float(totalBalAtBegin),"expense":expense,"income":income}
                #     return {"gkstatus": gkcore.enumdict["Success"], "gkresult":total }
            # except:
            #     return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            # finally:
            #     self.con.close()

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
    
    @view_config(request_method='GET',request_param='type=cashReport', renderer='json')
    def cashReport(self):
        """
        Purpose:
        To calculate complete budget for given time period.
        Input from webapp: financialstartdate,budgetperiod,budgetid
        contents field is Json field which have all accountcodes which used in budget as key and their budget amount as value.
        
        OutFlow accounts : which are from Direct,Indirect Expense and Current Liabilities groups.
        InFlow accounts : which are from Direct,Indirect Income and Current Assets groups.

        Here we need to consider all accounts under the Bank and Cash subgroups to get transaction details from vouchers.
        For each accounts of cash and bank we are getting opening and closing balance for budget using calculateBalance function.
        Opening balance = from financial start date to previous date of budget start date.
        Closing balance = from financial start date to end date of budget.
        Again actual opening balance and budgeted opening balance will be same.But the actual closing and bugdeted closing balances will e different.
        Budgeted closing bal. = Actual opening + total inflow - total outflow

        For Inflow and Outflow if any accounts which has transaction with cash and bank accounts but not used in budget, we also consider that accounts with budget 0.

        For transaction consider payment,receipt vouchers and only that sales and purchase vouchers which having transaction with Cash and Bank accounts.
        
        variance part will only for inflow and outflow accounts.
        variance inflow = actual - budgeted , variance outflow = budgeted - actuals
        variance in percent = (variance * 100)/ budgeted

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
                content = list["contents"]
                accountslist = content.keys()

                # To calaculate total Outflow and Inflow 
                totalBudgetInflow = 0.00
                totalBudgetOutflow = 0.00
                for acc in content:
                    groupData = self.con.execute("select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"%(int(acc),int(acc)))
                    groupRecord = groupData.fetchone()
                    if(groupRecord[0] == 'Direct Expense' or groupRecord[0] == 'Indirect Expense' or groupRecord[0] == 'Current Liabilities' ):
                        totalBudgetOutflow = float(totalBudgetOutflow) + float(content[str(acc)])
                    if(groupRecord[0] == 'Direct Income' or groupRecord[0] == 'Indirect Income' or groupRecord[0] == 'Current Assets' ):
                        totalBudgetInflow = float(totalBudgetInflow) + float(content[str(acc)])

                # getting all accounts under cash and bank subgroups.
                cbAccountsData = self.con.execute("select accountcode, openingbal, accountname from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Bank','Cash')) order by accountname"%(authDetails["orgcode"],authDetails["orgcode"]))
                cbAccounts = cbAccountsData.fetchall()
                cbAccountscode=[]
                totalopeningbal = 0.00
                actualClosingBal = 0.00
                
                openingacc=[]
                closing=[]
                if(startdate != financialStart):
                    d = startdate
                    calculateToDate = datetime.strptime(d,"%Y-%m-%d")
                    prevday = (calculateToDate - timedelta(days=1))
                    prevday = str(prevday)[0:10]
                else:
                    prevday = startdate
                # for all cash and bank accounts.
                for bal in cbAccounts:
                    cbAccountscode.append(bal["accountcode"])
                    # If budget is done with branchwise. goid is branchid.
                    if (list["goid"] != None):
                        calculate = calculateBalance2(self.con,bal["accountcode"],financialStart, financialStart, prevday,list["goid"])
                        closingdata = calculateBalance2(self.con,bal["accountcode"],financialStart, financialStart, enddate,list["goid"])
                    else:
                        calculate = calculateBalance(self.con,bal["accountcode"],financialStart, financialStart, prevday)
                        closingdata = calculateBalance(self.con,bal["accountcode"], financialStart, financialStart, enddate)
                    openaccountbal = 0.00
                    # To calculate opening balance.
                    if(startdate != financialStart):
                        if (calculate["baltype"] == 'Cr'):
                            totalopeningbal = float(totalopeningbal) - float(calculate["curbal"])
                            openaccountbal = - float(calculate["curbal"])
                        if (calculate["baltype"] == 'Dr'):
                            totalopeningbal = float(totalopeningbal) + float(calculate["curbal"])
                            openaccountbal = float(calculate["curbal"])
                    else:
                        # Opening balances of accounts                                                                      
                        totalopeningbal = float(totalopeningbal) + float(bal["openingbal"])
                        openaccountbal = float(bal["openingbal"])                           
                    openingacc.append({"accountname":bal["accountname"],"balance":"%.2f"%float(openaccountbal)})

                    # Actual Closing and Budgeted Closing Balance calculation for Cash and Bank accounts.
                    closingaccountbal = 0.00
                    if (closingdata["baltype"] == 'Cr'):
                        actualClosingBal = float(actualClosingBal) - float(closingdata["curbal"])
                        closingaccountbal = - float(closingdata["curbal"])
                    if (closingdata["baltype"] == 'Dr'):
                        actualClosingBal = float(actualClosingBal) + float(closingdata["curbal"])
                        closingaccountbal = float(closingdata["curbal"])
                    #closing budgeted balance for each account
                    accbudget = float(openaccountbal) + float(totalBudgetInflow) - float(totalBudgetOutflow) 
                    var= float(closingaccountbal) - float(accbudget)
                    varinpercent = (float(var) * 100)/ float(accbudget)
                    closing.append({"accountname":bal["accountname"],"balance":"%.2f"%float(closingaccountbal),"budget":"%.2f"%float(accbudget),"var":"%.2f"%float(var),"varinpercent":"%.2f"%float(varinpercent)})
                    
                    # To get all accounts which having transaction with Bank and Cash accounts.
                    # If Cash or Bank account is present in drs then get accountcode present in crs and crs accounts are consider in inflow
                    # If Cash or Bank account is present in crs then get accountcode present in drs and drs accounts are consider in outflow
                    inflowAccData = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s')  order by voucherdate DESC,vouchercode ;"%(startdate, enddate,bal["accountcode"]))
                    outflowAccData = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s')  order by voucherdate DESC,vouchercode ;"%(startdate, enddate,bal["accountcode"]))

                    inAcc = inflowAccData.fetchall()
                    outAcc = outflowAccData.fetchall()
                    # here we making new list (accountslist) of all accountcodes for inflow and outflow.
                    # That accounts which are used in budget and that also which having transaction cash and bank accounts but not used in budget.
                    # accountlist already having accounts used in budget.
                    for acc in inAcc:
                        if acc[0].keys()[0] not in accountslist:
                            accountslist.append(acc[0].keys()[0])
                    for acc in outAcc:
                        if acc[0].keys()[0] not in accountslist:
                            accountslist.append(acc[0].keys()[0])
                
                inflowAccounts=[]
                outflowAccounts=[]
                totalActualOutflow = 0.00
                totalActualInflow = 0.00
                # all inflow and outflow accountcodes are in accountslist
                for acc in accountslist:
                    # To get account name and their groupname.
                    result = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode == int(acc)))
                    accountname = result.fetchone()
                    groupData = self.con.execute("select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"%(int(acc),int(acc)))
                    groupRecord = groupData.fetchone()
                    
                    if(groupRecord[0] == 'Direct Expense' or groupRecord[0] == 'Indirect Expense' or groupRecord[0] == 'Current Liabilities' ):
                        # if accounts is under this group then that will consider for outflow.
                        # fetching drs as expense are always consider as debit.Fetching crs to check weather transaction with bank or cash accounts.
                        outflowacc = self.con.execute("select drs,crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') order by voucherdate DESC,vouchercode ;"%(startdate, enddate,int(acc)))
                        outflowacc = outflowacc.fetchall()
                        accountbal = 0.00
                        for a in outflowacc:
                            # cbAccountscode is having all cash and bank accounts. If crs have accounts from cash and bank only then this vouchers amount will consider.
                            if int(a["crs"].keys()[0]) in cbAccountscode:
                                accountbal += float(a["drs"][str(int(acc))])
                            else:
                                accountbal += 0.00
                        totalActualOutflow = float(totalActualOutflow) + float(accountbal)
                        # if this account used in budget then add budgeted value, calculate variance and variance in percentage.
                        # else budgetd value will be 0 and variance in percentage will consider 0. 
                        if acc in content:
                            var = float(content[str(acc)]) - float(accountbal)
                            varInPercent = (var* 100) / (content[str(acc)] )
                            outflowAccounts.append({"accountname":accountname[0],"actual":"%.2f"%float(accountbal),"budget":"%.2f"%float(content[str(acc)]),"var":"%.2f"%float(var),"varinpercent":"%.2f"%float(varInPercent)})
                        else:
                            var = float(0) - float(accountbal)
                            varInPercent = 0.00
                            outflowAccounts.append({"accountname":accountname[0],"actual":"%.2f"%float(accountbal),"budget":"%.2f"%float(0),"var":"%.2f"%float(var),"varinpercent":"%.2f"%float(varInPercent)})
                    
                    # Almost similar for work for inflow accounts as done for outflow in above.
                    # Only difference is insted of drs,crs consider crs,drs 
                    if(groupRecord[0] == 'Direct Income' or groupRecord[0] == 'Indirect Income' or groupRecord[0] == 'Current Assets' ):
                        inflowacc = self.con.execute("select crs,drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') order by voucherdate DESC,vouchercode ;"%(startdate, enddate,int(acc)))
                        inflowacc = inflowacc.fetchall()
                        accountbal = 0.00
                        for a in inflowacc:
                            if int(a["drs"].keys()[0]) in cbAccountscode:
                                accountbal += float(a["crs"][str(int(acc))])
                            else:
                                accountbal += 0.00
                        totalActualInflow = float(totalActualInflow) + float(accountbal)
                        
                        if acc in content:
                            var = float(accountbal) - float(content[str(acc)])
                            varInPercent = (var * 100) / content[str(acc)] 
                            inflowAccounts.append({"accountname":accountname[0],"actual":"%.2f"%float(accountbal),"budget":"%.2f"%float(content[str(acc)]),"var":"%.2f"%float(var),"varinpercent":"%.2f"%float(varInPercent)})
                        else:
                            var = float(accountbal) - float(0)
                            varInPercent = 0.00
                            inflowAccounts.append({"accountname":accountname[0],"actual":"%.2f"%float(accountbal),"budget":"%.2f"%float(0),"var":"%.2f"%float(var),"varinpercent":"%.2f"%float(varInPercent)})
                
                total={"inflow":inflowAccounts,"outflow":outflowAccounts,"openingacc":openingacc,"closing":closing}
                total["opening"]= "%.2f"%float(totalopeningbal)
                total["actualclosing"] = "%.2f"%float(actualClosingBal)
                total["budgetclosing"] = "%.2f"%float(float(totalBudgetInflow) + float(totalopeningbal) - float(totalBudgetOutflow))
                total["budgetin"] = "%.2f"%float(totalBudgetInflow)
                total["budgetout"] = "%.2f"%float(totalBudgetOutflow)
                total["actualin"] = "%.2f"%float(totalActualInflow)
                total["actualout"] = "%.2f"%float(totalActualOutflow)
                total["varin"] = "%.2f"%float(float(totalActualInflow) - float(totalBudgetInflow))
                total["varout"] = "%.2f"%float(float(totalBudgetOutflow) - float(totalActualOutflow))
                total["varpercentin"] = "%.2f"%float(float(total["varin"]) * 100 / totalBudgetInflow)
                total["varpercentout"] = "%.2f"%float(float(total["varout"]) * 100 / totalBudgetOutflow)
                return{"gkstatus": gkcore.enumdict["Success"], "gkresult":total}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET',request_param='type=expenseReport', renderer='json')
    def expenseReport(self):
        """Purpose:
                To calculate report for expense budget. It takes budgetid(budid) and fanancialstart as input.
            In this only that accounts will consider which comes under the Direct and Indirect expense group.
            Here contents field of budget table will have json type data. In which key will be accountcode and their value will be budget amount.
            Firstly will fetch budget details from budget table as per budget id.
            Here we need previuos date of start date of budget to get the previously expense of each accounts.
            For getting accounts balance we will considr only Dr from vouchers because expense is nominal accounts so it means debit all losses and expense.
            By fetching balance for each accounts we will takes vouchers for budget periods. So that we will get actual expense balance of each account for that period.
            To calculate variance of accounts: Budgeted - Actual 
            Here we need to consider gross profit to calculate net profit.
            gross profit = total Direct Income - total Direct Expense
            budget gross profit is from financial start to budget start date
            Actual gross profit is from financial start date to budget end date.

            budgeted net profit = budget gross profit - total budget
            Actual net profit = actual gross profit - total actual
            variance of net profit = actual - budgeted.

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
                budgetdata = result.fetchone()
                startdate = str(budgetdata["startdate"])[0:10]
                enddate = str(budgetdata["enddate"])[0:10]
                accounts = budgetdata["contents"]
                accountdata=[]
                totalbudget =0.00
                totalactual =0.00
                totalvariance =0.00
                totalbudgetedbal =0.00
                totalactualbal =0.00
                # To calculate actual of each accounts used in budget and total actual expense.
                for key in accounts:
                    budgetamount = "%.2f"%float(accounts[key])
                    accountname = self.con.execute("select accountname from accounts where accountcode = %d"%(int(key)))
                    accountname = accountname.fetchone()
                    if (budgetdata["goid"] != None):
                        actualAccData = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(startdate, enddate,key, budgetdata["goid"]))
                    else:
                        actualAccData = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') order by voucherdate DESC,vouchercode ;"%(startdate, enddate,key))
                    actualAccData = actualAccData.fetchall()
                    actualAmount =0.00
                    
                    for transaction in actualAccData:
                        actualAmount += float(transaction["drs"][key])

                    accVariance = float(budgetamount) - float(actualAmount)
                    totalbudget += float(budgetamount)
                    totalactual += float(actualAmount)
                    totalvariance += float(accVariance)

                    accountdata.append({"actualamount":"%.2f"%float(actualAmount),"accountname":accountname[0],"accountcode":key,"budgetamount":"%.2f"%float(budgetamount),"accvariance":"%.2f"%float(accVariance)})
                
                total={"totalbudget":"%.2f"%float(totalbudget),"totalactual":"%.2f"%float(totalactual),"totalvariance":"%.2f"%float(totalvariance),"accountdata":accountdata}
                
                if(startdate != financialStart):
                    calculateToDate = datetime.strptime(startdate,"%Y-%m-%d")
                    startdate = (calculateToDate - timedelta(days=1))
                    startdate = str(startdate)[0:10]

                # budget gross profit is before the budget start date and actual gross profit is up to the end date of budget.
                # Net profit calculation using gross profit.
                directExp = self.con.execute("select accountcode from accounts where orgcode = %d and (groupcode in (select groupcode from groupsubgroups where orgcode=%d and (groupname = 'Direct Expense' or subgroupof in (select groupcode from groupsubgroups where orgcode= %d and (groupname='Direct Expense')))))"%(authDetails["orgcode"],authDetails["orgcode"],authDetails["orgcode"]))
                expAccounts = directExp.fetchall()
                expBalance = 0.00
                actualExpBal=0.00
                directIncome = self.con.execute("select accountcode from accounts where orgcode = %d and (groupcode in (select groupcode from groupsubgroups where orgcode=%d and (groupname = 'Direct Income' or subgroupof in (select groupcode from groupsubgroups where orgcode= %d and (groupname='Direct Income')))))"%(authDetails["orgcode"],authDetails["orgcode"],authDetails["orgcode"]))
                incomeAccounts = directIncome.fetchall()
                incomeBalance = 0.00
                actualIncomeBal=0.00
                # Expense accounts calculation for gross profit
                for account in expAccounts:
                    # Expenses data for previous or budget gross profit and actualdata is for actual gross profit.
                    if "goid" in authDetails:
                        data = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(str(financialStart), startdate,account["accountcode"], authDetails["goid"]))
                        actualdata = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(str(financialStart), enddate,account["accountcode"], authDetails["goid"]))
                    else:
                        data = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') order by voucherdate DESC,vouchercode ;"%(str(financialStart), startdate,account["accountcode"]))
                        actualdata = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') order by voucherdate DESC,vouchercode ;"%(str(financialStart), enddate,account["accountcode"]))
                    data = data.fetchall()
                    actualdata = actualdata.fetchall()

                    accountbal=0.00
                    for transaction in data:
                        accountbal += float(transaction["drs"][str(account["accountcode"])])
                    expBalance = float(expBalance) + float(accountbal)
                    actualAccountbal=0.00
                    for transaction in actualdata:
                        actualAccountbal += float(transaction["drs"][str(account["accountcode"])])
                    actualExpBal = float(actualExpBal) + float(actualAccountbal)
                
                # Incomes accounts calculation for gross profit
                for account in incomeAccounts:
                    # Incomes data for previous or budget gross profit and actualdata is for actual gross profit.
                    if "goid" in authDetails:
                        data = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(str(financialStart), startdate,account["accountcode"], authDetails["goid"]))
                        actualdata = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(str(financialStart), enddate,account["accountcode"], authDetails["goid"]))
                    else:
                        data = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') order by voucherdate DESC,vouchercode ;"%(str(financialStart), startdate,account["accountcode"]))
                        actualdata = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') order by voucherdate DESC,vouchercode ;"%(str(financialStart), enddate,account["accountcode"]))
                    data = data.fetchall()
                    actualdata = actualdata.fetchall()

                    accountbal=0.00
                    for transaction in data:
                        accountbal += float(transaction["crs"][str(account["accountcode"])])
                    incomeBalance = float(incomeBalance) + float(accountbal)
                    
                    actualAccountbal=0.00
                    for transaction in actualdata:
                        actualAccountbal += float(transaction["crs"][str(account["accountcode"])])
                    actualIncomeBal = float(actualIncomeBal) + float(actualAccountbal)

                grossProfit = float(incomeBalance) - float(expBalance)
                actualGrossProfit = float(actualIncomeBal) - float(actualExpBal)
                # Net profit calculation
                budgetedNetProfit = float(grossProfit) - float(total["totalbudget"])
                actualNetProfit = float(actualGrossProfit) - float(total["totalactual"])
                varNetProfit = float(actualNetProfit) - float(budgetedNetProfit)

                total["grossprofit"] = "%.2f"%float(grossProfit)
                total["budgetnet"] = "%.2f"%float(budgetedNetProfit)
                total["actualnet"] = "%.2f"%float(actualNetProfit)
                total["varnet"] = "%.2f"%float(varNetProfit)
                
                return{"gkstatus": gkcore.enumdict["Success"], "gkresult":total}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
    
    @view_config(request_method='GET',request_param='type=salesReport', renderer='json')
    def salesReport(self):
        """ Purpose:
            To calculate report for sales budget. It will take budgetid and financial start date as input.
            Here Sales budget will deal with two groups. Direct Expense and Direct Income. So it will consider only that accounts which
            comes under this group or its subgroups. 
            The contents field of budget table will have json data and that having 'accounts' as keys and budget amount as value.
            For expense we will consider all drs from voucher for expense group accounts which will give total of expense for budgeted period.
            For income (sales) we will consider all crs from voucher for income group accounts which will give total of income for budgeted period.
            Here we calculate profit as:
            budget income(sales) - budget expense = budget profit
            actual income(sales) - actual expense = actual profit
            And Variance of all :
            sales variance = actual sales - budgeted sales
            purchase variance = budgeted purchase - actual purchase
            profit = actual - budgeted
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
                budgetdata = result.fetchone()
                startdate = str(budgetdata["startdate"])[0:10]
                enddate = str(budgetdata["enddate"])[0:10]
                accountsList = budgetdata["contents"].keys()
                
                totalOpeningBal=0.00
                actualTotalExpense=0.00
                actualTotalIncome=0.00
                expensedata = []
                incomedata = []
                budgetIncome = 0.00
                budgetExpense = 0.00
                # all accounts in budget
                for bal in accountsList:
                    accountName = self.con.execute("select accountname from accounts where accountcode = %d"%(int(bal)))
                    accountName = accountName.fetchone()
                    groupName = self.con.execute("select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"%(int(bal),int(bal)))
                    groupName = groupName.fetchone()
                    # Purchase or expenses accounts 
                    if (groupName[0] == 'Direct Expense'):
                        if (budgetdata["goid"] != None):
                            actualAccData = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(startdate, enddate,bal, budgetdata["goid"]))
                        else:
                            actualAccData = self.con.execute("select drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') order by voucherdate DESC,vouchercode ;"%(startdate, enddate,bal))
                        actualAccData = actualAccData.fetchall()
                        actualAmount = 0.00
                        for transaction in actualAccData:
                            actualAmount += float(transaction["drs"][bal])

                        actualTotalExpense = float(actualTotalExpense) + float(actualAmount)
                        budgetExpense = float(budgetExpense) + float(budgetdata["contents"][bal])
                        accountVar = budgetdata["contents"][bal] - float(actualAmount)

                        expensedata.append({"budget":"%.2f"%float(budgetdata["contents"][bal]),"accountname":accountName[0],"actual":"%.2f"%float(actualAmount),"var":"%.2f"%float(accountVar)})
                    # sales or income accounts
                    if (groupName[0] == 'Direct Income'):
                        calculateToDate = datetime.strptime(startdate,"%Y-%m-%d")
                        prevday = (calculateToDate - timedelta(days=1))
                        prevday = str(prevday)[0:10]
                        if (budgetdata["goid"] != None):
                            openingAccBal = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(str(financialStart), prevday,bal, budgetdata["goid"]))
                            actualAccBal = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') and goid = '%d' order by voucherdate DESC,vouchercode ;"%(startdate, enddate,bal, budgetdata["goid"]))
                        else:
                            openingAccBal = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') order by voucherdate DESC,vouchercode ;"%(str(financialStart), prevday,bal))
                            actualAccBal = self.con.execute("select crs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') order by voucherdate DESC,vouchercode ;"%(startdate, enddate,bal))
                        actualAccBal = actualAccBal.fetchall()
                        openingAccBal = openingAccBal.fetchall()

                        actualAmount = 0.00
                        for transaction in actualAccBal:
                            actualAmount += float(transaction["crs"][bal])

                        actualTotalIncome = float(actualTotalIncome) + float(actualAmount)
                        budgetIncome = float(budgetIncome) + float(budgetdata["contents"][bal])
                        accountVar = float(actualAmount) - float(budgetdata["contents"][bal])

                        accOpeningBal=0.00
                        for transaction in openingAccBal:
                            accOpeningBal += float(transaction["crs"][bal])
                        totalOpeningBal = float(totalOpeningBal) + float(accOpeningBal)
                        
                        accBalance = float(actualAmount) + float(accOpeningBal)
                        incomedata.append({"budget":"%.2f"%float(budgetdata["contents"][bal]),"var":"%.2f"%float(accountVar),"accountname":accountName[0],"actual":"%.2f"%float(actualAmount),"accbalance":"%.2f"%float(accOpeningBal)})
                
                BudgetedProfit = float(budgetIncome) - float(budgetExpense)
                ActualProfit = float(actualTotalIncome) - float(actualTotalExpense)
                # variance calculation
                varProfit =  float(ActualProfit) - float(BudgetedProfit)
                varExpense = float(budgetExpense) - float(actualTotalExpense)
                varIncome =  float(actualTotalIncome) - float(budgetIncome)
                # Total sales amount
                closingBal = float(totalOpeningBal) + float(actualTotalIncome)
                total = {"closingbal":"%.2f"%float(closingBal),"varexpense":"%.2f"%float(varExpense),"varincome":"%.2f"%float(varIncome),"openingbal":"%.2f"%float(totalOpeningBal),"budgetincome":"%.2f"%float(budgetIncome),"budgetexpense":"%.2f"%float(budgetExpense),"budgetprofit":"%.2f"%float(BudgetedProfit),"actualincome":"%.2f"%float(actualTotalIncome),"actualexpense":"%.2f"%float(actualTotalExpense),"actualprofit":"%.2f"%float(ActualProfit),"varprofit":"%.2f"%float(varProfit),"expensedata":expensedata,"incomedata":incomedata}
                
                return{"gkstatus": gkcore.enumdict["Success"], "gkresult":total}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

                        
            