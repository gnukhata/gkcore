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
