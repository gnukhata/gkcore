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
@view_defaults(route_name='dashboard')
class api_dashboard(object):
    print("inside function")
 
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

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

                types = {1:"Amount Wise", 4:"Due Wise"}
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

                return{"gkstatus":enumdict["Success"],"invoices":fiveInvoiceslistdata, "type":types[typeflag]}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()

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
            # try:
                self.con = eng.connect()
                startenddate=self.con.execute(select([organisation.c.yearstart,organisation.c.yearend]).where(and_(organisation.c.orgcode == authDetails["orgcode"])))
                startenddateprint=startenddate.fetchone()
                startdate = datetime.strftime(startenddateprint["yearstart"])
                print(startdate)
            #     return{"gkstatus":enumdict["Success"],"invoices":fiveInvoiceslistdata, "type":types[typeflag]}
            #     self.con.close()
            # except:
            #     return{"gkstatus":enumdict["ConnectionFailed"]}
            #     self.con.close()
            # finally:
            #     self.con.close()

