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
import jwt
import gkcore
from gkcore.models.meta import dbconnect

@view_defaults(route_name='transfernote')
class api_transfernote(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
		
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
				fromgodown = dataset["fromgodown"]
				tnno = dataset["transfernoteno"]
				orgcode = dataset["orgcode"]
				productdict = dataset["productdetails"]
				productkey = productdict.keys()
				print productkey
				result = self.con.execute(transfernote.insert(),[dataset])
				try:
					for key in productkey:
						stockdata = {}
						stockdata["productcode"] = key
						stockdata["dcinvtnid"] = tnno
						stockdata["dcinvtnflag"] = 20
						stockdata["goid"] = fromgodown
						stockdata["inout"] = 1
						stockdata["qty"] = productdict[key]
						stockdata["orgcode"] = orgcode
						print stockdata
						pas = self.con.execute(stock.insert(),[stockdata])
				except:
					return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
			finally:
				self.con.close()
				
	@view_config(request_param="tn=all",request_method='GET',renderer='json')
	def getAllTransferNote(self):
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
				result = self.con.execute(select([transfernote.c.transfernoteno, transfernote.c.transfernotedate,transfernote.c.transportationmode,transfernote.c.productdetails,transfernote.c.nopkt, transfernote.c.recieved,transfernote.c.fromgodown,transfernote.c.togodown,transfernote.c.orgcode]).order_by(transfernote.c.transfernotedate))
				transfernote = []
				for row in result:
					tn.append({"TransferNote no": row["transfernoteno"], "TransferNote Date":row["transfernotedate"] , "Transportation Mode":row["transportationmode"], "Product Details": row["productdetails"], "No. of packets": row["nopkt"], "Recieved": row["recieved"], "From godown": row["fromgodown"], "To godown": row["togodown"], "OrgCode": row["orgcode"] })
				self.con.close()
				return {"gkstatus":enumdict["Success"], "gkdata":transfernote}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}

				
	@view_config(request_method='PUT', renderer='json')
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
				result = self.con.execute(transfernote.update().where(transfernote.c.transfernoteno==dataset["transfernoteno"]).values(dataset))
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
				result = self.con.execute(transfernote.delete().where(transfernote.c.transfernoteno == dataset["transfernoteno"]))
				#result = self.con.execute(stock.delete().where(and_(stock.c.dcinvid==dataset["dcid"],stock.c.dcinvflag==4)))
				return {"gkstatus":enumdict["Success"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()












	
	   
	   
