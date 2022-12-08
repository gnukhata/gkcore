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

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.engine.base import Connection

import gkcore.views.data as data


class api_data(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.conn = Connection

    @view_config(
        route_name="export-xlsx",
        request_method="GET",
        renderer="json",
    )
    def export_spreadsheet(self):
        return data.spreadsheet_handler.export_ledger(self)

    @view_config(
        route_name="export-json",
        request_method="GET",
        renderer="json",
    )
    def export_json(self):
        return data.json_handler.export_json(self)

    @view_config(
        route_name="import-xlsx",
        request_method="POST",
        renderer="json",
    )
    def import_tally_spreadsheet(self):
        return data.spreadsheet_handler.import_tally(self)

    @view_config(
        route_name="import-json",
        request_method="POST",
        renderer="json",
    )
    def import_json(self):
        return data.json_handler.import_json(self)
