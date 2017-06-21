"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
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
Prajkta Patkar" <prajkta.patkar007@gmail.com>
"""

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc,alias, or_, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.sql.expression import null
from gkcore.models.meta import dbconnect
from gkcore.models.gkdb import accounts
@view_defaults(route_name='billwise')
class api_billWise(object):
    """
    This class is a resource for billwise accounting.
It will be used for creating entries in the billwise table and updating it as new entries are passed.
    The invoice table will also be updated every time an adjustment is made.
    We will have get and post methods.
    """
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print "billwise initialized"

        
        
