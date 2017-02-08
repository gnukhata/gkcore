
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.

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


#login function
from gkcore import eng, enumdict
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result
from Crypto.PublicKey import RSA
from gkcore.models.meta import inventoryMigration,addFields
import jwt
import gkcore
con= Connection

@view_config(route_name='login',request_method='POST',renderer='json')
def gkLogin(request):
	"""
	purpose: take org code, username and password and authenticate the user.
	Return true if username and password matches or false otherwise.
	description:
	The function takes the orgcode and matches the username and password.
	if it is correct then the user is authorised and a jwt object is created.
	The object will have the userid and orgcode and this will be sent back as a response.
	Else the function will not issue any token.
	"""
#	try:
	con= eng.connect()
	try:
		con.execute(select([gkdb.organisation.c.invflag]))
	
	except:
		inventoryMigration(con,eng)
	try:
		con.execute(select([gkdb.delchal.c.modeoftransport,gkdb.delchal.c.noofpackages]))
		con.execute(select([gkdb.transfernote.c.recieveddate]))
	except:
		addFields(con,eng)
		
	
	dataset = request.json_body
	result = con.execute(select([gkdb.users.c.userid]).where(and_(gkdb.users.c.username==dataset["username"], gkdb.users.c.userpassword== dataset["userpassword"], gkdb.users.c.orgcode==dataset["orgcode"])) )
	if result.rowcount == 1:
		record = result.fetchone()
		result = con.execute(select([gkdb.signature]))
		sign = result.fetchone()
		if sign == None:
			key = RSA.generate(2560)
			privatekey = key.exportKey('PEM')
			sig = {"secretcode":privatekey}
			gkcore.secret = privatekey
			result = con.execute(gkdb.signature.insert(),[sig])
		elif len(sign["secretcode"]) <= 20:
			result = con.execute(gkdb.signature.delete())
			if result.rowcount == 1:
				key = RSA.generate(2560)
				privatekey = key.exportKey('PEM')
				sig = {"secretcode":privatekey}
				gkcore.secret = privatekey
				result = con.execute(gkdb.signature.insert(),[sig])
		token = jwt.encode({"orgcode":dataset["orgcode"],"userid":record["userid"]},gkcore.secret,algorithm='HS256')
		return {"gkstatus":enumdict["Success"],"token":token }
	else:
		return {"gkstatus":enumdict["UnauthorisedAccess"]}
#	except:
#		return {"gkstatus":enumdict["ConnectionFailed"]}
#	finally:
#			con.close()

@view_config(route_name='login',request_method='GET',renderer='json')
def getuserorgdetails(request):
	try:
		token =request.headers["gktoken"]
	except:
		return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
	authDetails = authCheck(token)
	if authDetails["auth"] == False:
		return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
	else:
		try:
			con = eng.connect()
			user=con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
			row = user.fetchone()
			flagsdata=con.execute(select([gkdb.organisation.c.booksclosedflag,gkdb.organisation.c.roflag]).where(gkdb.organisation.c.orgcode == authDetails["orgcode"] ))
			flags = flagsdata.fetchone()
			return {"gkstatus": gkcore.enumdict["Success"], "gkresult":{"userrole":int(row["userrole"]),"booksclosedflag":int(flags["booksclosedflag"]),"roflag":int(flags["roflag"])}}
		except:
			return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
		finally:
			con.close();

def authCheck(token):
	"""
	Purpose: on every request check if userid and orgcode are valid combinations
	"""
	try:
		tokendict = jwt.decode(token,gkcore.secret,algorithms=['HS256'])
		tokendict["auth"] = True
		tokendict["orgcode"]=int(tokendict["orgcode"])
		tokendict["userid"]=int(tokendict["userid"])
		return tokendict
	except:
		tokendict = {"auth":False}
		return tokendict
