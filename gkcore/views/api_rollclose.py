


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
from gkcore.views.api_reports import api_report, api_reports
from gkcore.models.gkdb import vouchers, accounts, groupsubgroups, bankrecon, voucherbin, projects
from sqlalchemy.sql import select
from sqlalchemy import func
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ , between
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config

import datetime.date

@view_defaults(route_name="rollclose",request_method="get")
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
				orgCode = authDetails["orgcode"]
				financialStartEnd = self.con.execute("select yearstart, yearend, orgtype from organisation where orgcode = %d"%int(orgCode))
				startEndRow = financialStartEnd.fetchone()
				startDate = startEndRow["yearstart"]
				endDate = startEndRow["yearend"]
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
				directIncomeData = self.con.execute("select accountcode, accountname from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Income', 'Indirect Income' or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Income','Indirect Income'));"%(orgCode, orgCode, orgCode))
				diRecords = directIncomeData.fetchall()
				for di in diRecords:
					if di["accountname"]  == "Profit & Loss" or di["accountname"] == "Income & Expenditure":
						continue
					r = api_reports()
					cbRecord = r.calculateBalance(int(di["accountcode"]),startDate ,startDate ,endDate )
					curtime=datetime.datetime.now()
					str_time=str(curtime.microsecond)
					new_microsecond=str_time[0:2]		
					voucherNumber  = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond
					voucherDate = str(datetime.date.today())
					entryDate = voucherDate
					drs ={di["accountcode"]:cbRecord["curbal"]}
					crs = {closingAccountCode:cbRecord["curbal"]}
					cljv = {"vouchernumber":voucherNumber,"voucherdate":voucherDate,"entrydate":entryDate,"narration":"jv for closing books","drs":drs,"crs":crs,"vouchertype":"journal","orgcode":orgCode}
					result = self.con.execute(vouchers.insert(),[cljv])
				

				
				self.con.close()
			except Exception as E:
				print E
				self.con.close()
				return {"gkstatus":enumdict["ConnectionFailed"]}



