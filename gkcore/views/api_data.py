"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020 Digital Freedom Foundation & Accion Labs PVT LTD
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
"Krishnakant Mane" <kk@dff.org.in>
"Arun Kelkar" <arunkelkar@dff.org.in>
"Abhijith Balan" <abhijithb21@openmailbox.org>
"Prajkta Patkar" <prajakta@dff.org.in>
"Sai Karthik" <kskarthik@disroot.org>
"""
from pyramid.view import view_config, view_defaults
from pyramid.response import Response
from pyramid.request import Request

from openpyxl import load_workbook
from openpyxl import Workbook
from openpyxl.styles import Font
import json, io
from gkcore.models.meta import gk_api, dbconnect
from sqlalchemy.engine.base import Connection
from gkcore import eng, enumdict
from gkcore.views.api_user import authCheck, getUserRole
import gkcore.views.data as data

# import datetime

# def get_table_array(name):
#     c = eng.connect()
#     table = c.execute(f"select * from {name} where orgcode = 1")
#     content = io.StringIO()
#     writer = csv.writer(
#         content, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL
#     )
#     writer.writerow(table.keys())
#     for row in table:
#         writer.writerow(row)
#     return content.getvalue()


@view_defaults(route_name="data")
class api_data(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.conn = Connection
        print("Data Module Loaded")

    @view_config(request_param="import-tally", request_method="POST", renderer="json")
    def imt(self):
        return self.spreadsheet_handler.import_tally(self)

    @view_config(request_param="import-json", request_method="POST", renderer="json")
    def ij(self):
        return data.json_handler.import_json(self)

    @view_config(request_param="export", request_method="GET", renderer="json")
    def exl(self):
        return data.spreadsheet_handler.export_ledger(self)

    @view_config(request_param="export-json", request_method="GET", renderer="json")
    def ej(self):
        return data.json_handler.export_json(self)
