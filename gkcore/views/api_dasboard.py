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
from operator import itemgetter
from natsort import natsorted
import calendar
import math

def getinvoiceatdashboard(inoutflag,typeflag,orgcode):
    con = eng.connect()
    fiveInvoiceslistdata=[]

    # Invoices in descending order of amount.
    if typeflag == 1:
        fiveinvoices = con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.invoicetotal,invoice.c.amountpaid, invoice.c.custid]).where(and_(invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.icflag == 9,invoice.c.orgcode == orgcode, invoice.c.inoutflag == inoutflag)).order_by(desc(invoice.c.invoicetotal - invoice.c.amountpaid)).limit(5))
    # Invoices in ascending order of date.                
    if typeflag == 4:
        fiveinvoices = con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.invoicetotal,invoice.c.amountpaid, invoice.c.custid]).where(and_(invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.icflag == 9,invoice.c.orgcode == orgcode, invoice.c.inoutflag == inoutflag)).order_by(invoice.c.invoicedate).limit(5))
    fiveInvoiceslist = fiveinvoices.fetchall()

    for inv in fiveInvoiceslist:
        # for fetch customer or supplier name using cust id in invoice.
        csd = con.execute(select([customerandsupplier.c.custname, customerandsupplier.c.csflag]).where(and_(customerandsupplier.c.custid == inv["custid"],customerandsupplier.c.orgcode==orgcode)))
        csDetails = csd.fetchone()
        fiveInvoiceslistdata.append({"invid":inv["invid"],"invoiceno":inv["invoiceno"],"invoicedate":datetime.strftime(inv["invoicedate"],'%d-%m-%Y'),"balanceamount":"%.2f"%(float(inv["invoicetotal"]-inv["amountpaid"])), "custname":csDetails["custname"],"csflag":csDetails["csflag"]})
    return fiveInvoiceslistdata 

def getinvoicecountbymonth(inoutflag,orgcode):
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
    return invamount
                
def topfivecustsup(inoutflag,orgcode):
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
    return topfivecustdetails

def topfiveprodsev(orgcode):
    con = eng.connect()
    # this is to fetch top five product/service  which is sort by  invoice count. 
    topfiveprod= con.execute("select ky as productcode, count(*) as numkeys from invoice cross join lateral jsonb_object_keys(contents) as t(ky) where orgcode=%d and invoice.inoutflag=9 group by ky order by count(*) desc limit(5)"%(orgcode))
    topfiveprodlist=topfiveprod.fetchall()
                
    prodinfolist=[]
    for prodinfo in topfiveprodlist:
        proddesc=  con.execute("select productdesc as proddesc from product where productcode=%d and orgcode=%d"%(int(prodinfo["productcode"]),orgcode))
        proddesclist=proddesc.fetchone()
        prodinfolist.append({"prodcode":prodinfo["productcode"],"count":prodinfo["numkeys"],"proddesc":proddesclist["proddesc"]})
    return prodinfolist       
    
def  delchalcountbymonth(inoutflag,orgcode):
    con = eng.connect()
    #this is to fetch startdate and enddate
    startenddate=con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == orgcode))
    startenddateprint=startenddate.fetchone()                

    #this is to fetch delchal count month wise
    monthlysortdata=con.execute("select extract(month from stockdate) as month, sum(qty) as total_qty from stock where stockdate BETWEEN '%s' AND '%s' and inout=%d and orgcode= %d and dcinvtnflag=9 group by month order by month" %(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),inoutflag,orgcode))
    monthlysortdataset=monthlysortdata.fetchall()
                
    #this is use to send 0 if month have 0 delchal count
    totalamount=[0,0,0,0,0,0,0,0,0,0,0,0]
    for count in monthlysortdataset:
        totalamount[int(count["month"])-1]=float(count["total_qty"])
    return totalamount    

def transfernote(goid,orgcode):
    con = eng.connect()
    #this is to fetch startdate and enddate
    startenddate= con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == orgcode))
    startenddateprint=startenddate.fetchone()                
    #this is to fetch in transfer note count month wise
    monthlysortindata= con.execute("select extract(month from stockdate) as month, count(qty) as count from stock where stockdate BETWEEN '%s' AND '%s' and orgcode= %d and goid=%s and inout=15 group by month order by month"%(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),orgcode,goid))
    monthlysortindataset=monthlysortindata.fetchall() 

    #this is to fetch out transfer note count month wise
    monthlysortoutdata= con.execute("select extract(month from stockdate) as month, count(qty) as count from stock where stockdate BETWEEN '%s' AND '%s' and orgcode= %d and goid=%s and inout=9 group by month order by month"%(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),orgcode,goid))
    monthlysortoutdataset=monthlysortoutdata.fetchall()  
    #this is use to send 0 if month have 0 invoice count
    innotecount=[0,0,0,0,0,0,0,0,0,0,0,0]
    outnotecount=[0,0,0,0,0,0,0,0,0,0,0,0]
    for count in monthlysortindataset:
        innotecount[int(count["month"])-1]=count["count"]
    for count in monthlysortoutdataset:
        outnotecount[int(count["month"])-1]=count["count"]
    return innotecount, outnotecount     

