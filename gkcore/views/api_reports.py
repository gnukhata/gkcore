
"""
Copyright (C) 2014 2015 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

  GNUKhata is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public
  License along with GNUKhata (COPYING); if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,


Contributor: 
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>

"""


from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models.gkdb import accounts, vouchers, groupsubgroups 
from sqlalchemy.sql import select
import json 
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc 
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result

con = Connection
con = eng.connect()


@view_defaults(route_name='reports' , request_method='GET')
class api_reports(object):
	def __init__(self,request):
		self.request = Request
		self.request = request

	#calculateBalance is a private method so we won't expose it as REST method.
	def calculateBalance(self,orgCode,accountName,financialStart,calculateFrom,calculateTo):
		#first we will get the groupname for the provided account.
		#note that the given account may be associated with a subgroup for which we must get the group.
		groupData = eng.execute("select groupname from groupsubgroups where groupcode = (select subgroupof from groupsubgroups where groupcode=(select groupcode from accounts where accountname ="+accountName+"and orgcode = orgCode ))")
		groupRecord = groupData.fetchone()
		groupName = groupRecord["groupname"]
		#now similarly we will get the opening balance for this account.
		
