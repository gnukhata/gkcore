
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
@view_defaults(route_name='dashboard')
class api_dashboard(object):
 
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    #this function is use to show five invoice list at dasboard
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

                fiveInvoiceslistdata=[]
               
                # Invoices in descending order of amount.
                if typeflag == 1:
                    fiveinvoices = self.con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.invoicetotal,invoice.c.amountpaid, invoice.c.custid]).where(and_(invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.icflag == 9,invoice.c.orgcode == authDetails["orgcode"], invoice.c.inoutflag == inoutflag)).order_by(desc(invoice.c.invoicetotal - invoice.c.amountpaid)).limit(5))
                # Invoices in ascending order of date.                
                if typeflag == 4:
                    fiveinvoices = self.con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.invoicetotal,invoice.c.amountpaid, invoice.c.custid]).where(and_(invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.icflag == 9,invoice.c.orgcode == authDetails["orgcode"], invoice.c.inoutflag == inoutflag)).order_by(invoice.c.invoicedate).limit(5))
                fiveInvoiceslist = fiveinvoices.fetchall()

                for inv in fiveInvoiceslist:
                    # for fetch customer or supplier name using cust id in invoice.
                    csd = self.con.execute(select([customerandsupplier.c.custname, customerandsupplier.c.csflag]).where(and_(customerandsupplier.c.custid == inv["custid"],customerandsupplier.c.orgcode==authDetails["orgcode"])))
                    csDetails = csd.fetchone()
                    fiveInvoiceslistdata.append({"invid":inv["invid"],"invoiceno":inv["invoiceno"],"invoicedate":datetime.strftime(inv["invoicedate"],'%d-%m-%Y'),"balanceamount":"%.2f"%(float(inv["invoicetotal"]-inv["amountpaid"])), "custname":csDetails["custname"],"csflag":csDetails["csflag"]})

                return{"gkstatus":enumdict["Success"],"invoices":fiveInvoiceslistdata}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()

    # this function use to show invoice count by month at dasgbord in bar chart  
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
                monthlyrecord=[]
                dict1 ={}

                #this is to fetch startdate and enddate
                startenddate=self.con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == authDetails["orgcode"]))
                startenddateprint=startenddate.fetchone()                
                
                #this is to fetch invoice count month wise
                monthlysortdata=self.con.execute("select extract(month from invoicedate) as month, count(invid) as invoice_count from invoice where invoicedate BETWEEN '%s' AND '%s' and inoutflag= %d and orgcode= %d group by month order by month" %(datetime.strftime(startenddateprint["yearstart"],'%Y-%m-%d'),datetime.strftime(startenddateprint["yearend"],'%Y-%m-%d'),inoutflag,authDetails["orgcode"]))
                monthlysortdataset=monthlysortdata.fetchall()

                month=[]
                invcount=[]
                for count in monthlysortdataset:
                    month.append(calendar.month_name[int(count['month'])])
                    invcount.append(count["invoice_count"])
                return{"gkstatus":enumdict["Success"],"month":month,"invcount":invcount}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()

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
                inoutflag = int(self.request.params["inoutflag"])   
                self.con = eng.connect()
                # this is to fetch top five custid and customer and supplier count.
                topfivecust=self.con.execute("select custid as custid, count(custid) as custcount, sum(invoicetotal) as balance from invoice where inoutflag=%d and orgcode= %d group by custid order by sum(invoicetotal) desc limit(5)"%(inoutflag,authDetails["orgcode"]))
                topfivecustlist=topfivecust.fetchall()

                topfivecustdetails=[]
                for inv in topfivecustlist:
                    # for fetch customer or supplier name using cust id in invoice.
                    csd = self.con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.custid == inv["custid"],customerandsupplier.c.orgcode==authDetails["orgcode"])))
                    csDetails = csd.fetchone()
                    topfivecustdetails.append({"custname":csDetails["custname"],"balance":[float(inv["balance"])]})
                return{"gkstatus":enumdict["Success"],"topfivecustlist":topfivecustdetails}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()
