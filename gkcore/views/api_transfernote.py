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
"Prajkta Patkar" <prajkta.patkar007@gmail.com>
"Abhijith Balan" <abhijithb21@openmailbox.org>
"Vasudha Kadge" <kadge.vasudha@gmail.com>
"""


from pyramid.view import view_defaults, view_config
from gkcore.utils import authCheck
from gkcore import eng, enumdict
from pyramid.request import Request
from gkcore.models.gkdb import (
    transfernote,
    stock,
    godown,
    product,
    unitofmeasurement,
    goprod,
)
from sqlalchemy.sql import select, distinct
from sqlalchemy import func, desc, func
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, or_
from datetime import datetime, date
import jwt
import gkcore
from gkcore.models.meta import dbconnect
from gkcore.views.api_godown import getusergodowns


@view_defaults(route_name="transfernote")
class api_transfernote(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print("transfernote initialized")

    @view_config(request_method="POST", renderer="json")
    def createtn(self):
        """create method for discrepancynote resource.
        orgcode is first authenticated, returns a json object containing success.
        Inserts data into transfernote table.
             -transfernoteno goes in dcinvtnid column of stock table.
             -dcinvflag column will be set to 20 for transfernote no entry.
             - inout column will be set 1 , i.e. goods are out from the godown.
         If stock table insert fails then the transfernote entry will be deleted.

        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body
                transferdata = dataset["transferdata"]
                stockdata = dataset["stockdata"]
                transferdata["orgcode"] = authDetails["orgcode"]
                stockdata["orgcode"] = authDetails["orgcode"]
                # Check for duplicate entry before insertion
                result_duplicate_check = self.con.execute(
                    select([transfernote.c.transfernoteno]).where(
                        and_(
                            transfernote.c.orgcode == authDetails["orgcode"],
                            func.lower(transfernote.c.transfernoteno) == func.lower(transferdata["transfernoteno"]),
                        )
                    )
                )
                
                if result_duplicate_check.rowcount > 0:
                    # Duplicate entry found, handle accordingly
                    return {"gkstatus": enumdict["DuplicateEntry"]}
                result = self.con.execute(transfernote.insert(), [transferdata])

                if result.rowcount == 1:
                    transfernoteiddata = self.con.execute(
                        select(
                            [
                                transfernote.c.transfernoteid,
                                transfernote.c.transfernotedate,
                            ]
                        ).where(
                            and_(
                                transfernote.c.orgcode == authDetails["orgcode"],
                                transfernote.c.transfernoteno
                                == transferdata["transfernoteno"],
                            )
                        )
                    )
                    transfernoteidrow = transfernoteiddata.fetchone()
                    stockdata["dcinvtnid"] = transfernoteidrow["transfernoteid"]
                    stockdata["stockdate"] = transfernoteidrow["transfernotedate"]
                    stockdata["goid"] = transferdata["fromgodown"]
                    stockdata["dcinvtnflag"] = 20
                    stockdata["inout"] = 15
                    items = stockdata.pop("items")
                    try:
                        for key in list(items.keys()):
                            stockdata["rate"] = 0
                            stockdata["productcode"] = key
                            stockdata["qty"] = items[key]
                            result = self.con.execute(stock.insert(), [stockdata])
                    except:
                        result = self.con.execute(
                            stock.delete().where(
                                and_(
                                    stock.c.dcinvtnid
                                    == transfernoteidrow["transfernoteid"],
                                    stock.c.dcinvtnflag == 20,
                                )
                            )
                        )
                        result = self.con.execute(
                            transfernote.delete().where(
                                transfernote.c.transfernoteid
                                == transfernoteidrow["transfernoteid"]
                            )
                        )
                        return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
                    return {
                        "gkstatus": enumdict["Success"],
                        "gkresult": transfernoteidrow["transfernoteid"],
                    }
                else:
                    return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="GET", request_param="tn=all", renderer="json")
    def getAllTransferNote(self):
        """This method returns  all existing transfernotes which are not received"""
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
                """
                Retreiving date, id, number and togodown of all transfernotes.
                """
                result = self.con.execute(
                    select(
                        [
                            transfernote.c.transfernotedate,
                            transfernote.c.transfernoteid,
                            transfernote.c.transfernoteno,
                            transfernote.c.togodown,
                        ]
                    )
                    .where(
                        and_(
                            transfernote.c.recieved == False,
                            transfernote.c.orgcode == authDetails["orgcode"],
                        )
                    )
                    .order_by(transfernote.c.transfernotedate)
                )
                """
                A list of all godowns assigned to a user is retreived from API for godowns using the method usergodowmns.
                If user is not a godown keeper this list will be empty.
                """
                usergodowmns = getusergodowns(authDetails["userid"])["gkresult"]
                """
                If user has godowns assigned only those unreceived transfernotes for moving goods into those godowns are returned.
                Otherwise all transfernotes that have not been received are returned.
                """
                tn = []
                if usergodowmns:
                    godowns = []
                    for godown in usergodowmns:
                        godowns.append(godown["goid"])
                    for row in result:
                        if row["togodown"] in godowns:
                            tn.append(
                                {
                                    "transfernoteno": row["transfernoteno"],
                                    "transfernoteid": row["transfernoteid"],
                                    "transfernotedate": datetime.strftime(
                                        row["transfernotedate"], "%d-%m-%Y"
                                    ),
                                }
                            )
                else:
                    for row in result:
                        tn.append(
                            {
                                "transfernoteno": row["transfernoteno"],
                                "transfernoteid": row["transfernoteid"],
                                "transfernotedate": datetime.strftime(
                                    row["transfernotedate"], "%d-%m-%Y"
                                ),
                            }
                        )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": tn}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="GET", request_param="type=all", renderer="json")
    def getAllTransferNotes(self):
        """This method returns  all existing transfernotes"""
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
                            transfernote.c.transfernotedate,
                            transfernote.c.transfernoteid,
                            transfernote.c.transfernoteno,
                        ]
                    )
                    .where(transfernote.c.orgcode == authDetails["orgcode"])
                    .order_by(transfernote.c.transfernotedate)
                )
                tn = []
                for row in result:
                    tn.append(
                        {
                            "transfernoteno": row["transfernoteno"],
                            "transfernoteid": row["transfernoteid"],
                            "transfernotedate": datetime.strftime(
                                row["transfernotedate"], "%d-%m-%Y"
                            ),
                        }
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": tn}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="GET", request_param="tn=single", renderer="json")
    def getTn(self):
        """Shows single transfernote by matching transfernoteno"""
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
                    select([transfernote]).where(
                        and_(
                            transfernote.c.transfernoteid
                            == self.request.params["transfernoteid"],
                            transfernote.c.orgcode == authDetails["orgcode"],
                        )
                    )
                )
                row = result.fetchone()

                togo = self.con.execute(
                    select([godown.c.goname, godown.c.goaddr, godown.c.state]).where(
                        godown.c.goid == row["togodown"]
                    )
                )
                togodata = togo.fetchone()
                fromgo = self.con.execute(
                    select([godown.c.goname, godown.c.goaddr, godown.c.state]).where(
                        godown.c.goid == row["fromgodown"]
                    )
                )
                fromgodata = fromgo.fetchone()

                items = {}

                stockdata = self.con.execute(
                    select([stock.c.productcode, stock.c.qty]).where(
                        and_(
                            stock.c.dcinvtnflag == 20,
                            stock.c.dcinvtnid == self.request.params["transfernoteid"],
                        )
                    )
                )
                for stockrow in stockdata:
                    productdata = self.con.execute(
                        select([product.c.productdesc, product.c.uomid]).where(
                            product.c.productcode == stockrow["productcode"]
                        )
                    )
                    productdesc = productdata.fetchone()
                    uomresult = self.con.execute(
                        select([unitofmeasurement.c.unitname]).where(
                            unitofmeasurement.c.uomid == productdesc["uomid"]
                        )
                    )
                    unitnamrrow = uomresult.fetchone()
                    items[stockrow["productcode"]] = {
                        "qty": "%.2f" % float(stockrow["qty"]),
                        "productdesc": productdesc["productdesc"],
                        "unitname": unitnamrrow["unitname"],
                    }

                tn = {}
                tn = {
                    "transfernoteno": row["transfernoteno"],
                    "transfernotedate": datetime.strftime(
                        row["transfernotedate"], "%d-%m-%Y"
                    ),
                    "transportationmode": row["transportationmode"],
                    "productdetails": items,
                    "nopkt": row["nopkt"],
                    "togodown": togodata["goname"],
                    "togodownstate": togodata["state"],
                    "togodownaddr": togodata["goaddr"],
                    "togodownid": row["togodown"],
                    "fromgodownid": row["fromgodown"],
                    "fromgodown": fromgodata["goname"],
                    "fromgodownstate": fromgodata["state"],
                    "fromgodownaddr": fromgodata["goaddr"],
                    "issuername": row["issuername"],
                    "designation": row["designation"],
                    "orgcode": row["orgcode"],
                }
                if row["duedate"] != None:
                    tn["duedate"] = datetime.strftime(row["duedate"], "%d-%m-%Y")
                    tn["grace"] = row["grace"]
                if row["recieved"]:
                    tn["recieved"] = (row["recieved"],)
                    tn["receiveddate"] = datetime.strftime(
                        row["recieveddate"], "%d-%m-%Y"
                    )
                else:
                    tn["recieved"] = row["recieved"]

                return {"gkstatus": enumdict["Success"], "gkresult": tn}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="GET", request_param="type=list", renderer="json")
    def listofTransferNotes(self):
        """
        This method returns  all existing transfernotes within a given period.
        If an id of a godown is received it will return all transfernotes involving that godown.
        The result will be a list of dictionaries.
        Each dictionary will have hey value pairs as illustrated below :-
        {""transfernoteno": transfernote no,"transfernoteid": transfernote id, "transfernotedate":transfernote date,"fromgodown":name and address of godown from which goods are dispatched,"togodown":name and address of godown to which goods are dispatched, "products":details of products,"status": Received/Pending}"}
        If orderflag is 4 date is return in descending order otherwise in ascending order.
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
                startDate = datetime.strptime(
                    str(self.request.params["startdate"]), "%d-%m-%Y"
                ).strftime("%Y-%m-%d")
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%d-%m-%Y"
                ).strftime("%Y-%m-%d")
                if "goid" in self.request.params:
                    tngodown = int(self.request.params["goid"])
                    if "orderflag" in self.request.params:
                        result = self.con.execute(
                            select([transfernote])
                            .where(
                                and_(
                                    transfernote.c.orgcode == authDetails["orgcode"],
                                    transfernote.c.transfernotedate >= startDate,
                                    transfernote.c.transfernotedate <= endDate,
                                    or_(
                                        transfernote.c.fromgodown == tngodown,
                                        transfernote.c.togodown == tngodown,
                                    ),
                                )
                            )
                            .order_by(desc(transfernote.c.transfernotedate))
                        )
                    else:
                        result = self.con.execute(
                            select([transfernote])
                            .where(
                                and_(
                                    transfernote.c.orgcode == authDetails["orgcode"],
                                    transfernote.c.transfernotedate >= startDate,
                                    transfernote.c.transfernotedate <= endDate,
                                    or_(
                                        transfernote.c.fromgodown == tngodown,
                                        transfernote.c.togodown == tngodown,
                                    ),
                                )
                            )
                            .order_by(transfernote.c.transfernotedate)
                        )
                else:
                    if "orderflag" in self.request.params:
                        result = self.con.execute(
                            select([transfernote])
                            .where(
                                and_(
                                    transfernote.c.orgcode == authDetails["orgcode"],
                                    transfernote.c.transfernotedate >= startDate,
                                    transfernote.c.transfernotedate <= endDate,
                                )
                            )
                            .order_by(desc(transfernote.c.transfernotedate))
                        )
                    else:
                        result = self.con.execute(
                            select([transfernote])
                            .where(
                                and_(
                                    transfernote.c.orgcode == authDetails["orgcode"],
                                    transfernote.c.transfernotedate >= startDate,
                                    transfernote.c.transfernotedate <= endDate,
                                )
                            )
                            .order_by(transfernote.c.transfernotedate)
                        )
                tn = []
                srno = 1
                for row in result:
                    stockdata = self.con.execute(
                        select([stock.c.productcode, stock.c.qty])
                        .where(
                            and_(
                                stock.c.orgcode == authDetails["orgcode"],
                                stock.c.dcinvtnid == row["transfernoteid"],
                                stock.c.dcinvtnflag == 20,
                            )
                        )
                        .distinct()
                    )
                    productqty = []
                    for data in stockdata:
                        productdata = self.con.execute(
                            select([product.c.productdesc, product.c.uomid]).where(
                                and_(
                                    product.c.productcode == data["productcode"],
                                    product.c.orgcode == authDetails["orgcode"],
                                )
                            )
                        )
                        productdetails = productdata.fetchone()
                        uomdata = self.con.execute(
                            select([unitofmeasurement.c.unitname]).where(
                                unitofmeasurement.c.uomid == productdetails["uomid"]
                            )
                        )
                        uomdetails = uomdata.fetchone()
                        productqty.append(
                            {
                                "productdesc": productdetails["productdesc"],
                                "quantity": "%.2f" % float(data["qty"]),
                                "uom": uomdetails["unitname"],
                            }
                        )
                    fromgodown = self.con.execute(
                        select([godown.c.goname, godown.c.goaddr]).where(
                            and_(
                                godown.c.goid == row["fromgodown"],
                                godown.c.orgcode == authDetails["orgcode"],
                            )
                        )
                    )
                    fromgodowndata = fromgodown.fetchone()
                    fromgodowndesc = (
                        fromgodowndata["goname"] + " (" + fromgodowndata["goaddr"] + ")"
                    )
                    togodown = self.con.execute(
                        select([godown.c.goname, godown.c.goaddr]).where(
                            and_(
                                godown.c.goid == row["togodown"],
                                godown.c.orgcode == authDetails["orgcode"],
                            )
                        )
                    )
                    togodowndata = togodown.fetchone()
                    togodowndesc = (
                        togodowndata["goname"] + " (" + fromgodowndata["goaddr"] + ")"
                    )
                    tn.append(
                        {
                            "transfernoteno": row["transfernoteno"],
                            "transfernoteid": row["transfernoteid"],
                            "transfernotedate": datetime.strftime(
                                row["transfernotedate"], "%d-%m-%Y"
                            ),
                            "fromgodown": fromgodowndesc,
                            "togodown": togodowndesc,
                            "productqty": productqty,
                            "numberofproducts": len(productqty),
                            "receivedflag": row["recieved"],
                            "srno": srno,
                        }
                    )
                    srno = srno + 1
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": tn}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="received=true", request_method="PUT", renderer="json")
    def editransfernote(self):
        """when other godown receives the stock , Received entry is made and according to that changes are done ithe stock table"""
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                transferdata = self.request.json_body
                stockdata = {}
                stockdata["orgcode"] = authDetails["orgcode"]
                result = self.con.execute(
                    select(
                        [
                            transfernote.c.togodown,
                            transfernote.c.recieved,
                            transfernote.c.togodown,
                        ]
                    ).where(
                        transfernote.c.transfernoteid == transferdata["transfernoteid"]
                    )
                )
                row = result.fetchone()
                if row["recieved"]:
                    return {"gkstatus": enumdict["ActionDisallowed"]}
                else:
                    stockdata["dcinvtnid"] = transferdata["transfernoteid"]
                    stockdata["stockdate"] = transferdata["recieveddate"]
                    stockdata["dcinvtnflag"] = 20
                    stockdata["inout"] = 9
                    stockdata["goid"] = row["togodown"]
                    stockresult = self.con.execute(
                        select([stock.c.productcode, stock.c.qty]).where(
                            and_(
                                stock.c.dcinvtnid == transferdata["transfernoteid"],
                                stock.c.dcinvtnflag == 20,
                            )
                        )
                    )
                    for key in stockresult:
                        resultgoprod = self.con.execute(
                            select([goprod]).where(
                                and_(
                                    goprod.c.goid == row["togodown"],
                                    goprod.c.productcode == key["productcode"],
                                )
                            )
                        )
                        if resultgoprod.rowcount == 0:
                            result = self.con.execute(
                                goprod.insert(),
                                [
                                    {
                                        "goid": row["togodown"],
                                        "productcode": key["productcode"],
                                        "goopeningstock": 0,
                                        "orgcode": authDetails["orgcode"],
                                    }
                                ],
                            )
                        stockdata["productcode"] = key["productcode"]
                        stockdata["qty"] = key["qty"]
                        stockdata["rate"] = 0
                        result = self.con.execute(stock.insert(), [stockdata])

                    result = self.con.execute(
                        transfernote.update()
                        .where(
                            transfernote.c.transfernoteid
                            == transferdata["transfernoteid"]
                        )
                        .values(
                            recieved=True, recieveddate=transferdata["recieveddate"]
                        )
                    )
                return {"gkstatus": enumdict["Success"]}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
