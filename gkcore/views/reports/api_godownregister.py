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
from gkcore import enumdict
from gkcore.utils import authCheck
from pyramid.view import view_defaults, view_config
from pyramid.request import Request
from gkcore import eng, enumdict
from gkcore.models.gkdb import goprod, product
from sqlalchemy.sql import select, and_


@view_defaults(route_name="godown-register")
class api_godownregister(object):
    def __init__(self, request):
        self.request = Request
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