@view_defaults(route_name='dashboard')
class api_dashboard(object):
 
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print "dashboard initialize"
    #this function is use to show top five unpaid invoice list at dashboard
    @view_config(request_method='GET',renderer='json', request_param="type=fiveinvoicelist")
    def getinvoiceatdashboard(self):
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
                inoutflag = int(self.request.params["inoutflag"])              
                typeflag = int(self.request.params["typeflag"])
                orgcode = authDetails["orgcode"]

                fiveInvoiceslistdata=getinvoiceatdashboard(inoutflag,typeflag,orgcode)
                # fiveInvoiceslistdata=[]

                # # Invoices in descending order of amount.
                # if typeflag == 1:
                #     fiveinvoices = self.con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.invoicetotal,invoice.c.amountpaid, invoice.c.custid]).where(and_(invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.icflag == 9,invoice.c.orgcode == authDetails["orgcode"], invoice.c.inoutflag == inoutflag)).order_by(desc(invoice.c.invoicetotal - invoice.c.amountpaid)).limit(5))
                # # Invoices in ascending order of date.                
                # if typeflag == 4:
                #     fiveinvoices = self.con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.invoicetotal,invoice.c.amountpaid, invoice.c.custid]).where(and_(invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.icflag == 9,invoice.c.orgcode == authDetails["orgcode"], invoice.c.inoutflag == inoutflag)).order_by(invoice.c.invoicedate).limit(5))
                # fiveInvoiceslist = fiveinvoices.fetchall()

                # for inv in fiveInvoiceslist:
                #     # for fetch customer or supplier name using cust id in invoice.
                #     csd = self.con.execute(select([customerandsupplier.c.custname, customerandsupplier.c.csflag]).where(and_(customerandsupplier.c.custid == inv["custid"],customerandsupplier.c.orgcode==authDetails["orgcode"])))
                #     csDetails = csd.fetchone()
                #     fiveInvoiceslistdata.append({"invid":inv["invid"],"invoiceno":inv["invoiceno"],"invoicedate":datetime.strftime(inv["invoicedate"],'%d-%m-%Y'),"balanceamount":"%.2f"%(float(inv["invoicetotal"]-inv["amountpaid"])), "custname":csDetails["custname"],"csflag":csDetails["csflag"]})

                return{"gkstatus":enumdict["Success"],"invoices":fiveInvoiceslistdata}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()

    # this function use to show invoice count by month at dashbord in bar chart  
    @view_config(request_method='GET',renderer='json', request_param="type=invoicecountbymonth")
    def getinvoicecountbymonth(self):
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
                inoutflag = int(self.request.params["inoutflag"])   
                orgcode = authDetails["orgcode"]
                invamount = getinvoicecountbymonth(inoutflag,orgcode)

                # #this is to fetch startdate and enddate
                # startenddate=self.con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == authDetails["orgcode"]))
                # startenddateprint=startenddate.fetchone()                
                
                # #this is to fetch invoice totalamount month wise
                # monthlysortdata=self.con.execute("select extract(month from invoicedate) as month, sum(invoicetotal) as totalamount from invoice where invoicedate BETWEEN '%s' AND '%s' and inoutflag= %d and icflag=9 and  orgcode= %d group by month order by month" %(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),inoutflag,authDetails["orgcode"]))
                # # monthlysortdata=self.con.execute("select extract(month from invoicedate) as month, count(invid) as inv_count from invoice where invoicedate BETWEEN '%s' AND '%s' and inoutflag= %d and orgcode= %d group by month order by month" %(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),inoutflag,authDetails["orgcode"]))
                # monthlysortdataset=monthlysortdata.fetchall()  
                # #this is use to send 0 if month have 0 invoice count
                # invamount=[0,0,0,0,0,0,0,0,0,0,0,0]
                # for count in monthlysortdataset:
                #     invamount[int(count["month"])-1]=float(count["totalamount"])
               
                return{"gkstatus":enumdict["Success"],"invcount":invamount}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()

    # this function use to show top five customer/supplier at dashbord in most valued costomer and supplier div 
    @view_config(request_method='GET',renderer='json', request_param="type=topfivecustsup")
    def topfivecustsup(self):
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
                inoutflag = int(self.request.params["inoutflag"])  
                orgcode = authDetails["orgcode"] 
                topfivecustdetails=topfivecustsup(inoutflag,orgcode)

                # # this is to fetch top five customer which is sort by total amount.
                # if inoutflag == 15:
                #     topfivecust=self.con.execute("select custid as custid, sum(invoicetotal) as data from invoice where inoutflag=15 and orgcode= %d and icflag=9 group by custid order by data desc limit(5)"%(authDetails["orgcode"]))
                #     topfivecustlist=topfivecust.fetchall()
                #     # this is to fetch top five suppplier which is sort by total invoice.
                # else:
                #     topfivecust=self.con.execute("select custid as custid, count(custid) as data from invoice where inoutflag=9 and orgcode=%d and icflag=9  group by custid order by data desc limit(5)"%(authDetails["orgcode"]))
                #     topfivecustlist=topfivecust.fetchall()

                # topfivecustdetails=[]
                # for inv in topfivecustlist:
                #     # for fetch customer or supplier name using cust id in invoice.
                #     csd = self.con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.custid == inv["custid"],customerandsupplier.c.orgcode==authDetails["orgcode"])))
                #     csDetails = csd.fetchone()
                #     topfivecustdetails.append({"custname":csDetails["custname"],"data":float(inv["data"])})
                
                return{"gkstatus":enumdict["Success"],"topfivecustlist":topfivecustdetails}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()
   
    # this function use to show top five most bought product and service at dashbord in most bought  product/service div  
    @view_config(request_method='GET',renderer='json', request_param="type=topfiveproduct")
    def topfiveprod(self):
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
                prodinfolist=topfiveprodsev(orgcode)

                # # this is to fetch top five product/service  which is sort by  invoice count. 
                # topfiveprod=self.con.execute("select ky as productcode, count(*) as numkeys from invoice cross join lateral jsonb_object_keys(contents) as t(ky) where orgcode=%d and invoice.inoutflag=9 group by ky order by count(*) desc limit(5)"%(authDetails["orgcode"]))
                # topfiveprodlist=topfiveprod.fetchall()
                
                # prodinfolist=[]
                # for prodinfo in topfiveprodlist:
                #     proddesc=self.con.execute("select productdesc as proddesc from product where productcode=%d"%(int(prodinfo["productcode"])))
                #     proddesclist=proddesc.fetchone()
                #     prodinfolist.append({"prodcode":prodinfo["productcode"],"count":prodinfo["numkeys"],"proddesc":proddesclist["proddesc"]})
                return{"gkstatus":enumdict["Success"],"topfiveprod":prodinfolist}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()

    # this function use to show delchal count by month at dashbord in bar chart      
    @view_config(request_method='GET',renderer='json', request_param="type=delchalcountbymonth")
    def delchalcountbymonth(self):
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
                inoutflag = int(self.request.params["inoutflag"])   
                orgcode = authDetails["orgcode"]

                totalamount=delchalcountbymonth(inoutflag,orgcode)

                # #this is to fetch startdate and enddate
                # startenddate=self.con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == authDetails["orgcode"]))
                # startenddateprint=startenddate.fetchone()                

                # #this is to fetch delchal count month wise
                # monthlysortdata=self.con.execute("select extract(month from stockdate) as month, sum(qty) as total_qty from stock where stockdate BETWEEN '%s' AND '%s' and inout=%d and orgcode= %d and dcinvtnflag=9 group by month order by month" %(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),inoutflag,authDetails["orgcode"]))
                # monthlysortdataset=monthlysortdata.fetchall()
                
                # #this is use to send 0 if month have 0 delchal count
                # totalamount=[0,0,0,0,0,0,0,0,0,0,0,0]
                # for count in monthlysortdataset:
                #     totalamount[int(count["month"])-1]=float(count["total_qty"])
                return{"gkstatus":enumdict["Success"],"delchalcount":totalamount}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()


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
                self.con = eng.connect()
                goid = self.request.params["goid"]
                orgcode = authDetails["orgcode"]

                #this is to fetch startdate and enddate
                startenddate=self.con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == authDetails["orgcode"]))
                startenddateprint=startenddate.fetchone()                
                #this is to fetch in transfer note count month wise
                monthlysortindata=self.con.execute("select extract(month from stockdate) as month, count(qty) as count from stock where stockdate BETWEEN '%s' AND '%s' and orgcode= %d and goid=%s and inout=15 group by month order by month"%(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),authDetails["orgcode"],goid))
                monthlysortindataset=monthlysortindata.fetchall() 

                #this is to fetch out transfer note count month wise
                monthlysortoutdata=self.con.execute("select extract(month from stockdate) as month, count(qty) as count from stock where stockdate BETWEEN '%s' AND '%s' and orgcode= %d and goid=%s and inout=9 group by month order by month"%(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),authDetails["orgcode"],goid))
                monthlysortoutdataset=monthlysortoutdata.fetchall()  
                #this is use to send 0 if month have 0 invoice count
                innotecount=[0,0,0,0,0,0,0,0,0,0,0,0]
                outnotecount=[0,0,0,0,0,0,0,0,0,0,0,0]
                for count in monthlysortindataset:
                    innotecount[int(count["month"])-1]=count["count"]
                for count in monthlysortoutdataset:
                    outnotecount[int(count["month"])-1]=count["count"]
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