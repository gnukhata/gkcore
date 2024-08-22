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
"Krishnakant Mane" <kk@dff.org.in>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"""


from gkcore import eng, enumdict
from gkcore.models import gkdb
from gkcore.views.contact.schemas import ContactDetails, ContactDetailsUpdate
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
import jwt
import gkcore
from gkcore.utils import authCheck

# import traceback  # for printing detailed exception logs


def getStateCode(StateName, con):
    stateData = con.execute(
        select([gkdb.state.c.statecode]).where(gkdb.state.c.statename == StateName)
    )
    staterow = stateData.fetchone()
    return {"statecode": staterow["statecode"]}


@view_defaults(route_name="customer")
class api_customer(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    @view_config(request_method="POST", renderer="json")
    def addCustomerSupplier(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            validated_data = ContactDetails.model_validate(
                self.request.json_body, context={"orgcode": authDetails["orgcode"]}
            )
            dataset = validated_data.model_dump()

            with eng.begin() as con:
                dataset["orgcode"] = authDetails["orgcode"]

                result = con.execute(gkdb.customerandsupplier.insert(), [dataset])
                custid = con.execute(
                    select([gkdb.customerandsupplier.c.custid]).where(
                        and_(
                            gkdb.customerandsupplier.c.orgcode
                            == authDetails["orgcode"],
                            gkdb.customerandsupplier.c.custname == dataset["custname"],
                        )
                    )
                ).fetchone()
                custid = custid["custid"]
                if result.rowcount == 1:
                    # Account for customer / supplier
                    if dataset["csflag"] == 3:
                        groupname = "Sundry Debtors"
                    else:
                        groupname = "Sundry Creditors for Purchase"
                    groupcode = con.execute(
                        select([gkdb.groupsubgroups.c.groupcode]).where(
                            and_(
                                gkdb.groupsubgroups.c.orgcode == authDetails["orgcode"],
                                gkdb.groupsubgroups.c.groupname == groupname,
                            )
                        )
                    )
                    group = groupcode.fetchone()
                    subgroupcode = group["groupcode"]
                    accountData = {
                        "openingbal": 0.00,
                        "accountname": dataset["custname"],
                        "groupcode": subgroupcode,
                        "orgcode": authDetails["orgcode"],
                    }
                    result = con.execute(gkdb.accounts.insert(), [accountData])
                    return {
                        "gkstatus": enumdict["Success"],
                        "gkresult": {"custid": custid},
                    }
                else:
                    return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}


    # route_name="customer_custid",
    @view_config(route_name="customer_custid", request_method="GET", renderer="json")
    def getCustomerSupplier(self):
        """
        this function returns details on one customer or supplier.
        the request parameter determines that there is only single entity to be returned.
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
                custid = self.request.matchdict["custid"]
                result = self.con.execute(
                    select([gkdb.customerandsupplier]).where(
                        gkdb.customerandsupplier.c.custid == custid
                    )
                )
                row = result.fetchone()
                if row["bankdetails"] == None:
                    bankdetails = ""
                else:
                    bankdetails = row["bankdetails"]

                statelist = []

                if row["state"] is not None and row["state"]:
                    statedata = self.con.execute(
                        select([gkdb.state.c.statecode]).where(
                            gkdb.state.c.statename == row["state"]
                        )
                    )
                    statename = statedata.fetchone()
                    statelist.append({statename["statecode"]: row["state"]})

                if row["gstin"] != None and bool(row["gstin"]):
                    for statecd in row["gstin"]:
                        statedata = self.con.execute(
                            select(
                                [gkdb.state.c.statename, gkdb.state.c.statecode]
                            ).where(gkdb.state.c.statecode == statecd)
                        )
                        statename = statedata.fetchone()
                        statelist.append(
                            {statename["statecode"]: statename["statename"]}
                        )
                elif row["state"] is not None and row["state"]:
                    custsupstatecode = getStateCode(row["state"], self.con)["statecode"]
                    statelist.append({custsupstatecode: row["state"]})

                Customer = {
                    "custid": row["custid"],
                    "custname": row["custname"],
                    "custaddr": row["custaddr"],
                    "custphone": row["custphone"],
                    "custemail": row["custemail"],
                    "custfax": row["custfax"],
                    "custpan": row["custpan"],
                    "custtan": row["custtan"],
                    "state": row["state"],
                    "country": row["country"],
                    "custdoc": row["custdoc"],
                    "csflag": row["csflag"],
                    "gstin": row["gstin"],
                    "tin": row["tin"],
                    "pincode": row["pincode"],
                    "bankdetails": bankdetails,
                    "statelist": statelist,
                    "gst_reg_type": row["gst_reg_type"],
                    "gst_party_type": row["gst_party_type"],
                }
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": Customer}
            except:
                # print(traceback.format_exc())
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(route_name="customer_custid", request_method="PUT", renderer="json")
    def editCustomerSupplier(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            validated_data = ContactDetailsUpdate.model_validate(
                self.request.json_body, context={"orgcode": authDetails["orgcode"]}
            )
            dataset = validated_data.model_dump()
            with eng.begin() as con:
                dataset["orgcode"] = authDetails["orgcode"]
                custcode = dataset["custid"]
                result = con.execute(
                    select([gkdb.customerandsupplier.c.custname]).where(
                        and_(
                            gkdb.customerandsupplier.c.orgcode == authDetails["orgcode"],
                            gkdb.customerandsupplier.c.custid == custcode,
                        )
                    )
                )
                if result.rowcount == 1:
                    if "bankdetails" not in dataset:
                        # if bankdetails are null, set bankdetails as null in database.
                        con.execute(
                            "update customerandsupplier set bankdetails = NULL where bankdetails is NOT NULL and custid = %d"
                            % int(custcode)
                        )
                    if "gstin" not in dataset:
                        # if gstin are null, set gstin as null in database.
                        con.execute(
                            "update customerandsupplier set gstin = NULL where gstin is NOT NULL and custid = %d"
                            % int(custcode)
                        )
                    con.execute(
                        gkdb.customerandsupplier.update()
                        .where(gkdb.customerandsupplier.c.custid == dataset["custid"])
                        .values(dataset))
                    return {
                            "gkstatus": enumdict["Success"],
                            "gkresult": {"custid": dataset["custid"]},
                        }
                else:
                    return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}


    @view_config(request_param="qty=custall", request_method="GET", renderer="json")
    def getAllCustomers(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            with eng.connect() as con:
                # there is only one possibility for a catch which is failed connection to db.
                result = con.execute(
                    select(
                        [
                            gkdb.customerandsupplier.c.custname,
                            gkdb.customerandsupplier.c.custid,
                        ]
                    )
                    .where(
                        and_(
                            gkdb.customerandsupplier.c.orgcode
                            == authDetails["orgcode"],
                            gkdb.customerandsupplier.c.csflag == 3,
                        )
                    )
                    .order_by(gkdb.customerandsupplier.c.custname)
                )
                customers = []
                for row in result:
                    customers.append(
                        {"custid": row["custid"], "custname": row["custname"]}
                    )
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": customers}


    @view_config(request_param="qty=supall", request_method="GET", renderer="json")
    def getAllSuppliers(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            with eng.connect() as con:
                # there is only one possibility for a catch which is failed connection to db.
                result = con.execute(
                    select(
                        [
                            gkdb.customerandsupplier.c.custname,
                            gkdb.customerandsupplier.c.custid,
                        ]
                    )
                    .where(
                        and_(
                            gkdb.customerandsupplier.c.orgcode
                            == authDetails["orgcode"],
                            gkdb.customerandsupplier.c.csflag == 19,
                        )
                    )
                    .order_by(gkdb.customerandsupplier.c.custname)
                )
                suppliers = []
                for row in result:
                    suppliers.append(
                        {"custid": row["custid"], "custname": row["custname"]}
                    )
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": suppliers}


    @view_config(route_name="customer_custid", request_method="DELETE", renderer="json")
    def deleteCustomer(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            with eng.begin() as con:
                result = con.execute(
                    select([gkdb.customerandsupplier.c.custname]).where(
                        and_(
                            gkdb.customerandsupplier.c.orgcode == authDetails["orgcode"],
                            gkdb.customerandsupplier.c.custid == self.request.matchdict["custid"],
                        )
                    )
                )
                if result.rowcount == 1:
                    con.execute(
                        gkdb.customerandsupplier.delete().where(
                            gkdb.customerandsupplier.c.custid
                            == self.request.matchdict["custid"]
                        )
                    )
                    return {"gkstatus": enumdict["Success"]}
                else:
                    return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}


    @view_config(
        route_name="customer_search_by_name", request_method="GET", renderer="json"
    )
    def getCustSupByName(self):
        """
        this function returns details on one customer or supplier.
        the request parameter determines that there is only single entity to be returned.
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
                custname = self.request.matchdict["custname"]
                result = con.execute(
                    select([gkdb.customerandsupplier]).where(
                        and_(
                            gkdb.customerandsupplier.c.orgcode
                            == authDetails["orgcode"],
                            gkdb.customerandsupplier.c.custname == custname,
                        )
                    )
                )
                row = result.fetchone()
                Customer = {}
                if row != None:
                    if row["bankdetails"] == None:
                        bankdetails = ""
                    else:
                        bankdetails = row["bankdetails"]

                    statelist = []
                    if row["gstin"] != None and bool(row["gstin"]):
                        for statecd in row["gstin"]:
                            statedata = con.execute(
                                select(
                                    [gkdb.state.c.statename, gkdb.state.c.statecode]
                                ).where(gkdb.state.c.statecode == statecd)
                            )
                            statename = statedata.fetchone()
                            statelist.append(
                                {statename["statecode"]: statename["statename"]}
                            )
                    else:
                        custsupstatecode = getStateCode(row["state"], con)[
                            "statecode"
                        ]
                        statelist.append({custsupstatecode: row["state"]})

                    Customer = {
                        "custid": row["custid"],
                        "custname": row["custname"],
                        "custaddr": row["custaddr"],
                        "custphone": row["custphone"],
                        "custemail": row["custemail"],
                        "custfax": row["custfax"],
                        "custpan": row["custpan"],
                        "custtan": row["custtan"],
                        "state": row["state"],
                        "custdoc": row["custdoc"],
                        "csflag": row["csflag"],
                        "gstin": row["gstin"],
                        "pincode": row["pincode"],
                        "bankdetails": bankdetails,
                        "statelist": statelist,
                        "gst_reg_type": row["gst_reg_type"],
                        "gst_party_type": row["gst_party_type"],
                    }
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": Customer}


    @view_config(
        route_name="customer_search_by_account", request_method="GET", renderer="json"
    )
    def getCustomerSupplierByAccount(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            with eng.connect() as con:
                accountcode = self.request.matchdict["accountcode"]
                # there is only one possibility for a catch which is failed connection to db.
                result = con.execute(
                    select([gkdb.accounts.c.accountname]).where(
                        and_(
                            gkdb.accounts.c.orgcode == authDetails["orgcode"],
                            gkdb.accounts.c.accountcode == accountcode,
                        )
                    )
                )
                account = result.fetchone()
                accountname = account["accountname"]
                result = con.execute(
                    select([gkdb.customerandsupplier.c.custid]).where(
                        and_(
                            gkdb.customerandsupplier.c.orgcode
                            == authDetails["orgcode"],
                            gkdb.customerandsupplier.c.custname == accountname,
                        )
                    )
                )
                customer = result.fetchone()
                return {
                    "gkstatus": gkcore.enumdict["Success"],
                    "gkresult": customer["custid"],
                }
