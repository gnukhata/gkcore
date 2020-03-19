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
"Rupali Badgujar" <rupalibadgujar1234@gmail.com>
'Prajkta Patkar' <prajkta@riseup.net>
"Abhijith Balan" <abhijithb21@openmailbox.org>
"""
from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc,alias, or_, func, desc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.sql.expression import null
from gkcore.models.meta import dbconnect
from gkcore.models.gkdb import billwise, invoice, customerandsupplier, vouchers,accounts,organisation
from datetime import datetime, date
from monthdelta import monthdelta
from operator import itemgetter
from natsort import natsorted
import calendar
import math
from gkcore.views.api_user import getUserRole
from gkcore.views.api_reports import stockonhandfun
from gkcore.views.api_reports import calculateBalance

#This function is use to show amount wise top five unpaid invoice list at dashboard
def amountwiseinvoice(inoutflag,orgcode):
    try:
        con = eng.connect()
        fiveInvoiceslistdata=[]
        # Invoices in descending order of amount.
        fiveinvoices = con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.invoicetotal,invoice.c.amountpaid, invoice.c.custid]).where(and_(invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.icflag == 9,invoice.c.orgcode == orgcode, invoice.c.inoutflag == inoutflag)).order_by(desc(invoice.c.invoicetotal - invoice.c.amountpaid)).limit(5))
        fiveInvoiceslist = fiveinvoices.fetchall()
        for inv in fiveInvoiceslist:
            # for fetch customer or supplier name using cust id in invoice.
            csd = con.execute(select([customerandsupplier.c.custname, customerandsupplier.c.csflag]).where(and_(customerandsupplier.c.custid == inv["custid"],customerandsupplier.c.orgcode==orgcode)))
            csDetails = csd.fetchone()
            fiveInvoiceslistdata.append({"invid":inv["invid"],"invoiceno":inv["invoiceno"],"invoicedate":datetime.strftime(inv["invoicedate"],'%d-%m-%Y'),"balanceamount":"%.2f"%(float(inv["invoicetotal"]-inv["amountpaid"])), "custname":csDetails["custname"],"csflag":csDetails["csflag"]})
        con.close()
        return {"gkstatus":enumdict["Success"],"fiveInvoiceslistdata":fiveInvoiceslistdata}
    except:
        con.close()  
        return{"gkstatus":enumdict["ConnectionFailed"]}
    finally:
        con.close()


#This function is use to show date wise top five unpaid invoice list at dashboard
def datewiseinvoice(inoutflag,orgcode):
    try:
        con = eng.connect()
        fiveInvoiceslistdata=[]
    # Invoices in ascending order of date.                
        fiveinvoices = con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.invoicetotal,invoice.c.amountpaid, invoice.c.custid]).where(and_(invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.icflag == 9,invoice.c.orgcode == orgcode, invoice.c.inoutflag == inoutflag)).order_by(invoice.c.invoicedate).limit(5))
        fiveInvoiceslist = fiveinvoices.fetchall()

        for inv in fiveInvoiceslist:
            # for fetch customer or supplier name using cust id in invoice.
            csd = con.execute(select([customerandsupplier.c.custname, customerandsupplier.c.csflag]).where(and_(customerandsupplier.c.custid == inv["custid"],customerandsupplier.c.orgcode==orgcode)))
            csDetails = csd.fetchone()
            fiveInvoiceslistdata.append({"invid":inv["invid"],"invoiceno":inv["invoiceno"],"invoicedate":datetime.strftime(inv["invoicedate"],'%d-%m-%Y'),"balanceamount":"%.2f"%(float(inv["invoicetotal"]-inv["amountpaid"])), "custname":csDetails["custname"],"csflag":csDetails["csflag"]})
        con.close()
        return {"gkstatus":enumdict["Success"],"fiveInvoiceslistdata":fiveInvoiceslistdata}
    except:
        con.close()  
        return{"gkstatus":enumdict["ConnectionFailed"]}
    finally:
        con.close()

# this function use to show invoice count by month at dashbord in bar chart  
def getinvoicecountbymonth(inoutflag,orgcode):
    try:
        con = eng.connect()
        #this is to fetch startdate and enddate
        startenddate=con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == orgcode))
        startenddateprint=startenddate.fetchone()                
                    
        #this is to fetch invoice totalamount month wise
        monthlysortdata=con.execute("select extract(month from invoicedate) as month, sum(invoicetotal) as totalamount from invoice where invoicedate BETWEEN '%s' AND '%s' and inoutflag= %d and icflag=9 and  orgcode= %d group by month order by month" %(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),inoutflag,orgcode))
                    
        monthlysortdataset=monthlysortdata.fetchall()  
        #this is use to send 0 if month have 0 invoice count
        invamount=[0,0,0,0,0,0,0,0,0,0,0,0]
        for count in monthlysortdataset:
            invamount[int(count["month"])-1]=float(count["totalamount"])
        con.close()
        return {"gkstatus":enumdict["Success"],"invamount":invamount}
    except:
        con.close()  
        return{"gkstatus":enumdict["ConnectionFailed"]}
    finally:
        con.close()

# this function use to show top five customer/supplier at dashbord in most valued costomer and supplier div                     
def topfivecustsup(inoutflag,orgcode):
    try:
        con = eng.connect()
        # this is to fetch top five customer which is sort by total amount.
        if inoutflag == 15:
            topfivecust= con.execute("select custid as custid, sum(invoicetotal) as data from invoice where inoutflag=15 and orgcode= %d and icflag=9 group by custid order by data desc limit(5)"%(orgcode))
            topfivecustlist=topfivecust.fetchall()
        # this is to fetch top five suppplier which is sort by total invoice.
        else:
            topfivecust= con.execute("select custid as custid, count(custid) as data from invoice where inoutflag=9 and orgcode=%d and icflag=9  group by custid order by data desc limit(5)"%(orgcode))
            topfivecustlist=topfivecust.fetchall()

        topfivecustdetails=[]
        for inv in topfivecustlist:
            # for fetch customer or supplier name using cust id in invoice.
            csd = con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.custid == inv["custid"],customerandsupplier.c.orgcode==orgcode)))
            csDetails = csd.fetchone()
            topfivecustdetails.append({"custname":csDetails["custname"],"data":float(inv["data"])})
        con.close()
        return {"gkstatus":enumdict["Success"],"topfivecustdetails":topfivecustdetails}
    except:
        con.close()  
        return{"gkstatus":enumdict["ConnectionFailed"]}
    finally:
        con.close()

# this function use to show top five most bought product and service at dashbord in most bought product/service div  
def topfiveprodsev(orgcode):
    #try:
        con = eng.connect()
        # this is to fetch top five product/service  which is sort by  invoice count. 
        topfiveprod= con.execute("select ky as productcode, count(*) as numkeys from invoice cross join lateral jsonb_object_keys(contents) as t(ky) where orgcode=%d and invoice.inoutflag=9 group by ky order by count(*) desc limit(5)"%(orgcode))
        topfiveprodlist=topfiveprod.fetchall()
                        
        prodinfolist=[]
        for prodinfo in topfiveprodlist:
            print (prodinfo)
            proddesc=  con.execute("select productdesc as proddesc from product where productcode=%d and orgcode=%d"%(int(prodinfo["productcode"]),orgcode))
            proddesclist=proddesc.fetchone()
            print (proddesclist)
            prodinfolist.append({"prodcode":prodinfo["productcode"],"count":prodinfo["numkeys"],"proddesc":proddesclist["proddesc"]})
        con.close()
        return {"gkstatus":enumdict["Success"],"prodinfolist":prodinfolist}       
   # except:
   #     con.close()  
   #     return{"gkstatus":enumdict["ConnectionFailed"]}
   # finally:
   #     con.close()

# this function use to show delchal count by month at dashbord in bar chart      
def  delchalcountbymonth(inoutflag,orgcode):
    try:
        con = eng.connect()
        #this is to fetch startdate and enddate
        startenddate=con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == orgcode))
        startenddateprint=startenddate.fetchone()                

        #this is to fetch delchal count month wise
        monthlysortdata=con.execute("select extract(month from stockdate) as month, sum(qty) as total_qty from stock where stockdate BETWEEN '%s' AND '%s' and inout=%d and orgcode= %d and dcinvtnflag=4 group by month order by month" %(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),inoutflag,orgcode))
        monthlysortdataset=monthlysortdata.fetchall()
        #this is use to send 0 if month have 0 delchal count
        totalamount=[0,0,0,0,0,0,0,0,0,0,0,0]
        for count in monthlysortdataset:
            totalamount[int(count["month"])-1]=float(count["total_qty"])
        con.close()
        return {"gkstatus":enumdict["Success"],"totalamount":totalamount}    
    except:
        con.close()  
        return{"gkstatus":enumdict["ConnectionFailed"]}
    finally:
        con.close()

# this fuction returns most sold product and stock on hand count for daashboard
def stockonhanddashboard(orgcode):
    try:
        con = eng.connect()
        yearenddate=con.execute("select yearend as calculateto from organisation where orgcode=%d"%(orgcode))
        yearenddateresult=yearenddate.fetchone()
        calculateto= datetime.strftime(yearenddateresult["calculateto"],'%Y-%m-%d')
        # this is use to fetch top five product/service  which is order by  invoice count.  
        topfiveprod=con.execute("select ky as productcode from invoice cross join lateral jsonb_object_keys(contents) as t(ky) where orgcode=%d and invoice.inoutflag=15 group by ky order by count(*) desc limit(5)"%(orgcode))
        topfiveprodlist=topfiveprod.fetchall()
        prodcodedesclist=[]
        for prodcode in topfiveprodlist:
            proddesc=con.execute("select productdesc as proddesc from product where productcode=%d"%(int(prodcode["productcode"])))
            proddesclist=proddesc.fetchone()
            prodcodedesclist.append({"prodcode":prodcode["productcode"],"proddesc":proddesclist["proddesc"]})

        prodname=[]
        stockresultlist=[]    
        for i in prodcodedesclist:
            prodname.append({"prodname":i["proddesc"]})
            orgcode = orgcode
            productCode = i["prodcode"]
            endDate =datetime.strptime(str(calculateto),"%Y-%m-%d")
            stockresult=stockonhandfun(orgcode, productCode,endDate)
            stockresultlist.append(stockresult)
                    
        con.close()
        return {"gkstatus":enumdict["Success"],"stockresultlist":stockresultlist,"productname":prodname}           
    except:
        con.close()  
        return{"gkstatus":enumdict["ConnectionFailed"]}
    finally:
        con.close()

# this fuction returns month wise bank and cash sub account  balance on daashboard
def cashbankbalance(orgcode):
    try:
        con = eng.connect()
        #below query is fetch account code for bank account 
        accountcodebank=con.execute("select accountcode as accountcode from accounts where groupcode = (select groupcode from groupsubgroups where groupname = 'Bank' and orgcode=%d) and orgcode =%d"%(orgcode,orgcode))
        accountCodeBank=accountcodebank.fetchall()
        #below query is fetch account code for cash account 
        accountcodecash=con.execute("select accountcode as accountcode from accounts where groupcode = (select groupcode from groupsubgroups where groupname = 'Cash' and orgcode=%d) and orgcode =%d"%(orgcode,orgcode))
        accountCodeCash=accountcodecash.fetchall()
        #below query is fetch finantial yearstart and yearend date
        financialstart=con.execute("select yearstart as financialstart, yearend as financialend from organisation where orgcode=%d"% orgcode)
        financialStartresult=financialstart.fetchone()
        financialStart= datetime.strftime(financialStartresult["financialstart"],'%Y-%m-%d')
        financialEnd= financialStartresult["financialend"]
        monthCounter = 1
        monthname=[]
        bankbalancedata=[] 
        cashbalancedata=[]
        balancedata={}

        startMonthDate=financialStartresult["financialstart"]
        # endMonthDate gives last date of month 
        endMonthDate = date(startMonthDate.year, startMonthDate.month, (calendar.monthrange(startMonthDate.year, startMonthDate.month)[1]))
        while endMonthDate <= financialEnd:
            month=calendar.month_abbr[startMonthDate.month]
            monthname.append(month)
            bankbalance = 0.00
            cashbalance = 0.00
            #below code give calculate balance for bank account 
            for bal in accountCodeBank:                
                calbaldata = calculateBalance(con,bal["accountcode"],str(financialStart), str(startMonthDate), str(endMonthDate))
                if (calbaldata["baltype"] == 'Cr'):
                    bankbalance = float(bankbalance) - float(calbaldata["curbal"])
                if (calbaldata["baltype"] == 'Dr'):
                    bankbalance = float(bankbalance) + float(calbaldata["curbal"])
            bankbalancedata.append(bankbalance)
            #below code give calculate balance for cash account 
            for bal in accountCodeCash:
                calbaldata = calculateBalance(con,bal["accountcode"],str(financialStart), str(financialStart), str(endMonthDate))
                if (calbaldata["baltype"] == 'Cr'):
                    cashbalance = float(cashbalance) - float(calbaldata["curbal"])
                if (calbaldata["baltype"] == 'Dr'):
                    cashbalance = float(cashbalance) + float(calbaldata["curbal"])
            cashbalancedata.append(cashbalance)

            startMonthDate = date(financialStartresult["financialstart"].year,financialStartresult["financialstart"].month,financialStartresult["financialstart"].day) + monthdelta(monthCounter)
            endMonthDate = date(startMonthDate.year, startMonthDate.month, calendar.monthrange(startMonthDate.year, startMonthDate.month)[1])

            monthCounter  +=1
        balancedata["monthname"] = monthname
        balancedata["bankbalancedata"] = bankbalancedata
        balancedata["cashbalancedata"] = cashbalancedata
        con.close()
        return {"gkstatus":enumdict["Success"],"balancedata":balancedata}           
    except:
        con.close()  
        return{"gkstatus":enumdict["ConnectionFailed"]}
    finally:
        con.close()    

@view_defaults(route_name='dashboard')
class api_dashboard(object):
 
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print "dashboard initialize"

    # This function is use to send user wise data for dashboard divs 
    @view_config(request_method='GET',renderer='json', request_param="type=dashboarddata")
    def dashboarddata(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            #try:
                userinfo = getUserRole(authDetails["userid"])
                userrole= userinfo["gkresult"]["userrole"]
                orgcode =authDetails["orgcode"]
                if userrole == -1 or userrole == 0:
                    amountwiise_purchaseinv=amountwiseinvoice(9,orgcode)
                    datewise_purchaseinv=datewiseinvoice(9,orgcode)
                    amountwiise_saleinv=amountwiseinvoice(15,orgcode)
                    datewise_saleinv=datewiseinvoice(15,orgcode)
                    purchase_inv=getinvoicecountbymonth(9,orgcode)
                    sale_inv=getinvoicecountbymonth(15,orgcode)
                    sup_data=topfivecustsup(9,orgcode)
                    cust_data=topfivecustsup(15,orgcode)
                    mostbought_prodsev=topfiveprodsev(orgcode)
                    stockonhanddata = stockonhanddashboard(orgcode)
                    balancedata=cashbankbalance(orgcode)
                    return{"gkstatus":enumdict["Success"],"userrole":userrole,"gkresult":{"amtwisepurinv":amountwiise_purchaseinv["fiveInvoiceslistdata"],"datewisepurinv":datewise_purchaseinv["fiveInvoiceslistdata"],"amtwisesaleinv":amountwiise_saleinv["fiveInvoiceslistdata"],"datewisesaleinv":datewise_saleinv["fiveInvoiceslistdata"],"puchaseinvcount":purchase_inv["invamount"],"saleinvcount":sale_inv["invamount"],"topfivecustlist":cust_data["topfivecustdetails"],"topfivesuplist":sup_data["topfivecustdetails"],"mostboughtprodsev":mostbought_prodsev["prodinfolist"],"stockonhanddata":stockonhanddata,"balancedata":balancedata["balancedata"]}}
                if userrole == 1:
                    amountwiise_purchaseinv=amountwiseinvoice(9,orgcode)
                    datewise_purchaseinv=datewiseinvoice(9,orgcode)
                    amountwiise_saleinv=amountwiseinvoice(15,orgcode)
                    datewise_saleinv=datewiseinvoice(15,orgcode)
                    purchase_inv=getinvoicecountbymonth(9,orgcode)
                    sale_inv=getinvoicecountbymonth(15,orgcode)
                    delchal_out=delchalcountbymonth(15,orgcode)
                    delchal_in=delchalcountbymonth(9,orgcode)
                    sup_data=topfivecustsup(9,orgcode)
                    cust_data=topfivecustsup(15,orgcode)
                    mostbought_prodsev=topfiveprodsev(orgcode)
                    stockonhanddata = stockonhanddashboard(orgcode)
                    balancedata=cashbankbalance(orgcode)
                    return{"gkstatus":enumdict["Success"],"userrole":userrole,"gkresult":{"amtwisepurinv":amountwiise_purchaseinv["fiveInvoiceslistdata"],"datewisepurinv":datewise_purchaseinv["fiveInvoiceslistdata"],"amtwisesaleinv":amountwiise_saleinv["fiveInvoiceslistdata"],"datewisesaleinv":datewise_saleinv["fiveInvoiceslistdata"],"puchaseinvcount":purchase_inv["invamount"],"saleinvcount":sale_inv["invamount"],"delchalout":delchal_out["totalamount"],"delchalin":delchal_in["totalamount"],"topfivesuplist":sup_data["topfivecustdetails"],"topfivecustlist":cust_data["topfivecustdetails"],"mostboughtprodsev":mostbought_prodsev["prodinfolist"],"stockonhanddata":stockonhanddata,"balancedata":balancedata["balancedata"]}}  
                if userrole == 2:
                    purchase_inv=getinvoicecountbymonth(9,orgcode)
                    sale_inv=getinvoicecountbymonth(15,orgcode)
                    delchal_out=delchalcountbymonth(15,orgcode)
                    delchal_in=delchalcountbymonth(9,orgcode)
                    return{"gkstatus":enumdict["Success"],"userrole":userrole,"gkresult":{"puchaseinvcount":purchase_inv["invamount"],"saleinvcount":sale_inv["invamount"],"delchalout":delchal_out["totalamount"],"delchalin":delchal_in["totalamount"]}}
                if userrole == 3:
                    delchal_out=delchalcountbymonth(15,orgcode)
                    delchal_in=delchalcountbymonth(9,orgcode)
                    return{"gkstatus":enumdict["Success"],"userrole":userrole,"gkresult":{"delchalout":delchal_out["totalamount"],"delchalin":delchal_in["totalamount"]}}
           # except:
           #     return{"gkstatus":enumdict["ConnectionFailed"]}



    #this function use to show transfer note count by month at dashbord in bar chart  
    @view_config(request_method='GET',renderer='json', request_param="type=transfernotecountbymonth")
    def transferNoteCountbyMonth(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                goid = self.request.params["goid"]
                self.con = eng.connect()                
                #this is to fetch startdate and enddate
                startenddate=self.con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == authDetails["orgcode"]))
                startenddateprint=startenddate.fetchone()                
                #this is to fetch in transfer note count month wise
                monthlysortindata=self.con.execute("select extract(month from stockdate) as month, sum(qty) as count from stock where stockdate BETWEEN '%s' AND '%s' and orgcode= %d and goid=%s and dcinvtnflag=20 and inout=9 group by month order by month"%(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),authDetails["orgcode"],goid))
                monthlysortindataset=monthlysortindata.fetchall() 

                #this is to fetch out transfer note count month wise
                monthlysortoutdata=self.con.execute("select extract(month from stockdate) as month, sum(qty) as count from stock where stockdate BETWEEN '%s' AND '%s' and orgcode= %d and goid=%s and dcinvtnflag=20 and inout=15 group by month order by month"%(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),authDetails["orgcode"],goid))
                monthlysortoutdataset=monthlysortoutdata.fetchall()  
                #this is use to send 0 if month have 0 invoice count
                innotecount=[0,0,0,0,0,0,0,0,0,0,0,0]
                outnotecount=[0,0,0,0,0,0,0,0,0,0,0,0]
                for count in monthlysortindataset:
                    innotecount[int(count["month"])-1]= "%.2f"%count["count"]
                for count in monthlysortoutdataset:
                    outnotecount[int(count["month"])-1]="%.2f"%count["count"]
                return{"gkstatus":enumdict["Success"],"innotecount":innotecount,"outnotecount":outnotecount}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()

    # this function use to godwn name assign to godown incharge   
    @view_config(request_method='GET',renderer='json', request_param="type=godowndesc")
    def godowndesc(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                userid=authDetails["userid"]
                orgcode=authDetails["orgcode"]
                self.con = eng.connect()
                godownid=self.con.execute("select goid from usergodown where orgcode=%d and userid=%d"%(authDetails["orgcode"],authDetails["userid"]))
                godownidresult=godownid.fetchall()
                goname=[]
                for goid in godownidresult:
                    godownname=self.con.execute("select goname as goname from godown where goid =%d and orgcode=%d"%(goid["goid"],authDetails["orgcode"]))
                    godownnameresult=godownname.fetchone()
                    goname.append({"goid":goid["goid"],"goname":godownnameresult[0]})
                return{"gkstatus":enumdict["Success"],"goname":goname}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()
    
    # this fuction returns bank and cash sub account balance
    @view_config(request_method='GET',renderer='json', request_param="type=cashbankaccountdata")
    def cashbankaccountdata(self):
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
                #below query is fetch account code and name for bank account 
                accountcodebank=self.con.execute("select accountcode as accountcode, accountname as accountname from accounts where groupcode = (select groupcode from groupsubgroups where groupname = 'Bank' and orgcode=%d) and orgcode =%d"%(orgcode,orgcode))
                accountCodeBank=accountcodebank.fetchall()
                #below query is fetch account code and name for cash account 
                accountcodecash=self.con.execute("select accountcode as accountcode, accountname as accountname from accounts where groupcode = (select groupcode from groupsubgroups where groupname = 'Cash' and orgcode=%d) and orgcode =%d"%(orgcode,orgcode))
                accountCodeCash=accountcodecash.fetchall()

                #below query is fetch finantial yearstart and yearend date
                financialstart=self.con.execute("select yearstart as financialstart, yearend as financialend from organisation where orgcode=%d"% orgcode)
                financialStartresult=financialstart.fetchone()
                financialStart= datetime.strftime(financialStartresult["financialstart"],'%Y-%m-%d')
                financialEnd= datetime.strftime(financialStartresult["financialend"],'%Y-%m-%d')
                bankbalance = 0.00
                cashbalance = 0.00
                bankaccdata=[]
                cashaccdata=[]
                #below code give calculate balance for bank account 
                for bankbal in accountCodeBank:
                    bankbalancedata={}
                    calbaldata = calculateBalance(self.con,bankbal["accountcode"],str(financialStart), str(financialStart), str(financialEnd))
                    bankbalancedata["bankbalance"]=calbaldata["curbal"]
                    bankbalancedata["bankaccname"]=bankbal["accountname"]
                    bankbalancedata["baltype"]=calbaldata["baltype"]
                    bankaccdata.append(bankbalancedata)
                #below code give calculate balance for cash account                 
                for cashbal in accountCodeCash:
                    cashbalancedata={}
                    calbaldata = calculateBalance(self.con,cashbal["accountcode"],str(financialStart), str(financialStart), str(financialEnd))
                    cashbalancedata["cashbalance"]=calbaldata["curbal"]
                    cashbalancedata["cashaccname"]=cashbal["accountname"]
                    cashbalancedata["baltype"]=calbaldata["baltype"]
                    cashaccdata.append(cashbalancedata)
                self.con.close()            
                return{"gkstatus":enumdict["Success"],"bankaccdata":bankaccdata,"cashaccdata":cashaccdata}               
            except:
                self.con.close()
                return{"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
    
