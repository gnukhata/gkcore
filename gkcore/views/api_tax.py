
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
"Prajkta Patkar"<prajkta.patkar007@gmail.com>
"Bhagyashree Pandhare"<bhagya.pandhare@openmailbox.org>
"""

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models.gkdb import tax,users
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result
import gkcore


@view_defaults(route_name='tax')
class api_tax(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
		print "tax initialized"

	@view_config(request_method='POST',renderer='json')
	def addtax(self):
		""" This method creates tax
			First it checks the user role if the user is admin then only user can add new tax					  """
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
				user=self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				dataset = self.request.json_body
				if userRole["userrole"]==-1 or userRole["userrole"]==1 or userRole["userrole"]==0:
					dataset["orgcode"] = authDetails["orgcode"]

					result = self.con.execute(tax.insert(),[dataset])
					return {"gkstatus":enumdict["Success"]}
				else:
					return {"gkstatus":  enumdict["BadPrivilege"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	@view_config(request_method='GET',request_param='pscflag',renderer='json')
	def getprodtax(self):
		"""
		This method will return the list of taxes for a product or a category.
		The tax will be either returned for a given product or a category, or with the combination of product and state (Specially for VAT).
		Takes in a parameter for productcode or categorycode, optionally statecode.
		If the flag is p then all the taxes for that product will be returned.
		If it is s then for that product for that state will be returned.
		If it is c then for that category will be returned.
		returns a list of JSON objects.
		"""
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
				if(self.request.params["pscflag"]=="p"):
					result = self.con.execute(select([tax.c.taxid,tax.c.taxname,tax.c.taxrate,tax.c.state]).where(tax.c.productcode==self.request.params["productcode"]))
					tx =[]
					for row in result:
						tx.append({"taxid":row["taxid"],"taxname":row["taxname"], "taxrate":"%.2f"%float(row["taxrate"]),"state":row["state"]})
					return {"gkstatus":enumdict["Success"],"gkresult":tx}


				if(self.request.params["pscflag"]=="s"):
					result = self.con.execute(select([tax.c.taxid,tax.c.taxname,tax.c.taxrate]).where(and_(tax.c.productcode==self.request.params["productcode"],tax.c.state==self.request.params["state"])))
					tx =[]
					for row in result:
						tx.append({"taxid":row["taxid"],"taxname":row["taxname"], "taxrate":"%.2f"%float(row["taxrate"])})
					return {"gkstatus":enumdict["Success"], "gkresult":tx}
					self.con.close()

				if(self.request.params["pscflag"]=="c"):
					result = self.con.execute(select([tax.c.taxid,tax.c.taxname,tax.c.taxrate,tax.c.state]).where(tax.c.categorycode==self.request.params["categorycode"]))
					tx =[]
					for row in result:
						tx.append({"taxid":row["taxid"],"taxname":row["taxname"], "taxrate":"%.2f"%float(row["taxrate"]),"state":row["state"]})
					return {"gkstatus":enumdict["Success"],"gkresult":tx}
				return {"gkstatus":enumdict["Success"],}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()


	@view_config(request_method='GET',renderer='json')
	def getAllTax(self):
		"""This method returns	all existing data about taxes for current organisation   """
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

				result = self.con.execute(select([tax]).where(tax.c.orgcode==authDetails["orgcode"]))
				tx = []
				for row in result:
					tx.append({"taxid": row["taxid"], "taxname":row["taxname"], "taxrate":"%.2f"%float(row["taxrate"]),"state":row["state"], "categorycode": row["categorycode"], "productcode": row["productcode"], "orgcode": row["orgcode"] })

				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkdata":tx}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()


	@view_config(request_method='PUT', renderer='json')
	def edittaxdata(self):
		"""  This method updates the taxdata				   """
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
				user=self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				dataset = self.request.json_body

				if userRole["userrole"]==-1 or userRole["userrole"]==1 or userRole["userrole"]==0:

					result = self.con.execute(tax.update().where(tax.c.taxid == dataset["taxid"]).values(dataset))
					return {"gkstatus":enumdict["Success"]}
				else:
					return {"gkstatus":  enumdict["BadPrivilege"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_method='DELETE', renderer ='json')
	def deletetaxdata(self):
		"""  This method delets the tax data by matching taxid				 """
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
				user=self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				dataset = self.request.json_body
				if userRole["userrole"]==-1 or userRole["userrole"]==1 or userRole["userrole"]==0:
					result = self.con.execute(tax.delete().where(tax.c.taxid==dataset["taxid"]))
					return {"gkstatus":enumdict["Success"]}
				else:
					{"gkstatus":  enumdict["BadPrivilege"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
