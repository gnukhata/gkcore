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
  Free Software Foundation, Inc.,51 Franklin Street, 
  Fifth Floor, Boston, MA 02110, United States


Contributors:
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"Prajkta Patkar" <prajakta@dff.org.in>
"Nitesh Chaughule" <nitesh@disroot.org>
"""

from gkcore import eng, enumdict
from gkcore.utils import authCheck
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, alias, or_, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.ext.baked import Result
from sqlalchemy.sql.expression import null
from gkcore.models.gkdb import accounts
from datetime import datetime, date
from gkcore.views.api_gkuser import getUserRole

"""
purpose:
This class is the resource to create, update, read and delete accounts.

connection rules:
con is used for executing sql expression language based queries,
while eng is used for raw sql execution.
routing mechanism:
@view_defaults is used for setting the default route for crud on the given resource class.
if specific route is to be attached to a certain method, or for giving get, post, put, delete methods to default route, the view_config decorator is used.
For other predicates view_config is generally used.
"""
"""
default route to be attached to this resource.
refer to the __init__.py of main gkcore package for details on routing url
"""


def reset_acc_defaults(con, orgcode):
    acc_list = con.execute(
        select([accounts.c.accountcode, accounts.c.accountname]).where(
            accounts.c.orgcode == orgcode
        )
    ).fetchall()
    default_acc = {
        "Bank A/C": 2,
        "Cash in hand": 3,
        "Purchase A/C": 16,
        "Sale A/C": 19,
        "Round Off Paid": 180,
        "Round Off Received": 181,
    }
    for acc in acc_list:
        default_code = 0
        if acc["accountname"] in default_acc:
            default_code = default_acc[acc["accountname"]]
        con.execute(
            accounts.update()
            .where(accounts.c.accountcode == acc["accountcode"])
            .values(defaultflag=default_code)
        )


@view_defaults(route_name="accounts")
class api_account(object):
    # constructor will initialise request.
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print("accounts initialized")

    @view_config(request_method="POST", renderer="json")
    def addAccount(self):
        """
                purpose:
                Adds an account under either a group or it's subgroup.

                Request_method is post which means adding a resource.

                returns a json object containing success result as true if account is created.

                Alchemy expression language will be used for inserting into accounts table.

                The data is fetched from request.json_body.

                Expects accountname,groupsubgroupcode and opening balance.

                Function will only proceed if auth check is successful, because orgcode needed as a common parameter can be procured only through the said method.

                If new accounts are added under sub-group 'Bank' or 'Cash' with defaultflag '2' or '3' respectively then existing account with
        defaultflag '2' or '3' set to the '0'.
                If new accounts are added under sub-group 'Purchase' or 'Sales' with defaultflag '16' or '19' respectively then existing account with defaultflag '16' or '19' set to the '0'.
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
                newdataset = self.request.json_body
                dataset = {}
                if "gkdata" in newdataset:
                    dataset = newdataset["gkdata"]
                if "accountname" in newdataset:
                    dataset = newdataset
                dataset["orgcode"] = authDetails["orgcode"]
                if "defaultflag" in dataset:
                    dflag = dataset["defaultflag"]
                    grpnames = self.con.execute(
                        select([gkdb.groupsubgroups.c.groupname]).where(
                            and_(
                                gkdb.groupsubgroups.c.groupcode == dataset["groupcode"],
                                gkdb.groupsubgroups.c.orgcode == dataset["orgcode"],
                            )
                        )
                    )
                    grpname = grpnames.fetchone()
                    if grpname["groupname"] == "Bank" and dflag == 2:
                        setdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=2 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Cash" and dflag == 3:
                        setdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=3 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Purchase" and dflag == 16:
                        setdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=16 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Sales" and dflag == 19:
                        setdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=19 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Indirect Expense" and dflag == 180:
                        setROPdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=180 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Indirect Income" and dflag == 181:
                        setRORdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=181 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                result = self.con.execute(gkdb.accounts.insert(), [dataset])
                if "moredata" in newdataset and len(newdataset["moredata"]) > 0:
                    moredata = newdataset["moredata"]
                    moredata["orgcode"] = authDetails["orgcode"]
                    result = self.con.execute(
                        gkdb.customerandsupplier.insert(), [moredata]
                    )
                    logdata = {}
                    logdata["orgcode"] = authDetails["orgcode"]
                    logdata["userid"] = authDetails["userid"]
                    logdata["time"] = datetime.today().strftime("%Y-%m-%d")
                    if int(moredata["csflag"]) == 3:
                        logdata["activity"] = moredata["custname"] + " customer created"
                    else:
                        logdata["activity"] = moredata["custname"] + " supplier created"
                    result = self.con.execute(gkdb.log.insert(), [logdata])

                self.con.close()
                return {"gkstatus": enumdict["Success"]}
            except exc.IntegrityError:
                self.con.close()
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="account", request_method="GET", renderer="json")
    def getAccount(self):
        """
        Purpose:
        Returns an account given it's account code.
        Returns a json object containing:
        *accountcode
        *accountname
        *openingbal as float
        *groupsubgroupcode
        The request_method is  get meaning retriving data.
        The route_name has been override here to make a special call which does not come under view_default.
        parameter will be taken from request.matchdict in a get request.
        Function will only proceed if auth check is successful, because orgcode needed as a common parameter can be procured only through the said method.
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
                result = self.con.execute(
                    select([gkdb.accounts]).where(
                        gkdb.accounts.c.accountcode
                        == self.request.matchdict["accountcode"]
                    )
                )
                row = result.fetchone()
                acc = {
                    "accountcode": row["accountcode"],
                    "accountname": row["accountname"],
                    "openingbal": "%.2f" % float(row["openingbal"]),
                    "groupcode": row["groupcode"],
                    "defaultflag": row["defaultflag"],
                }
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": acc}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=getAccCode", request_method="GET", renderer="json")
    def getCodeofAccount(self):
        """
        Purpose:
        Returns an account code given it's account name.
        The request_method is  get meaning retriving data.
        The route_name has been override here to make a special call which does not come under view_default.
        parameter will be taken from request.matchdict in a get request.
        Function will only proceed if auth check is successful, because orgcode needed as a common parameter can be procured only through the said method.
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
                result = self.con.execute(
                    select([gkdb.accounts.c.accountcode]).where(
                        and_(
                            gkdb.accounts.c.accountname
                            == self.request.params["accountname"],
                            gkdb.accounts.c.orgcode == authDetails["orgcode"],
                        )
                    )
                )
                accountcode = result.fetchone()
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "accountcode": accountcode["accountcode"],
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", renderer="json")
    def getAllAccounts(self):
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
                result = self.con.execute(
                    select([gkdb.accounts])
                    .where(gkdb.accounts.c.orgcode == authDetails["orgcode"])
                    .order_by(gkdb.accounts.c.accountname)
                )
                accs = []
                srno = 1
                default_acc = {
                    0: "",
                    2: "Bank Transaction",
                    3: "Cash Transaction",
                    16: "Purchase Tansaction",
                    19: "Sale Transaction",
                    180: "Round Off Paid",
                    181: "Round Off Received",
                }  # it is use for default flag
                for accrow in result:
                    g = gkdb.groupsubgroups.alias("g")
                    sg = gkdb.groupsubgroups.alias("sg")

                    defaultflag = default_acc[accrow["defaultflag"]]
                    resultset = self.con.execute(
                        select(
                            [
                                (g.c.groupcode).label("groupcode"),
                                (g.c.groupname).label("groupname"),
                                (sg.c.groupcode).label("subgroupcode"),
                                (sg.c.groupname).label("subgroupname"),
                            ]
                        ).where(
                            or_(
                                and_(
                                    g.c.groupcode == int(accrow["groupcode"]),
                                    g.c.subgroupof == null(),
                                    sg.c.groupcode == int(accrow["groupcode"]),
                                    sg.c.subgroupof == null(),
                                ),
                                and_(
                                    g.c.groupcode == sg.c.subgroupof,
                                    sg.c.groupcode == int(accrow["groupcode"]),
                                ),
                            )
                        )
                    )
                    grprow = resultset.fetchone()
                    if grprow["groupcode"] == grprow["subgroupcode"]:
                        accs.append(
                            {
                                "srno": srno,
                                "accountcode": accrow["accountcode"],
                                "accountname": accrow["accountname"],
                                "openingbal": "%.2f" % float(accrow["openingbal"]),
                                "groupcode": grprow["groupcode"],
                                "groupname": grprow["groupname"],
                                "subgroupcode": "",
                                "subgroupname": "",
                                "sysaccount": accrow["sysaccount"],
                                "defaultflag": defaultflag,
                            }
                        )

                    else:
                        accs.append(
                            {
                                "srno": srno,
                                "accountcode": accrow["accountcode"],
                                "accountname": accrow["accountname"],
                                "openingbal": "%.2f" % float(accrow["openingbal"]),
                                "groupcode": grprow["groupcode"],
                                "groupname": grprow["groupname"],
                                "subgroupcode": grprow["subgroupcode"],
                                "subgroupname": grprow["subgroupname"],
                                "sysaccount": accrow["sysaccount"],
                                "defaultflag": defaultflag,
                            }
                        )
                    srno = srno + 1
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": accs}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="accbygrp", renderer="json")
    def getAllAccountsByGroup(self):
        """
        Purpose:
        This function returns accountcode , accountname and openingbalance for a certain groupcode (group) which has been provided.
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
                result = self.con.execute(
                    select(
                        [
                            accounts.c.accountcode,
                            accounts.c.accountname,
                            accounts.c.openingbal,
                        ]
                    ).where(
                        and_(
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == self.request.params["groupcode"],
                        )
                    )
                )
                accData = result.fetchall()
                allAcc = []
                for row in accData:
                    allAcc.append(
                        {
                            "accountcode": row["accountcode"],
                            "accountname": row["accountname"],
                            "openingbal": "%.2f" % float(row["openingbal"]),
                        }
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": allAcc}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="acclist", renderer="json")
    def getAccountslist(self):
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
                accData = self.con.execute(
                    select([accounts.c.accountcode, accounts.c.accountname]).where(
                        accounts.c.orgcode == authDetails["orgcode"]
                    )
                )
                accRows = accData.fetchall()
                accList = {}
                for row in accRows:
                    accList[row["accountname"]] = row["accountcode"]

                return {"gkstatus": enumdict["Success"], "gkresult": accList}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="find=exists", renderer="json")
    def accountExists(self):
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
                accountname = self.request.params["accountname"]
                result = self.con.execute(
                    select(
                        [func.count(gkdb.accounts.c.accountname).label("acc")]
                    ).where(
                        and_(
                            gkdb.accounts.c.accountname == accountname,
                            gkdb.accounts.c.orgcode == authDetails["orgcode"],
                        )
                    )
                )
                acccount = result.fetchone()
                if acccount["acc"] > 0:
                    self.con.close()
                    return {"gkstatus": enumdict["DuplicateEntry"]}
                else:
                    self.con.close()
                    return {"gkstatus": enumdict["Success"]}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    """
    If account is updated under sub-group 'Bank' or 'Cash' with defaultflag '2' or '3' respectively then existing account with 
