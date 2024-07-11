"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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
"Vanita Rajpurohit" <vanita.rajpurohit9819@gmail.com>
"Prajkta Patkar" <prajkta@riseup.com>
"Bhavesh Bawadhane" <bbhavesh07@gmail.com>
"Parabjyot Singh" <parabjyot1996@gmail.com>
"Rahul Chaurasiya" <crahul4133@gmail.com>
"Vasudha Kadge" <kadge.vasudha@gmail.com>
"""


import logging
from gkcore import eng, enumdict
from gkcore.models import gkdb
from gkcore.utils import authCheck
from gkcore.views.api_invoice import getStateCode
from gkcore.models.gkdb import (
    accounts,
    vouchers,
    groupsubgroups,
    projects,
    organisation,
    users,
    voucherbin,
    delchal,
    invoice,
    customerandsupplier,
    stock,
    product,
    transfernote,
    goprod,
    dcinv,
    log,
    godown,
    categorysubcategories,
    rejectionnote,
    state,
    drcr,
)
from sqlalchemy.sql import select, not_
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, alias, or_, exc, distinct, desc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from gkcore.views.api_gkuser import getUserRole
from datetime import datetime, date
import calendar
from monthdelta import monthdelta
from gkcore.models.meta import dbconnect
from sqlalchemy.sql.functions import func
from time import strftime, strptime
from natsort import natsorted
from sqlalchemy.sql.expression import null
import traceback  # for printing detailed exception logs
from gkcore.views.reports.helpers.voucher import billwiseEntryLedger
from gkcore.views.reports.helpers.stock import (
    stockonhandfun,
    calculateStockValue,
    godownwisestockonhandfun,
    calculateOpeningStockValue,
    calculateClosingStockValue,
)
from gkcore.views.reports.helpers.balance import calculateBalance, getBalanceSheet
from gkcore.views.reports.helpers.profit_loss import calculateProfitLossValue

"""
purpose:
This class is the resource to generate reports,
Such as Trial Balance, Ledger, Cash flowe, Balance sheet etc.

connection rules:
con is used for executing sql expression language based queries,
while eng is used for raw sql execution.
routing mechanism:
@view_defaults is used for setting the default route for crud on the given resource class.
if specific route is to be attached to a certain method, or for giving get, post, put, delete methods to default route, the view_config decorator is used.
For other predicates view_config is generally used.
This class has single route with only get as method.
Depending on the request_param, different methods will be called on the route given in view_default.

