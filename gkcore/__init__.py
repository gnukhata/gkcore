"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020 Digital Freedom Foundation & Accion Labs 
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
"Prajkta Patkar"<prajakta@dff.org.in>


Main entry point:
This package initializer module is run when the application is served.
The module contains enum dict containing all gnukahta success and failure messages.
It also contains all the routes which are connected to respective resources.
To trace the link of the routes we look at the name of a route and then see where it appeares in any of the @view_defaults or @view_config decorator of any resource.
This module also scanns for the secret from the database which is then used for jwt authentication.
"""

import os
from pyramid.config import Configurator
from gkcore.models.meta import dbconnect
from wsgicors import CORS
from gkcore.enum import STATUS_CODES

try:
    eng = dbconnect()
    resultset = eng.execute("select * from signature")
    secret = resultset.fetchone()[0]
except:
    secret = ""

enumdict = STATUS_CODES


def main(global_config, **settings):
    config = Configurator(settings=settings)

    # organisation
    config.add_route("organisation", "/organisation")
    config.add_route("organisation_gstin", "/organisation/gstin")
    config.add_route("organisation_attachment", "/organisation/attachment")
    config.add_route("organisation_gst_accounts", "/organisation/gst_accounts")
    config.add_route(
        "organisation_gst_accounts_codes", "/organisation/gst_accounts/codes"
    )
    config.add_route("organisation_registration", "/organisation/check_registration")
    config.add_route("organisation_orgname", "/organisation/check/{orgname}")
    config.add_route("organisation_rm_user", "/organisation/remove-user")

    # gkuser
    config.add_route("gkuser", "/gkuser")
    config.add_route("organisation_gkusers", "/organisation/gkusers")
    config.add_route("gkuser_orgs", "/gkuser/orgs")
    config.add_route("gkuser_role", "/gkuser/role")
    config.add_route("gkuser_pwd_question", "/gkuser/pwd/question")
    config.add_route("gkuser_pwd_answer", "/gkuser/pwd/answer")
    config.add_route("gkuser_pwd_reset", "/gkuser/pwd/reset")
    config.add_route("gkuser_change_pwd", "/gkuser/pwd/change")
    config.add_route("gkuser_pwd_validate", "/gkuser/pwd/validate")
    config.add_route("gkuser_users_of_role", "/gkuser/all/role/{userrole}")
    config.add_route("gkuser_uname", "/gkuser/check/{username}")

    # invite
    config.add_route("invite", "/invite")
    config.add_route("invite_accept", "/invite/accept")
    config.add_route("invite_reject", "/invite/reject")

    # login
    config.add_route("login_user", "/login/user")
    config.add_route("login_org", "/login/org")

    # product
    config.add_route("product", "/product")
    config.add_route("product_tax", "/product/tax")
    config.add_route("product_check_gst", "/product/check/gst")
    config.add_route("product_hsn", "/product/hsn")
    config.add_route("product_stock", "/product/stock")
    config.add_route("product_lastprice", "/product/lastprice")
    config.add_route("godown_product", "/godown/product/{productcode}")
    config.add_route("product_godown", "/product/godown/{godownid}")
    config.add_route("product_category", "/product/category/{categorycode}")
    config.add_route("product_productcode", "/product/{productcode}")

    # tax
    config.add_route("tax", "/tax")
    config.add_route("tax_search", "/tax/search/{pscflag}")
    config.add_route("tax_taxid", "/tax/{taxid}")

    # customer
    config.add_route("customer", "/customer")
    config.add_route(
        "customer_search_by_account", "/customer/search/account/{accountcode}"
    )
    config.add_route("customer_search_by_name", "/customer/search/name/{custname}")
    config.add_route("customer_custid", "/customer/{custid}")

    # invoice
    config.add_route("invoice", "/invoice")
    config.add_route("invoice_list", "/invoice/list")
    config.add_route("invoice_list_rectify", "/invoice/list/rectify")
    config.add_route("invoice_nonrejected", "/invoice/nonrejected")
    config.add_route("invoice_id", "/invoice/next_id")
    config.add_route("cashmemo", "/cashmemo")
    config.add_route("delnote_unbilled", "/delchal/unbilled")
    config.add_route("invoice_attachment", "/invoice/attachment/{invid}")
    config.add_route("invoice_cancel", "/invoice/cancel/{invid}")
    config.add_route("invoice_invid", "/invoice/{invid}")

    # delchal
    config.add_route("delchal", "/delchal")
    config.add_route("delchal_attachment", "/delchal/attachment/{dcid}")
    config.add_route("delchal_cancel", "/delchal/cancel")
    config.add_route("delchal_last", "/delchal/last")
    config.add_route("delchal_next_id", "/delchal/next_id")
    config.add_route("delchal_dcid", "/delchal/{dcid}")
    config.add_route("delchal_cancel_dcid", "/delchal/cancel/{dcid}")
    config.add_route("delchal_invid", "/delchal/invid/{dcid}")

    config.add_route("budget", "/budget")
    config.add_route("categoryspecs", "/categoryspecs")
    config.add_route("orgyears", "/orgyears/{orgname}/{orgtype}")
    config.add_route("transaction", "/transaction")
    config.add_route("bankrecon", "/bankrecon")
    config.add_route("accounts", "/accounts")
    config.add_route("accounts-xlsx", "/accounts/spreadsheet")
    config.add_route("account", "/account/{accountcode}")
    config.add_route("projects", "/projects")
    config.add_route("project", "/project/{projectcode}")
    config.add_route("accountsbyrule", "/accountsbyrule")
    config.add_route("groupallsubgroup", "/groupallsubgroup/{groupcode}")
    config.add_route("groupsubgroup", "/groupsubgroup/{groupcode}")
    config.add_route("groupsubgroups", "/groupsubgroups")
    config.add_route("groupDetails", "/groupDetails/{groupcode}")
    config.add_route("report", "/report")
    config.add_route("close-books", "/closebooks")
    config.add_route("roll-over", "/rollover")
    config.add_route("rollclose", "/rollclose")
    config.add_route("forgotpassword", "/forgotpassword")
    config.add_route("categories", "/categories")
    config.add_route("godown", "/godown")
    config.add_route("purchaseorder", "/purchaseorder")
    config.add_route("transfernote", "/transfernote")
    config.add_route("discrepancynote", "/discrepancynote")
    config.add_route("log", "/log")
    config.add_route("logSort", "/log/dateRange")
    config.add_route("rejectionnote", "/rejectionnote")
    config.add_route("billwise", "/billwise")
    config.add_route("state", "/state")
    config.add_route("drcrnote", "/drcrnote")
    config.add_route("dashboard", "/dashboard")
    config.add_route("config", "/config")
    config.add_route("spreadsheet", "/spreadsheet")
    config.add_route("ifsc", "/ifsc")
    config.add_route("dev", "/dev")  # Comment in production
    config.add_route("hsn", "/hsn")
    # export org data
    config.add_route("export-json", "/export/json")
    config.add_route("export-xlsx", "/export/xlsx")
    # import org data
    config.add_route("import-json", "/import/json")
    config.add_route("import-xlsx", "/import/xlsx")

    config.add_route("index", "/")

    # reports
    config.add_route("product-register", "/reports/product-register")
    config.add_route("registers", "/reports/registers")
    config.add_route("profit-loss", "/reports/profit-loss")
    config.add_route("balance-sheet", "/reports/balance-sheet")
    config.add_route("gross-trial-balance", "/reports/trial-balance/gross")
    config.add_route("net-trial-balance", "/reports/trial-balance/net")
    config.add_route("extended-trial-balance", "/reports/trial-balance/extended")
    config.add_route("ledger-monthly", "/reports/ledger/monthly")
    config.add_route("ledger", "/reports/ledger")
    config.add_route("ledger-crdr", "/reports/ledger/crdr")
    config.add_route("godown-register", "/reports/godown-register/{goid}")
    # WIP: v2 of profit loss report
    config.add_route("profit-loss-new", "/reports/v2/profit-loss")

    # reports spreadsheets
    config.add_route("product-register-xlsx", "/spreadsheet/product-register")
    config.add_route("profitloss-xlsx", "/spreadsheet/profit-loss")
    config.add_route("balance-sheet-xlsx", "/spreadsheet/balance-sheet")
    config.add_route("trial-balance-xlsx", "/spreadsheet/trial-balance")
    config.add_route("ledger-monthly-xlsx", "/spreadsheet/ledger/monthly")
    config.add_route("ledger-xlsx", "/spreadsheet/ledger")

    # Unit of measurement
    config.add_route("uom", "/unitofmeasurement")
    config.add_route("uom-single", "/unitofmeasurement/{uomid}")

    # GST returns
    config.add_route("gstr1", "/gst/returns/r1")
    config.add_route("gstr3b", "/gst/returns/3b")
    # GSTIN captcha validation
    config.add_route("gst-captcha", "/gst/captcha")
    # GST news
    config.add_route("gstnews", "/gst-news")

    config.scan("gkcore.views")

    # include the pyramid-openapi3 plugin config
    # link: https://github.com/Pylons/pyramid_openapi3
    config.include("pyramid_openapi3")
    config.add_static_view(name="spec", path="spec")
    config.pyramid_openapi3_spec_directory(
        os.path.join(os.path.dirname(__file__), "spec/main.yaml"), route="/spec"
    )
    # launch the swagger ui at /docs/
    config.pyramid_openapi3_add_explorer(route="/docs/", ui_version="5.1.0")

    return CORS(
        config.make_wsgi_app(), headers="*", methods="*", maxage="180", origin="*"
    )
