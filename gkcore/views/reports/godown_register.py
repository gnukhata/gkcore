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
"Ankita Chakrabarti"<chakrabarti.ankita94@gmail.com>
"Sai Karthik"<kskarthik@disrot.org>

"""
import logging
from gkcore import eng, enumdict
from gkcore.utils import authCheck
from pyramid.view import view_defaults, view_config
from gkcore.models.gkdb import (
    organisation,
    delchal,
    invoice,
    customerandsupplier,
    stock,
    product,
    transfernote,
    goprod,
    dcinv,
    rejectionnote,
    drcr,
)
from sqlalchemy.sql import select, and_, or_
from datetime import datetime
from sqlalchemy.sql.functions import func
import traceback  # for printing detailed exception logs
from gkcore.views.reports.helpers.stock import (
    calculateStockValue,
    godownwisestockonhandfun,
)

@view_defaults(route_name="godown-register")
class api_godownregister(object):
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET", renderer="json")
    def godown_register(self):
        # Check whether the user is registered & valid
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        auth_details = authCheck(token)

        if auth_details["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        goproddetails = None
        godownstock = []
        godown_items = []
        goid = self.request.matchdict["goid"]

        # Connecting to the DB table goprod & filtering the data for required org & godown

        try:
            result = eng.connect().execute(
                select([goprod]).where(
                    and_(
                        goprod.c.orgcode == auth_details["orgcode"],
                        goprod.c.goid == goid,
                    )
                )
            )
            goproddetails = result.fetchall()

        except:
            return {"gkstatus": enumdict["ConnectionFailed"]}

        # Connecting to the DB table product & filtering the data for the required productcode

        for productid in goproddetails:
            try:
                result = eng.connect().execute(
                    select([product]).where(
                        product.c.productcode == productid["productcode"]
                    )
                )
                godownstock.append(result.fetchone())
            except Exception as e:
                print(e)
                return {"gkstatus": enumdict["ConnectionFailed"]}

        # Formatting the fetched data

        for p in godownstock:
            temp_dict = dict()
            for name, val in p.items():
                value_type = str(type(val))
                if value_type == "<class 'decimal.Decimal'>":
                    temp_dict[name] = str(val)
                else:
                    temp_dict[name] = val
            godown_items.append(temp_dict)

        return {"gkstatus": enumdict["Success"], "gkresult": godown_items}

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

    @view_config(route_name="godown-stock-godownincharge", renderer="json")
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

    @view_config(route_name="godownwise-stock-value", renderer="json")
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

    @view_config(route_name="godownwise-stock-on-hand", renderer="json")
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
            with eng.connect() as con:
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
                    prows = con.execute(
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
                    gpcrows = con.execute(
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
                            con,
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
                        con,
                        orgcode,
                        startDate,
                        endDate,
                        stocktype,
                        productCode,
                        godownCode,
                    )
                return {"gkstatus": enumdict["Success"], "gkresult": result}
