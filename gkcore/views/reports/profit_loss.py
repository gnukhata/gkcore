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
from gkcore.utils import authCheck, gk_log
from pyramid.view import view_defaults, view_config
from pyramid.request import Request
from gkcore import eng, enumdict
from gkcore.models.gkdb import goprod, product
from sqlalchemy.sql import select, and_

from gkcore.views.api_reports import (
    calculateClosingStockValue,
    calculateOpeningStockValue,
)


@view_defaults(route_name="profit-loss-new")
class pl(object):
    def __init__(self, request):
        self.request = Request
        self.request = request

    @view_config(request_method="GET", renderer="json")
    def calculate_profit_loss(self):
        # Check whether the user is registered & valid
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        auth_details = authCheck(token)

        if auth_details["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        current_orgcode = auth_details["orgcode"]

        params = dict()

        try:
            params["calculatefrom"] = self.request.params["calculatefrom"]
            params["calculateto"] = self.request.params["calculateto"]
        except Exception as e:
            gk_log("gkcore").warn(e)
            return {"gkstatus": enumdict["ConnectionFailed"]}

        final_result = dict()
        # calculate the opening & closing stock values
        final_result["opening_stock_value"] = calculateOpeningStockValue(
            eng.connect(), current_orgcode
        )

        final_result["closing_stock_value"] = calculateClosingStockValue(
            eng.connect(), current_orgcode, params["calculateto"]
        )
        return {"gkstatus": enumdict["Success"], "gkresult": final_result}
