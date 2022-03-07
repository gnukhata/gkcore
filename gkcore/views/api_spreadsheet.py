"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020, 2021 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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


Contributors
============
Survesh VRL <123survesh@gmail.com>
Sai Karthik <kskarthik@disroot.org>

"""
from gkcore.views.api_login import authCheck
from sqlalchemy.engine.base import Connection
from pyramid.request import Request
from pyramid.view import view_defaults, view_config
import gkcore

# Spreadsheet libraries
import gkcore.views.spreadsheets as sheets

# from openpyxl.styles.colors import RED


@view_defaults(route_name="spreadsheet")
class api_spreadsheet(object):

    """
    This API returns a spreadsheet in XLSX format of the desired report.
    """

    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print("Spreadsheet API initialized")

    def check_auth(self):
        """Verify user's identity
        Check if the user has valid jwt token, else return appropriate status code
        """
        print("checking auth")
        token = self.request.headers["gktoken"] or None
        if token == None:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}

    # Reports
    @view_config(request_method="GET", request_param="stock-report", renderer="json")
    def psr(self):
        self.check_auth
        return sheets.stock_report.print_stock_report(self)

    @view_config(request_method="GET", request_param="trial-balance", renderer="json")
    def ptb(self):
        self.check_auth
        return sheets.trial_balance.print_trial_balance(self)

    @view_config(request_method="GET", request_param="pslist", renderer="json")
    def psl(self):
        self.check_auth
        return sheets.product_service.product_service_list(self)

    @view_config(request_method="GET", request_param="profit-loss", renderer="json")
    def ppl(self):
        self.check_auth
        return sheets.profit_loss.print_profit_loss(self)

    @view_config(request_method="GET", request_param="ledger", renderer="json")
    def led(self):
        self.check_auth
        return sheets.ledger.ledger_report(self)

    @view_config(request_method="GET", request_param="ledger-monthly", renderer="json")
    def ledm(self):
        self.check_auth
        return sheets.ledger.monthly_ledger(self)

    @view_config(
        request_method="GET", request_param="type=conv_bal_sheet", renderer="json"
    )
    def bals(self):
        self.check_auth
        return sheets.balance_sheet.print_balance_sheet(self)

    @view_config(request_method="GET", request_param="transfer-notes", renderer="json")
    def tnl(self):
        self.check_auth
        return sheets.transfer_note.all_transfer_notes(self)

    # Invoices
    @view_config(request_method="GET", request_param="invoice-list", renderer="json")
    def inv(self):
        self.check_auth
        return sheets.invoice.invoice_list(self)

    @view_config(
        request_method="GET", request_param="invoice-outstanding", renderer="json"
    )
    def invo(self):
        self.check_auth
        return sheets.invoice.outstanding_invoices(self)

    @view_config(
        request_method="GET", request_param="invoice-cancelled", renderer="json"
    )
    def invc(self):
        self.check_auth
        return sheets.invoice.cancelled_invoices(self)

    @view_config(request_method="GET", request_param="cash-flow", renderer="json")
    def caf(self):
        self.check_auth
        return sheets.cash_flow.print_cash_flow(self)

    # accounts
    @view_config(request_method="GET", request_param="accounts", renderer="json")
    def acc(self):
        self.check_auth
        return sheets.accounts.print_account_list(self)

    @view_config(request_method="GET", request_param="all-godowns", renderer="json")
    def ag(self):
        self.check_auth
        return sheets.godown.godown_list(self)

    @view_config(request_method="GET", request_param="user-list", renderer="json")
    def uli(self):
        self.check_auth
        return sheets.user.user_list(self)

    @view_config(request_method="GET", request_param="all-categories", renderer="json")
    def alc(self):
        self.check_auth
        return sheets.category.all_categories(self)

    @view_config(request_method="GET", request_param="budget", renderer="json")
    def bud(self):
        self.check_auth
        return sheets.budget.cash_report(self)

    @view_config(request_method="GET", request_param="budget-pnl", renderer="json")
    def bud_pnl(self):
        self.check_auth
        return sheets.budget.pnl(self)

    @view_config(
        request_method="GET", request_param="delivery-challan-unbilled", renderer="json"
    )
    def delcu(self):
        self.check_auth
        return sheets.delivery_challan.unbilled(self)

    @view_config(
        request_method="GET",
        request_param="delivery-challan-cancelled",
        renderer="json",
    )
    def delcc(self):
        self.check_auth
        return sheets.delivery_challan.cancelled(self)

    @view_config(
        request_method="GET",
        request_param="gstr1",
        renderer="json",
    )
    def gst_r1(self):
        self.check_auth
        return sheets.gst.r1(self)

    @view_config(
        request_method="GET",
        request_param="gst-summary",
        renderer="json",
    )
    def gst_summ(self):
        self.check_auth
        return sheets.gst.summary(self)

    @view_config(
        request_method="GET",
        request_param="cost-center-statement",
        renderer="json",
    )
    def cost_cen_st(self):
        self.check_auth
        return sheets.cost_center.statement(self)
