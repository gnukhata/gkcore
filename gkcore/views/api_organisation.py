


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


from cornice.resource import resource, view 
from gkcore import eng
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json 
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
con = Connection
con = eng.connect()

@resource(collection_path='/organisation',path='/organisation/{orgcode}')
class api_organisation(object):
	def __init__(self,request):
		self.request = request
	@view(renderer='json')
	def collection_get(self):
		result = con.execute(select([gkdb.organisation.c.orgcode, gkdb.organisation.c.orgname, gkdb.organisation.c.orgtype,gkdb.organisation.c.yearstart,gkdb.organisation.c.yearend]))
		orgs = []
		for row in result:
			orgs.append({"orgcode":row["orgcode"], "orgname":row["orgname"], "orgtype":row["orgtype"], "yearstart":str(row["yearstart"]), "yearend":str(row["yearend"])})
		print orgs
		return orgs
		
	@view(renderer='json', accept='text/json')
	def collection_post(self):
		
		try:
			dataset = self.request.json_body
			result = con.execute(gkdb.organisation.insert(),[dataset])
			try:
				orgcode = con.execute(select([gkdb.organisation.c.orgcode]).where(and_(gkdb.organisation.c.orgname==dataset["orgname"],gkdb.organisation.c.orgtype==dataset["orgtype"],gkdb.organisation.c.yearstart==dataset["yearstart"],gkdb.organisation.c.yearend==dataset["yearend"])))
				user = {"username":"admin", "userrole":-1,"userpassword":"admin"}
				row = orgcode.fetchone()
				user["orgcode"] = row["orgcode"] 
				result1= con.execute(gkdb.Users.insert(),[user])
				
				return True
			except:
				result = con.execute(gkdb.organisation.delete().where(gkdb.organisation.c.orgcode==row["orgcode"]))
				return False
		except:
			return False
		
	
	def get(self):
		result = con.execute(select([gkdb.organisation]).where(gkdb.organisation.c.orgcode==self.request.matchdict["orgcode"]))
		orgDetails = []
		row = result.fetchone()
		orgDetails.append({"orgcity":row["orgcity"], "orgaddr":row["orgaddr"], "orgpincode":row["orgpincode"], "orgstate":row["orgstate"], "orgcountry":row["orgcountry"], "orgtelno":row["orgtelno"], "orgfax":row["orgfax"], "orgwebsite":row["orgwebsite"], "orgemail":row["orgemail"], "orgpan":row["orgpan"], "orgmvat":row["orgmvat"], "orgstax":row["orgstax"], "orgregno":row["orgregno"], "orgregdate":row["orgregdate"], "orgfcrano":row["orgfcrano"], "orgfcradate":row["orgfcradate"], "roflag":row["roflag"], "booksclosedflag":row["booksclosedflag"]	})
		return orgDetails 
	
	def collection_put(self):
		#auth check
		dataset = self.request.json_body
		result = con.execute(gkdb.organisation.update().where(gkdb.organisation.c.orgcode==dataset["orgcode"]).values(dataset))
		print result.rowcount
		return result.rowcount

	def collection_delete(self):
		#auth check
		dataset = self.request.json_body
		result = con.execute(gkdb.organisation.delete().where(gkdb.organisation.c.orgcode==dataset["orgcode"]))
		print result.rowcount
		return result.rowcount
	 	