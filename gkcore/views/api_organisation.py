


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


from pyramid.view import view_defaults,  view_config
from gkcore import eng
from gkcore.models import gkdb
from sqlalchemy.sql import select, distinct
import json 
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
con = Connection
con = eng.connect()

@view_defaults(route_name='organisations')
class api_organisation(object):
	def __init__(self,request):
		self.request = request
		
	@view_config(request_method='GET', renderer ='json')
	def getOrgs(self):
		result = con.execute(select([gkdb.organisation.c.orgname, gkdb.organisation.c.orgtype]).distinct())
		orgs = []
		for row in result:
			orgs.append({"orgname":row["orgname"], "orgtype":row["orgtype"]})
		print orgs
		return orgs
	
	@view_config(route_name='orgyears', request_method='GET', renderer ='json')
	def getYears(self):
		result = con.execute(select([gkdb.organisation.c.yearstart, gkdb.organisation.c.yearend]).where(and_(gkdb.organisation.c.orgname==self.request.matchdict["orgname"], gkdb.organisation.c.orgtype == self.request.matchdict["orgtype"])))
		years = []
		for row in result:
			years.append({"yearstart":str(row["yearstart"]), "yearend":str(row["yearend"])})
		print years
		return years
		
	@view_config(request_method='POST',renderer='json')
	def postOrg(self):
		
		try:
			dataset = self.request.json_body
			print dataset
			result = con.execute(gkdb.organisation.insert(),[dataset])
			print result.rowcount
			return result.rowcount
		except:
			return False
		
	@view_config(route_name='organisation', request_method='GET',renderer='json')
	def getOrg(self):
		result = con.execute(select([gkdb.organisation]).where(gkdb.organisation.c.orgcode==self.request.matchdict["orgcode"]))
		row = result.fetchone()
		orgDetails={"orgname":row["orgname"], "orgtype":row["orgtype"], "yearstart":str(row["yearstart"]), "yearend":str(row["yearend"]),"orgcity":row["orgcity"], "orgaddr":row["orgaddr"], "orgpincode":row["orgpincode"], "orgstate":row["orgstate"], "orgcountry":row["orgcountry"], "orgtelno":row["orgtelno"], "orgfax":row["orgfax"], "orgwebsite":row["orgwebsite"], "orgemail":row["orgemail"], "orgpan":row["orgpan"], "orgmvat":row["orgmvat"], "orgstax":row["orgstax"], "orgregno":row["orgregno"], "orgregdate":row["orgregdate"], "orgfcrano":row["orgfcrano"], "orgfcradate":row["orgfcradate"], "roflag":row["roflag"], "booksclosedflag":row["booksclosedflag"]	}
		return orgDetails 
	@view_config(request_method='PUT', renderer='json')
	def putOrg(self):
		#auth check
		try:
			dataset = self.request.json_body
			result = con.execute(gkdb.organisation.update().where(gkdb.organisation.c.orgcode==dataset["orgcode"]).values(dataset))
			print result.rowcount
			return result.rowcount
		except:
			return False
	@view_config(request_method='DELETE', renderer='json')
	def deleteOrg(self):
		#auth check
		dataset = self.request.json_body
		result = con.execute(gkdb.organisation.delete().where(gkdb.organisation.c.orgcode==dataset["orgcode"]))
		print result.rowcount
		return result.rowcount
	
	@view_config(route_name='orgid', request_method='GET',renderer='json')
	def getOrgCode(self):
		result = con.execute(select([gkdb.organisation.c.orgcode]).where(and_(gkdb.organisation.c.orgname==self.request.matchdict["orgname"], gkdb.organisation.c.orgtype==self.request.matchdict["orgtype"], gkdb.organisation.c.yearstart==self.request.matchdict["yearstart"], gkdb.organisation.c.yearend==self.request.matchdict["yearend"])))
		row = result.fetchone()
		orgcode={"orgcode":row["orgcode"]}
		return orgcode 
	 	