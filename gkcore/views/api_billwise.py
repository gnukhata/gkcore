"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
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
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
Prajkta Patkar" <prajkta.patkar007@gmail.com>
"""

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc,alias, or_, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.sql.expression import null
from gkcore.models.meta import dbconnect
from gkcore.models.gkdb import billwise, invoice, customerandsupplier, vouchers,accounts
from datetime import datetime, date
@view_defaults(route_name='billwise')
class api_billWise(object):
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
        print "billwise initialized"
    @view_config(request_method='POST',renderer='json')
    def adjustBills(self):
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
                dataSet = self.request.json_body
                adjBills = dataSet["adjbills"]
                for bill in adjBills:
                    result = self.con.execute(billwise.insert(),[bill])
                    updres = self.con.execute("update invoice set amountpaid = amountpaid + %f where invid = %d"%(float(bill["adjamount"]),bill["invid"]))
                return{"gkstatus":enumdict["Success"]}
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
    @view_config(request_method='GET',renderer='json')
    def getUnadjustedBills(self):
        """
        Purpose:
        Gets the list of unadjusted receipts and invoices.
        description:
        first we provide it a customerandsupplier code.
        Then get all the receipts vouchers for that customer or supplyer.
        now the receipts are filtered on the basis of 2 conditions.
        firstly the vouchers is unused at all.
        secondly if it is used then it's total should not be equal to the sum of all adjusted amounts of those invoices which have been adjusted using this vouchers.
        For this we loop through the list of vouchers.
        at the beginning of the loop we set a qualification flag to true.
        we will have a nested set of 2 if conditions.
        first we check if the given vouchers is present in the billwise table or not.
        if it is present then the secondly if conditions checks
        if the total amountpaid in the vouchers is equal to the sum of invoices as mentioned above.
        if this condition too is satisfied then the flag is set to false.
        if any of this conditions fail then flag remains true.
        finaly there will be a 3rd if condition which checks this flag.
        if it is true then the vouchers is added to the list to be returned.
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
                csid =int(self.request.params["csid"])
                csFlag =int(self.request.params["csflag"])
                csn = self.con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.custid == csid,customerandsupplier.c.orgcode==authDetails["orgcode"])))
                csName = csn.fetchone()
                accData = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname == csName["custname"],accounts.c.orgcode== authDetails["orgcode"])))
                acccode = accData.fetchone()
                csReceiptData = self.con.execute("select vouchercode, vouchernumber, voucherdate, crs->>'%d' as amt from vouchers where crs ? '%d' and orgcode = %d and vouchertype = 'receipt'"%(acccode["accountcode"],acccode["accountcode"],authDetails["orgcode"]))
                csReceipts = csReceiptData.fetchall()
                unAdjReceipts = []
                unAdjInvoices = []
                for rcpt in csReceipts:
                    invs = self.con.execute(select([func.count(billwise.c.invid).label('invFound'),func.sum(billwise.c.adjamount).label("amtAdjusted")]).where(billwise.c.vouchercode == rcpt["vouchercode"]))
                    invsData = invs.fetchone()
                    amtadj = 0.00
                    if int(invsData["invFound"]) > 0:
                        amtadj = invsData["amtAdjusted"]
                        
                        if float(rcpt["amt"]) == float(invsData["amtAdjusted"]):
                            continue
                    unAdjReceipts.append({"vouchercode":rcpt["vouchercode"],"voucherdate":datetime.strftime(rcpt["voucherdate"],'%d-%m-%Y'),"amtadj":"%.2f"%(float(float(rcpt["amt"]) - float (amtadj)))})
                    
                csInvoices = self.con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.invoicetotal,invoice.c.amountpaid]).where(and_(invoice.c.custid == csid,invoice.c.invoicetotal > invoice.c.amountpaid, invoice.c.orgcode == authDetails["orgcode"])))
                csInvoicesData = csInvoices.fetchall()
                for inv in csInvoicesData:
                    unAdjInvoices.append({"invid":inv["invid"],"invoiceno":inv["invoiceno"],"invoicedate":datetime.strftime(inv["invoicedate"],'%d-%m-%Y'),"invoiceamount":"%.2f"%(float(inv["invoicetotal"])),"balanceamount":"%.2f"%(float(inv["invoicetotal"]-inv["amountpaid"]))})
                return{"gkstatus":enumdict["Success"],"receipts":unAdjReceipts,"invoices":unAdjInvoices}
            except:
                return{"gkstatus":enumdict["ConnectionFailed"]}
                

        
        