defaultflag '2' or '3' set to the '0'.
    If account is updated under sub-group 'Purchase' or 'Sales' with defaultflag '16' or '19' respectively then existing account with 
defaultflag '16' or '19' set to the '0'.
    """

    @view_config(request_method="PUT", renderer="json")
    def editAccount(self):
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
                newdataset = self.request.json_body
                dataset = newdataset["gkdata"]
                dataset["orgcode"] = authDetails["orgcode"]
                # To update defaultflag check whether key exists and then update only those accounts which are under the respective group.
                if "defaultflag" in dataset:
                    dflag = dataset["defaultflag"]
                    grpnames = self.con.execute(
                        select([gkdb.groupsubgroups.c.groupname]).where(
                            and_(
                                gkdb.groupsubgroups.c.groupcode == dataset["groupcode"],
                                gkdb.groupsubgroups.c.orgcode == dataset["orgcode"],
                            )
                        )
                    )
                    grpname = grpnames.fetchone()
                    if grpname["groupname"] == "Bank" and dflag == 2:
                        setdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=2 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Cash" and dflag == 3:
                        setdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=3 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Purchase" and dflag == 16:
                        setdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=16 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Sales" and dflag == 19:
                        setdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=19 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Indirect Expense" and dflag == 180:
                        setROPdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=180 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )
                    if grpname["groupname"] == "Indirect Income" and dflag == 181:
                        setRORdflag = self.con.execute(
                            "update accounts set defaultflag=0 where defaultflag=181 and orgcode=%d"
                            % int(authDetails["orgcode"])
                        )

                accPrevName = self.con.execute(
                    select([gkdb.accounts.c.accountname]).where(
                        gkdb.accounts.c.accountcode == dataset["accountcode"]
                    )
                )
                accountName = accPrevName.fetchone()
                result = self.con.execute(
                    gkdb.accounts.update()
                    .where(gkdb.accounts.c.accountcode == dataset["accountcode"])
                    .values(dataset)
                )

                # custsupflag is 1 only when sub groub of selected account for edit is Sundry Debtors or Sundry Creditors for Purchase.
                if newdataset["custsupflag"] == 1:
                    custdataset = {}
                    custdataset["orgcode"] = authDetails["orgcode"]
                    custnamelist = self.con.execute(
                        "select exists(select 1 from customerandsupplier where orgcode =%d and custname='%s')"
                        % (authDetails["orgcode"], newdataset["oldcustname"])
                    )
                    listcust = custnamelist.fetchone()
                    # this condition is true when account name is match with custsup name.
                    if listcust[0] == True:
                        # to fetch custid  using custname.
                        fcustid = self.con.execute(
                            select([gkdb.customerandsupplier.c.custid]).where(
                                and_(
                                    gkdb.customerandsupplier.c.orgcode
                                    == authDetails["orgcode"],
                                    gkdb.customerandsupplier.c.custname
                                    == newdataset["oldcustname"],
                                )
                            )
                        )
                        fetchcustname = fcustid.fetchone()
                        custid = fetchcustname["custid"]
                        # if custsup data already filled at time of create acount and then update.
                        if "moredata" in newdataset:
                            custdataset = newdataset["moredata"]
                            del custdataset["oldcustname"]
                        else:
                            # if change are only in account name then only custsup name will change at this time 'moredata' field is absent in newdataset.
                            custdataset["custname"] = dataset["accountname"]
                        # update custsup data
                        result = self.con.execute(
                            gkdb.customerandsupplier.update()
                            .where(gkdb.customerandsupplier.c.custid == custid)
                            .values(custdataset)
                        )
                        if (
                            "moredata" in newdataset
                            and "bankdetails" not in custdataset
                        ):
                            # if bankdetails are null, set bankdetails as null in database.
                            self.con.execute(
                                "update customerandsupplier set bankdetails = NULL where bankdetails is NOT NULL and custid = %d"
                                % int(custid)
                            )
                        if "moredata" in newdataset and "gstin" not in custdataset:
                            # if gstin are null, set gstin as null in database.
                            self.con.execute(
                                "update customerandsupplier set gstin = NULL where gstin is NOT NULL and custid = %d"
                                % int(custid)
                            )
                    # when custsup details filled at the time of edit account.
                    elif "moredata" in newdataset:
                        custdataset = newdataset["moredata"]
                        custdataset["orgcode"] = authDetails["orgcode"]
                        result = self.con.execute(
                            gkdb.customerandsupplier.insert(), [custdataset]
                        )
                        logdata = {}
                        logdata["orgcode"] = authDetails["orgcode"]
                        logdata["userid"] = authDetails["userid"]
                        logdata["time"] = datetime.today().strftime("%Y-%m-%d")
                        if int(custdataset["csflag"]) == 3:
                            logdata["activity"] = (
                                custdataset["custname"] + " customer created"
                            )
                        else:
                            logdata["activity"] = (
                                custdataset["custname"] + " supplier created"
                            )
                        result = self.con.execute(gkdb.log.insert(), [logdata])

                self.con.close()
                return {"gkstatus": enumdict["Success"]}
            except exc.IntegrityError:
                self.con.close()
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="DELETE", renderer="json")
    def deleteAccount(self):
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
                userRoleData = getUserRole(
                    authDetails["userid"], authDetails["orgcode"]
                )
                userRole = userRoleData["gkresult"]["userrole"]
                dataset = self.request.json_body
                if userRole == -1:
                    vouchercountdata = self.con.execute(
                        select([gkdb.accounts.c.vouchercount]).where(
                            gkdb.accounts.c.accountcode == dataset["accountcode"]
                        )
                    )
                    vouchercountrow = vouchercountdata.fetchone()
                    if vouchercountrow["vouchercount"] != 0:
                        self.con.close()
                        return {"gkstatus": enumdict["ActionDisallowed"]}
                    else:
                        result = self.con.execute(
                            gkdb.accounts.delete().where(
                                gkdb.accounts.c.accountcode == dataset["accountcode"]
                            )
                        )
                        self.con.close()
                        return {"gkstatus": enumdict["Success"]}
                else:
                    self.con.close()
                    return {"gkstatus": enumdict["BadPrivilege"]}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    """
    This function returns a list of accounts whose details can be edited.
    Accounts with group Direct Income or Direct Expense and are marked as sysstem account cannot be edited.
    All accounts other than that mentioned above are included in this list.
    """

    @view_config(request_method="GET", renderer="json", request_param="editaccount")
    def getAllEditableAccounts(self):
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
                result = self.con.execute(
                    select([gkdb.accounts])
                    .where(gkdb.accounts.c.orgcode == authDetails["orgcode"])
                    .order_by(gkdb.accounts.c.accountname)
                )
                accs = []
                srno = 1
                default_acc = {
                    0: "",
                    2: "Bank Transaction",
                    3: "Cash Transaction",
                    16: "Purchase Tansaction",
                    19: "Sale Transaction",
                    180: "Round Off Paid",
                    181: "Round Off Received",
                }  # it is use for default flag
                for accrow in result:
                    g = gkdb.groupsubgroups.alias("g")
                    sg = gkdb.groupsubgroups.alias("sg")

                    defaultflag = default_acc[accrow["defaultflag"]]
                    resultset = self.con.execute(
                        select(
                            [
                                (g.c.groupcode).label("groupcode"),
                                (g.c.groupname).label("groupname"),
                                (sg.c.groupcode).label("subgroupcode"),
                                (sg.c.groupname).label("subgroupname"),
                            ]
                        ).where(
                            or_(
                                and_(
                                    g.c.groupcode == int(accrow["groupcode"]),
                                    g.c.subgroupof == null(),
                                    sg.c.groupcode == int(accrow["groupcode"]),
                                    sg.c.subgroupof == null(),
                                ),
                                and_(
                                    g.c.groupcode == sg.c.subgroupof,
                                    sg.c.groupcode == int(accrow["groupcode"]),
                                ),
                            )
                        )
                    )
                    grprow = resultset.fetchone()
                    if not (
                        grprow["groupname"] in ["Direct Expense", "Direct Income"]
                        and accrow["sysaccount"] == 1
                    ):
                        if grprow["groupcode"] == grprow["subgroupcode"]:
                            accs.append(
                                {
                                    "srno": srno,
                                    "accountcode": accrow["accountcode"],
                                    "accountname": accrow["accountname"],
                                    "openingbal": "%.2f" % float(accrow["openingbal"]),
                                    "groupcode": grprow["groupcode"],
                                    "groupname": grprow["groupname"],
                                    "subgroupcode": "",
                                    "subgroupname": "",
                                    "sysaccount": accrow["sysaccount"],
                                    "defaultflag": defaultflag,
                                }
                            )

                        else:
                            accs.append(
                                {
                                    "srno": srno,
                                    "accountcode": accrow["accountcode"],
                                    "accountname": accrow["accountname"],
                                    "openingbal": "%.2f" % float(accrow["openingbal"]),
                                    "groupcode": grprow["groupcode"],
                                    "groupname": grprow["groupname"],
                                    "subgroupcode": grprow["subgroupcode"],
                                    "subgroupname": grprow["subgroupname"],
                                    "sysaccount": accrow["sysaccount"],
                                    "defaultflag": defaultflag,
                                }
                            )
                    srno = srno + 1
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": accs}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    """
    This function resets the defaultflag of all acounts to system default
    """

    @view_config(
        request_method="GET", renderer="json", request_param="type=reset_default_flags"
    )
    def reset_default_flags(self):
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
                reset_acc_defaults(self.con, self.request.params["orgcode"])
                self.con.close()
                return {"gkstatus": enumdict["Success"]}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
