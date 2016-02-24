
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


from gkcore import eng
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json 
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ , alias
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
import jwt
import gkcore
from gkcore.views.api_login import authCheck
from sqlalchemy.sql.expression import null

con = Connection
con = eng.connect()


@view_defaults(route_name='groupsubgroups')
class api_user(object):
	def __init__(self,request):
		self.request = Request
		self.request = request

	@view_config(request_method='POST',renderer='json')
	def addSubgroup(self):
		try:
			dataset = self.request.json_body
			print dataset
			result = con.execute(gkdb.groupsubgroups.insert(),[dataset])
			return result.rowcount
		except:
			return False
	@view_config(route_name='groupsubgroup', request_method='GET',renderer='json')
	def getGroupSubgroup(self):
		resultset = eng.execute("select g.groupname, sg.groupname as subgroupname from groupsubgroups as g, groupsubgroups as sg where g.groupcode=sg.subgroupof and g.groupcode="+self.request.matchdict["groupcode"])
		row = resultset.fetchone()
		dict = {"groupname":row["groupname"],"subgroupname":row["subgroupname"]}
		print dict
		return dict
	@view_config(request_method='PUT', renderer='json')
	def editSubgroup(self):
		try:
			dataset = self.request.json_body
			result = con.execute(gkdb.groupsubgroups.update().where(and_(gkdb.groupsubgroups.c.groupname==dataset["groupname"],gkdb.groupsubgroups.c.orgcode==dataset["orgcode"])).values(dataset))
			print result.rowcount
			return result.rowcount
		except:
			return False
	@view_config(request_method='GET', renderer ='json')
	def getAllGroups(self):
		result = con.execute(select([gkdb.groupsubgroups.c.groupname,gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.orgcode==self.request.matchdict["orgcode"], gkdb.groupsubgroups.c.subgroupof==null())))
		grps = []
		for row in result:
			grps.append({"groupname":row["groupname"], "groupcode":row["groupcode"]})
		print grps
		return grps
	
	@view_config(route_name="groupDetails", request_method='GET', renderer ='json')
	def getSubgroupsByGroup(self):
		result = con.execute(select([gkdb.groupsubgroups.c.groupname,gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.subgroupof==self.request.matchdict["groupcode"])))
		subs = []
		for row in result:
			subs.append({"subgroupname":row["groupname"], "groupcode":row["groupcode"]})
		print subs
		return subs
