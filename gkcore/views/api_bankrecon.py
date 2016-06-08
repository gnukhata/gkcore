
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
from gkcore.models.gkdb import bankrecon,vouchers,accounts,organisation
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import null
import json
from gkcore.views.api_reports import calculateBalance
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc,or_
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
				return {"gkstatus": enumdict["Success"], "gkresult":accs}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"] }
			finally:
				self.con.close()

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
				recongrid= self.showUnclearedTransactions(accountCode,calculateFrom,calculateTo)
				finStartData = self.con.execute(select([organisation.c.yearstart]).where(organisation.c.orgcode==authDetails["orgcode"]))
				finstartrow = finStartData.fetchone()
				reconstmt= self.reconStatement(accountCode,str(self.request.params["calculatefrom"]),str(self.request.params["calculateto"]),recongrid["uctotaldr"],recongrid["uctotalcr"],str(finstartrow["yearstart"]))
				return {"gkstatus":enumdict["Success"],"gkresult":{"recongrid":recongrid["recongrid"],"reconstatement":reconstmt}}

			except:
				return{"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	def showUnclearedTransactions(self,accountCode,calculateFrom,calculateTo):
		result = result = self.con.execute(select([bankrecon]).where(or_(and_(bankrecon.c.accountcode==accountCode,bankrecon.c.clearancedate!=null(),bankrecon.c.clearancedate>calculateTo),and_(bankrecon.c.accountcode==accountCode,bankrecon.c.clearancedate==null()))))
		recongrid=[]
		uctotaldr=0.00
		uctotalcr=0.00
		for record in result:
			voucherdata=self.con.execute(select([vouchers]).where(and_(vouchers.c.vouchercode==int(record["vouchercode"]),vouchers.c.delflag==False,vouchers.c.voucherdate<=calculateTo)))
			voucher= voucherdata.fetchone()
			if voucher==None:
				continue
			if voucher["drs"].has_key(str(record["accountcode"])):
				for cr in voucher["crs"].keys():
					accountnameRow = self.con.execute(select([accounts.c.accountname]).where(accounts.c.accountcode==int(cr)))
					accountname = accountnameRow.fetchone()
					reconRow ={"reconcode":record["reconcode"],"date":datetime.strftime(voucher["voucherdate"],"%d-%m-%Y"),"particulars":str(accountname["accountname"]),"vno":voucher["vouchernumber"],"dr":"%.2f"%float(voucher["crs"][cr]),"cr":"","narration":voucher["narration"]}
					uctotaldr +=float(voucher["crs"][cr])
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
					uctotalcr +=float(voucher["drs"][dr])
					if record["clearancedate"]==None:
						reconRow["clearancedate"]=""
					else:
						reconRow["clearancedate"]=datetime.strftime(record["clearancedate"],"%d-%m-%Y")
					if record["memo"]==None:
						reconRow["memo"]=""
					else:
						reconRow["memo"]=record["memo"]
					recongrid.append(reconRow)
		return {"recongrid":recongrid,"uctotaldr":uctotaldr,"uctotalcr":uctotalcr}

	@view_config(request_method='PUT',renderer='json')
	def updateRecon(self):
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
				accountCode = dataset.pop("accountcode")
				calculateFrom = datetime.strptime(str(dataset.pop("calculatefrom")),"%Y-%m-%d")
				calculateTo = datetime.strptime(str(dataset.pop("calculateto")),"%Y-%m-%d")
				result = self.con.execute(bankrecon.update().where(bankrecon.c.reconcode==dataset["reconcode"]).values(dataset))
				recongrid= self.showUnclearedTransactions(accountCode,calculateFrom,calculateTo)
				finStartData = self.con.execute(select([organisation.c.yearstart]).where(organisation.c.orgcode==authDetails["orgcode"]))
				finstartrow = finStartData.fetchone()
				reconstmt= self.reconStatement(accountCode,str(self.request.json_body["calculatefrom"]),str(self.request.json_body["calculateto"]),recongrid["uctotaldr"],recongrid["uctotalcr"],str(finstartrow["yearstart"]))
				return {"gkstatus":enumdict["Success"],"gkresult":{"reconstatement":reconstmt}}
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	@view_config(request_method='GET', request_param='recon=cleared',renderer='json')
	def getClearedTransactions(self):
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
				result = self.con.execute(select([bankrecon]).where(and_(bankrecon.c.accountcode==accountCode,bankrecon.c.clearancedate!=null(),bankrecon.c.clearancedate<=calculateTo)))
				recongrid=[]
				for record in result:
					voucherdata=self.con.execute(select([vouchers]).where(and_(vouchers.c.vouchercode==int(record["vouchercode"]),vouchers.c.delflag==False,vouchers.c.voucherdate<=calculateTo)))
					voucher= voucherdata.fetchone()
					if voucher==None:
						continue
					if voucher["drs"].has_key(str(record["accountcode"])):
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
				return recongrid
			except:
				return {"gkstatus":enumdict["ConnectionFailed"]}
			finally:
				self.con.close()

	def reconStatement(self,accountCode,calculateFrom,calculateTo,uctotaldr,uctotalcr,financialStart):
		calbaldata = calculateBalance(self.con,accountCode,financialStart,calculateFrom,calculateTo )
		recostmt = [{"particulars":"RECONCILIATION STATEMENT","amount":"AMOUNT"}]
		midTotal = 0.00
		BankBal = 0.00
		if calbaldata["baltype"]=="Dr" or calbaldata["curbal"]==0:
			recostmt.append({"particulars":"Balance as per our book (Debit) on "+datetime.strftime(datetime.strptime(str(calculateTo),"%Y-%m-%d").date(),'%d-%m-%Y'),"amount":'%.2f'%(calbaldata["curbal"])})
			recostmt.append({"particulars":"Add: Cheques issued but not presented","amount":'%.2f'%(uctotalcr)})
			midTotal = calbaldata["curbal"]+uctotalcr
			recostmt.append({"particulars":"","amount":'%.2f'%(abs(midTotal))})
			recostmt.append({"particulars":"Less: Cheques deposited but not cleared","amount":'%.2f'%(uctotaldr)})
			BankBal = midTotal - uctotaldr
		elif calbaldata["baltype"]=="Cr":
			recostmt.append({"particulars":"Balance as per our book (Credit) on "+datetime.strftime(datetime.strptime(str(calculateTo),"%Y-%m-%d").date(),'%d-%m-%Y'),"amount":'%.2f'%(calbaldata["curbal"])})
			recostmt.append({"particulars":"Less: Cheques issued but not presented","amount":'%.2f'%(uctotalcr)})
			midTotal = calbaldata["curbal"]-uctotalcr
			if midTotal>=0:
				recostmt.append({"particulars":"","amount":'%.2f'%(abs(midTotal))})
				recostmt.append({"particulars":"Add: Cheques deposited but not cleared","amount":'%.2f'%(uctotaldr)})
				BankBal = abs(midTotal) + uctotaldr
			else:
				recostmt.append({"particulars":"","amount":'%.2f'%(abs(midTotal))})
				recostmt.append({"particulars":"Less: Cheques deposited but not cleared","amount":'%.2f'%(uctotaldr)})
				BankBal = abs(midTotal) - uctotaldr
		if BankBal < 0:
			recostmt.append({"particulars":"Balance as per Bank (Debit)","amount":'%.2f'%(abs(BankBal))})

		if BankBal > 0:
			recostmt.append({"particulars":"Balance as per Bank (Credit)","amount":'%.2f'%(abs(BankBal))})

		if BankBal == 0:
			recostmt.append({"particulars":"Balance as per Bank","amount":'%.2f'%(abs(BankBal))})
		return recostmt
