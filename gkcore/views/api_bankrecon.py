
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
#imports contain sqlalchemy modules,
#enumdict containing status messages,
#eng for executing raw sql,
#gkdb from models for all the alchemy expressed tables.
#view_default for setting default route
#view_config for per method configurations predicates etc.
from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models.gkdb import bankrecon,vouchers,accounts
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result
from datetime import datetime


"""
default route to be attached to this resource.
refer to the __init__.py of main gkcore package for details on routing url
"""
@view_defaults(route_name='bankrecon')
class bankreconciliation(object):
	#constructor will initialise request.
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection

	@view_config(request_method='GET',renderer='json')
	def banklist(self):
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
				result = self.con.execute(select([gkdb.accounts.c.accountname,gkdb.accounts.c.accountcode]).where(and_(gkdb.accounts.c.orgcode==authDetails["orgcode"],gkdb.accounts.c.groupcode ==(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.orgcode==authDetails["orgcode"],gkdb.groupsubgroups.c.groupname=='Bank'))))).order_by(gkdb.accounts.c.accountname))
				accs = []
				for row in result:
					accs.append({"accountcode":row["accountcode"], "accountname":row["accountname"]})
				self.con.close()
				return {"gkstatus": enumdict["Success"], "gkresult":accs}
			except:
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"] }

	@view_config(request_method='GET', request_param='recon=uncleared',renderer='json')
	def getUnclearedTransactions(self):
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
				accountCode = self.request.params["accountcode"]
				calculateFrom = datetime.strptime(str(self.request.params["calculatefrom"]),"%Y-%m-%d")
				calculateTo = datetime.strptime(str(self.request.params["calculateto"]),"%Y-%m-%d")
				result = self.con.execute(select([bankrecon]).where(bankrecon.c.accountcode==accountCode))
				recongrid=[]
				for record in result:
					if record["clearancedate"]!=None and record["clearancedate"]<calculateFrom:
						continue
					else:
						voucherdata=self.con.execute(select([vouchers]).where(and_(vouchers.c.vouchercode==int(record["vouchercode"]),vouchers.c.delflag==False,vouchers.c.voucherdate<=calculateTo)))
						voucher= voucherdata.fetchone()
						if voucher==None:
							continue
						print "awidaijdoygfia: ",voucher
						if voucher["drs"].has_key(str(record["accountcode"])):
							print "ifffff,  ",voucher["drs"]
							for cr in voucher["crs"].keys():
	  							accountnameRow = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(cr)))
	  							accountname = accountnameRow.fetchone()
								reconRow ={"reconcode":record["reconcode"],"date":datetime.strftime(voucher["voucherdate"],"%d-%m-%Y"),"particulars":str(accountname["accountname"]),"vno":voucher["vouchernumber"],"dr":"%.2f"%float(voucher["crs"][cr]),"cr":"","narration":voucher["narration"]}
								if record["clearancedate"]==None:
									reconRow["clearancedate"]=""
								else:
									reconRow["clearancedate"]=datetime.strftime(record["clearancedate"],"%d-%m-%Y")
								if record["memo"]==None:
									reconRow["memo"]=""
								else:
									reconRow["memo"]=record["memo"]
								recongrid.append(reconRow)

						if voucher["crs"].has_key(str(record["accountcode"])):
							for dr in voucher["drs"].keys():
	  							accountnameRow = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(dr)))
	  							accountname = accountnameRow.fetchone()
								reconRow ={"reconcode":record["reconcode"],"date":datetime.strftime(voucher["voucherdate"],"%d-%m-%Y"),"particulars":str(accountname["accountname"]),"vno":voucher["vouchernumber"],"cr":"%.2f"%float(voucher["drs"][dr]),"dr":"","narration":voucher["narration"]}
								if record["clearancedate"]==None:
									reconRow["clearancedate"]=""
								else:
									reconRow["clearancedate"]=datetime.strftime(record["clearancedate"],"%d-%m-%Y")
								if record["memo"]==None:
									reconRow["memo"]=""
								else:
									reconRow["memo"]=record["memo"]
								recongrid.append(reconRow)
				self.con.close()
				return {"gkstatus":enumdict["Success"],"gkresult":recongrid}
			except:
				self.con.close()
				return{"gkstatus":enumdict["ConnectionFailed"]}
