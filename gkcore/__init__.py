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
   
    # organisation api routes
    config.add_route("organisation", "/organisation")
    config.add_route("organisation_all", "/organisation/all")
    config.add_route("organisation_gstin", "/organisation/gstin")
    config.add_route("organisation_attachment", "/organisation/attachment")
    config.add_route("organisation_gst_accounts", "/organisation/gst_accounts")
    config.add_route("organisation_gst_accounts_codes", "/organisation/gst_accounts/codes")
    config.add_route("organisation_registration", "/organisation/check_registration")
    config.add_route("organisation_orgname", "/organisation/check/{orgname}")
    
    # gkuser api routes
    config.add_route("gkuser", "/gkuser")
    config.add_route("organisation_gkusers", "/organisation/gkusers")
    config.add_route("gkuser_orgs", "/gkuser/orgs")
    config.add_route("gkuser_pwd_question", "/gkuser/pwd/question")
    config.add_route("gkuser_pwd_answer", "/gkuser/pwd/answer")
    config.add_route("gkuser_pwd_reset", "/gkuser/pwd/reset")
    config.add_route("gkuser_uname", "/gkuser/check/{username}")

    # invite api routes
    config.add_route("invite", "/invite")
    config.add_route("invite_accept", "/invite/accept")
    config.add_route("invite_reject", "/invite/reject")

    config.add_route("invoice", "/invoice")
    config.add_route("budget", "/budget")
    config.add_route("categoryspecs", "/categoryspecs")
    config.add_route("orgyears", "/orgyears/{orgname}/{orgtype}")
    config.add_route("transaction", "/transaction")
    config.add_route("bankrecon", "/bankrecon")
    config.add_route("accounts", "/accounts")
    config.add_route("account", "/account/{accountcode}")
    config.add_route("projects", "/projects")
    config.add_route("project", "/project/{projectcode}")
    config.add_route("customersupplier", "/customersupplier")
    config.add_route("unitofmeasurement", "/unitofmeasurement")
    config.add_route("accountsbyrule", "/accountsbyrule")
    config.add_route("login", "/login")
    config.add_route("groupallsubgroup", "/groupallsubgroup/{groupcode}")
    config.add_route("groupsubgroup", "/groupsubgroup/{groupcode}")
    config.add_route("groupsubgroups", "/groupsubgroups")
    config.add_route("groupDetails", "/groupDetails/{groupcode}")
    config.add_route("report", "/report")
    config.add_route("rollclose", "/rollclose")
    config.add_route("forgotpassword", "/forgotpassword")
    config.add_route("categories", "/categories")
    config.add_route("products", "/products")
    config.add_route("godown", "/godown")
    config.add_route("delchal", "/delchal")
    config.add_route("purchaseorder", "/purchaseorder")
    config.add_route("transfernote", "/transfernote")
    config.add_route("discrepancynote", "/discrepancynote")
    config.add_route("tax", "/tax")
    config.add_route("tax2", "/tax2")
    config.add_route("log", "/log")
    config.add_route("logSort", "/log/dateRange")
    config.add_route("rejectionnote", "/rejectionnote")
    config.add_route("billwise", "/billwise")
    config.add_route("state", "/state")
    config.add_route("drcrnote", "/drcrnote")
    config.add_route("gstreturns", "/gstreturns")
    config.add_route("dashboard", "/dashboard")
    config.add_route("config", "/config")
    config.add_route("spreadsheet", "/spreadsheet")
    config.add_route("ifsc", "/ifsc")
    config.add_route("dev", "/dev")  # Comment in production
    config.add_route("hsn", "/hsn")
    # import / export
    config.add_route("export-json", "/export/json")
    config.add_route("export-xlsx", "/export/xlsx")

    config.add_route("import-json", "/import/json")
    config.add_route("import-xlsx", "/import/xlsx")

    config.add_route("index", "/")
    config.add_route("gstnews", "/gst-news")
    # config.add_route("organisations", "/organisations") # legacy
    # config.add_route("users", "/users") # legacy
    # config.add_route("user", "/user") # legacy

    config.scan("gkcore.views")
    # include the pyramid pyramid-openapi3 plugin & it's config
    config.include("pyramid_openapi3")
    config.add_static_view(name="spec", path="spec")
    config.pyramid_openapi3_spec_directory(
        os.path.join(os.path.dirname(__file__), "spec/main.yaml")
    )
    # launch the swagger ui at /docs/
    config.pyramid_openapi3_add_explorer(ui_version="4.15.5")

    return CORS(
        config.make_wsgi_app(), headers="*", methods="*", maxage="180", origin="*"
    )
