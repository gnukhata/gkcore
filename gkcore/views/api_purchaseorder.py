"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
This file is part of GNUKhata:A modular,robust anhd Free Accounting System.

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
"Abhijith Balan" <abhijith@dff.org.in>
"Pornima Kolte <pornima@openmailbox.org>"
"Prajkta Patkar<prajkta.patkar007@gmail.com>"
"Pravin Dake" <pravindake24@gmail.com>
"""


from pyramid.view import view_defaults, view_config
from gkcore.utils import authCheck
from gkcore import eng, enumdict
from pyramid.request import Request
from gkcore.models.gkdb import (
    purchaseorder,
    stock,
    product,
    customerandsupplier,
    unitofmeasurement,
    godown,
    tax,
    state,
    users,
)
from sqlalchemy.sql import select, distinct
from sqlalchemy import func, desc
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from datetime import datetime, date
import jwt
import gkcore
from gkcore.models.meta import dbconnect

from datetime import datetime, date


def getStateCode(StateName, con):
    stateData = con.execute(
        select([state.c.statecode]).where(state.c.statename == StateName)
    )
    staterow = stateData.fetchone()
    return {"statecode": staterow["statecode"]}


@view_defaults(route_name="purchaseorder")
class api_purchaseorder(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print("Purchase order initialized")

    @view_config(request_method="POST", renderer="json")
    def addPoSo(self):
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
                self.con.execute(purchaseorder.insert(), [dataset])
                orderIdData = self.con.execute(
                    select([purchaseorder.c.orderid]).where(
                        and_(
                            purchaseorder.c.orderno == dataset["orderno"],
                            purchaseorder.c.orderdate == dataset["orderdate"],
                        )
                    )
                )
                orderIdRow = orderIdData.fetchone()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": orderIdRow["orderid"],
                }
            except exc.IntegrityError:
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="GET", renderer="json")
    def getAllPoSoData(self):
        """This function returns all existing PO and SO"""
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
                if "psflag" in self.request.params:
                    result = self.con.execute(
                        select(
                            [
                                purchaseorder.c.orderid,
                                purchaseorder.c.orderdate,
                                purchaseorder.c.orderno,
                                purchaseorder.c.csid,
                                purchaseorder.c.attachmentcount,
                                purchaseorder.c.purchaseordertotal,
                            ]
                        )
                        .where(
                            and_(
                                purchaseorder.c.orgcode == authDetails["orgcode"],
                                purchaseorder.c.psflag
                                == "%d" % int(self.request.params["psflag"]),
                            )
                        )
                        .order_by(purchaseorder.c.orderdate)
                    )
                else:
                    result = self.con.execute(
                        select(
                            [
                                purchaseorder.c.orderid,
                                purchaseorder.c.orderdate,
                                purchaseorder.c.orderno,
                                purchaseorder.c.csid,
                                purchaseorder.c.attachmentcount,
                                purchaseorder.c.purchaseordertotal,
                            ]
                        )
                        .where(purchaseorder.c.orgcode == authDetails["orgcode"])
                        .order_by(purchaseorder.c.orderdate)
                    )
                allposo = []
                for row in result:
                    custdata = self.con.execute(
                        select([customerandsupplier.c.custname, customerandsupplier.c.csflag]).where(
                            customerandsupplier.c.custid == row["csid"]
                        )
                    )
                    custrow = custdata.fetchone()
                    allposo.append(
                        {
                            "orderid": row["orderid"],
                            "orderno": row["orderno"],
                            "orderdate": datetime.strftime(
                                row["orderdate"], "%d-%m-%Y"
                            ),
                            "attachmentcount": row["attachmentcount"],
                            "customer": custrow["custname"],
                            "ordertotal": float(row["purchaseordertotal"]),
                            "csflag":  custrow["csflag"],
                        }
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": allposo}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="GET", request_param="poso=single", renderer="json")
    def getSingleposo(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(
                    select([purchaseorder]).where(
                        purchaseorder.c.orderid == self.request.params["orderid"]
                    )
                )
                podata = result.fetchone()
                purchaseorderdetails = {
                    "orderno": podata["orderno"],
                    "orderdate": datetime.strftime(podata["orderdate"], "%d-%m-%Y"),
                    "creditperiod": podata["creditperiod"],
                    "payterms": podata["payterms"],
                    "modeoftransport": podata["modeoftransport"],
                    "psflag": podata["psflag"],
                    "csid": podata["csid"],
                    "taxflag": podata["taxflag"],
                    "tax": podata["tax"],
                    "purchaseordertotal": "%.2f" % float(podata["purchaseordertotal"]),
                    "pototalwords": podata["pototalwords"],
                    "orgstategstin": podata["orgstategstin"],
                    "consignee": podata["consignee"],
                    "reversecharge": podata["reversecharge"],
                    "bankdetails": podata["bankdetails"],
                    "vehicleno": podata["vehicleno"],
                    "paymentmode": podata["paymentmode"],
                    "orgcode": podata["orgcode"],
                    "roundoffflag": podata["roundoffflag"],
                    "roundedoffvalue": "%.2f"
                    % float(round(podata["purchaseordertotal"])),
                }
                if podata["address"] != None:
                    purchaseorderdetails["address"] = podata["address"]
                if podata["pincode"] != None:
                    purchaseorderdetails["pincode"] = podata["pincode"]
                if podata["dateofsupply"] != None:
                    purchaseorderdetails["dateofsupply"] = datetime.strftime(
                        podata["dateofsupply"], "%d-%m-%Y"
                    )
                if podata["psflag"] == 16:
                    purchaseorderdetails["issuername"] = podata["issuername"]
                    purchaseorderdetails["designation"] = podata["designation"]
                    purchaseorderdetails["address"] = podata["address"]

                # If sourcestate and taxstate are present.
                if podata["sourcestate"] != None:
                    purchaseorderdetails["sourcestate"] = podata["sourcestate"]
                    purchaseorderdetails["sourcestatecode"] = getStateCode(
                        podata["sourcestate"], self.con
                    )["statecode"]
                    sourceStateCode = getStateCode(podata["sourcestate"], self.con)[
                        "statecode"
                    ]
                if podata["taxstate"] != None:
                    purchaseorderdetails["destinationstate"] = podata["taxstate"]
                    taxStateCode = getStateCode(podata["taxstate"], self.con)[
                        "statecode"
                    ]
                    purchaseorderdetails["taxstatecode"] = taxStateCode
                if podata["togodown"] != None:
                    godowndata = self.con.execute(
                        select([godown.c.goname, godown.c.goaddr]).where(
                            and_(
                                godown.c.goid == podata["togodown"],
                                godown.c.orgcode == authDetails["orgcode"],
                            )
                        )
                    )
                    godowndetails = godowndata.fetchone()
                    purchaseorderdetails["goname"] = godowndetails["goname"]
                    purchaseorderdetails["goaddr"] = godowndetails["goaddr"]
                # Customer And Supplier details
                custandsup = self.con.execute(
                    select(
                        [
                            customerandsupplier.c.custname,
                            customerandsupplier.c.state,
                            customerandsupplier.c.custaddr,
                            customerandsupplier.c.custtan,
                            customerandsupplier.c.pincode,
                            customerandsupplier.c.gstin,
                            customerandsupplier.c.csflag,
                        ]
                    ).where(customerandsupplier.c.custid == podata["csid"])
                )
                custData = custandsup.fetchone()
                custsupstatecode = getStateCode(custData["state"], self.con)[
                    "statecode"
                ]
                custSupDetails = {
                    "custname": custData["custname"],
                    "custsupstate": custData["state"],
                    "custaddr": custData["custaddr"],
                    "csflag": custData["csflag"],
                    "pincode": custData["pincode"],
                    "custsupstatecode": custsupstatecode,
                }
                if custData["custtan"] != None:
                    custSupDetails["custtin"] = custData["custtan"]
                if custData["gstin"] != None:
                    if int(custData["csflag"]) == 3:
                        try:
                            custSupDetails["custgstin"] = custData["gstin"][
                                str(taxStateCode)
                            ]
                        except:
                            custSupDetails["custgstin"] = None
                    else:
                        try:
                            custSupDetails["custgstin"] = custData["gstin"][
                                str(sourceStateCode)
                            ]
                        except:
                            custSupDetails["custgstin"] = None
                purchaseorderdetails["custSupDetails"] = custSupDetails
                schedule = podata["schedule"]
                details = {}  # Stores schedule
                totalDisc = 0.00
                totalTaxableVal = 0.00
                totalTaxAmt = 0.00
                totalCessAmt = 0.00
                discounts = podata["discount"]
                freeqtys = podata["freeqty"]
                for productCode in schedule:
                    if discounts != None:
                        discount = discounts[productCode]
                    else:
                        discount = 0.00

                    if freeqtys != None:
                        freeqty = freeqtys[productCode]
                    else:
                        freeqty = 0.00
                    # Productname and unitofMeasurement depending on productcode.
                    prod = self.con.execute(
                        select(
                            [
                                product.c.productdesc,
                                product.c.uomid,
                                product.c.gsflag,
                                product.c.gscode,
                            ]
                        ).where(product.c.productcode == productCode)
                    )
                    prodrow = prod.fetchone()
                    if int(prodrow["gsflag"]) == 7:
                        um = self.con.execute(
                            select([unitofmeasurement.c.unitname]).where(
                                unitofmeasurement.c.uomid == int(prodrow["uomid"])
                            )
                        )
                        unitrow = um.fetchone()
                        unitofMeasurement = unitrow["unitname"]
                        taxableAmount = (
                            (float(schedule[productCode]["rateperunit"]))
                            * float(schedule[productCode]["quantity"])
                        ) - float(discount)
                    else:
                        unitofMeasurement = ""
                        taxableAmount = float(
                            schedule[productCode]["rateperunit"]
                        ) - float(discount)
                    taxRate = 0.00
                    totalAmount = 0.00
                    taxRate = float(podata["tax"][productCode])
                    if int(podata["taxflag"]) == 22:
                        taxRate = float(podata["tax"][productCode])
                        taxAmount = taxableAmount * float(taxRate / 100)
                        taxname = "VAT"
                        totalAmount = float(taxableAmount) + (
                            float(taxableAmount) * float(taxRate / 100)
                        )
                        totalDisc = totalDisc + float(podata["discount"][productCode])
                        totalTaxableVal = totalTaxableVal + taxableAmount
                        totalTaxAmt = totalTaxAmt + taxAmount
                        details[productCode] = {
                            "proddesc": prodrow["productdesc"],
                            "gscode": prodrow["gscode"],
                            "uom": unitofMeasurement,
                            "qty": "%.2f" % (float(schedule[productCode]["quantity"])),
                            "freeqty": "%.2f" % (float(freeqty)),
                            "priceperunit": "%.2f"
                            % (float(schedule[productCode]["rateperunit"])),
                            "discount": "%.2f" % (float(discount)),
                            "taxableamount": "%.2f" % (float(taxableAmount)),
                            "totalAmount": "%.2f" % (float(totalAmount)),
                            "taxname": "VAT",
                            "taxrate": "%.2f" % (float(taxRate)),
                            "taxamount": "%.2f" % (float(taxAmount)),
                        }

                    else:
                        cessRate = 0.00
                        cessAmount = 0.00
                        cessVal = 0.00
                        taxname = ""
                        if podata["cess"] != None:
                            cessVal = float(podata["cess"][productCode])
                            cessAmount = taxableAmount * (cessVal / 100)
                            totalCessAmt = totalCessAmt + cessAmount

                        if podata["sourcestate"] != podata["taxstate"]:
                            taxname = "IGST"
                            taxAmount = taxableAmount * (taxRate / 100)
                            totalAmount = taxableAmount + taxAmount + cessAmount
                        else:
                            taxname = "SGST"
                            taxRate = taxRate / 2
                            taxAmount = taxableAmount * (taxRate / 100)
                            totalAmount = (
                                taxableAmount
                                + (taxableAmount * ((taxRate * 2) / 100))
                                + cessAmount
                            )

                        totalDisc = totalDisc + float(podata["discount"][productCode])
                        totalTaxableVal = totalTaxableVal + taxableAmount
                        totalTaxAmt = totalTaxAmt + taxAmount

                        details[productCode] = {
                            "proddesc": prodrow["productdesc"],
                            "gscode": prodrow["gscode"],
                            "gsflag": prodrow["gsflag"],
                            "uom": unitofMeasurement,
                            "qty": "%.2f" % (float(schedule[productCode]["quantity"])),
                            "freeqty": "%.2f" % (float(freeqty)),
                            "priceperunit": "%.2f"
                            % (float(schedule[productCode]["rateperunit"])),
                            "discount": "%.2f" % (float(discount)),
                            "taxableamount": "%.2f" % (float(taxableAmount)),
                            "totalAmount": "%.2f" % (float(totalAmount)),
                            "taxname": taxname,
                            "taxrate": "%.2f" % (float(taxRate)),
                            "taxamount": "%.2f" % (float(taxAmount)),
                            "cess": "%.2f" % (float(cessAmount)),
                            "cessrate": "%.2f" % (float(cessVal)),
                        }
                    if "staggered" in schedule[productCode]:
                        details[productCode]["staggered"] = schedule[productCode][
                            "staggered"
                        ]
                purchaseorderdetails["totaldiscount"] = "%.2f" % (float(totalDisc))
                purchaseorderdetails["totaltaxablevalue"] = "%.2f" % (
                    float(totalTaxableVal)
                )
                purchaseorderdetails["totaltaxamt"] = "%.2f" % (float(totalTaxAmt))
                purchaseorderdetails["totalcessamt"] = "%.2f" % (float(totalCessAmt))
                purchaseorderdetails["taxname"] = taxname
                purchaseorderdetails["schedule"] = details
                purchaseorderdetails["psnarration"] = podata["psnarration"]
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": purchaseorderdetails,
                }
                self.con.close()
            except:
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
                orderid = self.request.params["orderid"]
                purchaseorderData = self.con.execute(
                    select([purchaseorder.c.orderno, purchaseorder.c.attachment]).where(
                        and_(purchaseorder.c.orderid == orderid)
                    )
                )
                attachment = purchaseorderData.fetchone()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": attachment["attachment"],
                    "orderno": attachment["orderno"],
                }
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="PUT", renderer="json")
    def editPurchaseOrder(self):
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
                result = self.con.execute(
                    purchaseorder.update()
                    .where(purchaseorder.c.orderid == dataset["orderid"])
                    .values(dataset)
                )
                return {"gkstatus": enumdict["Success"]}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="DELETE", renderer="json")
    def deletePurchaseOrder(self):
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
                result = self.con.execute(
                    purchaseorder.delete().where(
                        purchaseorder.c.orderid == dataset["orderid"]
                    )
                )
                return {"gkstatus": enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
