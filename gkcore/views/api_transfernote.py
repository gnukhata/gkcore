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
"""


from pyramid.view import view_defaults,  view_config
from gkcore.views.api_login import authCheck
from gkcore import eng, enumdict
from pyramid.request import Request
from gkcore.models.gkdb import transfernote, stock,godown, product
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


	@view_config(request_method='POST',renderer='json')
	def createtn(self):
		"""	 create method for discrepancynote resource.
			 orgcode is first authenticated, returns a json object containing success.
			 Inserts data into transfernote table.
					-transfernoteno goes in dcinvtnid column of stock table.
					-dcinvflag column will be set to 20 for transfernote no entry.
					- inout column will be set 1 , i.e. goods are out from the godown.
			 If stock table insert fails then the transfernote entry will be deleted.

		"""
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
				transferdata = dataset["transferdata"]
				stockdata = dataset["stockdata"]
				transferdata["orgcode"] = authDetails["orgcode"]
				stockdata["orgcode"] = authDetails["orgcode"]
				result = self.con.execute(transfernote.insert(),[transferdata])
				if result.rowcount==1:
					transfernoteiddata = self.con.execute(select([transfernote.c.transfernoteid]).where(and_(transfernote.c.orgcode==authDetails["orgcode"],transfernote.c.transfernoteno==transferdata["transfernoteno"])))
					transfernoteidrow = transfernoteiddata.fetchone()
					stockdata["dcinvtnid"] = transfernoteidrow["transfernoteid"]
					stockdata["dcinvtnflag"] = 20
					stockdata["inout"] = 15
					items = stockdata.pop("items")
					try:
						for key in items.keys():
							stockdata["productcode"] = key
							stockdata["qty"] = items[key]
							result = self.con.execute(stock.insert(),[stockdata])
					except:
						result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==transfernoteidrow["transfernoteid"],stock.c.dcinvtnflag==20)))
						result = self.con.execute(transfernote.delete().where(transfernote.c.transfernoteid==transfernoteidrow["transfernoteid"]))
						return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
					return {"gkstatus":enumdict["Success"]}
				else:
					return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()


	@view_config(request_method='GET',request_param='tn=all',renderer='json')
	def getAllTransferNote(self):
		"""This method returns	all existing transfernotes  """
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
				result = self.con.execute(select([transfernote.c.transfernotedate,transfernote.c.transfernoteid,transfernote.c.transfernoteno]).where(transfernote.c.orgcode==authDetails["orgcode"]).order_by(transfernote.c.transfernotedate))
				tn = []
				for row in result:
					tn.append({"transfernoteno": row["transfernoteno"],"transfernoteid": row["transfernoteid"], "transfernotedate":datetime.strftime(row["transfernotedate"],'%d-%m-%Y')})
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkresult":tn}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	@view_config(request_method='GET',request_param='tn=single',renderer='json')
	def getTn(self):
		""" Shows single transfernote by matching transfernoteno			   """
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
				result = self.con.execute(select([transfernote]).where(and_(transfernote.c.transfernoteid == self.request.params["transfernoteid"])))
				row = result.fetchone()
				togo = self.con.execute(select([godown.c.goname,godown.c.goaddr,godown.c.state]).where(godown.c.goid==row["togodown"]))
				togodata = togo.fetchone()
				items = {}
				stockdata = self.con.execute(select([stock.c.productcode,stock.c.qty,stock.c.goid]).where(and_(stock.c.dcinvtnflag==20,stock.c.dcinvtnid==self.request.params["transfernoteid"])))
				for stockrow in stockdata:
					productdata = self.con.execute(select([product.c.productdesc]).where(product.c.productcode==stockrow["productcode"]))
					productdesc = productdata.fetchone()
					items[stockrow["productcode"]] = {"qty":stockrow["qty"],"productdesc":productdesc["productdesc"]}
					goiddata = stockrow["goid"]
				fromgo = self.con.execute(select([godown.c.goname,godown.c.goaddr,godown.c.state]).where(godown.c.goid==goiddata))
				fromgodata = fromgo.fetchone()
				tn={"transfernoteno": row["transfernoteno"],
					"transfernotedate":datetime.strftime(row["transfernotedate"],'%d-%m-%Y'),
					"transportationmode":row["transportationmode"],
					"productdetails": items,
					"nopkt": row["nopkt"],
					"recieved": row["recieved"],
					"togodown": togodata["goname"],
					"togodownstate": togodata["state"],
					"togodownaddr": togodata["goaddr"],
					"togodownid": row["togodown"],
					"fromgodownid":goiddata,
					"fromgodown": fromgodata["goname"],
					"fromgodownstate": fromgodata["state"],
					"fromgodownaddr": fromgodata["goaddr"],
					"issuername":row["issuername"],
					"designation":row["designation"],
					"orgcode": row["orgcode"] }
				return {"gkstatus":enumdict["Success"], "gkresult":tn}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()


	@view_config(request_method='PUT', renderer='json')
	def updatetransfernote(self):
		""" This method updates the transfer note, If the transfernote is updated at the same time stock table also has to updated with new entries  """
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
				transferdata = dataset["transferdata"]
				stockdata = dataset["stockdata"]
				transferdata["orgcode"] = authDetails["orgcode"]
				stockdata["orgcode"] = authDetails["orgcode"]
				stockdata["dcinvtnid"] = transferdata["transfernoteid"]
				stockdata["dcinvtnflag"] = 20
				stockdata["inout"]=15
				result = self.con.execute(transfernote.update().where(transfernote.c.transfernoteid==transferdata["transfernoteid"]).values(transferdata))
				if result.rowcount==1:
					result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==transferdata["transfernoteid"],stock.c.dcinvtnflag==20)))
					items = stockdata.pop("items")
					for key in items.keys():
						stockdata["productcode"] = key
						stockdata["qty"] = items[key]
						result = self.con.execute(stock.insert(),[stockdata])
					return {"gkstatus":enumdict["Success"]}
				else:
					return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()



	@view_config(request_param='received=true',request_method='PUT', renderer='json')
	def editransfernote(self):
		""" when other godown receives the stock , Received entry is made and according to that changes are done ithe stock table								  """
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
				transferdata = self.request.json_body
				stockdata = {}
				stockdata["orgcode"] = authDetails["orgcode"]
				stockdata["dcinvtnid"] = transferdata["transfernoteid"]
				stockdata["dcinvtnflag"] = 20
				stockdata["inout"]=9
				result = self.con.execute(select([transfernote.c.togodown,transfernote.c.recieved]).where(transfernote.c.transfernoteid==transferdata["transfernoteid"]))
				row = result.fetchone()
				if row["recieved"]:
					return {"gkstatus":enumdict["ActionDisallowed"]}
				stockdata["goid"]=row["togodown"]
				stockresult = self.con.execute(select([stock.c.productcode,stock.c.qty]).where(and_(stock.c.dcinvtnid==transferdata["transfernoteid"],stock.c.dcinvtnflag==20)))
				for key in stockresult:
					stockdata["productcode"] = key["productcode"]
					stockdata["qty"] = key["qty"]
					result = self.con.execute(stock.insert(),[stockdata])
				result = self.con.execute(transfernote.update().where(transfernote.c.transfernoteid==transferdata["transfernoteid"]).values(recieved=True))
				return {"gkstatus":enumdict["Success"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

	@view_config(request_method='DELETE', renderer ='json')
	def deleteTransferNote(self):
		""" This method deletes the row of transfernote   by matching transfernote no which is provided	   """
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
				result = self.con.execute(transfernote.delete().where(transfernote.c.transfernoteid == dataset["transfernoteid"]))
				if result.rowcount==1:
					result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid == dataset["transfernoteid"], stock.c.dcinvtnflag == 20)))
					return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
