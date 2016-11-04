"""REST API for tax """

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
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
#		print authCheck(token)
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		else:
			try:
				
				self.con = eng.connect()
				user=self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				dataset = self.request.json_body
				if userRole[0]==-1:
					dataset["orgcode"] = authDetails["orgcode"]
					print dataset
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
				
	@view_config(request_method='GET',request_param='psflag',renderer='json')
	def getprodtax(self):
		"""
		This method will return the list of taxes for a product.
		The tax will be either returned for a given product, or with the combination of product and state (Specially for VAT).
		Takes in a parameter for productcode, optionally statecode.
		If the flag is p then all the taxes for that product will be returned.
		If it is s then for that product for that state will be returned.
		returns a list of JSON objects.
		"""
		try:
			print "all tax"
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			#try:
				self.con = eng.connect()
				if(self.request.params["psflag"]=="p"):
					result = self.con.execute(select([tax.c.taxname,tax.c.taxrate,tax.c.state]).where(tax.c.productcode==self.request.params["productcode"]))
					taxRow = result.fetchone()
					taxDetails = {"taxname":taxRow["taxname"]}
					#return result
					return {"gkstatus":enumdict["Success"],"gkresult":result}
					self.con.close()
				
				if(self.request.params["psflag"]=="s"):
					result = self.con.execute(select([tax.c.taxname,tax.c.taxrate]).where(and_(tax.c.productcode==self.request.params["productcode"],tax.c.state==self.request.params[state])))
					
					return {"gkstatus":enumdict["Success"], "gkresult":result}
					self.con.close()
					
			
				return {"gkstatus":enumdict["Success"],}
			#except:
				#self.con.close()
				#return {"gkstatus":enumdict["ConnectionFailed"]}
			#finally:
				#self.con.close()

			
					
			
		
		
		
	@view_config(request_method='GET',renderer='json')
	def getAllTax(self):
		"""This method returns	all existing data about taxes """
		try:
			print "all tax"
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				result = self.con.execute(select([tax]).order_by(tax.c.taxid))
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
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
#		print authCheck(token)
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				print "editing data"
				user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				dataset = self.request.json_body
				if userRole[0]==-1:
					result = self.con.execute(gkdb.users.update().where(gkdb.tax.c.taxid==dataset["taxid"]).values(dataset))
					print result
					return {"gkstatus":enumdict["Success"]}
				else:
					return {"gkstatus":  enumdict["BadPrivilege"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
				
	@view_config(request_method='DELETE', renderer ='json')
	def deletetaxdata(self):
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
				user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				dataset = self.request.json_body
				if userRole[0]==-1:
					result = self.con.execute(gkdb.tax.delete().where(gkdb.tax.c.taxid==dataset["taxid"]))
					return {"gkstatus":enumdict["Success"]}
				else:
					{"gkstatus":  enumdict["BadPrivilege"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()