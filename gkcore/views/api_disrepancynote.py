"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

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
"Prajkta Patkar"<prajkta.patkar007@gmail.com>
"""


from pyramid.view import view_defaults,  view_config
from gkcore.views.api_login import authCheck
from gkcore import eng, enumdict
from pyramid.request import Request
from gkcore.models.gkdb import discrepancynote
from sqlalchemy.sql import select, distinct
from sqlalchemy import func, desc
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ ,exc
from datetime import datetime,date
import jwt
import gkcore
from gkcore.models.meta import dbconnect


@view_defaults(route_name='discrepancynote')
class api_transfernote(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
		print "discrepancyote initialized"
		
	@view_config(request_method='POST',renderer='json')
	def createdn(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dataset = self.request.json_body
				dataset["orgcode"] = authDetails["orgcode"]
				result = self.con.execute(discrepancynote.insert(),[dataset])
			
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
				
				
				
	@view_config(request_param='dn=all',request_method='GET',renderer='json')
	def getAllDn(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				result = self.con.execute(select([discrepancynote]).order_by(discrepancynote.c.discrepancydate))
				dn = []
				for row in result:
					
					dn.append({"discrepancyno": row["discrepancyno"], "discrepancydate":datetime.strftime(row["discrepancydate"],'%d-%m-%Y') , "discrepancydetails": row["discrepancydetails"],"dcinvpotncode":["dcinvpotncode"],"dcinvpotnflag":row["dcinvpotnflag"],"supplier":row["supplier"],"orgcode": row["orgcode"] })
					#print dn
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult":purchaseorders}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			
			
			
			
			
			
	@view_config(request_method='PUT',renderer='json')
	def editDiscrepancyNote(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dataset = self.request.json_body
				result = self.con.execute(discrepancynote.update().where(discrepancynote.c.discrepancyno == dataset["discrepancyno"]).values(dataset))
				
				return {"gkstatus":enumdict["Success"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()		
				
				
				
				
				
				
	@view_config(request_method='DELETE',renderer='json')
	def deleteDiscrepancyNote(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				dataset = self.request.json_body
				result = self.con.execute(discrepancynote.delete().where(discrepancynote.c.discrepancyno == dataset["discrepancyno"]))
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
