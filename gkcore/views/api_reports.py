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
