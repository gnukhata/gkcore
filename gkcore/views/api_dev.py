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
"Survesh" <123survesh@gmail.com>
"Sai Karthik"<kskarthik@disroot.org>

"""

from gkcore import eng, enumdict
from gkcore.models.gkdb import (
    stock,
    invoice,
    delchal,
    organisation,
    product,
    customerandsupplier,
)
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.ext.baked import Result
import gkcore

from gkcore.views.api_login import authCheck
from gkcore.views.api_transaction import getInvVouchers
from gkcore.views.api_invoice import getDefaultAcc

import traceback  # for printing detailed exception logs

"""
The Dev API is used to perform tasks during development. 

Note: This API modifies tables directly and can cause unwanted behaviour during normal use or be misused. 
And hence must be commented out in __init__.py file outside this folder during production.
"""


def recalculateStock(con, data, data_type, flag):
    try:
        id_key = data_type + "id"
        for item in data:
            id = item[id_key]
            orgcode = item["orgcode"]
            new_fqty = {}
            for prod_code in item["contents"]:
                if prod_code and prod_code != "undefined":
                    # print("================")
                    p_qty = (
                        float(
                            item["contents"][prod_code][
                                list(item["contents"][prod_code].keys())[0]
                            ]
                        )
                        or 0
                    )
                    p_fqty = float(item["freeqty"][prod_code])

                    if p_fqty != p_fqty:
                        new_fqty[prod_code] = 0
                        p_fqty = 0

                    prod_qty = p_qty + p_fqty
                    stock_row = con.execute(
                        select([stock.c.stockid, stock.c.qty]).where(
                            and_(
                                stock.c.orgcode == orgcode,
                                stock.c.dcinvtnid == id,
                                stock.c.productcode == prod_code,
                                stock.c.dcinvtnflag == flag,
                            )
                        )
                    )
                    # print(
                    #     "stock.c.orgcode == %s; stock.c.dcinvtnid == %s; stock.c.productcode == %s; stock.c.dcinvtnflag == 3"
                    #     % (orgcode, invid, prod_code)
                    # )
                    if stock_row.rowcount > 0:
                        stock_data = stock_row.fetchone()
                        # print(id_key + ": " + str(id) + ", qty = " +str(stock_data["qty"])+ ", pqty = "+str(prod_qty))
                        if float(stock_data["qty"]) != prod_qty:
                            con.execute(
                                stock.update()
                                .where(stock.c.stockid == stock_data["stockid"])
                                .values(qty=prod_qty)
                            )
                            # print(
                            #     "stockid = %s;  bad qty = %s;  good qty = %s"
                            #     % (
                            #         str(stock_data["stockid"]),
                            #         str(stock_data["qty"]),
                            #         str(prod_qty),
                            #     )
                            # )
            if len(new_fqty):
                if data_type == "inv":
                    con.execute(
                        invoice.update()
                        .where(invoice.c.invid == item[id_key])
                        .values(freeqty=new_fqty)
                    )
                elif data_type == "dc":
                    con.execute(
                        delchal.update()
                        .where(delchal.c.dcid == item[id_key])
                        .values(freeqty=new_fqty)
                    )
    except:
        print(traceback.format_exc())


def recalculateVoucher(con, orgcode, invid, maflag):
    try:
        inv_data = con.execute(
            select([invoice]).where(
                and_(invoice.c.orgcode == orgcode, invoice.c.invid == invid)
            )
        ).fetchone()
        vouchers = getInvVouchers(con, orgcode, invid)
        voucherData = {}
        if len(vouchers) > 0:
            # recalculate vouchers
            print("%s Has Voucher" % (str(invid)))
        else:
            # create vouchers
            avData = {
                "totaltaxable": 0,
                "product": {},
                "prodData": {},
                "taxpayment": 0,
                "avtax": {
                    "GSTName": "CGST"
                    if inv_data["taxstate"] == inv_data["sourcestate"]
                    else "IGST",
                    "CESSName": "CESS",
                },
            }
            for pid in inv_data["contents"]:
                prod_row = con.execute(
                    select([product.c.productdesc]).where(
                        and_(product.c.productcode == pid, product.c.orgcode == orgcode)
                    )
                ).fetchone()
                pname = prod_row["productdesc"]
                price = float(list(inv_data["contents"][pid].keys())[0]) or 0
                qty = float(list(inv_data["contents"][pid].values())[0]) or 0
                discount = float(inv_data["discount"][pid]) or 0
                fqty = float(inv_data["freeqty"][pid]) or 0
                taxable = (price * (qty - fqty)) - discount
                avData["totaltaxable"] += taxable
                avData["prodData"][pid] = taxable
                avData["product"][pname] = taxable
            avData["taxpayment"] = avData["totaltaxable"]

            queryParams = {
                "invtype": inv_data["inoutflag"],
                "pmtmode": inv_data["paymentmode"],
                "taxType": inv_data["taxflag"],
                "destinationstate": inv_data["taxstate"],
                "totaltaxablevalue": avData["totaltaxable"],
                "maflag": maflag,
                "totalAmount": (inv_data["invoicetotal"]),
                "invoicedate": inv_data["invoicedate"],
                "invid": invid,
                "invoiceno": inv_data["invoiceno"],
                "taxes": inv_data["tax"],
                "cess": inv_data["cess"],
                "products": avData["product"],
                "prodData": avData["prodData"],
                "csname": ""
            }

            if inv_data["custid"]:
                csName = con.execute(
                    select([customerandsupplier.c.custname]).where(
                        and_(
                            customerandsupplier.c.orgcode == orgcode,
                            customerandsupplier.c.custid == int(inv_data["custid"]),
                        )
                    )
                ).fetchone()
                queryParams["csname"] = csName["custname"]
            
            # when invoice total is rounded off
            if inv_data["roundoffflag"] == 1:
                roundOffAmount = float(inv_data["invoicetotal"]) - round(
                    float(inv_data["invoicetotal"])
                )
                if float(roundOffAmount) != 0.00:
                    queryParams["roundoffamt"] = float(roundOffAmount)

            if int(inv_data["taxflag"]) == 7:
                queryParams["gstname"] = avData["avtax"]["GSTName"]
                queryParams["cessname"] = avData["avtax"]["CESSName"]

            if int(inv_data["taxflag"]) == 22:
                queryParams["taxpayment"] = avData["taxpayment"]

            # call getDefaultAcc
            av_Result = getDefaultAcc(con, queryParams, orgcode)

            if av_Result["gkstatus"] == 0:
                voucherData["status"] = 0
                voucherData["vchno"] = av_Result["vchNo"]
                voucherData["vchid"] = av_Result["vid"]
            else:
                voucherData["status"] = 1

        return voucherData
    except:
        print(traceback.format_exc())
        return {}


@view_defaults(route_name="dev")
class api_dev(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print("Dev API is ON")

    @view_config(
        request_method="GET", request_param="task=stock_rectify", renderer="json"
    )
    def rectifyStock(self):
        """
        This methods recalculates the stock table data, using the invoice / delivery note of the respective stock table entry.
        """
        try:
            self.con = eng.connect()

            # Rectify all invoice
            invoices = self.con.execute(
                select(
                    [
                        invoice.c.invid,
                        invoice.c.contents,
                        invoice.c.freeqty,
                        invoice.c.orgcode,
                    ]
                ).where(invoice.c.icflag == 9)
            ).fetchall()
            recalculateStock(self.con, invoices, "inv", 9)

            # Rectify all cash memos
            invoices = self.con.execute(
                select(
                    [
                        invoice.c.invid,
                        invoice.c.contents,
                        invoice.c.freeqty,
                        invoice.c.orgcode,
                    ]
                ).where(invoice.c.icflag == 3)
            ).fetchall()
            recalculateStock(self.con, invoices, "inv", 3)

            # Rectify all Delivery Notes
            delnotes = self.con.execute(
                select(
                    [
                        delchal.c.dcid,
                        delchal.c.contents,
                        delchal.c.freeqty,
                        delchal.c.orgcode,
                    ]
                )
            ).fetchall()
            recalculateStock(self.con, delnotes, "dc", 4)

            # Rectify any remaining entries that are NaN
            # stocks = self.con.execute(
            #     select([stock.c.dcinvtnid, stock.c.dcinvtnflag, stock.c.orgcode]).where(
            #         stock.c.qty == "NaN"
            #     )
            # ).fetchall()
            # stock_map = {}
            # for item in stocks:
            #     if not item["dcinvtnflag"] in stock_map:
            #         stock_map[item["dcinvtnflag"]] = []
            #     if item["dcinvtnflag"] == 4:
            #         delnote = self.con.execute(
            #             select(
            #                 [
            #                     delchal.c.dcid,
            #                     delchal.c.contents,
            #                     delchal.c.freeqty,
            #                     delchal.c.orgcode,
            #                 ]
            #             ).where(
            #                 and_(
            #                     delchal.c.dcid == item["dcinvtnid"],
            #                     delchal.c.orgcode == item["orgcode"],
            #                 )
            #             )
            #         ).fetchone()
            #         stock_map[item["dcinvtnflag"]].append(delnote)
            # for stock_flag in stock_map:
            #     # print(stock_map[stock_flag])
            #     stock_type = "inv" if stock_flag == 9 else "dc"
            #     recalculateStock(self.con, stock_map[stock_flag], stock_type, stock_flag)

            # dcinvtnflag = 3 for cash memo, 9 for invoice and 4 for delchal
            self.con.close()
            return {
                "gkstatus": enumdict["Success"],
            }
        except Exception:
            print(traceback.format_exc())
            self.con.close()
            return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(
        request_method="GET", request_param="task=voucher_rectify", renderer="json"
    )
    def rectifyVouchers(self):
        """
        This methods recalculates the vouchers, using the invoice data for a given orgcode.
        """
        try:
            self.con = eng.connect()

            orgcode = self.request.params["orgcode"]

            # check automatic voucher flag  if it is 1 get maflag
            avfl = self.con.execute(
                select([organisation.c.avflag]).where(organisation.c.orgcode == orgcode)
            )
            av = avfl.fetchone()
            if av["avflag"] == 1:
                mafl = self.con.execute(
                    select([organisation.c.maflag]).where(
                        organisation.c.orgcode == orgcode
                    )
                ).fetchone()
                maFlag = mafl["maflag"]

                invlist = self.con.execute(
                    select([invoice.c.invid]).where(invoice.c.orgcode == orgcode)
                ).fetchall()

                voucherData = {}
                for inv in invlist:
                    voucherData[inv["invid"]] = recalculateVoucher(
                        self.con, orgcode, inv["invid"], maFlag
                    )

                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": voucherData}
            else:
                self.con.close()
                return {
                    "gkstatus": enumdict["ActionDisallowed"],
                }

        except Exception:
            print(traceback.format_exc())
            self.con.close()
            return {"gkstatus": enumdict["ConnectionFailed"]}
