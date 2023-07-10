"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020,2019 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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
'Prajkta Patkar' <prajkta@riseup.net>
"""


from gkcore import eng, enumdict
from gkcore.utils import authCheck
from gkcore.models.gkdb import (
    vouchers,
    accounts,
    groupsubgroups,
    bankrecon,
    voucherbin,
    projects,
)
from sqlalchemy.sql import select
from sqlalchemy import func
from gkcore.views.api_gkuser import getUserRole
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, between
from pyramid.request import Request

# from pyramid.response import Response
from pyramid.view import view_defaults, view_config

# from sqlalchemy.ext.baked import Result
from datetime import datetime

# import base64
# from PIL import Image


# This function deletes a voucher and inserts an entry into voucherbin table.
def voucherBinInsert(con, vcode, orgcode):
    voucherdata = con.execute(
        select([vouchers]).where(vouchers.c.vouchercode == int(vcode))
    )
    voucherRow = voucherdata.fetchone()

    # Actual delete of voucher.
    con.execute(
        "delete from vouchers  where vouchercode = %d and lockflag= 'f'" % (int(vcode))
    )

    # Updating vouchercount field of accounts.
    DrData = voucherRow["drs"]
    CrData = voucherRow["crs"]
    for drKey in list(DrData.keys()):
        con.execute(
            "update accounts set vouchercount = (vouchercount -1) where accountcode = %d"
            % (int(drKey))
        )
    for crKey in list(CrData.keys()):
        con.execute(
            "update accounts set vouchercount = (vouchercount -1) where accountcode = %d"
            % (int(crKey))
        )
    finalCrs = {}
    finalDrs = {}

    # Collecting details for insert query for voucherbin.
    projectNameData = con.execute(
        select([projects.c.projectname]).where(
            projects.c.projectcode == voucherRow["projectcode"]
        )
    )
    prjNameRow = projectNameData.fetchone()
    if prjNameRow == None:
        projectName = ""
    else:
        projectName = prjNameRow["projectname"]
    for d in list(DrData.keys()):
        accname = con.execute(
            select([accounts.c.accountname]).where(accounts.c.accountcode == int(d))
        )
        account = accname.fetchone()
        finalDrs[account["accountname"]] = DrData[d]
    for c in list(CrData.keys()):
        accname = con.execute(
            select([accounts.c.accountname]).where(accounts.c.accountcode == int(c))
        )
        account = accname.fetchone()
        finalCrs[account["accountname"]] = CrData[c]
    voucherBinData = {
        "vouchercode": voucherRow["vouchercode"],
        "vouchertype": voucherRow["vouchertype"],
        "voucherdate": voucherRow["voucherdate"],
        "vouchernumber": voucherRow["vouchernumber"],
        "narration": voucherRow["narration"],
        "drs": finalDrs,
        "crs": finalCrs,
        "projectname": projectName,
        "orgcode": orgcode,
    }
    voucherBinInsert = con.execute(voucherbin.insert(), [voucherBinData])


# this fuction is called to delete vouchers.
def deleteVoucherFun(vcode, orgcode):
    try:
        con = eng.connect()
        # Removing invoice related entries.
        invoices = con.execute(
            "select invid from billwise  where vouchercode = %d " % (int(vcode))
        )
        invid = invoices.fetchall()
        for row in invid:
            amt = con.execute(
                "select adjamount from billwise  where vouchercode = %d and invid = %d "
                % (int(vcode), row["invid"])
            )
            adjamount = amt.fetchone()
            # Updating amountpaid field of invoice.
            con.execute(
                "update invoice set amountpaid = amountpaid - %.2f where invid =%d and orgcode = %d"
                % (float(adjamount["adjamount"]), row["invid"], (int(orgcode)))
            )
            # Deleting round off vouchers.
            voucherToBeDeleted = con.execute(
                select([vouchers.c.vouchercode]).where(
                    and_(
                        vouchers.c.invid == int(row["invid"]),
                        vouchers.c.orgcode == int(orgcode),
                        vouchers.c.narration.like("Round off amount%"),
                    )
                )
            )
            voucherCodeToDelete = voucherToBeDeleted.fetchone()
            if voucherCodeToDelete and voucherCodeToDelete["vouchercode"] != None:
                con.execute(
                    "delete from billwise where vouchercode=%d"
                    % (int(voucherCodeToDelete["vouchercode"]))
                )
                voucherBinInsert(con, voucherCodeToDelete["vouchercode"], orgcode)
        con.execute("delete from billwise where vouchercode=%d" % (int(vcode)))
        # Removing drcr related vouchers.
        drcrs = con.execute(
            "select drcrid from vouchers  where vouchercode = %d " % (int(vcode))
        )
        drcridToBeDeleted = drcrs.fetchone()
        if drcridToBeDeleted and drcridToBeDeleted["drcrid"] != None:
            # Deleting round off vouchers.
            voucherToBeDeleted = con.execute(
                select([vouchers.c.vouchercode]).where(
                    and_(
                        vouchers.c.drcrid == int(drcridToBeDeleted["drcrid"]),
                        vouchers.c.orgcode == int(orgcode),
                        vouchers.c.narration.like("Round off amount%"),
                    )
                )
            )
            voucherCodeToDelete = voucherToBeDeleted.fetchone()
            if voucherCodeToDelete and voucherCodeToDelete["vouchercode"] != None:
                voucherBinInsert(con, voucherCodeToDelete["vouchercode"], orgcode)
        voucherBinInsert(con, vcode, orgcode)
        con.close()
        return {"gkstatus": enumdict["Success"]}
    except:
        return {"gkstatus": enumdict["ConnectionFailed"]}


def getInvVouchers(con, orgcode, invid):
    try:
        vouchersData = con.execute(
            select(
                [
                    vouchers.c.vouchercode,
                    vouchers.c.attachmentcount,
                    vouchers.c.vouchernumber,
                    vouchers.c.voucherdate,
                    vouchers.c.narration,
                    vouchers.c.drs,
                    vouchers.c.crs,
                    vouchers.c.prjcrs,
                    vouchers.c.prjdrs,
                    vouchers.c.vouchertype,
                    vouchers.c.lockflag,
                    vouchers.c.delflag,
                    vouchers.c.projectcode,
                    vouchers.c.orgcode,
                ]
            )
            .where(
                and_(
                    vouchers.c.orgcode == orgcode,
                    vouchers.c.invid == invid,
                    vouchers.c.delflag == False,
                )
            )
            .order_by(vouchers.c.voucherdate, vouchers.c.vouchercode)
        )
        voucherRecords = []

        for voucher in vouchersData:
            rawDr = dict(voucher["drs"])
            rawCr = dict(voucher["crs"])
            finalDR = {}
            finalCR = {}
            tdr = 0.00
            tcr = 0.00

            for d in list(rawDr.keys()):
                accname = con.execute(
                    select([accounts.c.accountname]).where(
                        accounts.c.accountcode == int(d)
                    )
                )
                account = accname.fetchone()
                finalDR[account["accountname"]] = rawDr[d]

            for c in list(rawCr.keys()):
                accname = con.execute(
                    select([accounts.c.accountname]).where(
                        accounts.c.accountcode == int(c)
                    )
                )
                account = accname.fetchone()
                finalCR[account["accountname"]] = rawCr[c]

            if voucher["narration"] == "null":
                voucher["narration"] = ""
            voucherRecords.append(
                {
                    "invid": invid,
                    "vouchercode": voucher["vouchercode"],
                    "attachmentcount": voucher["attachmentcount"],
                    "vouchernumber": voucher["vouchernumber"],
                    "voucherdate": datetime.strftime(
                        voucher["voucherdate"], "%d-%m-%Y"
                    ),
                    "narration": voucher["narration"],
                    "drs": finalDR,
                    "crs": finalCR,
                    "prjdrs": voucher["prjdrs"],
                    "prjcrs": voucher["prjcrs"],
                    "vouchertype": voucher["vouchertype"],
                    "delflag": voucher["delflag"],
                    "orgcode": voucher["orgcode"],
                    "status": voucher["lockflag"],
                }
            )
        return voucherRecords
    except:
        return []


@view_defaults(route_name="transaction")
class api_transaction(object):
    """
    This class is the resource to create, update, read and delete vouchers (transactions)   connection rules:
    con is used for executing sql expression language based queries,
    while eng is used for raw sql execution.
    routing mechanism:
    @view_defaults is used for setting the default route for crud on the given resource class.
    if specific route is to be attached to a certain method, overriding view_default, , or for giving get, post, put, delete methods to default route, the view_config decorator is used.
    For other predicates view_config is generally used.
    If there are more than one methods with get as the request_method, then other predicates like request_param will be used for routing request to that method.
    """

    def __init__(self, request):
        """
        Initialising the request object which gets the data from client.
        """
        self.request = Request
        self.request = request
        self.con = Connection

    def __genVoucherNumber(self, con, voucherType, orgcode):
        """
        Purpose:
        Generates a new vouchernumber based on vouchertype and max count for that type.
        """
        initialType = ""
        if voucherType == "journal":
            initialType = "jr"
        if voucherType == "contra":
            initialType = "cr"
        if voucherType == "payment":
            initialType = "pt"
        if voucherType == "receipt":
            initialType = "rt"
        if voucherType == "sales":
            initialType = "sl"
        if voucherType == "purchase":
            initialType = "pu"
        if voucherType == "creditnote":
            initialType = "cn"
        if voucherType == "debitnote":
            initialType = "dn"
        if voucherType == "salesreturn":
            initialType = "sr"
        if voucherType == "purchasereturn":
            initialType = "pr"

        vchCountResult = self.con.execute(
            "select count(vouchercode) as vcount from vouchers where orgcode = %d and vouchertype = '%s'"
            % (int(orgcode), str(voucherType))
        )
        vchCount = vchCountResult.fetchone()
        initialType = initialType + str(vchCount["vcount"] + 1)

        return initialType

    @view_config(request_method="POST", renderer="json")
    def addVoucher(self):
        """

        Purpose:
        adds a new voucher for given organisation and returns success as gkstatus if adding is successful.
        Description:
        Adds a voucher into the voucher table.
        Method uses the route given in view_default while post in request_method of view_config implies create.
        The method gets request which has json_body containing:
        *voucher number
        *entry date (default as current date )
        * voucher date,
        * narration
        * Drs json object containing dr accounts as keys and their respective Dr amount as values.
        * project Drs (currently null) as well as project Crs.
        * project name if any,
        * voucher type,
        * attachment (to be implemented)
        * lockflag default False,
        * del flag default False
        After voucher is added using insert query, the vouchercount for given accounts will be incremented by 1.
        since there will be at least 2 accounts in a transaction (minimum 1 each for Dr and Cr),
        We will run a loop on the dictionary for accountcode and amounts both for Dr and Cr dicts.
        And for each account code we will fire update query.
        As usual the checking for jwt in request headers will be first done only then the code will procede.
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
                dataset = self.request.json_body
                dataset["orgcode"] = authDetails["orgcode"]
                drs = dataset["drs"]
                crs = dataset["crs"]
                if "instrumentdate" in dataset:
                    instrumentdate = dataset["instrumentdate"]
                    dataset["instrumentdate"] = datetime.strptime(
                        instrumentdate, "%Y-%m-%d"
                    )

                # generate voucher number if it is not sent.
                if ("vouchernumber" in dataset) == False:
                    voucherType = dataset["vouchertype"]
                    vchNo = self.__genVoucherNumber(
                        self.con, voucherType, dataset["orgcode"]
                    )
                    dataset["vouchernumber"] = vchNo
                result = self.con.execute(vouchers.insert(), [dataset])
                for drkeys in list(drs.keys()):
                    self.con.execute(
                        "update accounts set vouchercount = vouchercount +1 where accountcode = %d"
                        % (int(drkeys))
                    )
                    accgrpdata = self.con.execute(
                        select(
                            [groupsubgroups.c.groupname, groupsubgroups.c.groupcode]
                        ).where(
                            groupsubgroups.c.groupcode
                            == (
                                select([accounts.c.groupcode]).where(
                                    accounts.c.accountcode == int(drkeys)
                                )
                            )
                        )
                    )
                    accgrp = accgrpdata.fetchone()
                    if accgrp["groupname"] == "Bank":
                        vouchercodedata = self.con.execute(
                            "select max(vouchercode) as vcode from vouchers"
                        )
                        vouchercode = vouchercodedata.fetchone()
                        recoresult = self.con.execute(
                            bankrecon.insert(),
                            [
                                {
                                    "vouchercode": int(vouchercode["vcode"]),
                                    "accountcode": drkeys,
                                    "orgcode": authDetails["orgcode"],
                                }
                            ],
                        )
                for crkeys in list(crs.keys()):
                    self.con.execute(
                        "update accounts set vouchercount = vouchercount +1 where accountcode = %d"
                        % (int(crkeys))
                    )
                    accgrpdata = self.con.execute(
                        select(
                            [groupsubgroups.c.groupname, groupsubgroups.c.groupcode]
                        ).where(
                            groupsubgroups.c.groupcode
                            == (
                                select([accounts.c.groupcode]).where(
                                    accounts.c.accountcode == int(crkeys)
                                )
                            )
                        )
                    )
                    accgrp = accgrpdata.fetchone()
                    if accgrp["groupname"] == "Bank":
                        vouchercodedata = self.con.execute(
                            "select max(vouchercode) as vcode from vouchers"
                        )
                        vouchercode = vouchercodedata.fetchone()
                        recoresult = self.con.execute(
                            bankrecon.insert(),
                            [
                                {
                                    "vouchercode": int(vouchercode["vcode"]),
                                    "accountcode": crkeys,
                                    "orgcode": authDetails["orgcode"],
                                }
                            ],
                        )
                vchdata = self.con.execute(
                    "select max(vouchercode) as vcode from vouchers"
                )
                vchcode = vchdata.fetchone()
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "vouchercode": int(vchcode["vcode"]),
                    "vouchernumber": dataset["vouchernumber"],
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="POST", request_param="mode=auto", renderer="json")
    def addVoucherAuto(self):
        """
        Purpose:
        Adds a new reciept/payment voucher to an organisation
        This method is used if organisation has mode set to automatic
        Method requires a request with two dictionaries `vdetails` and
        `transactions`
        Contents of `vdetails`:
            * voucherdate
            * vouchertype
            * attachmentcount
            * attachment
            * narration
        Contents of `transactions`:
            * bamount: If transaction includes bank transfer
            * camount: If transaction includes cash transfer
            * payment_mode
            * party
        `vdetails` can be inserted into voucher table after crs and drs have
        been calculated
        """

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        authDetails = authCheck(token)
        if authDetails["auth"] is False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()

                dataset = self.request.json_body
                vdetails = dataset["vdetails"]
                transactions = dataset["transactions"]

                vdetails["orgcode"] = authDetails["orgcode"]
                payment_mode = transactions["payment_mode"]
                party_accCode = transactions["party"]

                if payment_mode in ["both", "bank"]:
                    bamount = transactions["bamount"]
                if payment_mode in ["both", "cash"]:
                    camount = transactions["camount"]
                if payment_mode == "both":
                    total_amount = "%.2f" % (float(bamount) + float(camount))

                # b_accCode is the user's default bank account code
                if payment_mode in ["both", "bank"]:
                    b_accCode = self.con.execute(
                        select([accounts.c.accountcode])
                        .where(accounts.c.defaultflag == 2)
                        .where(accounts.c.orgcode == int(vdetails["orgcode"]))
                    ).fetchone()[0]
                # c_accCode is the user's default cash account code
                if payment_mode in ["both", "cash"]:
                    c_accCode = self.con.execute(
                        select([accounts.c.accountcode])
                        .where(accounts.c.defaultflag == 3)
                        .where(accounts.c.orgcode == int(vdetails["orgcode"]))
                    ).fetchone()[0]

                # We define an internal function to calculate Dr & Cr
                # This function returns a tuple with two dictionaries
                # Which dictionary is Dr and which is Cr will depend on type of receipt
                def constructDrCr(mode):
                    if mode == "both":
                        return (
                            {b_accCode: bamount, c_accCode: camount},
                            {party_accCode: total_amount},
                        )
                    elif mode == "bank":
                        return ({b_accCode: bamount}, {party_accCode: bamount})
                    else:
                        return ({c_accCode: camount}, {party_accCode: camount})

                if vdetails["vouchertype"] == "receipt":
                    vdetails["drs"], vdetails["crs"] = constructDrCr(payment_mode)
                else:
                    vdetails["crs"], vdetails["drs"] = constructDrCr(payment_mode)

                # Database expects vouchernumber to be unicode encoded
                vdetails["vouchernumber"] = str(
                    self.__genVoucherNumber(
                        self.con, vdetails["vouchertype"], vdetails["orgcode"]
                    )
                )

                self.con.execute(vouchers.insert(), [vdetails])

                if payment_mode == "both":
                    self.con.execute(
                        "update accounts set vouchercount = vouchercount+1 where accountcode = %d"
                        % (int(b_accCode))
                    )
                    self.con.execute(
                        "update accounts set vouchercount = vouchercount+1 where accountcode = %d"
                        % (int(c_accCode))
                    )
                elif payment_mode == "bank":
                    self.con.execute(
                        "update accounts set vouchercount = vouchercount+1 where accountcode = %d"
                        % (int(b_accCode))
                    )
                else:
                    self.con.execute(
                        "update accounts set vouchercount = vouchercount+1 where accountcode = %d"
                        % (int(c_accCode))
                    )

                self.con.execute(
                    "update accounts set vouchercount = vouchercount+1 where accountcode = %d"
                    % (int(party_accCode))
                )

                vouchercodedata = self.con.execute(
                    "select max(vouchercode) as vcode from vouchers"
                )
                vouchercode = vouchercodedata.fetchone()
                if transactions["payment_mode"] in ["bank", "both"]:
                    self.con.execute(
                        bankrecon.insert(),
                        [
                            {
                                "vouchercode": int(vouchercode["vcode"]),
                                "accountcode": b_accCode,
                                "orgcode": authDetails["orgcode"],
                            }
                        ],
                    )
                return {
                    "gkstatus": enumdict["Success"],
                    "vouchercode": int(vouchercode["vcode"]),
                }
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="details=last", request_method="GET", renderer="json")
    def getLastVoucherDetails(self):
        try:
            """
            Purpose:
            gets a single voucher given it's voucher code.
            Returns a json dictionary containing that voucher.
            """
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(
                    select(
                        [
                            vouchers.c.vouchernumber,
                            vouchers.c.narration,
                            vouchers.c.voucherdate,
                        ]
                    ).where(
                        vouchers.c.vouchercode
                        == (
                            select([func.max(vouchers.c.vouchercode)]).where(
                                and_(
                                    vouchers.c.delflag == False,
                                    vouchers.c.vouchertype
                                    == self.request.params["type"],
                                    vouchers.c.orgcode == authDetails["orgcode"],
                                )
                            )
                        )
                    )
                )
                row = result.fetchone()
                if row == None:
                    voucher = {"vdate": "", "vno": "", "narration": ""}
                else:
                    voucher = {
                        "vdate": datetime.strftime((row["voucherdate"]), "%d-%m-%Y"),
                        "vno": row["vouchernumber"],
                        "narration": row["narration"],
                    }
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": voucher}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", renderer="json")
    def getVoucher(self):
        try:
            """
            Purpose:
            gets a single voucher given it's voucher code.
            Returns a json dictionary containing that voucher.
            """
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                voucherCode = self.request.params["code"]
                result = self.con.execute(
                    select(
                        [
                            vouchers.c.vouchercode,
                            vouchers.c.attachmentcount,
                            vouchers.c.vouchernumber,
                            vouchers.c.voucherdate,
                            vouchers.c.narration,
                            vouchers.c.drs,
                            vouchers.c.crs,
                            vouchers.c.prjcrs,
                            vouchers.c.prjdrs,
                            vouchers.c.vouchertype,
                            vouchers.c.lockflag,
                            vouchers.c.delflag,
                            vouchers.c.projectcode,
                            vouchers.c.orgcode,
                            vouchers.c.invid,
                            vouchers.c.instrumentno,
                            vouchers.c.bankname,
                            vouchers.c.branchname,
                            vouchers.c.instrumentdate,
                        ]
                    ).where(
                        and_(
                            vouchers.c.delflag == False,
                            vouchers.c.vouchercode == voucherCode,
                        )
                    )
                )
                row = result.fetchone()
                rawDr = dict(row["drs"])
                rawCr = dict(row["crs"])
                finalDR = {}
                finalCR = {}
                for d in list(rawDr.keys()):
                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(d)
                        )
                    )
                    account = accname.fetchone()
                    finalDR[account["accountname"]] = rawDr[d]

                for c in list(rawCr.keys()):
                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(c)
                        )
                    )
                    account = accname.fetchone()
                    finalCR[account["accountname"]] = rawCr[c]

                if row["narration"] == "null":
                    row["narration"] = ""
                voucher = {
                    "project": row["projectcode"],
                    "vouchercode": row["vouchercode"],
                    "attachmentcount": row["attachmentcount"],
                    "vouchernumber": row["vouchernumber"],
                    "voucherdate": datetime.strftime(row["voucherdate"], "%d-%m-%Y"),
                    "narration": row["narration"],
                    "drs": finalDR,
                    "crs": finalCR,
                    "prjdrs": row["prjdrs"],
                    "prjcrs": row["prjcrs"],
                    "vouchertype": row["vouchertype"],
                    "delflag": row["delflag"],
                    "orgcode": row["orgcode"],
                    "status": row["lockflag"],
                    "invid": row["invid"],
                    "instrumentno": row["instrumentno"],
                    "bankname": row["bankname"],
                    "branchname": row["branchname"],
                }
                if row["instrumentdate"]:
                    voucher["instrumentdate"] = datetime.strftime(
                        row["instrumentdate"], "%d-%m-%Y"
                    )
                else:
                    voucher["instrumentdate"] = ""
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": voucher,
                    "userrole": urole["userrole"],
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="searchby=type", renderer="json")
    def searchByType(self):
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
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                voucherType = self.request.params["vouchertype"]
                vouchersData = self.con.execute(
                    select(
                        [
                            vouchers.c.vouchercode,
                            vouchers.c.attachmentcount,
                            vouchers.c.vouchernumber,
                            vouchers.c.voucherdate,
                            vouchers.c.narration,
                            vouchers.c.drs,
                            vouchers.c.crs,
                            vouchers.c.prjcrs,
                            vouchers.c.prjdrs,
                            vouchers.c.vouchertype,
                            vouchers.c.lockflag,
                            vouchers.c.delflag,
                            vouchers.c.projectcode,
                            vouchers.c.orgcode,
                        ]
                    )
                    .where(
                        and_(
                            vouchers.c.orgcode == authDetails["orgcode"],
                            func.lower(vouchers.c.vouchertype)
                            == func.lower(voucherType),
                            vouchers.c.delflag == False,
                        )
                    )
                    .order_by(vouchers.c.voucherdate, vouchers.c.vouchercode)
                )
                voucherRecords = []

                for voucher in vouchersData:
                    rawDr = dict(voucher["drs"])
                    rawCr = dict(voucher["crs"])
                    finalDR = {}
                    finalCR = {}
                    tdr = 0.00
                    tcr = 0.00
                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(list(rawDr.keys())[0])
                        )
                    )
                    account = accname.fetchone()

                    if len(rawDr) > 1:
                        drcount = account["accountname"] + " + " + str(len(rawDr) - 1)

                        for d in rawDr:
                            tdr = tdr + float(rawDr[d])

                        finalDR["%s" % (drcount)] = tdr
                    else:
                        finalDR[account["accountname"]] = rawDr[list(rawDr.keys())[0]]

                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(list(rawCr.keys())[0])
                        )
                    )
                    account = accname.fetchone()

                    if len(rawCr) > 1:
                        crcount = account["accountname"] + " + " + str(len(rawCr) - 1)

                        for d in rawCr:
                            tcr = tcr + float(rawCr[d])
                        finalCR["%s" % (crcount)] = tcr
                    else:
                        finalCR[account["accountname"]] = rawCr[list(rawCr.keys())[0]]
                    if voucher["narration"] == "null":
                        voucher["narration"] = ""

                    voucherRecords.append(
                        {
                            "vouchercode": voucher["vouchercode"],
                            "attachmentcount": voucher["attachmentcount"],
                            "vouchernumber": voucher["vouchernumber"],
                            "voucherdate": datetime.strftime(
                                voucher["voucherdate"], "%d-%m-%Y"
                            ),
                            "narration": voucher["narration"],
                            "drs": finalDR,
                            "crs": finalCR,
                            "prjdrs": voucher["prjdrs"],
                            "prjcrs": voucher["prjcrs"],
                            "vouchertype": voucher["vouchertype"],
                            "delflag": voucher["delflag"],
                            "orgcode": voucher["orgcode"],
                            "status": voucher["lockflag"],
                        }
                    )
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": voucherRecords,
                    "userrole": urole["userrole"],
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(
        request_method="GET", request_param="searchby=invoice", renderer="json"
    )
    def searchByInvoice(self):
        # Purpose: To get vouchers details by using invoice id (invid).
        # Used in view invoice to get voucher of that invoice.
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
                voucherRecords = getInvVouchers(
                    self.con, authDetails["orgcode"], self.request.params["invid"]
                )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": voucherRecords}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="searchby=vnum", renderer="json")
    def searchByVoucherNumber(self):
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
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                voucherNo = self.request.params["voucherno"]
                vouchersData = self.con.execute(
                    select(
                        [
                            vouchers.c.vouchercode,
                            vouchers.c.attachmentcount,
                            vouchers.c.vouchernumber,
                            vouchers.c.voucherdate,
                            vouchers.c.narration,
                            vouchers.c.drs,
                            vouchers.c.crs,
                            vouchers.c.prjcrs,
                            vouchers.c.prjdrs,
                            vouchers.c.vouchertype,
                            vouchers.c.lockflag,
                            vouchers.c.delflag,
                            vouchers.c.projectcode,
                            vouchers.c.orgcode,
                        ]
                    )
                    .where(
                        and_(
                            vouchers.c.orgcode == authDetails["orgcode"],
                            func.lower(vouchers.c.vouchernumber)
                            == func.lower(voucherNo),
                            vouchers.c.delflag == False,
                        )
                    )
                    .order_by(vouchers.c.voucherdate, vouchers.c.vouchercode)
                )
                voucherRecords = []

                for voucher in vouchersData:
                    rawDr = dict(voucher["drs"])
                    rawCr = dict(voucher["crs"])
                    finalDR = {}
                    finalCR = {}
                    tdr = 0.00
                    tcr = 0.00

                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(list(rawDr.keys())[0])
                        )
                    )
                    account = accname.fetchone()

                    if len(rawDr) > 1:
                        drcount = account["accountname"] + " + " + str(len(rawDr) - 1)

                        for d in rawDr:
                            tdr = tdr + float(rawDr[d])

                        finalDR["%s" % (drcount)] = tdr
                    else:
                        finalDR[account["accountname"]] = rawDr[list(rawDr.keys())[0]]

                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(list(rawCr.keys())[0])
                        )
                    )
                    account = accname.fetchone()

                    if len(rawCr) > 1:
                        crcount = account["accountname"] + " + " + str(len(rawCr) - 1)

                        for d in rawCr:
                            tcr = tcr + float(rawCr[d])
                        finalCR["%s" % (crcount)] = tcr
                    else:
                        finalCR[account["accountname"]] = rawCr[list(rawCr.keys())[0]]
                    if voucher["narration"] == "null":
                        voucher["narration"] = ""
                    voucherRecords.append(
                        {
                            "vouchercode": voucher["vouchercode"],
                            "attachmentcount": voucher["attachmentcount"],
                            "vouchernumber": voucher["vouchernumber"],
                            "voucherdate": datetime.strftime(
                                voucher["voucherdate"], "%d-%m-%Y"
                            ),
                            "narration": voucher["narration"],
                            "drs": finalDR,
                            "crs": finalCR,
                            "prjdrs": voucher["prjdrs"],
                            "prjcrs": voucher["prjcrs"],
                            "vouchertype": voucher["vouchertype"],
                            "delflag": voucher["delflag"],
                            "orgcode": voucher["orgcode"],
                            "status": voucher["lockflag"],
                        }
                    )
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": voucherRecords,
                    "userrole": urole["userrole"],
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="searchby=amount", renderer="json")
    def searchByAmount(self):
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
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                voucherAmount = self.request.params["total"]
                vouchersData = self.con.execute(
                    select([vouchers.c.vouchercode, vouchers.c.drs])
                    .where(
                        and_(
                            vouchers.c.orgcode == authDetails["orgcode"],
                            vouchers.c.delflag == False,
                        )
                    )
                    .order_by(vouchers.c.voucherdate, vouchers.c.vouchercode)
                )
                voucherRecords = []

                for vr in vouchersData:
                    total = 0.00
                    drs = dict(vr["drs"])
                    for d in list(drs.keys()):
                        total = total + float(drs[d])
                    if total == float(voucherAmount):
                        voucherDetailsData = self.con.execute(
                            select(
                                [
                                    vouchers.c.vouchercode,
                                    vouchers.c.attachmentcount,
                                    vouchers.c.vouchernumber,
                                    vouchers.c.voucherdate,
                                    vouchers.c.narration,
                                    vouchers.c.drs,
                                    vouchers.c.crs,
                                    vouchers.c.prjcrs,
                                    vouchers.c.prjdrs,
                                    vouchers.c.vouchertype,
                                    vouchers.c.lockflag,
                                    vouchers.c.delflag,
                                    vouchers.c.projectcode,
                                    vouchers.c.orgcode,
                                ]
                            ).where(vouchers.c.vouchercode == vr["vouchercode"])
                        )
                        voucher = voucherDetailsData.fetchone()
                        rawDr = dict(voucher["drs"])
                        rawCr = dict(voucher["crs"])
                        finalDR = {}
                        finalCR = {}
                        tdr = 0.00
                        tcr = 0.00
                        accname = self.con.execute(
                            select([accounts.c.accountname]).where(
                                accounts.c.accountcode == int(list(rawDr.keys())[0])
                            )
                        )
                        account = accname.fetchone()

                        if len(rawDr) > 1:
                            drcount = (
                                account["accountname"] + " + " + str(len(rawDr) - 1)
                            )

                            for d in rawDr:
                                tdr = tdr + float(rawDr[d])

                            finalDR["%s" % (drcount)] = tdr
                        else:
                            finalDR[account["accountname"]] = rawDr[
                                list(rawDr.keys())[0]
                            ]

                        accname = self.con.execute(
                            select([accounts.c.accountname]).where(
                                accounts.c.accountcode == int(list(rawCr.keys())[0])
                            )
                        )
                        account = accname.fetchone()

                        if len(rawCr) > 1:
                            crcount = (
                                account["accountname"] + " + " + str(len(rawCr) - 1)
                            )

                            for d in rawCr:
                                tcr = tcr + float(rawCr[d])
                            finalCR["%s" % (crcount)] = tcr
                        else:
                            finalCR[account["accountname"]] = rawCr[
                                list(rawCr.keys())[0]
                            ]
                        if voucher["narration"] == "null":
                            voucher["narration"] = ""
                        voucherRecords.append(
                            {
                                "vouchercode": voucher["vouchercode"],
                                "attachmentcount": voucher["attachmentcount"],
                                "vouchernumber": voucher["vouchernumber"],
                                "voucherdate": datetime.strftime(
                                    voucher["voucherdate"], "%d-%m-%Y"
                                ),
                                "narration": voucher["narration"],
                                "drs": finalDR,
                                "crs": finalCR,
                                "prjdrs": voucher["prjdrs"],
                                "prjcrs": voucher["prjcrs"],
                                "vouchertype": voucher["vouchertype"],
                                "delflag": voucher["delflag"],
                                "orgcode": voucher["orgcode"],
                                "status": voucher["lockflag"],
                            }
                        )

                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": voucherRecords,
                    "userrole": urole["userrole"],
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="searchby=date", renderer="json")
    def searchByDate(self):
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
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                fromDate = self.request.params["from"]
                toDate = self.request.params["to"]
                vouchersData = self.con.execute(
                    select(
                        [
                            vouchers.c.vouchercode,
                            vouchers.c.attachmentcount,
                            vouchers.c.vouchernumber,
                            vouchers.c.voucherdate,
                            vouchers.c.narration,
                            vouchers.c.drs,
                            vouchers.c.crs,
                            vouchers.c.prjcrs,
                            vouchers.c.prjdrs,
                            vouchers.c.vouchertype,
                            vouchers.c.lockflag,
                            vouchers.c.delflag,
                            vouchers.c.projectcode,
                            vouchers.c.orgcode,
                        ]
                    )
                    .where(
                        and_(
                            vouchers.c.orgcode == authDetails["orgcode"],
                            between(vouchers.c.voucherdate, fromDate, toDate),
                            vouchers.c.delflag == False,
                        )
                    )
                    .order_by(vouchers.c.voucherdate, vouchers.c.vouchercode)
                )
                voucherRecords = []

                for voucher in vouchersData:
                    rawDr = dict(voucher["drs"])
                    rawCr = dict(voucher["crs"])
                    finalDR = {}
                    finalCR = {}
                    tdr = 0.00
                    tcr = 0.00
                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(list(rawDr.keys())[0])
                        )
                    )
                    account = accname.fetchone()

                    if len(rawDr) > 1:
                        drcount = account["accountname"] + " + " + str(len(rawDr) - 1)

                        for d in rawDr:
                            tdr = tdr + float(rawDr[d])

                        finalDR["%s" % (drcount)] = tdr
                    else:
                        finalDR[account["accountname"]] = rawDr[list(rawDr.keys())[0]]

                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(list(rawCr.keys())[0])
                        )
                    )
                    account = accname.fetchone()

                    if len(rawCr) > 1:
                        crcount = account["accountname"] + " + " + str(len(rawCr) - 1)

                        for d in rawCr:
                            tcr = tcr + float(rawCr[d])
                        finalCR["%s" % (crcount)] = tcr
                    else:
                        finalCR[account["accountname"]] = rawCr[list(rawCr.keys())[0]]
                    if voucher["narration"] == "null":
                        voucher["narration"] = ""
                    voucherRecords.append(
                        {
                            "vouchercode": voucher["vouchercode"],
                            "attachmentcount": voucher["attachmentcount"],
                            "vouchernumber": voucher["vouchernumber"],
                            "voucherdate": datetime.strftime(
                                voucher["voucherdate"], "%d-%m-%Y"
                            ),
                            "narration": voucher["narration"],
                            "drs": finalDR,
                            "crs": finalCR,
                            "prjdrs": voucher["prjdrs"],
                            "prjcrs": voucher["prjcrs"],
                            "vouchertype": voucher["vouchertype"],
                            "delflag": voucher["delflag"],
                            "orgcode": voucher["orgcode"],
                            "status": voucher["lockflag"],
                        }
                    )
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": voucherRecords,
                    "userrole": urole["userrole"],
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(
        request_method="GET", request_param="searchby=narration", renderer="json"
    )
    def searchByNarration(self):
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
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                voucherNarration = self.request.params["nartext"]
                vouchersData = self.con.execute(
                    select(
                        [
                            vouchers.c.vouchercode,
                            vouchers.c.attachmentcount,
                            vouchers.c.vouchernumber,
                            vouchers.c.voucherdate,
                            vouchers.c.narration,
                            vouchers.c.drs,
                            vouchers.c.crs,
                            vouchers.c.prjcrs,
                            vouchers.c.prjdrs,
                            vouchers.c.vouchertype,
                            vouchers.c.lockflag,
                            vouchers.c.delflag,
                            vouchers.c.projectcode,
                            vouchers.c.orgcode,
                        ]
                    )
                    .where(
                        and_(
                            vouchers.c.orgcode == authDetails["orgcode"],
                            func.lower(vouchers.c.narration).like(
                                "%" + func.lower(voucherNarration) + "%"
                            ),
                            vouchers.c.delflag == False,
                        )
                    )
                    .order_by(vouchers.c.voucherdate, vouchers.c.vouchercode)
                )
                voucherRecords = []

                for voucher in vouchersData:
                    rawDr = dict(voucher["drs"])
                    rawCr = dict(voucher["crs"])
                    finalDR = {}
                    finalCR = {}
                    tdr = 0.00
                    tcr = 0.00
                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(list(rawDr.keys())[0])
                        )
                    )
                    account = accname.fetchone()

                    if len(rawDr) > 1:
                        drcount = account["accountname"] + " + " + str(len(rawDr) - 1)

                        for d in rawDr:
                            tdr = tdr + float(rawDr[d])

                        finalDR["%s" % (drcount)] = tdr
                    else:
                        finalDR[account["accountname"]] = rawDr[list(rawDr.keys())[0]]

                    accname = self.con.execute(
                        select([accounts.c.accountname]).where(
                            accounts.c.accountcode == int(list(rawCr.keys())[0])
                        )
                    )
                    account = accname.fetchone()

                    if len(rawCr) > 1:
                        crcount = account["accountname"] + " + " + str(len(rawCr) - 1)

                        for d in rawCr:
                            tcr = tcr + float(rawCr[d])
                        finalCR["%s" % (crcount)] = tcr
                    else:
                        finalCR[account["accountname"]] = rawCr[list(rawCr.keys())[0]]
                    if voucher["narration"] == "null":
                        voucher["narration"] = ""
                    voucherRecords.append(
                        {
                            "vouchercode": voucher["vouchercode"],
                            "attachmentcount": voucher["attachmentcount"],
                            "vouchernumber": voucher["vouchernumber"],
                            "voucherdate": datetime.strftime(
                                voucher["voucherdate"], "%d-%m-%Y"
                            ),
                            "narration": voucher["narration"],
                            "drs": finalDR,
                            "crs": finalCR,
                            "prjdrs": voucher["prjdrs"],
                            "prjcrs": voucher["prjcrs"],
                            "vouchertype": voucher["vouchertype"],
                            "delflag": voucher["delflag"],
                            "orgcode": voucher["orgcode"],
                            "status": voucher["lockflag"],
                        }
                    )
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": voucherRecords,
                    "userrole": urole["userrole"],
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="attach=image", renderer="json")
    def getattachment(self):
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
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                voucherCode = self.request.params["vouchercode"]
                vouchersData = self.con.execute(
                    select([vouchers.c.attachment, vouchers.c.lockflag]).where(
                        and_(vouchers.c.vouchercode == voucherCode)
                    )
                )
                attachment = vouchersData.fetchone()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": attachment["attachment"],
                    "lockflag": attachment["lockflag"],
                    "userrole": urole["userrole"],
                }
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="PUT", renderer="json")
    def updateVoucher(self):
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
                dataset = self.request.json_body
                if "lockflag" in dataset:
                    if dataset["lockflag"] == "True":
                        dataset["lockflag"] = True
                    else:
                        dataset["lockflag"] = False
                    result = self.con.execute(
                        vouchers.update()
                        .where(vouchers.c.vouchercode == dataset["vouchercode"])
                        .values(dataset)
                    )
                else:
                    result = self.con.execute(
                        vouchers.update()
                        .where(vouchers.c.lockflag == "f")
                        .where(vouchers.c.vouchercode == dataset["vouchercode"])
                        .values(dataset)
                    )
                if "drs" in dataset:
                    drs = dataset["drs"]
                    crs = dataset["crs"]
                    delrecoresult = self.con.execute(
                        "delete from bankrecon where vouchercode = %d"
                        % (int(dataset["vouchercode"]))
                    )
                    for drkeys in list(drs.keys()):
                        accgrpdata = self.con.execute(
                            select(
                                [groupsubgroups.c.groupname, groupsubgroups.c.groupcode]
                            ).where(
                                groupsubgroups.c.groupcode
                                == (
                                    select([accounts.c.groupcode]).where(
                                        accounts.c.accountcode == int(drkeys)
                                    )
                                )
                            )
                        )
                        accgrp = accgrpdata.fetchone()
                        if accgrp["groupname"] == "Bank":
                            vouchercode = dataset["vouchercode"]
                            recoresult = self.con.execute(
                                bankrecon.insert(),
                                [
                                    {
                                        "vouchercode": int(vouchercode),
                                        "accountcode": drkeys,
                                        "orgcode": authDetails["orgcode"],
                                    }
                                ],
                            )
                    for crkeys in list(crs.keys()):
                        accgrpdata = self.con.execute(
                            select(
                                [groupsubgroups.c.groupname, groupsubgroups.c.groupcode]
                            ).where(
                                groupsubgroups.c.groupcode
                                == (
                                    select([accounts.c.groupcode]).where(
                                        accounts.c.accountcode == int(crkeys)
                                    )
                                )
                            )
                        )
                        accgrp = accgrpdata.fetchone()
                        if accgrp["groupname"] == "Bank":
                            vouchercode = dataset["vouchercode"]
                            recoresult = self.con.execute(
                                bankrecon.insert(),
                                [
                                    {
                                        "vouchercode": int(vouchercode),
                                        "accountcode": crkeys,
                                        "orgcode": authDetails["orgcode"],
                                    }
                                ],
                            )
                self.con.close()
                return {"gkstatus": enumdict["Success"]}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="DELETE", renderer="json")
    def deleteVoucher(self):
        """
        Purpose:
        Deletes a voucher given it's voucher code.
        Returns success if deletion is successful.
        Purpose:
        This function deletes a given voucher with it's vouchercode as input.
        After deleting the voucher, the vouchercount for the involved accounts on Dr and Cr side is decremented by 1.
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
                dataset = self.request.json_body
                vcode = int(dataset["vouchercode"])
                orgcode = authDetails["orgcode"]
                deletestatus = deleteVoucherFun(vcode, orgcode)
                return deletestatus
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}

    # Get all data of all vouchers for certain period.
    @view_config(request_method="GET", request_param="getdataby=date", renderer="json")
    def getAllDataByDate(self):
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
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                fromDate = self.request.params["from"]
                toDate = self.request.params["to"]
                vouchersData = self.con.execute(
                    select(
                        [
                            vouchers.c.vouchercode,
                            vouchers.c.attachmentcount,
                            vouchers.c.vouchernumber,
                            vouchers.c.voucherdate,
                            vouchers.c.narration,
                            vouchers.c.drs,
                            vouchers.c.crs,
                            vouchers.c.vouchertype,
                            vouchers.c.orgcode,
                        ]
                    )
                    .where(
                        and_(
                            vouchers.c.orgcode == authDetails["orgcode"],
                            between(vouchers.c.voucherdate, fromDate, toDate),
                            vouchers.c.delflag == False,
                        )
                    )
                    .order_by(vouchers.c.voucherdate, vouchers.c.vouchercode)
                )
                voucherRecords = []

                for voucher in vouchersData:
                    rawDr = dict(voucher["drs"])
                    rawCr = dict(voucher["crs"])
                    finalDR = {}
                    finalCR = {}
                    for Dac in list(rawDr.keys()):
                        accname = self.con.execute(
                            select([accounts.c.accountname]).where(
                                accounts.c.accountcode == int(Dac)
                            )
                        )
                        account = accname.fetchone()
                        finalDR[account["accountname"]] = rawDr[Dac]
                    for Cac in list(rawCr.keys()):
                        accname = self.con.execute(
                            select([accounts.c.accountname]).where(
                                accounts.c.accountcode == int(Cac)
                            )
                        )
                        account = accname.fetchone()
                        finalCR[account["accountname"]] = rawCr[Cac]
                    if voucher["narration"] == "null":
                        voucher["narration"] = ""
                    voucherRecords.append(
                        {
                            "vouchercode": voucher["vouchercode"],
                            "attachmentcount": voucher["attachmentcount"],
                            "voucherno": voucher["vouchernumber"],
                            "voucherdate": datetime.strftime(
                                voucher["voucherdate"], "%Y-%m-%d"
                            ),
                            "narration": voucher["narration"],
                            "drs": finalDR,
                            "crs": finalCR,
                            "vouchertype": voucher["vouchertype"],
                            "orgcode": voucher["orgcode"],
                        }
                    )
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": voucherRecords,
                    "userrole": urole["userrole"],
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
