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
from gkcore.models.gkdb import transfernote, stock
from sqlalchemy.sql import select, distinct
from sqlalchemy import func, desc
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ ,exc
from datetime import datetime,date
import jwt
import gkcore
from gkcore.models.meta import dbconnect

@view_defaults(route_name='transfernote')
class api_transfernote(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
		print "transfernote initialized"
		
		"""
	create method for discrepancynote resource.
	orgcode is first authenticated, returns a json object containing success.
	Inserts data into transfernote table. 
		-transfernoteno goes in dcinvtnid column of stock table.
		-dcinvflag column will be set to 20 for transfernote no entry.
		- inout column will be set 1 , i.e. goods are out from the godown.

	If stock table insert fails then the transfernote entry will be deleted. 
	"""
		
	@view_config(request_method='POST',renderer='json')
	def createtn(self):
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
				result = self.con.execute(transfernote.insert(),[dataset])
				productdict = dataset["productdetails"]
				try:
					for key in productdict.keys():
						stockdata = {}
						stockdata["productcode"] = key
						stockdata["dcinvtnid"] = dataset["transfernoteno"]
						stockdata["dcinvtnflag"] = 20
						stockdata["goid"] = dataset["fromgodown"]
						stockdata["inout"] = 1
						stockdata["qty"] = productdict[key]
						stockdata["orgcode"] = authDetails["orgcode"]
						pas = self.con.execute(stock.insert(),[stockdata])
						return {"gkstatus":enumdict["Success"]}
				except:
					result = self.con.execute(transfernote.delete().where( transfernote.c.transfernoteno == tnno ))
					return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
				
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
				
	@view_config(request_param='tn=all',request_method='GET',renderer='json')
	def getAllTransferNote(self):
		try:
			#print transfernote all
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				result = self.con.execute(select([transfernote]).order_by(transfernote.c.transfernotedate))
				tn = []
				for row in result:
					tn.append({"transfernoteno": row["transfernoteno"], "transfernotedate":datetime.strftime(row["transfernotedate"],'%d-%m-%Y') , "transportationmode":row["transportationmode"], "productdetails": row["productdetails"], "nopkt": row["nopkt"], "recieved": row["recieved"], "fromgodown": row["fromgodown"], "togodown": row["togodown"], "orgcode": row["orgcode"] })
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkdata":tn}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()
	
	@view_config(request_param='tn=single',request_method='GET',renderer='json')
	def getTn(self):
		try:
			#print "transfernote" 
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				result = self.con.execute(select([transfernote]).where(and_(transfernote.c.transfernoteno == self.request.params["transfernoteno"],transfernote.c.orgcode==authDetails["orgcode"])))
				tn = []
				for row in result:
					tn.append({"transfernoteno": row["transfernoteno"], "transfernotedate":datetime.strftime(row["transfernotedate"],'%d-%m-%Y') , "transportationmode":row["transportationmode"], "productdetails": row["productdetails"], "nopkt": row["nopkt"], "recieved": row["recieved"], "fromgodown": row["fromgodown"], "togodown": row["togodown"], "orgcode": row["orgcode"] })
					print tn
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkdata":tn}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()
	
				
				
	@view_config(request_param='browse',request_method='GET',renderer='json')
	def browse(self):
		try:
			#print transfernote all
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				result = self.con.execute(select([transfernote.c.transfernoteno,transfernote.c.transfernotedate,transfernote.c.fromgodown,transfernote.c.togodown]).order_by(transfernote.c.transfernotedate,transfernote.c.transfernoteno))
				tn = []
				for row in result:
					tn.append({"transfernoteno": row["transfernoteno"], "transfernotedate":datetime.strftime(row["transfernotedate"],'%d-%m-%Y') ,"fromgodown": row["fromgodown"], "togodown":row["togodown"] })
					print tn
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkdata":tn}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()
				
				
	@view_config(request_method='PUT', renderer='json')
	def updatetransfernote(self):
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
				print dataset
				productdict = dataset["productdetails"]
				productchanged = dataset["productchanged"]
				
				del dataset["productchanged"]
				result = self.con.execute(transfernote.update().where(transfernote.c.transfernoteno == dataset["transfernoteno"]).values(dataset))
				try:
					
					if (productchanged == True):
						result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid == dataset["transfernoteno"], stock.c.dcinvtnflag == 20)))
						print hello
						for key in productdict.keys():	 
							stockdata = {}
							stockdata["productcode"] = key
							stockdata["dcinvtnid"] = dataset["transfernoteno"]
							stockdata["dcinvtnflag"] = 20
							stockdata["goid"] = dataset["fromgodown"]
							stockdata["inout"] = 1
							stockdata["qty"] = productdict[key]
							stockdata["orgcode"] = authDetails["orgcode"]
							pas = self.con.execute(stock.insert(),[stockdata])
							
							if dataset.has_key("togodown"):
									stockdata["goid"] = dataset["togodown"]
									stockdata["inout"] = 0
									pas = self.con.execute(stock.insert(),[stockdata])
									
								
				except:
					return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
					
						
					   			
				return {"gkstatus":enumdict["Success"]}		   
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
					

				
	@view_config(request_param='received=true',request_method='PUT', renderer='json')
	def editransfernote(self):
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
				tnno = dataset["transfernoteno"]
				togodown = dataset["togodown"]
				orgcode = dataset["orgcode"]
				productdict = dataset["productdetails"]
				productkey = productdict.keys()
				result = self.con.execute(transfernote.update().where(transfernote.c.transfernoteno == tnno).value(recieved = True))
				try:
					for key in productkey:
						stockdata = {}
						stockdata["productcode"] = key
						stockdata["dcinvtnid"] = tnno
						stockdata["dcinvtnflag"] = 20
						stockdata["goid"] = togodown
						stockdata["inout"] = 0
						stockdata["qty"] = productdict[key]
						stockdata["orgcode"] = orgcode
						pas = self.con.execute(stock.insert(),[stockdata])
				except:
					result = self.con.execute(transfernote.update().where(transfernote.c.transfernoteno == tnno).value(recieved = False))
					return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
				
				return {"gkstatus":enumdict["Success"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
				
				
				
				
			

	
				
	@view_config(request_method='DELETE', renderer ='json')
	def deleteTransferNote(self):
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
				tnno = dataset["transfernoteno"]
				result = self.con.execute(transfernote.delete().where(transfernote.c.transfernoteno == tnno))
				
				if result.rowcount==1:
					result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid == tnno, stock.c.dcinvtnflag == 20)))
					return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()












	
	   
	   
