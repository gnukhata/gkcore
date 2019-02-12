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
    """
    This class is a resource for billwise accounting.
It will be used for creating entries in the billwise table and updating it as new entries are passed.
    The invoice table will also be updated every time an adjustment is made.
    We will have get and post methods.
    """
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
    @view_config(request_method='GET',renderer='json', request_param="type=dashboard")
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
               
                # Period for which this report is created is determined by startdate and enddate. They are formatted as YYYY-MM-DD.
                startdate =datetime.strptime(str(self.request.params["startdate"]),"%d-%m-%Y").strftime("%Y-%m-%d")
                enddate =datetime.strptime(str(self.request.params["enddate"]),"%d-%m-%Y").strftime("%Y-%m-%d")

                # goid is branchid checking branch related invoice when login as branchvise
                if "goid" in authDetails:
                    # Invoices in ascending order of amount.
                    if typeflag == 1:
                        csInvoices = self.con.execute(select top 5([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.amountpaid, invoice.c.custid]).where(and_(invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.icflag == 9, invoice.c.goid == authDetails["goid"],invoice.c.orgcode == authDetails["orgcode"],invoice.c.invoicedate >= startdate, invoice.c.invoicedate <= enddate, invoice.c.inoutflag == inoutflag)).order_by(desc(invoice.c.invoicetotal - invoice.c.amountpaid)))
                        fiveinvoicelist = fiveInvoices.fetchone()
                    if typeflag == 4:
                return{"gkstatus":enumdict["Success"],"invoices":fiveinvoicelist, "type":types[typeflag]}
                self.con.close()
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                self.con.close()
            finally:
                self.con.close()

        