"""


@view_defaults(route_name="report", request_method="GET")
class api_reports(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    @view_config(request_param="type=stockreport", renderer="json")
    def stockReport(self):
        """
        Purpose:
        Return the structured data grid of stock report for given product.
        Input will be productcode,startdate,enddate.
        orgcode will be taken from header and startdate and enddate of fianancial year taken from organisation table .
        returns a list of dictionaries where every dictionary will be one row.
        description:
        This function returns the complete stock report,
        including opening stock every inward and outward quantity and running balance for every transaction along with transaction type.
        at the end we get total inward and outward quantity.
        This report will be on the basis of productcode, startdate and enddate given from the client.
        The orgcode is taken from the header.
        The report will query database to get all in and out records for the given product where the dcinvtn flag is not 20.
        For every iteration of this list with a for loop we will find out the date of transaction from the delchal or invoice table depending on the flag being 4 or 9.
        Cash memo is in the invoice table so even 3 will qualify.
        Then we wil find the customer or supplyer name on the basis of given data.
        Note that if the startdate is same as the yearstart of the organisation then opening stock can be directly taken from the product table.
        if it is later than the startyear then we will have to come to the closing balance of the day before startdate given by client and use it as the opening balance.
        The row will be represented in this grid with every key denoting a column.
        The columns (keys) will be,
        date,particulars,invoice/dcno, transaction type (invoice /delchal),inward quantity,outward quantity ,total inward quantity , total outwrd quanity and balance.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                orgcode = authDetails["orgcode"]
                productCode = self.request.params["productcode"]
                startDate = datetime.strptime(
                    str(self.request.params["startdate"]), "%Y-%m-%d"
                )
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stockReport = []
                totalinward = 0.00
                totaloutward = 0.00
                openingStockResult = self.con.execute(
                    select([product.c.openingstock]).where(
                        and_(
                            product.c.productcode == productCode,
                            product.c.orgcode == orgcode,
                        )
                    )
                )
                osRow = openingStockResult.fetchone()
                openingStock = osRow["openingstock"]
                stockRecords = self.con.execute(
                    select([stock])
                    .where(
                        and_(
                            stock.c.productcode == productCode,
                            stock.c.orgcode == orgcode,
                            or_(
                                stock.c.dcinvtnflag != 20,
                                stock.c.dcinvtnflag != 40,
                                stock.c.dcinvtnflag != 30,
                                stock.c.dcinvtnflag != 90,
                            ),
                        )
                    )
                    .order_by(stock.c.stockdate)
                )
                stockData = stockRecords.fetchall()
                ysData = self.con.execute(
                    select([organisation.c.yearstart]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                ysRow = ysData.fetchone()
                yearStart = datetime.strptime(str(ysRow["yearstart"]), "%Y-%m-%d")
                enData = self.con.execute(
                    select([organisation.c.yearend]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                enRow = enData.fetchone()
                yearend = datetime.strptime(str(enRow["yearend"]), "%Y-%m-%d")
                if startDate > yearStart:
                    for stockRow in stockData:
                        if stockRow["dcinvtnflag"] == 3 or stockRow["dcinvtnflag"] == 9:
                            countresult = self.con.execute(
                                select(
                                    [func.count(invoice.c.invid).label("inv")]
                                ).where(
                                    and_(
                                        invoice.c.invoicedate >= yearStart,
                                        invoice.c.invoicedate < startDate,
                                        invoice.c.invid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["inv"] == 1:
                                if stockRow["inout"] == 9:
                                    openingStock = float(openingStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    openingStock = float(openingStock) - float(
                                        stockRow["qty"]
                                    )
                        if stockRow["dcinvtnflag"] == 4:
                            countresult = self.con.execute(
                                select([func.count(delchal.c.dcid).label("dc")]).where(
                                    and_(
                                        delchal.c.dcdate >= yearStart,
                                        delchal.c.dcdate < startDate,
                                        delchal.c.dcid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["dc"] == 1:
                                if stockRow["inout"] == 9:
                                    openingStock = float(openingStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    openingStock = float(openingStock) - float(
                                        stockRow["qty"]
                                    )
                        if stockRow["dcinvtnflag"] == 18:
                            if stockRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    stockRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    stockRow["qty"]
                                )
                            if stockRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    stockRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    stockRow["qty"]
                                )
                        if stockRow["dcinvtnflag"] == 7:
                            countresult = self.con.execute(
                                select([func.count(drcr.c.drcrid).label("dc")]).where(
                                    and_(
                                        drcr.c.drcrdate >= yearStart,
                                        drcr.c.drcrdate < startDate,
                                        drcr.c.drcrid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["dc"] == 1:
                                if stockRow["inout"] == 9:
                                    openingStock = float(openingStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    openingStock = float(openingStock) - float(
                                        stockRow["qty"]
                                    )
                stockReport.append(
                    {
                        "date": "",
                        "particulars": "opening stock",
                        "trntype": "",
                        "dcid": "",
                        "dcno": "",
                        "drcrno": "",
                        "drcrid": "",
                        "invid": "",
                        "invno": "",
                        "rnid": "",
                        "rnno": "",
                        "inward": "%.2f" % float(openingStock),
                    }
                )
                totalinward = totalinward + float(openingStock)
                for finalRow in stockData:
                    if finalRow["dcinvtnflag"] == 3 or finalRow["dcinvtnflag"] == 9:
                        countresult = self.con.execute(
                            select(
                                [
                                    invoice.c.invoicedate,
                                    invoice.c.invoiceno,
                                    invoice.c.custid,
                                ]
                            ).where(
                                and_(
                                    invoice.c.invoicedate >= startDate,
                                    invoice.c.invoicedate <= endDate,
                                    invoice.c.invid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()

                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == countrow["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            if custrow != None:
                                custnamedata = custrow["custname"]
                            else:
                                custnamedata = "Cash Memo"
                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["invoicedate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custnamedata,
                                        "trntype": "invoice",
                                        "dcid": "",
                                        "dcno": "",
                                        "drcrno": "",
                                        "drcrid": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": finalRow["dcinvtnid"],
                                        "invno": countrow["invoiceno"],
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["invoicedate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custnamedata,
                                        "trntype": "invoice",
                                        "dcid": "",
                                        "dcno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": finalRow["dcinvtnid"],
                                        "invno": countrow["invoiceno"],
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )

                    if finalRow["dcinvtnflag"] == 4:
                        countresult = self.con.execute(
                            select(
                                [delchal.c.dcdate, delchal.c.dcno, delchal.c.custid]
                            ).where(
                                and_(
                                    delchal.c.dcdate >= startDate,
                                    delchal.c.dcdate <= endDate,
                                    delchal.c.dcid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()

                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == countrow["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            dcinvresult = self.con.execute(
                                select([dcinv.c.invid]).where(
                                    dcinv.c.dcid == finalRow["dcinvtnid"]
                                )
                            )
                            if dcinvresult.rowcount == 1:
                                dcinvrow = dcinvresult.fetchone()
                                invresult = self.con.execute(
                                    select(
                                        [invoice.c.invoiceno, invoice.c.icflag]
                                    ).where(invoice.c.invid == dcinvrow["invid"])
                                )
                                """ No need to check if invresult has rowcount 1 since it must be 1 """
                                invrow = invresult.fetchone()
                                trntype = "delchal&invoice"
                            else:
                                dcinvrow = {"invid": ""}
                                invrow = {"invoiceno": "", "icflag": ""}
                                trntype = "delchal"

                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["dcdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "dcid": finalRow["dcinvtnid"],
                                        "dcno": countrow["dcno"],
                                        "drcrno": "",
                                        "drcrid": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": dcinvrow["invid"],
                                        "invno": invrow["invoiceno"],
                                        "icflag": invrow["icflag"],
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["dcdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "dcid": finalRow["dcinvtnid"],
                                        "dcno": countrow["dcno"],
                                        "drcrno": "",
                                        "drcrid": "",
                                        "invid": dcinvrow["invid"],
                                        "invno": invrow["invoiceno"],
                                        "icflag": invrow["icflag"],
                                        "rnid": "",
                                        "rnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )

                    if finalRow["dcinvtnflag"] == 18:
                        countresult = self.con.execute(
                            select(
                                [
                                    rejectionnote.c.rndate,
                                    rejectionnote.c.rnno,
                                    rejectionnote.c.dcid,
                                    rejectionnote.c.invid,
                                ]
                            ).where(
                                and_(
                                    rejectionnote.c.rndate >= startDate,
                                    rejectionnote.c.rndate <= endDate,
                                    rejectionnote.c.rnid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            if countrow["dcid"] != None:
                                custdata = self.con.execute(
                                    select([customerandsupplier.c.custname]).where(
                                        customerandsupplier.c.custid
                                        == (
                                            select([delchal.c.custid]).where(
                                                delchal.c.dcid == countrow["dcid"]
                                            )
                                        )
                                    )
                                )
                            elif countrow["invid"] != None:
                                custdata = self.con.execute(
                                    select([customerandsupplier.c.custname]).where(
                                        customerandsupplier.c.custid
                                        == (
                                            select([invoice.c.custid]).where(
                                                invoice.c.invid == countrow["invid"]
                                            )
                                        )
                                    )
                                )
                            custrow = custdata.fetchone()
                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["rndate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": "Rejection Note",
                                        "rnid": finalRow["dcinvtnid"],
                                        "rnno": countrow["rnno"],
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["rndate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": "Rejection Note",
                                        "rnid": finalRow["dcinvtnid"],
                                        "rnno": countrow["rnno"],
                                        "dcno": "",
                                        "drcrno": "",
                                        "drcrid": "",
                                        "invid": "",
                                        "invno": "",
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                    if finalRow["dcinvtnflag"] == 7:
                        countresult = self.con.execute(
                            select(
                                [
                                    drcr.c.drcrdate,
                                    drcr.c.drcrno,
                                    drcr.c.invid,
                                    drcr.c.dctypeflag,
                                ]
                            ).where(
                                and_(
                                    drcr.c.drcrdate >= startDate,
                                    drcr.c.drcrdate <= endDate,
                                    drcr.c.drcrid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            drcrinvdata = self.con.execute(
                                select([invoice.c.custid]).where(
                                    invoice.c.invid == countrow["invid"]
                                )
                            )
                            drcrinv = drcrinvdata.fetchone()
                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == drcrinv["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            if int(countrow["dctypeflag"] == 3):
                                trntype = "Credit Note"
                            else:
                                trntype = "Debit Note"
                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["drcrdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "drcrid": finalRow["dcinvtnid"],
                                        "drcrno": countrow["drcrno"],
                                        "dcno": "",
                                        "dcid": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": "",
                                        "invno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["drcrdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "drcrid": finalRow["dcinvtnid"],
                                        "drcrno": countrow["drcrno"],
                                        "dcid": "",
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )

                stockReport.append(
                    {
                        "date": "",
                        "particulars": "Total",
                        "dcid": "",
                        "dcno": "",
                        "invid": "",
                        "invno": "",
                        "rnid": "",
                        "rnno": "",
                        "drcrno": "",
                        "drcrid": "",
                        "trntype": "",
                        "totalinwardqty": "%.2f" % float(totalinward),
                        "totaloutwardqty": "%.2f" % float(totaloutward),
                    }
                )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": stockReport}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="product-register", renderer="json")
    def godownStockReport(self):
        """
        Purpose:
        Return the structured data grid of stock report for given product.
        Input will be productcode,startdate,enddate and goid.
        orgcode will be taken from header and startdate and enddate of fianancial year taken from organisation table .
        returns a list of dictionaries where every dictionary will be one row.
        description:
        This function returns the complete stock report,
        including opening stock every inward and outward quantity and running balance for every transaction along with transaction type for a selected product and godown.
        at the end we get total inward and outward quantity.
        This report will be on the basis of productcode, startdate and enddate given from the client.
        The orgcode is taken from the header.
        The report will query database to get all in and out records for the given product where the dcinvtn flag is not 20.
        For every iteration of this list with a for loop we will find out the date of transaction from the delchal or invoice table depending on the flag being 4 or 9.
        Cash memo is in the invoice table so even 3 will qualify.
        Then we wil find the customer or supplyer name on the basis of given data.
        Note that if the startdate is same as the yearstart of the organisation then opening stock can be directly taken from the product table.
        if it is later than the startyear then we will have to come to the closing balance of the day before startdate given by client and use it as the opening balance.
        The row will be represented in this grid with every key denoting a column.
        The columns (keys) will be,
        date,particulars,invoice/dcno, transaction type (invoice /delchal),inward quantity,outward quantity ,total inward quantity , total outwrd quanity and balance.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                orgcode = authDetails["orgcode"]
                productCode = self.request.params["productcode"]
                godownCode = self.request.params["goid"]
                startDate = datetime.strptime(
                    str(self.request.params["startdate"]), "%Y-%m-%d"
                )
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stockReport = []
                totalinward = 0.00
                totaloutward = 0.00
                openingStock = 0.00
                goopeningStockResult = self.con.execute(
                    select([goprod.c.goopeningstock]).where(
                        and_(
                            goprod.c.productcode == productCode,
                            goprod.c.goid == godownCode,
                            goprod.c.orgcode == orgcode,
                        )
                    )
                )
                gosRow = goopeningStockResult.fetchone()
                if gosRow != None:
                    gopeningStock = gosRow["goopeningstock"]
                else:
                    gopeningStock = 0.00
                stockRecords = self.con.execute(
                    select([stock])
                    .where(
                        and_(
                            stock.c.productcode == productCode,
                            stock.c.goid == godownCode,
                            stock.c.orgcode == orgcode,
                            or_(
                                stock.c.dcinvtnflag != 40,
                                stock.c.dcinvtnflag != 30,
                                stock.c.dcinvtnflag != 90,
                            ),
                        )
                    )
                    .order_by(stock.c.stockdate)
                )
                stockData = stockRecords.fetchall()
                ysData = self.con.execute(
                    select([organisation.c.yearstart]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                ysRow = ysData.fetchone()
                yearStart = datetime.strptime(str(ysRow["yearstart"]), "%Y-%m-%d")
                enData = self.con.execute(
                    select([organisation.c.yearend]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                enRow = enData.fetchone()
                yearend = datetime.strptime(str(enRow["yearend"]), "%Y-%m-%d")
                if startDate > yearStart:
                    for stockRow in stockData:
                        if stockRow["dcinvtnflag"] == 4:
                            # delivery note
                            countresult = self.con.execute(
                                select([func.count(delchal.c.dcid).label("dc")]).where(
                                    and_(
                                        delchal.c.dcdate >= yearStart,
                                        delchal.c.dcdate < startDate,
                                        delchal.c.dcid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["dc"] == 1:
                                if stockRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        stockRow["qty"]
                                    )
                        if stockRow["dcinvtnflag"] == 20:
                            # transfer note
                            countresult = self.con.execute(
                                select(
                                    [
                                        func.count(transfernote.c.transfernoteid).label(
                                            "tn"
                                        )
                                    ]
                                ).where(
                                    and_(
                                        transfernote.c.transfernotedate >= yearStart,
                                        transfernote.c.transfernotedate < startDate,
                                        transfernote.c.transfernoteid
                                        == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["tn"] == 1:
                                if stockRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        stockRow["qty"]
                                    )
                        if stockRow["dcinvtnflag"] == 18:
                            # Rejection Note
                            if stockRow["inout"] == 9:
                                gopeningstock = float(gopeningstock) + float(
                                    stockRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    stockRow["qty"]
                                )
                            if stockRow["inout"] == 15:
                                gopeningstock = float(gopeningstock) - float(
                                    stockRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    stockRow["qty"]
                                )
                        if stockRow["dcinvtnflag"] == 7:
                            # Debit Credit Note
                            countresult = self.con.execute(
                                select([func.count(drcr.c.drcrid).label("dc")]).where(
                                    and_(
                                        drcr.c.drcrdate >= yearStart,
                                        drcr.c.drcrdate < startDate,
                                        drcr.c.drcrid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["dc"] == 1:
                                if stockRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        stockRow["qty"]
                                    )
                stockReport.append(
                    {
                        "date": "",
                        "particulars": "opening stock",
                        "trntype": "",
                        "dcid": "",
                        "dcno": "",
                        "invid": "",
                        "invno": "",
                        "tnid": "",
                        "tnno": "",
                        "rnid": "",
                        "rnno": "",
                        "inward": "%.2f" % float(gopeningStock),
                    }
                )
                totalinward = totalinward + float(gopeningStock)

                for finalRow in stockData:
                    if finalRow["dcinvtnflag"] == 4:
                        countresult = self.con.execute(
                            select(
                                [delchal.c.dcdate, delchal.c.dcno, delchal.c.custid]
                            ).where(
                                and_(
                                    delchal.c.dcdate >= startDate,
                                    delchal.c.dcdate <= endDate,
                                    delchal.c.dcid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == countrow["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            dcinvresult = self.con.execute(
                                select([dcinv.c.invid]).where(
                                    dcinv.c.dcid == finalRow["dcinvtnid"]
                                )
                            )
                            if dcinvresult.rowcount == 1:
                                dcinvrow = dcinvresult.fetchone()
                                invresult = self.con.execute(
                                    select(
                                        [invoice.c.invoiceno, invoice.c.icflag]
                                    ).where(invoice.c.invid == dcinvrow["invid"])
                                )
                                """ No need to check if invresult has rowcount 1 since it must be 1 """
                                invrow = invresult.fetchone()
                                trntype = "delchal&invoice"
                            else:
                                dcinvrow = {"invid": ""}
                                invrow = {"invoiceno": "", "icflag": ""}
                                trntype = "delchal"

                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["dcdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "dcid": finalRow["dcinvtnid"],
                                        "dcno": countrow["dcno"],
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": dcinvrow["invid"],
                                        "invno": invrow["invoiceno"],
                                        "icflag": invrow["icflag"],
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["dcdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "dcid": finalRow["dcinvtnid"],
                                        "dcno": countrow["dcno"],
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": dcinvrow["invid"],
                                        "invno": invrow["invoiceno"],
                                        "icflag": invrow["icflag"],
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                    if finalRow["dcinvtnflag"] == 20:
                        countresult = self.con.execute(
                            select(
                                [
                                    transfernote.c.transfernotedate,
                                    transfernote.c.transfernoteno,
                                ]
                            ).where(
                                and_(
                                    transfernote.c.transfernotedate >= startDate,
                                    transfernote.c.transfernotedate <= endDate,
                                    transfernote.c.transfernoteid
                                    == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(
                                                    countrow["transfernotedate"].date()
                                                ),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": "",
                                        "trntype": "transfer note",
                                        "dcid": "",
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "tnid": finalRow["dcinvtnid"],
                                        "tnno": countrow["transfernoteno"],
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(
                                                    countrow["transfernotedate"].date()
                                                ),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": "",
                                        "trntype": "transfer note",
                                        "dcid": "",
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "tnid": finalRow["dcinvtnid"],
                                        "tnno": countrow["transfernoteno"],
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )

                    if finalRow["dcinvtnflag"] == 18:
                        countresult = self.con.execute(
                            select(
                                [
                                    rejectionnote.c.rndate,
                                    rejectionnote.c.rnno,
                                    rejectionnote.c.dcid,
                                    rejectionnote.c.invid,
                                ]
                            ).where(
                                and_(
                                    rejectionnote.c.rndate >= startDate,
                                    rejectionnote.c.rndate <= endDate,
                                    rejectionnote.c.rnid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            if countrow["dcid"] != None:
                                custdata = self.con.execute(
                                    select([customerandsupplier.c.custname]).where(
                                        customerandsupplier.c.custid
                                        == (
                                            select([delchal.c.custid]).where(
                                                delchal.c.dcid == countrow["dcid"]
                                            )
                                        )
                                    )
                                )
                            elif countrow["invid"] != None:
                                custdata = self.con.execute(
                                    select([customerandsupplier.c.custname]).where(
                                        customerandsupplier.c.custid
                                        == (
                                            select([invoice.c.custid]).where(
                                                invoice.c.invid == countrow["invid"]
                                            )
                                        )
                                    )
                                )
                            custrow = custdata.fetchone()
                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["rndate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": "Rejection Note",
                                        "rnid": finalRow["dcinvtnid"],
                                        "rnno": countrow["rnno"],
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["rndate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": "Rejection Note",
                                        "rnid": finalRow["dcinvtnid"],
                                        "rnno": countrow["rnno"],
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                    if finalRow["dcinvtnflag"] == 7:
                        countresult = self.con.execute(
                            select(
                                [
                                    drcr.c.drcrdate,
                                    drcr.c.drcrno,
                                    drcr.c.invid,
                                    drcr.c.dctypeflag,
                                ]
                            ).where(
                                and_(
                                    drcr.c.drcrdate >= startDate,
                                    drcr.c.drcrdate <= endDate,
                                    drcr.c.drcrid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            drcrinvdata = self.con.execute(
                                select([invoice.c.custid]).where(
                                    invoice.c.invid == countrow["invid"]
                                )
                            )
                            drcrinv = drcrinvdata.fetchone()
                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == drcrinv["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            if int(countrow["dctypeflag"] == 3):
                                trntype = "Credit Note"
                            else:
                                trntype = "Debit Note"
                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["drcrdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "drcrid": finalRow["dcinvtnid"],
                                        "drcrno": countrow["drcrno"],
                                        "dcno": "",
                                        "dcid": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": "",
                                        "invno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["drcrdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "drcrid": finalRow["dcinvtnid"],
                                        "drcrno": countrow["drcrno"],
                                        "dcid": "",
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )

                stockReport.append(
                    {
                        "date": "",
                        "particulars": "Total",
                        "dcid": "",
                        "dcno": "",
                        "invid": "",
                        "invno": "",
                        "rnid": "",
                        "rnno": "",
                        "tnid": "",
                        "tnno": "",
                        "trntype": "",
                        "totalinwardqty": "%.2f" % float(totalinward),
                        "totaloutwardqty": "%.2f" % float(totaloutward),
                    }
                )
                return {"gkstatus": enumdict["Success"], "gkresult": stockReport}

                self.con.close()
            except:
                print(traceback.format_exc())
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="stockonhandreport", renderer="json")
    def stockOnHandReport(self):
        """
        Purpose:
        Return the structured data grid of stock report for given product.
        Input will be productcode,startdate,enddate.
        orgcode will be taken from header and enddate
        returns a list of dictionaries where every dictionary will be one row.
        description:
        This function returns the complete stock report,
        including opening stock every inward and outward quantity and running balance for every transaction along with transaction type.
        at the end we get total inward and outward quantity.
        This report will be on the basis of productcode, startdate and enddate given from the client.
        The orgcode is taken from the header.
        The report will query database to get all in and out records for the given product where the dcinvtn flag is not 20.
        For every iteration of this list with a for loop we will find out the date of transaction from the delchal or invoice table depending on the flag being 4 or 9.
        Cash memo is in the invoice table so even 3 will qualify.
        Then we wil find the customer or supplyer name on the basis of given data.
        Note that if the startdate is same as the yearstart of the organisation then opening stock can be directly taken from the product table.
        if it is later than the startyear then we will have to come to the closing balance of the day before startdate given by client and use it as the opening balance.
        The row will be represented in this grid with every key denoting a column.
        The columns (keys) will be,
        date,particulars,invoice/dcno, transaction type (invoice /delchal),inward quantity,outward quantity ,total inward quantity , total outwrd quanity and balance.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                orgcode = authDetails["orgcode"]
                productCode = self.request.params["productcode"]
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stockresult = stockonhandfun(orgcode, productCode, endDate)
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": stockresult["gkresult"],
                }
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="godownwisestockforgodownincharge", renderer="json")
    def godownwisestockforgodownincharge(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()

                orgcode = authDetails["orgcode"]

                startDate = ""

                if "startdate" in self.request.params:
                    startDate = datetime.strptime(
                        str(self.request.params["startdate"]), "%Y-%m-%d"
                    )

                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stocktype = self.request.params["type"]
                godownCode = int(self.request.params["goid"])

                prodcode = self.con.execute(
                    "select productcode as productcode from goprod where goid=%d and orgcode=%d"
                    % (godownCode, orgcode)
                )
                prodcodelist = prodcode.fetchall()

                if prodcodelist == None:
                    return {"gkstatus": enumdict["Success"], "gkresult": prodcodelist}
                else:
                    stocklist = []
                    prodcodedesclist = []
                    for productcode in prodcodelist:
                        productCode = productcode["productcode"]
                        result = godownwisestockonhandfun(
                            self.con,
                            orgcode,
                            startDate,
                            endDate,
                            stocktype,
                            productCode,
                            godownCode,
                        )
                        resultlist = result[0]["prodid"] = productCode
                        stocklist.append(result[0])

                    allprodstocklist = sorted(
                        stocklist, key=lambda x: float(x["balance"])
                    )[0:5]
                    for prodcode in allprodstocklist:
                        proddesc = self.con.execute(
                            "select productdesc as proddesc from product where productcode=%d"
                            % (prodcode["prodid"])
                        )
                        proddesclist = proddesc.fetchone()
                        prodcodedesclist.append(
                            {
                                "prodcode": prodcode["prodid"],
                                "proddesc": proddesclist["proddesc"],
                            }
                        )
                    self.con.close()
                    return {
                        "gkstatus": enumdict["Success"],
                        "gkresult": allprodstocklist,
                        "proddesclist": prodcodedesclist,
                    }
            except Exception as e:
                logging.warn(e)
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="godownwise_stock_value", renderer="json")
    def godownwise_stock_value(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()

                orgcode = authDetails["orgcode"]

                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                godownCode = int(self.request.params["goid"])
                productCode = int(self.request.params["productcode"])

                valueOnHand = calculateStockValue(
                    self.con, orgcode, endDate, productCode, godownCode
                )
                self.con.close()

                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": valueOnHand,
                }
            except:
                print(traceback.format_exc())
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="godownwisestockonhand", renderer="json")
    def godownStockHReport(self):
        """
        Purpose:
        Return the structured data grid of godown wise stock on hand report for given product.
        Input will be productcode,enddate and goid(for specific godown) also type(mention at last).
        orgcode will be taken from header .
        returns a list of dictionaries where every dictionary will be one row.
        description:
        This function returns the complete godown wise stock on hand report,
        including opening stock every inward and outward quantity and running balance  for  selected product and godown.
        at the end we get total inward and outward quantity and balance.
        godownwise opening stock can be taken from goprod table . and godown name can be taken from godown
        The report will query database to get all in and out records for the given product where the dcinvtn flag 4 & 20.
        For every iteration of this list with a for loop we will find out the date of transaction from the delchal or transfernote table depending on the flag being 4 or 20.
        closing balance of the day before startdate given by client and use it as the opening balance.
        The row will be represented in this grid with every key denoting a column.
        The columns (keys) will be,
        total inward quantity , total outwrd quanity and balance , product name ,godownname.

        *product and godown = pg
        *all product and all godown = apag
        *all product and single godown = apg
        *product and all godown = pag
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            self.con = eng.connect()
            try:
                #
                orgcode = authDetails["orgcode"]
                startDate = ""

                if "startdate" in self.request.params:
                    startDate = datetime.strptime(
                        str(self.request.params["startdate"]), "%Y-%m-%d"
                    )
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stocktype = self.request.params["type"]
                productCode = (
                    self.request.params["productcode"]
                    if "productcode" in self.request.params
                    else ""
                )

                if stocktype in ["pg", "apg"]:
                    godownCode = self.request.params["goid"]
                else:
                    godownCode = 0

                result = []
                if stocktype == "apg":
                    prows = self.con.execute(
                        select([product.c.productcode, product.c.productdesc]).where(
                            and_(
                                product.c.orgcode == orgcode,
                            )
                        )
                    )
                    products = prows.fetchall()
                    pmap = {}
                    for prod in products:
                        pmap[prod["productcode"]] = prod["productdesc"]

                    # gpc - godown product code
                    gpcrows = self.con.execute(
                        select([goprod.c.productcode]).where(
                            and_(
                                goprod.c.goid == godownCode,
                                goprod.c.orgcode == orgcode,
                            )
                        )
                    )
                    gpcodes = gpcrows.fetchall()
                    for gpcode in gpcodes:
                        pcode = gpcode["productcode"]
                        temp = godownwisestockonhandfun(
                            self.con,
                            orgcode,
                            startDate,
                            endDate,
                            "pg",
                            pcode,
                            godownCode,
                        )
                        if len(temp):
                            temp[0]["srno"] = len(result) + 1
                            temp[0]["productcode"] = pcode
                            temp[0]["productname"] = pmap[pcode]
                            result.append(temp[0])
                else:
                    result = godownwisestockonhandfun(
                        self.con,
                        orgcode,
                        startDate,
                        endDate,
                        stocktype,
                        productCode,
                        godownCode,
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": result}
            except Exception as e:
                # print(traceback.format_exc())
                # print(e)
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=categorywisestockonhand", renderer="json")
    def categorywiseStockOnHandReport(self):
        """
        Purpose:
        Return the structured data grid of stock report for all products in given category.
        Input will be categorycodecode, enddate.
        orgcode will be taken from header
        returns a list of dictionaries where every dictionary will be one row.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                goid = self.request.params["goid"]
                subcategorycode = self.request.params["subcategorycode"]
                speccode = self.request.params["speccode"]
                orgcode = authDetails["orgcode"]
                categorycode = self.request.params["categorycode"]
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stockReport = []
                totalinward = 0.00
                totaloutward = 0.00
                """get its subcategories as well"""
                catdata = []
                # when there is some subcategory then get all N level categories of this category.
                if subcategorycode != "all":
                    catdata.append(int(subcategorycode))
                    for ccode in catdata:
                        result = self.con.execute(
                            select([categorysubcategories.c.categorycode]).where(
                                and_(
                                    categorysubcategories.c.orgcode == orgcode,
                                    categorysubcategories.c.subcategoryof == ccode,
                                )
                            )
                        )
                        result = result.fetchall()
                        for cat in result:
                            catdata.append(cat[0])
                # when subcategory is not there get all N level categories of main category.
                else:
                    catdata.append(int(categorycode))
                    for ccode in catdata:
                        result = self.con.execute(
                            select([categorysubcategories.c.categorycode]).where(
                                and_(
                                    categorysubcategories.c.orgcode == orgcode,
                                    categorysubcategories.c.subcategoryof == ccode,
                                )
                            )
                        )
                        result = result.fetchall()
                        for cat in result:
                            catdata.append(cat[0])
                # if godown wise report selected
                if goid != "-1" and goid != "all":
                    products = self.con.execute(
                        select(
                            [
                                goprod.c.goopeningstock.label("openingstock"),
                                product.c.productcode,
                                product.c.productdesc,
                            ]
                        ).where(
                            and_(
                                product.c.orgcode == orgcode,
                                goprod.c.orgcode == orgcode,
                                goprod.c.goid == int(goid),
                                product.c.productcode == goprod.c.productcode,
                                product.c.categorycode.in_(catdata),
                            )
                        )
                    )
                    prodDesc = products.fetchall()
                    srno = 1
                    for row in prodDesc:
                        totalinwardgo = 0.00
                        totaloutwardgo = 0.00
                        gopeningStock = row["openingstock"]
                        stockRecords = self.con.execute(
                            select([stock])
                            .where(
                                and_(
                                    stock.c.productcode == row["productcode"],
                                    stock.c.goid == int(goid),
                                    stock.c.orgcode == orgcode,
                                    or_(
                                        stock.c.dcinvtnflag != 40,
                                        stock.c.dcinvtnflag != 30,
                                        stock.c.dcinvtnflag != 90,
                                    ),
                                )
                            )
                            .order_by(stock.c.stockdate)
                        )
                        stockData = stockRecords.fetchall()
                        ysData = self.con.execute(
                            select([organisation.c.yearstart]).where(
                                organisation.c.orgcode == orgcode
                            )
                        )
                        ysRow = ysData.fetchone()
                        yearStart = datetime.strptime(
                            str(ysRow["yearstart"]), "%Y-%m-%d"
                        )
                        totalinwardgo = totalinwardgo + float(gopeningStock)
                        for finalRow in stockData:
                            if finalRow["dcinvtnflag"] == 4:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            delchal.c.dcdate,
                                            delchal.c.dcno,
                                            delchal.c.custid,
                                        ]
                                    ).where(
                                        and_(
                                            delchal.c.dcdate <= endDate,
                                            delchal.c.dcid == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    custdata = self.con.execute(
                                        select([customerandsupplier.c.custname]).where(
                                            customerandsupplier.c.custid
                                            == countrow["custid"]
                                        )
                                    )
                                    custrow = custdata.fetchone()
                                    dcinvresult = self.con.execute(
                                        select([dcinv.c.invid]).where(
                                            dcinv.c.dcid == finalRow["dcinvtnid"]
                                        )
                                    )
                                    if dcinvresult.rowcount == 1:
                                        dcinvrow = dcinvresult.fetchone()
                                        invresult = self.con.execute(
                                            select([invoice.c.invoiceno]).where(
                                                invoice.c.invid == dcinvrow["invid"]
                                            )
                                        )
                                        """ No need to check if invresult has rowcount 1 since it must be 1 """
                                        invrow = invresult.fetchone()
                                        trntype = "delchal&invoice"
                                    else:
                                        dcinvrow = {"invid": ""}
                                        invrow = {"invoiceno": ""}
                                        trntype = "delchal"
                                    if finalRow["inout"] == 9:
                                        gopeningStock = float(gopeningStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinwardgo = float(totalinwardgo) + float(
                                            finalRow["qty"]
                                        )

                                    if finalRow["inout"] == 15:
                                        gopeningStock = float(gopeningStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutward = float(totaloutwardgo) + float(
                                            finalRow["qty"]
                                        )
                            if finalRow["dcinvtnflag"] == 20:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            transfernote.c.transfernotedate,
                                            transfernote.c.transfernoteno,
                                        ]
                                    ).where(
                                        and_(
                                            transfernote.c.transfernotedate <= endDate,
                                            transfernote.c.transfernoteid
                                            == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    if finalRow["inout"] == 9:
                                        gopeningStock = float(gopeningStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinwardgo = float(totalinwardgo) + float(
                                            finalRow["qty"]
                                        )

                                    if finalRow["inout"] == 15:
                                        gopeningStock = float(gopeningStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutwardgo = float(totaloutwardgo) + float(
                                            finalRow["qty"]
                                        )
                            if finalRow["dcinvtnflag"] == 18:
                                if finalRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        finalRow["qty"]
                                    )
                                    totalinward = float(totalinward) + float(
                                        finalRow["qty"]
                                    )
                                if finalRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        finalRow["qty"]
                                    )
                                    totaloutward = float(totaloutward) + float(
                                        finalRow["qty"]
                                    )
                        stockReport.append(
                            {
                                "srno": srno,
                                "productname": row["productdesc"],
                                "totalinwardqty": "%.2f" % float(totalinwardgo),
                                "totaloutwardqty": "%.2f" % float(totaloutwardgo),
                                "balance": "%.2f" % float(gopeningStock),
                            }
                        )
                        srno += 1
                    self.con.close()
                    return {"gkstatus": enumdict["Success"], "gkresult": stockReport}
                # if godown wise report selected but all godowns selected
                elif goid == "all":
                    products = self.con.execute(
                        select(
                            [
                                goprod.c.goopeningstock.label("openingstock"),
                                goprod.c.goid,
                                product.c.productcode,
                                product.c.productdesc,
                            ]
                        ).where(
                            and_(
                                product.c.orgcode == orgcode,
                                goprod.c.orgcode == orgcode,
                                product.c.productcode == goprod.c.productcode,
                                product.c.categorycode.in_(catdata),
                            )
                        )
                    )
                    prodDesc = products.fetchall()
                    srno = 1
                    for row in prodDesc:
                        totalinwardgo = 0.00
                        totaloutwardgo = 0.00
                        gopeningStock = row["openingstock"]
                        godowns = self.con.execute(
                            select([godown.c.goname]).where(
                                and_(
                                    godown.c.goid == row["goid"],
                                    godown.c.orgcode == orgcode,
                                )
                            )
                        )
                        stockRecords = self.con.execute(
                            select([stock])
                            .where(
                                and_(
                                    stock.c.productcode == row["productcode"],
                                    stock.c.goid == int(row["goid"]),
                                    stock.c.orgcode == orgcode,
                                    or_(
                                        stock.c.dcinvtnflag != 40,
                                        stock.c.dcinvtnflag != 30,
                                        stock.c.dcinvtnflag != 90,
                                    ),
                                )
                            )
                            .order_by(stock.c.stockdate)
                        )
                        stockData = stockRecords.fetchall()
                        ysData = self.con.execute(
                            select([organisation.c.yearstart]).where(
                                organisation.c.orgcode == orgcode
                            )
                        )
                        ysRow = ysData.fetchone()
                        yearStart = datetime.strptime(
                            str(ysRow["yearstart"]), "%Y-%m-%d"
                        )
                        totalinwardgo = totalinwardgo + float(gopeningStock)
                        for finalRow in stockData:
                            if finalRow["dcinvtnflag"] == 4:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            delchal.c.dcdate,
                                            delchal.c.dcno,
                                            delchal.c.custid,
                                        ]
                                    ).where(
                                        and_(
                                            delchal.c.dcdate <= endDate,
                                            delchal.c.dcid == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    custdata = self.con.execute(
                                        select([customerandsupplier.c.custname]).where(
                                            customerandsupplier.c.custid
                                            == countrow["custid"]
                                        )
                                    )
                                    custrow = custdata.fetchone()
                                    dcinvresult = self.con.execute(
                                        select([dcinv.c.invid]).where(
                                            dcinv.c.dcid == finalRow["dcinvtnid"]
                                        )
                                    )
                                    if dcinvresult.rowcount == 1:
                                        dcinvrow = dcinvresult.fetchone()
                                        invresult = self.con.execute(
                                            select([invoice.c.invoiceno]).where(
                                                invoice.c.invid == dcinvrow["invid"]
                                            )
                                        )
                                        """ No need to check if invresult has rowcount 1 since it must be 1 """
                                        invrow = invresult.fetchone()
                                        trntype = "delchal&invoice"
                                    else:
                                        dcinvrow = {"invid": ""}
                                        invrow = {"invoiceno": ""}
                                        trntype = "delchal"
                                    if finalRow["inout"] == 9:
                                        gopeningStock = float(gopeningStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinwardgo = float(totalinwardgo) + float(
                                            finalRow["qty"]
                                        )

                                    if finalRow["inout"] == 15:
                                        gopeningStock = float(gopeningStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutward = float(totaloutwardgo) + float(
                                            finalRow["qty"]
                                        )
                            if finalRow["dcinvtnflag"] == 20:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            transfernote.c.transfernotedate,
                                            transfernote.c.transfernoteno,
                                        ]
                                    ).where(
                                        and_(
                                            transfernote.c.transfernotedate <= endDate,
                                            transfernote.c.transfernoteid
                                            == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    if finalRow["inout"] == 9:
                                        gopeningStock = float(gopeningStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinwardgo = float(totalinwardgo) + float(
                                            finalRow["qty"]
                                        )

                                    if finalRow["inout"] == 15:
                                        gopeningStock = float(gopeningStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutwardgo = float(totaloutwardgo) + float(
                                            finalRow["qty"]
                                        )

                            if finalRow["dcinvtnflag"] == 18:
                                if finalRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        finalRow["qty"]
                                    )
                                    totalinward = float(totalinward) + float(
                                        finalRow["qty"]
                                    )
                                if finalRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        finalRow["qty"]
                                    )
                                    totaloutward = float(totaloutward) + float(
                                        finalRow["qty"]
                                    )
                        stockReport.append(
                            {
                                "srno": srno,
                                "productname": row["productdesc"],
                                "godown": godowns.fetchone()["goname"],
                                "totalinwardqty": "%.2f" % float(totalinwardgo),
                                "totaloutwardqty": "%.2f" % float(totaloutwardgo),
                                "balance": "%.2f" % float(gopeningStock),
                            }
                        )
                        srno += 1
                    self.con.close()
                    return {"gkstatus": enumdict["Success"], "gkresult": stockReport}
                # No godown selected just categorywise stock on hand report
                else:
                    products = self.con.execute(
                        select(
                            [
                                product.c.openingstock,
                                product.c.productcode,
                                product.c.productdesc,
                            ]
                        ).where(
                            and_(
                                product.c.orgcode == orgcode,
                                product.c.categorycode.in_(catdata),
                            )
                        )
                    )
                    prodDesc = products.fetchall()
                    srno = 1
                    for row in prodDesc:
                        totalinward = 0.00
                        totaloutward = 0.00
                        openingStock = row["openingstock"]
                        productCd = row["productcode"]
                        prodName = row["productdesc"]
                        if goid != "-1" and goid != "all":
                            stockRecords = self.con.execute(
                                select([stock])
                                .where(
                                    and_(
                                        stock.c.productcode == productCd,
                                        stock.c.goid == int(goid),
                                        stock.c.orgcode == orgcode,
                                        or_(
                                            stock.c.dcinvtnflag != 40,
                                            stock.c.dcinvtnflag != 30,
                                            stock.c.dcinvtnflag != 90,
                                        ),
                                    )
                                )
                                .order_by(stock.c.stockdate)
                            )
                        else:
                            stockRecords = self.con.execute(
                                select([stock]).where(
                                    and_(
                                        stock.c.productcode == productCd,
                                        stock.c.orgcode == orgcode,
                                        or_(
                                            stock.c.dcinvtnflag != 20,
                                            stock.c.dcinvtnflag != 40,
                                            stock.c.dcinvtnflag != 30,
                                            stock.c.dcinvtnflag != 90,
                                        ),
                                    )
                                )
                            )
                        stockData = stockRecords.fetchall()
                        totalinward = totalinward + float(openingStock)
                        for finalRow in stockData:
                            if (
                                finalRow["dcinvtnflag"] == 3
                                or finalRow["dcinvtnflag"] == 9
                            ):
                                countresult = self.con.execute(
                                    select(
                                        [
                                            invoice.c.invoicedate,
                                            invoice.c.invoiceno,
                                            invoice.c.custid,
                                        ]
                                    ).where(
                                        and_(
                                            invoice.c.invoicedate <= endDate,
                                            invoice.c.invid == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    custdata = self.con.execute(
                                        select([customerandsupplier.c.custname]).where(
                                            customerandsupplier.c.custid
                                            == countrow["custid"]
                                        )
                                    )
                                    custrow = custdata.fetchone()
                                    if custrow != None:
                                        custnamedata = custrow["custname"]
                                    else:
                                        custnamedata = "Cash Memo"
                                    if finalRow["inout"] == 9:
                                        openingStock = float(openingStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinward = float(totalinward) + float(
                                            finalRow["qty"]
                                        )
                                    if finalRow["inout"] == 15:
                                        openingStock = float(openingStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutward = float(totaloutward) + float(
                                            finalRow["qty"]
                                        )

                            if finalRow["dcinvtnflag"] == 4:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            delchal.c.dcdate,
                                            delchal.c.dcno,
                                            delchal.c.custid,
                                        ]
                                    ).where(
                                        and_(
                                            delchal.c.dcdate <= endDate,
                                            delchal.c.dcid == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    custdata = self.con.execute(
                                        select([customerandsupplier.c.custname]).where(
                                            customerandsupplier.c.custid
                                            == countrow["custid"]
                                        )
                                    )
                                    custrow = custdata.fetchone()
                                    dcinvresult = self.con.execute(
                                        select([dcinv.c.invid]).where(
                                            dcinv.c.dcid == finalRow["dcinvtnid"]
                                        )
                                    )
                                    if dcinvresult.rowcount == 1:
                                        dcinvrow = dcinvresult.fetchone()
                                        invresult = self.con.execute(
                                            select([invoice.c.invoiceno]).where(
                                                invoice.c.invid == dcinvrow["invid"]
                                            )
                                        )
                                        """ No need to check if invresult has rowcount 1 since it must be 1 """
                                        invrow = invresult.fetchone()
                                        trntype = "delchal&invoice"
                                    else:
                                        dcinvrow = {"invid": ""}
                                        invrow = {"invoiceno": ""}
                                        trntype = "delchal"
                                    if finalRow["inout"] == 9:
                                        openingStock = float(openingStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinward = float(totalinward) + float(
                                            finalRow["qty"]
                                        )
                                    if finalRow["inout"] == 15:
                                        openingStock = float(openingStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutward = float(totaloutward) + float(
                                            finalRow["qty"]
                                        )

                            if finalRow["dcinvtnflag"] == 18:
                                if finalRow["inout"] == 9:
                                    openingStock = float(openingStock) + float(
                                        finalRow["qty"]
                                    )
                                    totalinward = float(totalinward) + float(
                                        finalRow["qty"]
                                    )
                                if finalRow["inout"] == 15:
                                    openingStock = float(openingStock) - float(
                                        finalRow["qty"]
                                    )
                                    totaloutward = float(totaloutward) + float(
                                        finalRow["qty"]
                                    )

                        stockReport.append(
                            {
                                "srno": srno,
                                "productname": prodName,
                                "totalinwardqty": "%.2f" % float(totalinward),
                                "totaloutwardqty": "%.2f" % float(totaloutward),
                                "balance": "%.2f" % float(openingStock),
                            }
                        )
                        srno = srno + 1
                    return {"gkstatus": enumdict["Success"], "gkresult": stockReport}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="type=closingbalance", renderer="json")
    def closingBalance(self):
        """
        Purpose: returns the current balance and balance type for the given account as per the current date.
        description:
        This function takes the startedate and enddate (date of transaction) as well as accountcode.
        Returns the balance as on that date with the baltype.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                accountCode = self.request.params["accountcode"]
                financialStart = self.request.params["financialstart"]
                calculateTo = self.request.params["calculateto"]
                calbalData = calculateBalance(
                    self.con, accountCode, financialStart, financialStart, calculateTo
                )
                if calbalData["curbal"] == 0:
                    currentBalance = "%.2f" % float(calbalData["curbal"])
                else:
                    currentBalance = "%.2f (%s)" % (
                        float(calbalData["curbal"]),
                        calbalData["baltype"],
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": currentBalance}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=logbyorg", renderer="json")
    def logByOrg(self):
        """
        purpose: returns complete log statement for an organisation.
        Date range is taken from calculatefrom and calculateto.
        description:
        This function returns entire log statement for a given organisation.
        Date range is taken from client and orgcode from authdetails.
        Date sorted according to orderflag.
        If request params has orderflag then date sorted in descending order otherwise in ascending order.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                if "orderflag" in self.request.params:
                    result = self.con.execute(
                        select([log])
                        .where(
                            and_(
                                log.c.orgcode == authDetails["orgcode"],
                                log.c.time >= self.request.params["calculatefrom"],
                                log.c.time <= self.request.params["calculateto"],
                            )
                        )
                        .order_by(desc(log.c.time))
                    )
                else:
                    result = self.con.execute(
                        select([log])
                        .where(
                            and_(
                                log.c.orgcode == authDetails["orgcode"],
                                log.c.time >= self.request.params["calculatefrom"],
                                log.c.time <= self.request.params["calculateto"],
                            )
                        )
                        .order_by(log.c.time)
                    )
                logdata = []
                ROLES = {
                    -1: "Admin",
                    0: "Manager",
                    1: "Operator",
                    2: "Internal Auditor",
                    3: "Godown In Charge",
                }
                for row in result:
                    rowuser = self.con.execute(
                        "select username, orgs->'%s'->'userrole' as userrole from gkusers where userid = %d"
                        % (str(authDetails["orgcode"]), int(row["userid"]))
                    ).fetchone()
                    userrole = ROLES[rowuser["userrole"]]
                    logdata.append(
                        {
                            "logid": row["logid"],
                            "time": datetime.strftime(row["time"], "%d-%m-%Y"),
                            "activity": row["activity"],
                            "userid": row["userid"],
                            "username": rowuser["username"] + "(" + userrole + ")",
                        }
                    )

                return {"gkstatus": enumdict["Success"], "gkresult": logdata}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="type=logbyuser", renderer="json")
    def logByUser(self):
        """
        This function is the replica of the previous one except the log here is for a particular user.
        All parameter are same with the addition of userid."""
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                if "orderflag" in self.request.params:
                    result = self.con.execute(
                        select([log])
                        .where(
                            and_(
                                log.c.userid == self.request.params["userid"],
                                log.c.orgcode == authDetails["orgcode"],
                                log.c.time >= self.request.params["calculatefrom"],
                                log.c.time <= self.request.params["calculateto"],
                            )
                        )
                        .order_by(desc(log.c.time))
                    )
                else:
                    result = self.con.execute(
                        select([log])
                        .where(
                            and_(
                                log.c.userid == self.request.params["userid"],
                                log.c.orgcode == authDetails["orgcode"],
                                log.c.time >= self.request.params["calculatefrom"],
                                log.c.time <= self.request.params["calculateto"],
                            )
                        )
                        .order_by(log.c.time)
                    )
                logdata = []
                for row in result:
                    logdata.append(
                        {
                            "logid": row["logid"],
                            "time": datetime.strftime(row["time"], "%d-%m-%Y"),
                            "activity": row["activity"],
                        }
                    )
                return {"gkstatus": enumdict["Success"], "gkresult": logdata}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="type=del_unbilled", renderer="json")
    def unbilled_deliveries(self):
        """
        purpose:
        presents a list of deliverys which are unbilled  There are exceptions which should be excluded.
        free replacement or sample are those which are excluded.
                Token is the only required input.
                We also require Orgcode, but it is extracted from the token itself.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                orgcode = authDetails["orgcode"]
                if "inputdate" in self.request.params:
                    dataset = {
                        "inputdate": self.request.params["inputdate"],
                        "del_unbilled_type": self.request.params["del_unbilled_type"],
                    }
                else:
                    dataset = self.request.json_body
                inout = self.request.params["inout"]
                inputdate = dataset["inputdate"]
                del_unbilled_type = dataset["del_unbilled_type"]
                new_inputdate = dataset["inputdate"]
                new_inputdate = datetime.strptime(new_inputdate, "%Y-%m-%d")
                dc_unbilled = []
                # Adding the query here only, which will select the dcids either with "delivery-out" type or "delivery-in".
                if inout == "i":  # in
                    # distinct clause must be added to the query.
                    # delchal dcdate need to be added into select clause, since it is mentioned in order_by clause.
                    if del_unbilled_type == "0":
                        alldcids = self.con.execute(
                            select([delchal.c.dcid, delchal.c.dcdate])
                            .distinct()
                            .where(
                                and_(
                                    delchal.c.orgcode == orgcode,
                                    delchal.c.dcdate <= new_inputdate,
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 9,
                                    delchal.c.dcid == stock.c.dcinvtnid,
                                )
                            )
                            .order_by(delchal.c.dcdate)
                        )
                    else:
                        alldcids = self.con.execute(
                            select([delchal.c.dcid, delchal.c.dcdate])
                            .distinct()
                            .where(
                                and_(
                                    delchal.c.orgcode == orgcode,
                                    delchal.c.dcflag == int(del_unbilled_type),
                                    delchal.c.dcdate <= new_inputdate,
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 9,
                                    delchal.c.dcid == stock.c.dcinvtnid,
                                )
                            )
                            .order_by(delchal.c.dcdate)
                        )
                if inout == "o":  # out
                    # distinct clause must be added to the query.
                    # delchal dcdate need to be added into select clause, since it is mentioned in order_by clause.
                    if del_unbilled_type == "0":
                        alldcids = self.con.execute(
                            select([delchal.c.dcid, delchal.c.dcdate])
                            .distinct()
                            .where(
                                and_(
                                    delchal.c.orgcode == orgcode,
                                    delchal.c.dcdate <= new_inputdate,
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 15,
                                    delchal.c.dcid == stock.c.dcinvtnid,
                                )
                            )
                            .order_by(delchal.c.dcdate)
                        )
                    else:
                        alldcids = self.con.execute(
                            select([delchal.c.dcid, delchal.c.dcdate])
                            .distinct()
                            .where(
                                and_(
                                    delchal.c.orgcode == orgcode,
                                    delchal.c.dcflag == int(del_unbilled_type),
                                    delchal.c.dcdate <= new_inputdate,
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 15,
                                    delchal.c.dcid == stock.c.dcinvtnid,
                                )
                            )
                            .order_by(delchal.c.dcdate)
                        )
                alldcids = alldcids.fetchall()
                dcResult = []
                # ********* What if multiple delchals are covered by single invoice?*******************
                i = 0
                while i < len(alldcids):
                    dcid = alldcids[i]
                    invidresult = self.con.execute(
                        select([dcinv.c.invid]).where(
                            and_(
                                dcid[0] == dcinv.c.dcid,
                                dcinv.c.orgcode == orgcode,
                                invoice.c.orgcode == orgcode,
                                invoice.c.invid == dcinv.c.invid,
                                invoice.c.invoicedate <= new_inputdate,
                            )
                        )
                    )
                    invidresult = invidresult.fetchall()
                    if len(invidresult) == 0:
                        pass
                    else:
                        # invid's will be distinct only. So no problem to explicitly applying distinct clause.
                        if inout == "i":  # in
                            dcprodresult = self.con.execute(
                                select([stock.c.productcode, stock.c.qty]).where(
                                    and_(
                                        stock.c.orgcode == orgcode,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 9,
                                        dcid[0] == stock.c.dcinvtnid,
                                    )
                                )
                            )
                        if inout == "o":  # out
                            dcprodresult = self.con.execute(
                                select([stock.c.productcode, stock.c.qty]).where(
                                    and_(
                                        stock.c.orgcode == orgcode,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 15,
                                        dcid[0] == stock.c.dcinvtnid,
                                    )
                                )
                            )
                        dcprodresult = dcprodresult.fetchall()
                        # I am assuming :productcode must be distinct. So, I haven't applied distinct construct.
                        # what if dcprodresult or invprodresult is empty?
                        invprodresult = []
                        for invid in invidresult:
                            temp = self.con.execute(
                                select([invoice.c.contents]).where(
                                    and_(
                                        invoice.c.orgcode == orgcode,
                                        invid == invoice.c.invid,
                                    )
                                )
                            )
                            temp = temp.fetchall()
                            # Below two lines are intentionally repeated. It's not a mistake.
                            temp = temp[0]
                            temp = temp[0]
                            invprodresult.append(temp)
                        # Now we have to compare the two results: dcprodresult and invprodresult
                        # I assume that the delchal must have at most only one entry for a particular product. If not, then it's a bug and needs to be rectified.
                        # But, in case of invprodresult, there can be more than one productcodes mentioned. This is because, with one delchal, there can be many invoices linked.
                        matchedproducts = []
                        remainingproducts = {}
                        for eachitem in dcprodresult:
                            # dcprodresult is a list of tuples. eachitem is one such tuple.
                            for eachinvoice in invprodresult:
                                # invprodresult is a list of dictionaries. eachinvoice is one such dictionary.
                                for eachproductcode in list(eachinvoice.keys()):
                                    # eachitem[0] is unique. It's not repeated.
                                    dcprodcode = eachitem[0]
                                    if int(dcprodcode) == int(
                                        eachproductcode
                                    ):  # why do we need to convert these into string to compare?
                                        # this means that the product in delchal matches with the product in invoice
                                        # now we will check its quantity
                                        invqty = list(
                                            eachinvoice[eachproductcode].values()
                                        )[0]
                                        dcqty = eachitem[1]
                                        if float(dcqty) == float(
                                            invqty
                                        ):  # conversion of datatypes to compatible ones is very important when comparing them.
                                            # this means the quantity of current individual product is matched exactly
                                            matchedproducts.append(int(eachproductcode))
                                        elif float(dcqty) > float(invqty):
                                            # this means current invoice has not billed the whole product quantity.
                                            if dcprodcode in list(
                                                remainingproducts.keys()
                                            ):
                                                if float(dcqty) == (
                                                    float(remainingproducts[dcprodcode])
                                                    + float(invqty)
                                                ):
                                                    matchedproducts.append(
                                                        int(eachproductcode)
                                                    )
                                                    # whether we use eachproductcode or dcprodcode, doesn't matter. Because, both values are the same here.
                                                    del remainingproducts[
                                                        int(eachproductcode)
                                                    ]
                                                else:
                                                    # It must not be the case that below addition is greater than dcqty.
                                                    remainingproducts[
                                                        dcprodcode
                                                    ] = float(
                                                        remainingproducts[dcprodcode]
                                                    ) + float(
                                                        invqty
                                                    )
                                            else:
                                                remainingproducts.update(
                                                    {dcprodcode: float(invqty)}
                                                )
                                        else:
                                            # "dcqty < invqty" should never happen.
                                            # It could happen when multiple delivery chalans have only one invoice.
                                            pass

                        # changing previous logic..
                        if len(matchedproducts) == len(dcprodresult):
                            # Now we have got the delchals, for which invoices are also sent completely.
                            alldcids.remove(dcid)
                            i -= 1
                    i += 1
                    pass

                for eachdcid in alldcids:
                    if inout == "i":  # in
                        # check if current dcid has godown name or it's None. Accordingly, our query should be changed.
                        tmpresult = self.con.execute(
                            select([stock.c.goid])
                            .distinct()
                            .where(
                                and_(
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 9,
                                    stock.c.dcinvtnid == eachdcid[0],
                                )
                            )
                        )
                        tmpresult = tmpresult.fetchone()
                        if tmpresult[0] == None:
                            singledcResult = self.con.execute(
                                select(
                                    [
                                        delchal.c.dcid,
                                        delchal.c.dcno,
                                        delchal.c.dcdate,
                                        delchal.c.dcflag,
                                        customerandsupplier.c.custname,
                                    ]
                                )
                                .distinct()
                                .where(
                                    and_(
                                        delchal.c.orgcode == orgcode,
                                        customerandsupplier.c.orgcode == orgcode,
                                        eachdcid[0] == delchal.c.dcid,
                                        delchal.c.custid
                                        == customerandsupplier.c.custid,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 9,
                                        eachdcid[0] == stock.c.dcinvtnid,
                                    )
                                )
                            )
                        else:
                            singledcResult = self.con.execute(
                                select(
                                    [
                                        delchal.c.dcid,
                                        delchal.c.dcno,
                                        delchal.c.dcdate,
                                        delchal.c.dcflag,
                                        customerandsupplier.c.custname,
                                        godown.c.goname,
                                    ]
                                )
                                .distinct()
                                .where(
                                    and_(
                                        delchal.c.orgcode == orgcode,
                                        customerandsupplier.c.orgcode == orgcode,
                                        godown.c.orgcode == orgcode,
                                        eachdcid[0] == delchal.c.dcid,
                                        delchal.c.custid
                                        == customerandsupplier.c.custid,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 9,
                                        eachdcid[0] == stock.c.dcinvtnid,
                                        stock.c.goid == godown.c.goid,
                                    )
                                )
                            )
                    if inout == "o":  # out
                        # check if current dcid has godown name or it's None. Accordingly, our query should be changed.
                        tmpresult = self.con.execute(
                            select([stock.c.goid])
                            .distinct()
                            .where(
                                and_(
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 15,
                                    stock.c.dcinvtnid == eachdcid[0],
                                )
                            )
                        )
                        tmpresult = tmpresult.fetchone()
                        if tmpresult[0] == None:
                            singledcResult = self.con.execute(
                                select(
                                    [
                                        delchal.c.dcid,
                                        delchal.c.dcno,
                                        delchal.c.dcdate,
                                        delchal.c.dcflag,
                                        customerandsupplier.c.custname,
                                    ]
                                )
                                .distinct()
                                .where(
                                    and_(
                                        delchal.c.orgcode == orgcode,
                                        customerandsupplier.c.orgcode == orgcode,
                                        eachdcid[0] == delchal.c.dcid,
                                        delchal.c.custid
                                        == customerandsupplier.c.custid,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 15,
                                        eachdcid[0] == stock.c.dcinvtnid,
                                    )
                                )
                            )
                        else:
                            singledcResult = self.con.execute(
                                select(
                                    [
                                        delchal.c.dcid,
                                        delchal.c.dcno,
                                        delchal.c.dcdate,
                                        delchal.c.dcflag,
                                        customerandsupplier.c.custname,
                                        godown.c.goname,
                                    ]
                                )
                                .distinct()
                                .where(
                                    and_(
                                        delchal.c.orgcode == orgcode,
                                        customerandsupplier.c.orgcode == orgcode,
                                        godown.c.orgcode == orgcode,
                                        eachdcid[0] == delchal.c.dcid,
                                        delchal.c.custid
                                        == customerandsupplier.c.custid,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 15,
                                        eachdcid[0] == stock.c.dcinvtnid,
                                        stock.c.goid == godown.c.goid,
                                    )
                                )
                            )
                    singledcResult = singledcResult.fetchone()
                    dcResult.append(singledcResult)

                temp_dict = {}
                srno = 1
                for row in dcResult:
                    # if (row["dcdate"].year < inputdate.year) or (row["dcdate"].year == inputdate.year and row["dcdate"].month < inputdate.month) or (row["dcdate"].year == inputdate.year and row["dcdate"].month == inputdate.month and row["dcdate"].day <= inputdate.day):
                    temp_dict = {
                        "dcid": row["dcid"],
                        "srno": srno,
                        "dcno": row["dcno"],
                        "dcdate": datetime.strftime(row["dcdate"], "%d-%m-%Y"),
                        "dcflag": row["dcflag"],
                        "custname": row["custname"],
                    }

                    canceldelchal = 1
                    exist_dcinv = self.con.execute(
                        "select count(dcid) as dccount from dcinv where dcid=%d and orgcode=%d"
                        % (row["dcid"], authDetails["orgcode"])
                    )
                    existDcinv = exist_dcinv.fetchone()
                    if existDcinv["dccount"] > 0:
                        canceldelchal = 0
                    temp_dict["canceldelchal"] = canceldelchal

                    if "goname" in list(row.keys()):
                        temp_dict["goname"] = row["goname"]
                    else:
                        temp_dict["goname"] = None
                    if temp_dict["dcflag"] == 1:
                        temp_dict["dcflag"] = "Approval"
                    elif temp_dict["dcflag"] == 3:
                        temp_dict["dcflag"] = "Consignment"
                    elif temp_dict["dcflag"] == 4:
                        temp_dict["dcflag"] = "Sale"
                    elif temp_dict["dcflag"] == 16:
                        temp_dict["dcflag"] = "Purchase"
                    elif temp_dict["dcflag"] == 19:
                        # We don't have to consider sample.
                        temp_dict["dcflag"] = "Sample"
                    elif temp_dict["dcflag"] == 6:
                        # we ignore this as well
                        temp_dict["dcflag"] = "Free Replacement"
                    else:
                        temp_dict["dcflag"] = "Bad Input"
                    if (
                        temp_dict["dcflag"] != "Sample"
                        and temp_dict["dcflag"] != "Free Replacement"
                    ):
                        dc_unbilled.append(temp_dict)
                        srno += 1
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": dc_unbilled}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="registers", renderer="json")
    def register(self):
        """
        purpose: Takes input: i.e. either sales/purchase register and time period.
        Returns a dictionary of all matched invoices.
        description:
        This function is used to see sales or purchase register of organisation.
        It means the total purchase and sales of different products. Also its amount,
        tax, etc.
        orderflag is checked in request params for sorting date in descending order.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                """This is a list of dictionaries. Each dictionary contains details of an invoice, like-invoiceno, invdate,
                customer or supllier name, TIN, then total amount of invoice in rs then different tax rates and their respective amounts
                """
                spdata = []
                """taxcolumns is a list, which contains all possible rates of tax which are there in invoices"""
                taxcolumns = []
                # sales register(flag = 0)
                if int(self.request.params["flag"]) == 0:
                    if "orderflag" in self.request.params:
                        invquery = self.con.execute(
                            "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax,cess ,freeqty, sourcestate,  taxstate, taxflag, discount, icflag from invoice where orgcode=%d AND inoutflag = 15 AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate DESC"
                            # "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax,cess ,freeqty, sourcestate,  taxstate, taxflag, discount, icflag from invoice where orgcode=%d AND custid IN (select custid from customerandsupplier where orgcode=%d AND csflag=3) AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate DESC"
                            % (
                                authDetails["orgcode"],
                                datetime.strptime(
                                    str(self.request.params["calculatefrom"]),
                                    "%d-%m-%Y",
                                ).strftime("%Y-%m-%d"),
                                datetime.strptime(
                                    str(self.request.params["calculateto"]), "%d-%m-%Y"
                                ).strftime("%Y-%m-%d"),
                            )
                        )
                    else:
                        invquery = self.con.execute(
                            "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax,cess ,freeqty, sourcestate,  taxstate, taxflag, discount, icflag from invoice where orgcode=%d AND inoutflag = 15 AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate"
                            # "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax,cess ,freeqty, sourcestate,  taxstate, taxflag, discount, icflag from invoice where orgcode=%d AND custid IN (select custid from customerandsupplier where orgcode=%d AND csflag=3) AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate"
                            % (
                                authDetails["orgcode"],
                                datetime.strptime(
                                    str(self.request.params["calculatefrom"]),
                                    "%d-%m-%Y",
                                ).strftime("%Y-%m-%d"),
                                datetime.strptime(
                                    str(self.request.params["calculateto"]), "%d-%m-%Y"
                                ).strftime("%Y-%m-%d"),
                            )
                        )

                # purchase register(flag = 1)
                elif int(self.request.params["flag"]) == 1:
                    if "orderflag" in self.request.params:
                        invquery = self.con.execute(
                            "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax, cess,freeqty, taxstate, sourcestate, taxflag, discount, icflag from invoice where orgcode=%d AND inoutflag = 9 AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate DESC"
                            # "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax, cess,freeqty, taxstate, sourcestate, taxflag, discount, icflag from invoice where orgcode=%d AND custid IN (select custid from customerandsupplier where orgcode=%d AND csflag=19) AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate DESC"
                            % (
                                authDetails["orgcode"],
                                datetime.strptime(
                                    str(self.request.params["calculatefrom"]),
                                    "%d-%m-%Y",
                                ).strftime("%Y-%m-%d"),
                                datetime.strptime(
                                    str(self.request.params["calculateto"]), "%d-%m-%Y"
                                ).strftime("%Y-%m-%d"),
                            )
                        )
                    else:
                        invquery = self.con.execute(
                            "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax, cess,freeqty, taxstate, sourcestate, taxflag, discount, icflag from invoice where orgcode=%d AND inoutflag = 9 AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate"
                            # "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax, cess,freeqty, taxstate, sourcestate, taxflag, discount, icflag from invoice where orgcode=%d AND custid IN (select custid from customerandsupplier where orgcode=%d AND csflag=19) AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate"
                            % (
                                authDetails["orgcode"],
                                datetime.strptime(
                                    str(self.request.params["calculatefrom"]),
                                    "%d-%m-%Y",
                                ).strftime("%Y-%m-%d"),
                                datetime.strptime(
                                    str(self.request.params["calculateto"]), "%d-%m-%Y"
                                ).strftime("%Y-%m-%d"),
                            )
                        )

                srno = 1
                """This totalrow dictionary is used for very last row of report which contains sum of all columns in report"""
                totalrow = {
                    "grossamount": "0.00",
                    "taxfree": "0.00",
                    "tax": {},
                    "taxamount": {},
                }
                # for each invoice
                result = invquery.fetchall()
                for row in result:
                    try:
                        custdata = self.con.execute(
                            select(
                                [
                                    customerandsupplier.c.custname,
                                    customerandsupplier.c.csflag,
                                    customerandsupplier.c.custtan,
                                    customerandsupplier.c.gstin,
                                ]
                            ).where(customerandsupplier.c.custid == row["custid"])
                        )
                        rowcust = custdata.fetchone()
                        if not rowcust:
                            rowcust = {
                                "custname": "",
                                "custtan": "",
                                "gstin": None,
                                "csflag": "",
                            }
                        invoicedata = {
                            "srno": srno,
                            "invid": row["invid"],
                            "invoiceno": row["invoiceno"],
                            "invoicedate": datetime.strftime(
                                row["invoicedate"], "%d-%m-%Y"
                            ),
                            "customername": rowcust["custname"],
                            "customertin": rowcust["custtan"],
                            "grossamount": "%.2f" % row["invoicetotal"],
                            "taxfree": "0.00",
                            "tax": "",
                            "taxamount": "",
                            "icflag": row["icflag"],
                        }

                        taxname = ""
                        disc = row["discount"]
                        # Decide tax type from taxflag
                        if int(row["taxflag"]) == 22:
                            taxname = "% VAT"

                        if int(row["taxflag"]) == 7:
                            destinationstate = row["taxstate"]
                            destinationStateCode = getStateCode(
                                row["taxstate"], self.con
                            )["statecode"]
                            sourcestate = row["sourcestate"]
                            sourceStateCode = getStateCode(
                                row["sourcestate"], self.con
                            )["statecode"]
                            # Gst has 2 types of tax Inter State(IGST) & Intra state(SGST & CGST).
                            if destinationstate != sourcestate:
                                taxname = "% IGST "
                            if destinationstate == sourcestate:
                                taxname = "% SGST"
                            # Get GSTIN on the basis of Customer / Supplier role.
                            if rowcust["gstin"] != None:
                                invoicedata["custgstin"] = ""
                                if int(rowcust["csflag"]) == 3:
                                    try:
                                        if (
                                            str(destinationStateCode)
                                            not in rowcust["gstin"]
                                        ):
                                            stcode = "0" + str(destinationStateCode)
                                            if stcode in rowcust["gstin"]:
                                                invoicedata["custgstin"] = rowcust[
                                                    "gstin"
                                                ][stcode]
                                        else:
                                            invoicedata["custgstin"] = rowcust["gstin"][
                                                str(destinationStateCode)
                                            ]
                                    except:
                                        invoicedata["custgstin"] = ""
                                else:
                                    try:
                                        if str(sourceStateCode) not in rowcust["gstin"]:
                                            stcode = "0" + str(sourceStateCode)
                                            if stcode in rowcust["gstin"]:
                                                invoicedata["custgstin"] = rowcust[
                                                    "gstin"
                                                ][stcode]
                                        else:
                                            invoicedata["custgstin"] = rowcust["gstin"][
                                                str(sourceStateCode)
                                            ]
                                    except:
                                        invoicedata["custgstin"] = ""

                        # Calculate total grossamount of all invoices.
                        totalrow["grossamount"] = "%.2f" % (
                            float(totalrow["grossamount"])
                            + float("%.2f" % row["invoicetotal"])
                        )
                        qty = 0.00
                        ppu = 0.00
                        # taxrate and cessrate are in percentage
                        taxrate = 0.00
                        cessrate = 0.00
                        # taxamount is net amount for some tax rate. eg. 2% tax on 200rs. This 200rs is taxamount, i.e. Taxable amount
                        taxamount = 0.00
                        """This taxdata dictionary has key as taxrate and value as amount of tax to be paid on this rate. eg. {"2.00": "2.80"}"""
                        taxdata = {}
                        """This taxamountdata dictionary has key as taxrate and value as Net amount on which tax to be paid. eg. {"2.00": "140.00"}"""
                        taxamountdata = {}
                        """for each product in invoice.
                        row["contents"] is JSONB which has format like this - {"22": {"20.00": "2"}, "61": {"100.00": "1"}} where 22 and 61 is productcode, {"20.00": "2"}
                        here 20.00 is price per unit and quantity is 2.
                        The other JSONB field in each invoice is row["tax"]. Its format is {"22": "2.00", "61": "2.00"}. Here, 22 and 61 are products and 2.00 is tax applied on those products, similarly for CESS {"22":"0.05"} where 22 is productcode snd 0.05 is cess rate"""

                        for pc in row["contents"].keys():
                            if not pc:
                                continue
                            discamt = 0.00
                            taxrate = float(row["tax"][pc])
                            if disc != None:
                                discamt = float(disc[pc])
                            else:
                                discamt = 0.00
                            for pcprice in row["contents"][pc].keys():
                                ppu = pcprice

                                gspc = self.con.execute(
                                    select([product.c.gsflag]).where(
                                        product.c.productcode == pc
                                    )
                                )
                                flag = gspc.fetchone()
                                # Check for product & service.
                                # In case of service quantity is not present.
                                if int(flag["gsflag"]) == 7:
                                    qty = float(row["contents"][pc][pcprice])
                                    # Taxable value of a product is calculated as (Price per unit * Quantity) - Discount
                                    taxamount = (float(ppu) * float(qty)) - float(
                                        discamt
                                    )
                                else:
                                    # Taxable value for service.
                                    taxamount = float(ppu) - float(discamt)
                            # There is a possibility of tax free product or service. This needs to be mention seperately.
                            # For this condition tax is saved as 0.00 in tax field of invoice.
                            if taxrate == 0.00:
                                invoicedata["taxfree"] = "%.2f" % (
                                    (
                                        float("%.2f" % float(invoicedata["taxfree"]))
                                        + taxamount
                                    )
                                )
                                totalrow["taxfree"] = "%.2f" % (
                                    float(totalrow["taxfree"]) + taxamount
                                )
                                continue
                            """if taxrate appears in this invoice then update invoice tax and taxamount for that rate Otherwise create new entries in respective dictionaries of that invoice"""
                            # When tax type is IGST or VAT.
                            if taxrate != 0.00:
                                if taxname != "% SGST":
                                    taxnames = "%.2f" % taxrate + taxname
                                    if str(taxnames) in taxdata:
                                        taxdata[taxnames] = "%.2f" % (
                                            float(taxdata[taxnames]) + taxamount
                                        )
                                        taxamountdata[taxnames] = "%.2f" % (
                                            float(taxamountdata[taxnames])
                                            + taxamount * float(taxrate) / 100.00
                                        )
                                    else:
                                        taxdata.update({taxnames: "%.2f" % taxamount})
                                        taxamountdata.update(
                                            {
                                                taxnames: "%.2f"
                                                % (taxamount * float(taxrate) / 100.00)
                                            }
                                        )

                                    """if new taxrate appears(in all invoices), ie. we found this rate for the first time then add this column to taxcolumns and also create new entries in tax & taxamount dictionaries Otherwise update existing data"""
                                    if taxnames not in taxcolumns:
                                        taxcolumns.append(taxnames)
                                        totalrow["taxamount"].update(
                                            {
                                                taxnames: "%.2f"
                                                % float(taxamountdata[taxnames])
                                            }
                                        )
                                        totalrow["tax"].update(
                                            {taxnames: "%.2f" % taxamount}
                                        )
                                    else:
                                        totalrow["taxamount"][taxnames] = "%.2f" % (
                                            float(totalrow["taxamount"][taxnames])
                                            + float(taxamount * float(taxrate) / 100.00)
                                        )
                                        totalrow["tax"][taxnames] = "%.2f" % (
                                            float(totalrow["tax"][taxnames]) + taxamount
                                        )

                                # when tax type is SGST & CGST , Tax rate needs to be diveded by 2.
                                if taxname == "% SGST":
                                    taxrate = taxrate / 2
                                    sgstTax = "%.2f" % taxrate + "% SGST"
                                    cgstTax = "%.2f" % taxrate + "% CGST"
                                    if sgstTax in taxdata:
                                        taxdata[sgstTax] = "%.2f" % (
                                            float(taxdata[sgstTax]) + taxamount
                                        )
                                        taxamountdata[sgstTax] = "%.2f" % (
                                            float(taxamountdata[sgstTax])
                                            + taxamount * float(taxrate) / 100.00
                                        )

                                    else:
                                        taxdata.update({sgstTax: "%.2f" % taxamount})
                                        taxamountdata.update(
                                            {
                                                sgstTax: "%.2f"
                                                % (taxamount * float(taxrate) / 100.00)
                                            }
                                        )

                                    if sgstTax not in taxcolumns:
                                        taxcolumns.append(sgstTax)
                                        totalrow["taxamount"].update(
                                            {
                                                sgstTax: "%.2f"
                                                % float(taxamountdata[sgstTax])
                                            }
                                        )
                                        totalrow["tax"].update(
                                            {sgstTax: "%.2f" % taxamount}
                                        )
                                    else:
                                        totalrow["taxamount"][sgstTax] = "%.2f" % (
                                            float(totalrow["taxamount"][sgstTax])
                                            + float(taxamount * float(taxrate) / 100.00)
                                        )
                                        totalrow["tax"][sgstTax] = "%.2f" % (
                                            float(totalrow["tax"][sgstTax]) + taxamount
                                        )

                                    if cgstTax in taxdata:
                                        taxdata[cgstTax] = "%.2f" % (
                                            float(taxdata[cgstTax]) + taxamount
                                        )
                                        taxamountdata[cgstTax] = "%.2f" % (
                                            float(taxamountdata[cgstTax])
                                            + taxamount * float(taxrate) / 100.00
                                        )

                                    else:
                                        taxdata.update({cgstTax: "%.2f" % taxamount})
                                        taxamountdata.update(
                                            {
                                                cgstTax: "%.2f"
                                                % (taxamount * float(taxrate) / 100.00)
                                            }
                                        )

                                    if cgstTax not in taxcolumns:
                                        taxcolumns.append(cgstTax)
                                        totalrow["taxamount"].update(
                                            {
                                                cgstTax: "%.2f"
                                                % float(taxamountdata[cgstTax])
                                            }
                                        )
                                        totalrow["tax"].update(
                                            {cgstTax: "%.2f" % taxamount}
                                        )
                                    else:
                                        totalrow["taxamount"][cgstTax] = "%.2f" % (
                                            float(totalrow["taxamount"][cgstTax])
                                            + float(taxamount * float(taxrate) / 100.00)
                                        )
                                        totalrow["tax"][cgstTax] = "%.2f" % (
                                            float(totalrow["tax"][cgstTax]) + taxamount
                                        )

                            if row["taxflag"] == 22:
                                continue

                            Cessname = ""
                            # Cess is a different type of TAX, only present in GST invoice.
                            if row["cess"] != None:
                                cessrate = "%.2f" % float(row["cess"][pc])
                                Cessname = str(cessrate) + "% CESS"
                                if cessrate != "0.00":
                                    if str(Cessname) in taxdata:
                                        taxdata[Cessname] = "%.2f" % (
                                            float(taxdata[Cessname]) + taxamount
                                        )
                                        taxamountdata[Cessname] = "%.2f" % (
                                            float(taxamountdata[Cessname])
                                            + taxamount * float(cessrate) / 100.00
                                        )
                                    else:
                                        taxdata.update({Cessname: "%.2f" % taxamount})
                                        taxamountdata.update(
                                            {
                                                Cessname: "%.2f"
                                                % (taxamount * float(cessrate) / 100.00)
                                            }
                                        )

                                    if Cessname not in taxcolumns:
                                        taxcolumns.append(Cessname)
                                        totalrow["taxamount"].update(
                                            {
                                                Cessname: "%.2f"
                                                % float(taxamountdata[Cessname])
                                            }
                                        )
                                        totalrow["tax"].update(
                                            {Cessname: "%.2f" % taxamount}
                                        )
                                    else:
                                        totalrow["taxamount"][Cessname] = "%.2f" % (
                                            float(totalrow["taxamount"][Cessname])
                                            + float(
                                                taxamount * float(cessrate) / 100.00
                                            )
                                        )
                                        totalrow["tax"][Cessname] = "%.2f" % (
                                            float(totalrow["tax"][Cessname]) + taxamount
                                        )

                        invoicedata["tax"] = taxdata
                        invoicedata["taxamount"] = taxamountdata
                        spdata.append(invoicedata)
                        srno += 1
                    except:
                        print(traceback.format_exc())
                        pass

                taxcolumns.sort()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": spdata,
                    "totalrow": totalrow,
                    "taxcolumns": taxcolumns,
                }

            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="type=GSTCalc", renderer="json")
    def GSTCalc(self):
        """
        Purpose:
        takes list of accounts for CGST,SGST,IGST and CESS at Input and Output side,
        Returns list of accounts with their closing balances.
        Description:
        This API will return list of all accounts for input and output side created by the user for GST calculation.
        The function takes json_body which will have 8 key: value pares.
        Each  key denoting the tax and value will be list of accounts.
        The keys of this json_body will be as follows.
        * CGSTIn,
        * CGSTOut,
        * SGSTIn,
        * SGSTOut,
        * IGSTIn,
        * IGSTOut,
        * CESSIn,
        * CESSOut.
        Function will also need the range for which calculatBalance is to be called for getting actual balances.
        The function will loop through every list getting closing balance for all the accounts.
        Then it will sum up all the balances for that list.
        Then it will compare total in amount with total out amount and will decide if it is payable or carried forward.
        Following code will return a dictionary which will have structure like  gstDict = {"cgstin":{"accname":calculated balance,...,"to        talCGSTIn":value},"cgstout":{"accname":calculatebalance ,...,"totalCGSTOut":value},.....,"cgstpayable":value,"sgstpayable":value,        ....,"cgstcrdfwd":value,"sgstcrdfwd":value,.....}
        """

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                # check if data is supplied as json or url params
                try:
                    dataset = self.request.json_body
                except:
                    dataset = self.request.params

                stateD = dataset["statename"]
                # Get abbreviation of state
                stateA = self.con.execute(
                    select([state.c.abbreviation]).where(state.c.statename == stateD)
                )
                stateABV = stateA.fetchone()
                # Retrived individual data from dictionary
                startDate = dataset["startdate"]
                endDate = dataset["enddate"]
                result = self.con.execute(
                    select([organisation.c.yearstart]).where(
                        organisation.c.orgcode == authDetails["orgcode"]
                    )
                )
                fStart = result.fetchone()
                financialStart = fStart["yearstart"]

                # get list of accountCodes for each type of taxes for their input and output taxes.
                grp = self.con.execute(
                    select([groupsubgroups.c.groupcode]).where(
                        and_(
                            groupsubgroups.c.groupname == "Duties & Taxes",
                            groupsubgroups.c.orgcode == authDetails["orgcode"],
                        )
                    )
                )
                grpCode = grp.fetchone()

                # Create string which has taxname with state abbreviation for selecting accounts
                Cgstin = "CGSTIN_" + stateABV["abbreviation"]
                cgstout = "CGSTOUT_" + stateABV["abbreviation"]
                sgstin = "SGSTIN_" + stateABV["abbreviation"]
                sgstout = "SGSTOUT_" + stateABV["abbreviation"]
                igstin = "IGSTIN_" + stateABV["abbreviation"]
                igstout = "IGSTOUT_" + stateABV["abbreviation"]
                cessin = "CESSIN_" + stateABV["abbreviation"]
                cessout = "CESSOUT_" + stateABV["abbreviation"]

                # Declare public variables to store total
                totalCGSTIn = 0.00
                totalCGSTOut = 0.00
                totalSGSTOut = 0.00
                totalSGSTIn = 0.00
                totalSGSTOut = 0.00
                totalIGSTIn = 0.00
                totalIGSTOut = 0.00
                totalCESSIn = 0.00
                totalCESSOut = 0.00
                # These variables are to store Payable and carried forward amount
                cgstPayable = 0.00
                cgstCrdFwd = 0.00
                sgstPayable = 0.00
                sgstCrdFwd = 0.00
                igstPayable = 0.00
                igstCrdFwd = 0.00
                cessPayable = 0.00
                cessCrdFwd = 0.00
                gstDict = {}

                cIN = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(Cgstin + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                CGSTIn = cIN.fetchall()
                cgstin = {}
                if CGSTIn != None:
                    for cin in CGSTIn:
                        calbalData = calculateBalance(
                            self.con,
                            cin["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        # fill dictionary with account name and its balance.
                        cgstin[cin["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        # calculate total cgst in amount by adding balance of each account in every iteration.
                        totalCGSTIn = totalCGSTIn + calbalData["curbal"]
                # Populate dictionary to be returned with cgstin and total values
                gstDict["cgstin"] = cgstin
                gstDict["totalCGSTIn"] = "%.2f" % (float(totalCGSTIn))

                cOUT = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(cgstout + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                CGSTOut = cOUT.fetchall()
                cgstout = {}
                if CGSTOut != None:
                    for cout in CGSTOut:
                        calbalData = calculateBalance(
                            self.con,
                            cout["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        cgstout[cout["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalCGSTOut = totalCGSTOut + calbalData["curbal"]
                gstDict["cgstout"] = cgstout
                gstDict["totalCGSTOut"] = "%.2f" % (float(totalCGSTOut))

                # calculate carried forward amount or payable.
                if totalCGSTIn > totalCGSTOut:
                    cgstCrdFwd = totalCGSTIn - totalCGSTOut
                    gstDict["cgstcrdfwd"] = "%.2f" % (float(cgstCrdFwd))
                else:
                    cgstPayable = totalCGSTOut - totalCGSTIn
                    gstDict["cgstpayable"] = "%.2f" % (float(cgstPayable))

                # For state tax
                sIN = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(sgstin + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                SGSTIn = sIN.fetchall()
                sgstin = {}
                if SGSTIn != None:
                    for sin in SGSTIn:
                        calbalData = calculateBalance(
                            self.con,
                            sin["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        sgstin[sin["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalSGSTIn = totalSGSTIn + calbalData["curbal"]
                    # Populate dictionary to be returned with cgstin and total values
                    gstDict["sgstin"] = sgstin
                    gstDict["totalSGSTIn"] = "%.2f" % (float(totalSGSTIn))

                sOUT = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(sgstout + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                SGSTOut = sOUT.fetchall()
                sgstout = {}
                if SGSTOut != None:
                    for sout in SGSTOut:
                        calbalData = calculateBalance(
                            self.con,
                            sout["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        sgstout[sout["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalSGSTOut = totalSGSTOut + calbalData["curbal"]
                gstDict["sgstout"] = sgstout
                gstDict["totalSGSTOut"] = "%.2f" % (float(totalSGSTOut))

                # calculate carried forward amount or payable.
                if totalSGSTIn > totalSGSTOut:
                    sgstCrdFwd = totalSGSTIn - totalSGSTOut
                    gstDict["sgstcrdfwd"] = "%.2f" % (float(sgstCrdFwd))
                else:
                    sgstPayable = totalSGSTOut - totalSGSTIn
                    gstDict["sgstpayable"] = "%.2f" % (float(sgstPayable))

                # For Inter state tax

                iIN = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(igstin + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                IGSTIn = iIN.fetchall()
                igstin = {}
                if IGSTIn != None:
                    for iin in IGSTIn:
                        calbalData = calculateBalance(
                            self.con,
                            iin["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        igstin[iin["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalIGSTIn = totalIGSTIn + calbalData["curbal"]
                gstDict["igstin"] = igstin
                gstDict["totalIGSTIn"] = "%.2f" % (float(totalIGSTIn))

                iOUT = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(igstout + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                IGSTOut = iOUT.fetchall()
                igstout = {}
                if IGSTOut != None:
                    for iout in IGSTOut:
                        calbalData = calculateBalance(
                            self.con,
                            iout["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        igstout[iout["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalIGSTOut = totalIGSTOut + calbalData["curbal"]
                gstDict["igstout"] = igstout
                gstDict["totalIGSTOut"] = "%.2f" % (float(totalIGSTOut))

                # calculate carried forward amount or payable.
                if totalIGSTIn > totalIGSTOut:
                    igstCrdFwd = totalIGSTIn - totalIGSTOut
                    gstDict["IgstCrdFwd"] = "%.2f" % (float(igstCrdFwd))
                else:
                    igstPayable = totalIGSTOut - totalIGSTIn
                    gstDict["IgstPayable"] = "%.2f" % (float(igstPayable))

                # For cess tax
                csIN = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(cessin + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                CESSIn = csIN.fetchall()
                cssin = {}
                if CESSIn != None:
                    for csin in CESSIn:
                        calbalData = calculateBalance(
                            self.con,
                            csin["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        cssin[csin["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalCESSIn = totalCESSIn + calbalData["curbal"]
                gstDict["cessin"] = cssin
                gstDict["totalCESSIn"] = "%.2f" % (float(totalCESSIn))

                csOUT = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(cessout + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                CESSOut = csOUT.fetchall()
                cssout = {}
                if CESSOut != None:
                    for csout in CESSOut:
                        calbalData = calculateBalance(
                            self.con,
                            csout["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        cssout[csout["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalCESSOut = totalCESSOut + calbalData["curbal"]
                gstDict["cessout"] = cssout
                gstDict["totalCESSOut"] = "%.2f" % (float(totalCESSOut))

                # calculate carried forward amount or payable.
                if totalCESSIn > totalCESSOut:
                    cessCrdFwd = totalCESSIn - totalCESSOut
                    gstDict["cessCrdFwd"] = "%.2f" % (float(cessCrdFwd))
                else:
                    cessPayable = totalCESSOut - totalCESSIn
                    gstDict["cesspayable"] = "%.2f" % (float(cessPayable))

                return {"gkstatus": enumdict["Success"], "gkresult": gstDict}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
