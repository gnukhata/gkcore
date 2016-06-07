


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


from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.views.api_user import getUserRole
from gkcore.views.api_reports import calculateBalance
from gkcore.models.gkdb import vouchers, accounts, groupsubgroups, projects, organisation
from sqlalchemy.sql import select
from sqlalchemy import func
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ , between
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config

from datetime import datetime,date, timedelta

@view_defaults(route_name="rollclose",request_method="GET")
class api_rollclose(object):
	"""
	This class has the functions for closing books and roll over, meaning creating new organisation's books for the subsequent financial year.
	It will have only one route namely rollclose and the 2 methods will be called on the basis of request_param,
	The request_method will be get and will be the default in view_defaults.
	"""

	def __init__(self,request):
		"""
		Initialising the request object which gets the data from client.
		"""
		self.request = Request
		self.request = request
		self.con = Connection
	@view_config(request_param='task=closebooks',renderer='json')
	def closeBooks(self):
		"""
		Purpose:
		Transfers all the income and expence accounts to P&L.
		Also updates organisation table and sets closebook flag to true for the given orgcode.
		Returns success status if true.
		description:
		This method is called when the /rollclose route is invoked with task=closebooks as parameter.
		First, the list of all accounts in direct indirect income and expence are collected with their account codes and name in the list.
		Then for each account under the said 4 groups a loop will be run to get closing balance and baltype using calculateBalance.
		The private metho is found in api_reports module.
		balances of all direct and indirect income accounts will be credited to P&L and debeted from the respective accounts through jv.
		Similarly all balances from direct and indirect expences will be debited to P&L.

		"""
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
				orgCode = int(authDetails["orgcode"])
				financialStartEnd = self.con.execute("select yearstart, yearend, orgtype from organisation where orgcode = %d"%int(orgCode))
				startEndRow = financialStartEnd.fetchone()
				startDate = str(startEndRow["yearstart"])
				endDate = str(startEndRow["yearend"])
				closingAccount = ""
				closingAccountCode = 0
				if startEndRow["orgtype"] == "Profit Making":
					closingAccount = "Profit & Loss"
					closeCodeData = self.con.execute("select accountcode from accounts where orgcode = %d and accountname = '%s'"%(orgCode,closingAccount))
					codeRow = closeCodeData.fetchone()
					closingAccountCode = int(codeRow["accountcode"])
				else:
					closingAccount = "Income & Expenditure"
					closeCodeData = self.con.execute("select accountcode from accounts where orgcode = %d and accountname = '%s'"%(orgCode,closingAccount))
					codeRow = closeCodeData.fetchone()
					closingAccountCode = int(codeRow["accountcode"])
				directIncomeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Income', 'Indirect Income') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Income','Indirect Income')));"%(orgCode, orgCode, orgCode))
				diRecords = directIncomeData.fetchall()
				for di in diRecords:
					if di["accountname"]  == "Profit & Loss" or di["accountname"] == "Income & Expenditure":
						continue
					cbRecord = calculateBalance(self.con,int(di["accountcode"]),startDate ,startDate ,endDate )
					if float(cbRecord["curbal"]) == 0:
						continue
					curtime=datetime.now()
					str_time=str(curtime.microsecond)
					new_microsecond=str_time[0:2]
					voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
					entryDate = str(date.today())
					voucherDate = endDate
					drs ={di["accountcode"]:"%.2f"%(cbRecord["curbal"])}
					crs = {closingAccountCode:"%.2f"%(cbRecord["curbal"])}
					cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"jv for closing books","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
					result = self.con.execute(vouchers.insert(),[cljv])
				directExpenseData =  self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Expense', 'Indirect Expense') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Indirect Expense')));"%(orgCode, orgCode, orgCode))
				deRecords = directExpenseData.fetchall()
				for de in deRecords:
					cbRecord = calculateBalance(self.con,int(de["accountcode"]),startDate ,startDate ,endDate )
					if float(cbRecord["curbal"]) == 0:
						continue
					curtime=datetime.now()
					str_time=str(curtime.microsecond)
					new_microsecond=str_time[0:2]
					voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
					entryDate = str(date.today())
					voucherDate = endDate
					crs ={de["accountcode"]:"%.2f"%(cbRecord["curbal"])}
					drs = {closingAccountCode:"%.2f"%(cbRecord["curbal"])}
					cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"jv for closing books","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
					result = self.con.execute(vouchers.insert(),[cljv])
				plResult = calculateBalance(self.con,closingAccountCode, startDate, startDate, endDate)
				print plResult["baltype"]
				startEndRow["orgtype"]
				groupCodeData = self.con.execute("select groupcode from groupsubgroups where groupname = 'Reserves' and orgcode = %d"%(orgCode) )
				gcRecord = groupCodeData.fetchone()
				groupCode = gcRecord["groupcode"]
				if plResult["baltype"]== "Cr" and startEndRow["orgtype"] == "Profit Making":
					pAccount = {"accountname":"Profit For The Year","groupcode":int(groupCode),"orgcode":orgCode}
					ins = self.con.execute(accounts.insert(),[pAccount])
					finalreservecode = 0
					curreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Profit For The Year")))
					curreserverow = curreservedata.fetchone()
					curreserve = curreserverow["accountcode"]
					curtime=datetime.now()
					str_time=str(curtime.microsecond)
					new_microsecond=str_time[0:2]
					voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
					entryDate = str(date.today())
					voucherDate = endDate
					drs ={closingAccountCode:"%.2f"%(plResult["curbal"])}
					crs = {curreserve:"%.2f"%(plResult["curbal"])}
					cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"Entry for recording Profit & Loss","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
					result = self.con.execute(vouchers.insert(),[cljv])
					paccnumdata = self.con.execute(select([func.count(accounts.c.accountcode).label('acccount')]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Profit B/F")))
					laccnumdata = self.con.execute(select([func.count(accounts.c.accountcode).label('acccount')]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Loss B/F")))
					paccnumrow = paccnumdata.fetchone()
					laccnumrow = laccnumdata.fetchone()
					if paccnumrow["acccount"]==0 or laccnumrow["acccount"]==0:
						pAccount = {"accountname":"Profit C/F","groupcode":int(groupCode),"orgcode":orgCode}
						ins = self.con.execute(accounts.insert(),[pAccount])
						finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Profit C/F")))
						finalreserverow = finalreservedata.fetchone()
						finalreservecode =  finalreserverow["accountcode"]
					else:
						if paccnumrow["account"]  > 0:
							res = self.con.execute("update accounts set accountname = 'Profit C/F' where orgcode = %d and accountname = 'Profit B/F'"%(orgCode))
							finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Profit C/F")))
							finalreserverow = finalreservedata.fetchone()
							finalreservecode =  finalreserverow["accountcode"]
						if laccnumrow["account"] > 0:
							lcfData = self.con.execute(select([accounts.c.openingbal]).where(and_(accounts.c.orgcode == orgCode,accounts.c.accountname == 'Loss B/F')))
							lcfRow = lcfData.fetchone()
							lcf = float(lcfRow["openingbal"])
							if lcf > plResult["curbal"]:
								res = self.con.execute("update accounts set accountname = 'Loss C/F' where orgcode = %d and accountname = 'Loss B/F'"%(orgCode))
								finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Loss C/F")))
								finalreserverow = finalreservedata.fetchone()
								finalreservecode =  finalreserverow["accountcode"]
							elif lcf < plResult["curbal"]:
								res = self.con.execute("update accounts set accountname = 'Profit C/F' where orgcode = %d and accountname = 'Loss B/F'"%(orgCode))
								finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Profit C/F")))
								finalreserverow = finalreservedata.fetchone()
								finalreservecode =  finalreserverow["accountcode"]
							else:
								res = self.con.execute("delete from accounts where orgcode = %d and accountname = 'Loss B/F'"%(orgCode))
								finalreservecode = 0
					if finalreservecode!=0:
						curtime=datetime.now()
						str_time=str(curtime.microsecond)
						new_microsecond=str_time[0:2]
						voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
						entryDate = str(date.today())
						voucherDate = endDate
						drs ={curreserve:"%.2f"%(plResult["curbal"])}
						crs = {finalreservecode:"%.2f"%(plResult["curbal"])}
						cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"Entry for recording Profit For The Year","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
						result = self.con.execute(vouchers.insert(),[cljv])


				if plResult["baltype"]== "Cr" and startEndRow["orgtype"] == "Not For Profit":
					sAccount = {"accountname":"Surplus For The Year","groupcode":int(groupCode),"orgcode":orgCode}
					ins = self.con.execute(accounts.insert(),[sAccount])
					finalreservecode = 0
					curreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Surplus For The Year")))
					curreserverow = curreservedata.fetchone()
					curreserve = curreserverow["accountcode"]
					curtime=datetime.now()
					str_time=str(curtime.microsecond)
					new_microsecond=str_time[0:2]
					voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
					entryDate = str(date.today())
					voucherDate = endDate
					drs ={closingAccountCode:"%.2f"%(plResult["curbal"])}
					crs = {curreserve:"%.2f"%(plResult["curbal"])}
					cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"Entry for recording Income & Expenditure","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
					result = self.con.execute(vouchers.insert(),[cljv])
					paccnumdata = self.con.execute(select([func.count(accounts.c.accountcode).label('acccount')]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Surplus B/F")))
					laccnumdata = self.con.execute(select([func.count(accounts.c.accountcode).label('acccount')]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Deficit B/F")))
					paccnumrow = paccnumdata.fetchone()
					laccnumrow = laccnumdata.fetchone()
					if paccnumrow["acccount"]==0 or laccnumrow["acccount"]==0:
						pAccount = {"accountname":"Surplus C/F","groupcode":int(groupCode),"orgcode":orgCode}
						ins = self.con.execute(accounts.insert(),[pAccount])
						finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Surplus C/F")))
						finalreserverow = finalreservedata.fetchone()
						finalreservecode =  finalreserverow["accountcode"]
					else:
						if paccnumrow["account"]  > 0:
							res = self.con.execute("update accounts set accountname = 'Surplus C/F' where orgcode = %d and accountname = 'Surplus B/F'"%(orgCode))
							finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Surplus C/F")))
							finalreserverow = finalreservedata.fetchone()
							finalreservecode =  finalreserverow["accountcode"]
						if laccnumrow["account"] > 0:
							lcfData = self.con.execute(select([accounts.c.openingbal]).where(and_(accounts.c.orgcode == orgCode,accounts.c.accountname == 'Deficit B/F')))
							lcfRow = lcfData.fetchone()
							lcf = float(lcfRow["openingbal"])
							if lcf > plResult["curbal"]:
								res = self.con.execute("update accounts set accountname = 'Deficit C/F' where orgcode = %d and accountname = 'Deficit B/F'"%(orgCode))
								finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Deficit C/F")))
								finalreserverow = finalreservedata.fetchone()
								finalreservecode =  finalreserverow["accountcode"]
							elif lcf < plResult["curbal"]:
								res = self.con.execute("update accounts set accountname = 'Surplus C/F' where orgcode = %d and accountname = 'Deficit B/F'"%(orgCode))
								finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Surplus C/F")))
								finalreserverow = finalreservedata.fetchone()
								finalreservecode =  finalreserverow["accountcode"]
							else:
								res = self.con.execute("delete from accounts where orgcode = %d and accountname = 'Deficit B/F'"%(orgCode))
								finalreservecode = 0
					if finalreservecode!=0:
						curtime=datetime.now()
						str_time=str(curtime.microsecond)
						new_microsecond=str_time[0:2]
						voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
						entryDate = str(date.today())
						voucherDate = endDate
						drs ={curreserve:"%.2f"%(plResult["curbal"])}
						crs = {finalreservecode:"%.2f"%(plResult["curbal"])}
						cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"Entry for recording Surplus For The Year","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
						result = self.con.execute(vouchers.insert(),[cljv])
				if plResult["baltype"]== "Dr" and startEndRow["orgtype"] == "Profit Making":
					lAccount = {"accountname":"Loss For The Year","groupcode":int(groupCode),"orgcode":orgCode}
					ins = self.con.execute(accounts.insert(),[lAccount])
					finalreservecode = 0
					curreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Loss For The Year")))
					curreserverow = curreservedata.fetchone()
					curreserve = curreserverow["accountcode"]
					curtime=datetime.now()
					str_time=str(curtime.microsecond)
					new_microsecond=str_time[0:2]
					voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
					entryDate = str(date.today())
					voucherDate = endDate
					crs ={closingAccountCode:"%.2f"%(plResult["curbal"])}
					drs = {curreserve:"%.2f"%(plResult["curbal"])}
					cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"Entry for recording Profit & Loss","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
					result = self.con.execute(vouchers.insert(),[cljv])
					paccnumdata = self.con.execute(select([func.count(accounts.c.accountcode).label('acccount')]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Profit B/F")))
					laccnumdata = self.con.execute(select([func.count(accounts.c.accountcode).label('acccount')]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Loss B/F")))
					paccnumrow = paccnumdata.fetchone()
					laccnumrow = laccnumdata.fetchone()
					if paccnumrow["acccount"]==0 or laccnumrow["acccount"]==0:
						pAccount = {"accountname":"Loss C/F","groupcode":int(groupCode),"orgcode":orgCode}
						ins = self.con.execute(accounts.insert(),[pAccount])
						finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Loss C/F")))
						finalreserverow = finalreservedata.fetchone()
						finalreservecode =  finalreserverow["accountcode"]
					else:
						if laccnumrow["account"]  > 0:
							res = self.con.execute("update accounts set accountname = 'Loss C/F' where orgcode = %D and accountname = 'Loss B/F'"%(orgCode))
							finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Loss C/F")))
							finalreserverow = finalreservedata.fetchone()
							finalreservecode =  finalreserverow["accountcode"]
						if paccnumrow["account"] > 0:
							pcfData = self.con.execute(select([accounts.c.openingbal]).where(and_(accounts.c.orgcode == orgCode,accounts.c.accountname == 'Profit B/F')))
							pcfRow = pcfData.fetchone()
							pcf = float(pcfRow["openingbal"])
							if pcf > plResult["curbal"]:
								res = self.con.execute("update accounts set accountname = 'Profit C/F' where orgcode = %d and accountname = 'Profit B/F'"%(orgCode))
								finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Profit C/F")))
								finalreserverow = finalreservedata.fetchone()
								finalreservecode =  finalreserverow["accountcode"]
							elif pcf < plResult["curbal"]:
								res = self.con.execute("update accounts set accountname = 'Loss C/F' where orgcode = %d and accountname = 'Profit B/F'"%(orgCode))
								finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Loss C/F")))
								finalreserverow = finalreservedata.fetchone()
								finalreservecode =  finalreserverow["accountcode"]
							else:
								res = self.con.execute("delete from accounts where orgcode = %d and accountname = 'Profit B/F'"%(orgCode))
								finalreservecode = 0
					if finalreservecode!=0:
						curtime=datetime.now()
						str_time=str(curtime.microsecond)
						new_microsecond=str_time[0:2]
						voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
						entryDate = str(date.today())
						voucherDate = endDate
						crs ={curreserve:"%.2f"%(plResult["curbal"])}
						drs = {finalreservecode:"%.2f"%(plResult["curbal"])}
						cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"Entry for recording Loss For The Year","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
						result = self.con.execute(vouchers.insert(),[cljv])
				if plResult["baltype"]== "Dr" and startEndRow["orgtype"] == "Not For Profit":
					dAccount = {"accountname":"Deficit For The Year","groupcode":int(groupCode),"orgcode":orgCode}
					ins = self.con.execute(accounts.insert(),[dAccount])
					finalreservecode = 0
					curreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Deficit For The Year")))
					curreserverow = curreservedata.fetchone()
					curreserve = curreserverow["accountcode"]
					curtime=datetime.now()
					str_time=str(curtime.microsecond)
					new_microsecond=str_time[0:2]
					voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
					entryDate = str(date.today())
					voucherDate = endDate
					crs ={closingAccountCode:"%.2f"%(plResult["curbal"])}
					drs = {curreserve:"%.2f"%(plResult["curbal"])}
					cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"Entry for recording Income & Expenditure","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
					result = self.con.execute(vouchers.insert(),[cljv])
					paccnumdata = self.con.execute(select([func.count(accounts.c.accountcode).label('acccount')]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Surplus B/F")))
					laccnumdata = self.con.execute(select([func.count(accounts.c.accountcode).label('acccount')]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Deficit B/F")))
					paccnumrow = paccnumdata.fetchone()
					laccnumrow = laccnumdata.fetchone()
					if paccnumrow["acccount"]==0 or laccnumrow["acccount"]==0:
						pAccount = {"accountname":"Deficit C/F","groupcode":int(groupCode),"orgcode":orgCode}
						ins = self.con.execute(accounts.insert(),[pAccount])
						finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Deficit C/F")))
						finalreserverow = finalreservedata.fetchone()
						finalreservecode =  finalreserverow["accountcode"]
					else:
						if laccnumrow["account"]  > 0:
							res = self.con.execute("update accounts set accountname = 'Deficit C/F' where orgcode = %D and accountname = 'Deficit B/F'"%(orgCode))
							finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Deficit C/F")))
							finalreserverow = finalreservedata.fetchone()
							finalreservecode =  finalreserverow["accountcode"]
						if paccnumrow["account"] > 0:
							pcfData = self.con.execute(select([accounts.c.openingbal]).where(and_(accounts.c.orgcode == orgCode,accounts.c.accountname == 'Surplus B/F')))
							pcfRow = pcfData.fetchone()
							pcf = float(pcfRow["openingbal"])
							if pcf > plResult["curbal"]:
								res = self.con.execute("update accounts set accountname = 'Surplus C/F', openingbal = %d where orgcode = %d and accountname = 'Surplus B/F'"%(orgCode))
								finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Surplus C/F")))
								finalreserverow = finalreservedata.fetchone()
								finalreservecode =  finalreserverow["accountcode"]
							elif pcf < plResult["curbal"]:
								res = self.con.execute("update accounts set accountname = 'Deficit C/F', openingbal = %d where orgcode = %d and accountname = 'Surplus B/F'"%(orgCode))
								finalreservedata = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.orgcode==orgCode,accounts.c.accountname=="Deficit C/F")))
								finalreserverow = finalreservedata.fetchone()
								finalreservecode =  finalreserverow["accountcode"]
							else:
								res = self.con.execute("delete from accounts where orgcode = %d and accountname = 'Profit B/F'"%(orgCode))
								finalreservecode =  0
					if finalreservecode!=0:
						curtime=datetime.now()
						str_time=str(curtime.microsecond)
						new_microsecond=str_time[0:2]
						voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
						entryDate = str(date.today())
						voucherDate = endDate
						crs ={curreserve:"%.2f"%(plResult["curbal"])}
						drs = {finalreservecode:"%.2f"%(plResult["curbal"])}
						cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"Entry for recording Deficit For The Year","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
						result = self.con.execute(vouchers.insert(),[cljv])
				result = self.con.execute(organisation.update().where(organisation.c.orgcode==orgCode).values({"booksclosedflag":1}))
				self.con.close()
				return {"gkstatus": enumdict["Success"]}
			except Exception as E:
				#print E
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}

	@view_config(request_param='task=rollover',renderer='json')
	def rollOver(self):
		"""
		Purpose:
		Creates a new organisation by adding new row in Organisation table,
		And transfering all accounts from the old organisation to the newly created one.
		Also updates organisation table and sets roflag to true for the old orgcode.
		Returns success status if true.
		description:
		This method is called when the /rollclose route is invoked with task=rollover as parameter.
		"""
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
				orgCode = int(authDetails["orgcode"])
				financialStartEnd = self.con.execute("select orgname, yearend, orgtype from organisation where orgcode = %d"%int(orgCode))
				startEndRow = financialStartEnd.fetchone()
				endDate = startEndRow["yearend"]
				newYearStart = date(endDate.year,endDate.month,endDate.day) + timedelta(DAYS=1)
				newYearEnd = date(endDate.year,endDate.month,endDate.day) + timedelta(years=1)
				print newYearStart
				print newYearEnd
				newOrg = {"orgname":startEndRow["orgname"],"orgtype":startEndRow["orgtype"],"yearstart":newYearStart,"yearend":newYearEnd}
				self.con.execute(organisation.insert( ),newOrg)
				newOrgCodeData = self.con.execute(select([organisation.c.orgcode]).where(and_(organisation.c.orgname == newOrg["orgname"],organisation.c.orgtype == newOrg["orgtype"],organisation.c.yearstart == newOrg["yearstart"], organisation.c.yearend == newOrg["yearend"])))
				newOrgRow = newOrgCodeData.fetchone()
				newOrgCode = newOrgRow["orgcode"]
				

				
				



				self.con.close()
				return {"gkstatus": enumdict["Success"]}
			except Exception as E:
				#print E
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}
