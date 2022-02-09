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
from gkcore.views.api_login import authCheck
from gkcore.models.gkdb import stock, invoice, delchal
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.ext.baked import Result
import gkcore
import traceback  # for printing detailed exception logs

"""
The Dev API is used to perform tasks during development. 

Note: This API modifies tables directly and can cause unwanted behaviour during normal use or be misused. 
And hence must be commented out in __init__.py file outside this folder during production.
"""


def recalculateStock(con, data, data_type):
    id_key = data_type + "id"
    for item in data:
        id = item[id_key]
        orgcode = item["orgcode"]
        for prod_code in item["contents"]:
            if prod_code and prod_code != 'undefined':
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
                p_fqty = 0 if (p_fqty != p_fqty) else p_fqty
                # print("p_qty = %s and p_fqty = %s" % (p_qty, p_fqty))
                prod_qty = p_qty + p_fqty
                stock_row = con.execute(
                    select([stock.c.stockid, stock.c.qty]).where(
                        and_(
                            stock.c.orgcode == orgcode,
                            stock.c.dcinvtnid == id,
                            stock.c.productcode == prod_code,
                        )
                    )
                )
                # print(
                #     "stock.c.orgcode == %s; stock.c.dcinvtnid == %s; stock.c.productcode == %s; stock.c.dcinvtnflag == 3"
                #     % (orgcode, invid, prod_code)
                # )
                if stock_row.rowcount > 0:
                    stock_data = stock_row.fetchone()
                    # print(float(stock_data["qty"]))
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

            invoices = self.con.execute(
                select(
                    [
                        invoice.c.invid,
                        invoice.c.contents,
                        invoice.c.freeqty,
                        invoice.c.orgcode,
                    ]
                )
            ).fetchall()
            recalculateStock(self.con, invoices, "inv")

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
            recalculateStock(self.con, delnotes, "dc")

            # dcinvtnflag = 3 for invoice and 4 for delchal
            self.con.close()
            return {
                "gkstatus": enumdict["Success"],
            }
        except Exception:
            print(traceback.format_exc())
            self.con.close()
            return {"gkstatus": enumdict["ConnectionFailed"]}
