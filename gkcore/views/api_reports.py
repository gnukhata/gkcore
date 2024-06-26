"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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
"Vanita Rajpurohit" <vanita.rajpurohit9819@gmail.com>
"Prajkta Patkar" <prajkta@riseup.com>
"Bhavesh Bawadhane" <bbhavesh07@gmail.com>
"Parabjyot Singh" <parabjyot1996@gmail.com>
"Rahul Chaurasiya" <crahul4133@gmail.com>
"Vasudha Kadge" <kadge.vasudha@gmail.com>
"""


import logging
from gkcore import eng, enumdict
from gkcore.models import gkdb
from gkcore.utils import authCheck
from gkcore.views.api_invoice import getStateCode
from gkcore.models.gkdb import (
    accounts,
    vouchers,
    groupsubgroups,
    projects,
    organisation,
    users,
    voucherbin,
    delchal,
    invoice,
    customerandsupplier,
    stock,
    product,
    transfernote,
    goprod,
    dcinv,
    log,
    godown,
    categorysubcategories,
    rejectionnote,
    state,
    drcr,
)
from sqlalchemy.sql import select, not_
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, alias, or_, exc, distinct, desc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from gkcore.views.api_gkuser import getUserRole
from datetime import datetime, date
import calendar
from monthdelta import monthdelta
from gkcore.models.meta import dbconnect
from sqlalchemy.sql.functions import func
from time import strftime, strptime
from natsort import natsorted
from sqlalchemy.sql.expression import null
import traceback  # for printing detailed exception logs

"""
purpose:
This class is the resource to generate reports,
Such as Trial Balance, Ledger, Cash flowe, Balance sheet etc.

connection rules:
con is used for executing sql expression language based queries,
while eng is used for raw sql execution.
routing mechanism:
@view_defaults is used for setting the default route for crud on the given resource class.
if specific route is to be attached to a certain method, or for giving get, post, put, delete methods to default route, the view_config decorator is used.
For other predicates view_config is generally used.
This class has single route with only get as method.
Depending on the request_param, different methods will be called on the route given in view_default.

"""


def getBalanceSheet(con, orgcode, calculateTo, calculatefrom, balancetype):
    financialstart = con.execute(
        "select yearstart, orgtype from organisation where orgcode = %d" % int(orgcode)
    )
    financialstartRow = financialstart.fetchone()
    financialStart = financialstartRow["yearstart"]
    orgtype = financialstartRow["orgtype"]
    sbalanceSheet = []
    abalanceSheet = []
    sourcesTotal = 0.00
    applicationsTotal = 0.00
    difference = 0.00
    openingStockVal = (calculateOpeningStockValue(con, orgcode))['total']
    closingStockVal = (calculateClosingStockValue(con, orgcode, calculateTo))['total']
    sbalanceSheet.append(
        {
            "groupAccname": "Sources:",
            "amount": "",
            "groupAcccode": "",
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )
    capital_Corpus = ""
    if orgtype == "Profit Making":
        capital_Corpus = "Capital"
    if orgtype == "Not For Profit":
        capital_Corpus = "Corpus"
    groupWiseTotal = 0.00

    # Calculate grouptotal for group Capital/Corpus
    accountcodeData = con.execute(
        "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = '%s') order by accountname;"
        % (orgcode, orgcode, capital_Corpus)
    )
    accountCodes = accountcodeData.fetchall()
    subgroupDataRow = con.execute(
        "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='%s');"
        % (orgcode, orgcode, capital_Corpus)
    )
    subgroupData = subgroupDataRow.fetchall()
    groupCode = con.execute(
        "select groupcode from groupsubgroups where (orgcode=%d and groupname='%s');"
        % (orgcode, capital_Corpus)
    )
    groupcode = groupCode.fetchone()["groupcode"]
    groupAccSubgroup = []

    for accountRow in accountCodes:
        accountTotal = 0.00
        adverseflag = 0
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Cr":
            groupWiseTotal += accountDetails["curbal"]
            accountTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Dr" and accountDetails["curbal"] != 0:
            adverseflag = 1
            accountTotal -= accountDetails["curbal"]
            groupWiseTotal -= accountDetails["curbal"]
        groupAccSubgroup.append(
            {
                "groupAccname": accountRow["accountname"],
                "amount": "%.2f" % (accountTotal),
                "groupAcccode": accountRow["accountcode"],
                "subgroupof": "",
                "accountof": groupcode,
                "groupAccflag": 1,
                "advflag": adverseflag,
            }
        )

    for subgroup in subgroupData:
        subgroupTotal = 0.00
        accounts = []
        subgroupAccDataRow = con.execute(
            "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
            % (orgcode, subgroup["groupcode"])
        )
        subgroupAccData = subgroupAccDataRow.fetchall()
        for account in subgroupAccData:
            accountTotal = 0.00
            adverseflag = 0
            accountDetails = calculateBalance(
                con,
                account["accountcode"],
                financialStart,
                calculatefrom,
                calculateTo,
            )
            if accountDetails["baltype"] == "Cr":
                subgroupTotal += accountDetails["curbal"]
                accountTotal += accountDetails["curbal"]
            if accountDetails["baltype"] == "Dr" and accountDetails["curbal"] != 0:
                adverseflag = 1
                subgroupTotal -= accountDetails["curbal"]
                accountTotal -= accountDetails["curbal"]
            if accountDetails["curbal"] != 0:
                accounts.append(
                    {
                        "groupAccname": account["accountname"],
                        "amount": "%.2f" % (accountTotal),
                        "groupAcccode": account["accountcode"],
                        "subgroupof": groupcode,
                        "accountof": subgroup["groupcode"],
                        "groupAccflag": 2,
                        "advflag": adverseflag,
                    }
                )
        groupWiseTotal += subgroupTotal
        groupAccSubgroup.append(
            {
                "groupAccname": subgroup["groupname"],
                "amount": "%.2f" % (subgroupTotal),
                "groupAcccode": subgroup["groupcode"],
                "subgroupof": groupcode,
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        groupAccSubgroup += accounts
    sourcesTotal += groupWiseTotal
    sbalanceSheet.append(
        {
            "groupAccname": capital_Corpus,
            "amount": "%.2f" % (groupWiseTotal),
            "groupAcccode": groupcode,
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )
    sbalanceSheet += groupAccSubgroup

    # Calculate grouptotal for group Loans(Liability)
    groupWiseTotal = 0.00
    accountcodeData = con.execute(
        "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Liability)') order by accountname;"
        % (orgcode, orgcode)
    )
    accountCodes = accountcodeData.fetchall()
    subgroupDataRow = con.execute(
        "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Loans(Liability)');"
        % (orgcode, orgcode)
    )
    subgroupData = subgroupDataRow.fetchall()
    groupCode = con.execute(
        "select groupcode from groupsubgroups where (orgcode=%d and groupname='Loans(Liability)');"
        % (orgcode)
    )
    groupcode = groupCode.fetchone()["groupcode"]
    groupAccSubgroup = []

    for accountRow in accountCodes:
        accountTotal = 0.00
        adverseflag = 0
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Cr":
            groupWiseTotal += accountDetails["curbal"]
            accountTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Dr" and accountDetails["curbal"] != 0:
            adverseflag = 1
            accountTotal -= accountDetails["curbal"]
            groupWiseTotal -= accountDetails["curbal"]
        groupAccSubgroup.append(
            {
                "groupAccname": accountRow["accountname"],
                "amount": "%.2f" % (accountTotal),
                "groupAcccode": accountRow["accountcode"],
                "subgroupof": "",
                "accountof": groupcode,
                "groupAccflag": 1,
                "advflag": adverseflag,
            }
        )

    for subgroup in subgroupData:
        subgroupTotal = 0.00
        accounts = []
        subgroupAccDataRow = con.execute(
            "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
            % (orgcode, subgroup["groupcode"])
        )
        subgroupAccData = subgroupAccDataRow.fetchall()
        for account in subgroupAccData:
            accountTotal = 0.00
            adverseflag = 0
            accountDetails = calculateBalance(
                con,
                account["accountcode"],
                financialStart,
                calculatefrom,
                calculateTo,
            )
            if accountDetails["baltype"] == "Cr":
                subgroupTotal += accountDetails["curbal"]
                accountTotal += accountDetails["curbal"]
            if accountDetails["baltype"] == "Dr" and accountDetails["curbal"] != 0:
                adverseflag = 1
                subgroupTotal -= accountDetails["curbal"]
                accountTotal -= accountDetails["curbal"]
            if accountDetails["curbal"] != 0:
                accounts.append(
                    {
                        "groupAccname": account["accountname"],
                        "amount": "%.2f" % (accountTotal),
                        "groupAcccode": account["accountcode"],
                        "subgroupof": groupcode,
                        "accountof": subgroup["groupcode"],
                        "groupAccflag": 2,
                        "advflag": adverseflag,
                    }
                )
        groupWiseTotal += subgroupTotal
        groupAccSubgroup.append(
            {
                "groupAccname": subgroup["groupname"],
                "amount": "%.2f" % (subgroupTotal),
                "groupAcccode": subgroup["groupcode"],
                "subgroupof": groupcode,
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        groupAccSubgroup += accounts

    sourcesTotal += groupWiseTotal
    sbalanceSheet.append(
        {
            "groupAccname": "Loans(Liability)",
            "amount": "%.2f" % (groupWiseTotal),
            "groupAcccode": groupcode,
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )
    sbalanceSheet += groupAccSubgroup

    # Calculate grouptotal for group Current Liabilities
    groupWiseTotal = 0.00
    accountcodeData = con.execute(
        "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Liabilities') order by accountname;"
        % (orgcode, orgcode)
    )
    accountCodes = accountcodeData.fetchall()
    subgroupDataRow = con.execute(
        "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Current Liabilities');"
        % (orgcode, orgcode)
    )
    subgroupData = subgroupDataRow.fetchall()
    groupCode = con.execute(
        "select groupcode from groupsubgroups where (orgcode=%d and groupname='Current Liabilities');"
        % (orgcode)
    )
    groupcode = groupCode.fetchone()["groupcode"]
    groupAccSubgroup = []

    for accountRow in accountCodes:
        accountTotal = 0.00
        adverseflag = 0
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Cr":
            groupWiseTotal += accountDetails["curbal"]
            accountTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Dr" and accountDetails["curbal"] != 0:
            adverseflag = 1
            accountTotal -= accountDetails["curbal"]
            groupWiseTotal -= accountDetails["curbal"]
        groupAccSubgroup.append(
            {
                "groupAccname": accountRow["accountname"],
                "amount": "%.2f" % (accountTotal),
                "groupAcccode": accountRow["accountcode"],
                "subgroupof": "",
                "accountof": groupcode,
                "groupAccflag": 1,
                "advflag": adverseflag,
            }
        )

    for subgroup in subgroupData:
        subgroupTotal = 0.00
        accounts = []
        subgroupAccDataRow = con.execute(
            "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
            % (orgcode, subgroup["groupcode"])
        )
        subgroupAccData = subgroupAccDataRow.fetchall()
        for account in subgroupAccData:
            accountTotal = 0.00
            adverseflag = 0
            accountDetails = calculateBalance(
                con,
                account["accountcode"],
                financialStart,
                calculatefrom,
                calculateTo,
            )
            if accountDetails["baltype"] == "Cr":
                subgroupTotal += accountDetails["curbal"]
                accountTotal += accountDetails["curbal"]
            if accountDetails["baltype"] == "Dr" and accountDetails["curbal"] != 0:
                adverseflag = 1
                subgroupTotal -= accountDetails["curbal"]
                accountTotal -= accountDetails["curbal"]
            if accountDetails["curbal"] != 0:
                accounts.append(
                    {
                        "groupAccname": account["accountname"],
                        "amount": "%.2f" % (accountTotal),
                        "groupAcccode": account["accountcode"],
                        "subgroupof": groupcode,
                        "accountof": subgroup["groupcode"],
                        "groupAccflag": 2,
                        "advflag": adverseflag,
                    }
                )
        groupWiseTotal += subgroupTotal
        groupAccSubgroup.append(
            {
                "groupAccname": subgroup["groupname"],
                "amount": "%.2f" % (subgroupTotal),
                "groupAcccode": subgroup["groupcode"],
                "subgroupof": groupcode,
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        groupAccSubgroup += accounts

    sourcesTotal += groupWiseTotal
    sbalanceSheet.append(
        {
            "groupAccname": "Current Liabilities",
            "amount": "%.2f" % (groupWiseTotal),
            "groupAcccode": groupcode,
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )
    sbalanceSheet += groupAccSubgroup

    # Calculate grouptotal for group "Reserves"
    groupWiseTotal = 0.00
    incomeTotal = 0.00
    expenseTotal = 0.00
    accountcodeData = con.execute(
        "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Reserves') order by accountname;"
        % (orgcode, orgcode)
    )
    accountCodes = accountcodeData.fetchall()
    subgroupDataRow = con.execute(
        "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Reserves');"
        % (orgcode, orgcode)
    )
    subgroupData = subgroupDataRow.fetchall()
    groupCode = con.execute(
        "select groupcode from groupsubgroups where (orgcode=%d and groupname='Reserves');"
        % (orgcode)
    )
    groupcode = groupCode.fetchone()["groupcode"]
    groupAccSubgroup = []

    for accountRow in accountCodes:
        accountTotal = 0.00
        adverseflag = 0
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Cr":
            groupWiseTotal += accountDetails["curbal"]
            accountTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Dr" and accountDetails["curbal"] != 0:
            adverseflag = 1
            accountTotal -= accountDetails["curbal"]
            groupWiseTotal -= accountDetails["curbal"]
        groupAccSubgroup.append(
            {
                "groupAccname": accountRow["accountname"],
                "amount": "%.2f" % (accountTotal),
                "groupAcccode": accountRow["accountcode"],
                "subgroupof": "",
                "accountof": groupcode,
                "groupAccflag": 1,
                "advflag": adverseflag,
            }
        )

    for subgroup in subgroupData:
        subgroupTotal = 0.00
        accounts = []
        subgroupAccDataRow = con.execute(
            "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
            % (orgcode, subgroup["groupcode"])
        )
        subgroupAccData = subgroupAccDataRow.fetchall()
        for account in subgroupAccData:
            accountTotal = 0.00
            adverseflag = 0
            accountDetails = calculateBalance(
                con,
                account["accountcode"],
                financialStart,
                calculatefrom,
                calculateTo,
            )
            if accountDetails["baltype"] == "Cr":
                subgroupTotal += accountDetails["curbal"]
                accountTotal += accountDetails["curbal"]
            if accountDetails["baltype"] == "Dr" and accountDetails["curbal"] != 0:
                adverseflag = 1
                subgroupTotal -= accountDetails["curbal"]
                accountTotal -= accountDetails["curbal"]
            if accountDetails["curbal"] != 0:
                accounts.append(
                    {
                        "groupAccname": account["accountname"],
                        "amount": "%.2f" % (accountTotal),
                        "groupAcccode": account["accountcode"],
                        "subgroupof": groupcode,
                        "accountof": subgroup["groupcode"],
                        "groupAccflag": 2,
                        "advflag": adverseflag,
                    }
                )
        groupWiseTotal += subgroupTotal
        groupAccSubgroup.append(
            {
                "groupAccname": subgroup["groupname"],
                "amount": "%.2f" % (subgroupTotal),
                "groupAcccode": subgroup["groupcode"],
                "subgroupof": groupcode,
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        groupAccSubgroup += accounts

    # Calculate all income(Direct and Indirect Income)
    accountcodeData = con.execute(
        "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Income','Indirect Income') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Income','Indirect Income')));"
        % (orgcode, orgcode, orgcode)
    )
    accountCodes = accountcodeData.fetchall()
    for accountRow in accountCodes:
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Cr":
            incomeTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Dr":
            incomeTotal -= accountDetails["curbal"]

    # Calculate all expense(Direct and Indirect Expense)
    accountcodeData = con.execute(
        "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Expense','Indirect Expense') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Indirect Expense')));"
        % (orgcode, orgcode, orgcode)
    )
    accountCodes = accountcodeData.fetchall()
    for accountRow in accountCodes:
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Dr":
            expenseTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Cr":
            expenseTotal -= accountDetails["curbal"]

    # Calculate Profit/Loss for the year
    profit = 0

    exp = float("%.2f" % (expenseTotal + openingStockVal))
    incm = float("%.2f" % (incomeTotal + closingStockVal))
    
    profit = incm - exp

    # In case of loss
    if exp > incm:
         
        groupWiseTotal -= profit
        sbalanceSheet.append(
            {
                "groupAccname": "Reserves",
                "amount": "%.2f" % (groupWiseTotal),
                "groupAcccode": groupcode,
                "subgroupof": "",
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        if orgtype == "Profit Making":
            sbalanceSheet.append(
                {
                    "groupAccname": "Loss for the Year:",
                    "amount": "%.2f" % (profit),
                    "groupAcccode": "",
                    "subgroupof": groupcode,
                    "accountof": "",
                    "groupAccflag": 2,
                    "advflag": "",
                }
            )
        else:
            sbalanceSheet.append(
                {
                    "groupAccname": "Deficit for the Year:",
                    "amount": "%.2f" % (profit),
                    "groupAcccode": "",
                    "subgroupof": groupcode,
                    "accountof": "",
                    "groupAccflag": 2,
                    "advflag": "",
                }
            )

    # In case of profit
    if exp < incm:
        groupWiseTotal += profit
        sbalanceSheet.append(
            {
                "groupAccname": "Reserves",
                "amount": "%.2f" % (groupWiseTotal),
                "groupAcccode": groupcode,
                "subgroupof": "",
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        if orgtype == "Profit Making":
            sbalanceSheet.append(
                {
                    "groupAccname": "Profit for the Year:",
                    "amount": "%.2f" % (profit),
                    "groupAcccode": "",
                    "subgroupof": groupcode,
                    "accountof": "",
                    "groupAccflag": 2,
                    "advflag": "",
                }
            )
        else:
            sbalanceSheet.append(
                {
                    "groupAccname": "Surplus for the Year:",
                    "amount": "%.2f" % (profit),
                    "groupAcccode": "",
                    "subgroupof": groupcode,
                    "accountof": "",
                    "groupAccflag": 2,
                    "advflag": "",
                }
            )
    # In case of no loss/profit
    if expenseTotal == incomeTotal:
        sbalanceSheet.append(
            {
                "groupAccname": "Reserves",
                "amount": "%.2f" % (groupWiseTotal),
                "groupAcccode": groupcode,
                "subgroupof": "",
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )

    sbalanceSheet += groupAccSubgroup
    sourcesTotal += groupWiseTotal
    sbalanceSheet.append(
        {
            "groupAccname": "Total",
            "amount": "%.2f" % (sourcesTotal),
            "groupAcccode": "",
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )

    # Applications:
    abalanceSheet.append(
        {
            "groupAccname": "Applications:",
            "amount": "",
            "groupAcccode": "",
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )

    # Calculate grouptotal for group "Fixed Assets"
    groupWiseTotal = 0.00
    accountcodeData = con.execute(
        "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Fixed Assets') order by accountname;"
        % (orgcode, orgcode)
    )
    accountCodes = accountcodeData.fetchall()
    subgroupDataRow = con.execute(
        "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Fixed Assets');"
        % (orgcode, orgcode)
    )
    subgroupData = subgroupDataRow.fetchall()
    groupCode = con.execute(
        "select groupcode from groupsubgroups where (orgcode=%d and groupname='Fixed Assets');"
        % (orgcode)
    )
    groupcode = groupCode.fetchone()["groupcode"]
    groupAccSubgroup = []

    for accountRow in accountCodes:
        accountTotal = 0.00
        adverseflag = 0
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Dr":
            groupWiseTotal += accountDetails["curbal"]
            accountTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
            adverseflag = 1
            accountTotal -= accountDetails["curbal"]
            groupWiseTotal -= accountDetails["curbal"]
        groupAccSubgroup.append(
            {
                "groupAccname": accountRow["accountname"],
                "amount": "%.2f" % (accountTotal),
                "groupAcccode": accountRow["accountcode"],
                "subgroupof": "",
                "accountof": groupcode,
                "groupAccflag": 1,
                "advflag": adverseflag,
            }
        )

    for subgroup in subgroupData:
        subgroupTotal = 0.00
        accounts = []
        subgroupAccDataRow = con.execute(
            "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
            % (orgcode, subgroup["groupcode"])
        )
        subgroupAccData = subgroupAccDataRow.fetchall()

        for account in subgroupAccData:
            accountTotal = 0.00
            adverseflag = 0
            accountDetails = calculateBalance(
                con,
                account["accountcode"],
                financialStart,
                calculatefrom,
                calculateTo,
            )
            if accountDetails["baltype"] == "Dr":
                subgroupTotal += accountDetails["curbal"]
                accountTotal += accountDetails["curbal"]
            if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
                adverseflag = 1
                subgroupTotal -= accountDetails["curbal"]
                accountTotal -= accountDetails["curbal"]
            if accountDetails["curbal"] != 0:
                accounts.append(
                    {
                        "groupAccname": account["accountname"],
                        "amount": "%.2f" % (accountTotal),
                        "groupAcccode": account["accountcode"],
                        "subgroupof": groupcode,
                        "accountof": subgroup["groupcode"],
                        "groupAccflag": 2,
                        "advflag": adverseflag,
                    }
                )
        groupWiseTotal += subgroupTotal
        groupAccSubgroup.append(
            {
                "groupAccname": subgroup["groupname"],
                "amount": "%.2f" % (subgroupTotal),
                "groupAcccode": subgroup["groupcode"],
                "subgroupof": groupcode,
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        groupAccSubgroup += accounts

    applicationsTotal += groupWiseTotal
    abalanceSheet.append(
        {
            "groupAccname": "Fixed Assets",
            "amount": "%.2f" % (groupWiseTotal),
            "groupAcccode": groupcode,
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )
    abalanceSheet += groupAccSubgroup

    # Calculate grouptotal for group "Investments"
    groupWiseTotal = 0.00
    accountcodeData = con.execute(
        "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Investments') order by accountname;"
        % (orgcode, orgcode)
    )
    accountCodes = accountcodeData.fetchall()
    subgroupDataRow = con.execute(
        "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Investments');"
        % (orgcode, orgcode)
    )
    subgroupData = subgroupDataRow.fetchall()
    groupCode = con.execute(
        "select groupcode from groupsubgroups where (orgcode=%d and groupname='Investments');"
        % (orgcode)
    )
    groupcode = groupCode.fetchone()["groupcode"]
    groupAccSubgroup = []

    for accountRow in accountCodes:
        accountTotal = 0.00
        adverseflag = 0
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Dr":
            groupWiseTotal += accountDetails["curbal"]
            accountTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
            adverseflag = 1
            accountTotal -= accountDetails["curbal"]
            groupWiseTotal -= accountDetails["curbal"]
        groupAccSubgroup.append(
            {
                "groupAccname": accountRow["accountname"],
                "amount": "%.2f" % (accountTotal),
                "groupAcccode": accountRow["accountcode"],
                "subgroupof": "",
                "accountof": groupcode,
                "groupAccflag": 1,
                "advflag": adverseflag,
            }
        )

    for subgroup in subgroupData:
        subgroupTotal = 0.00
        accounts = []
        subgroupAccDataRow = con.execute(
            "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
            % (orgcode, subgroup["groupcode"])
        )
        subgroupAccData = subgroupAccDataRow.fetchall()
        for account in subgroupAccData:
            accountTotal = 0.00
            adverseflag = 0
            accountDetails = calculateBalance(
                con,
                account["accountcode"],
                financialStart,
                calculatefrom,
                calculateTo,
            )
            if accountDetails["baltype"] == "Dr":
                subgroupTotal += accountDetails["curbal"]
                accountTotal += accountDetails["curbal"]
            if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
                adverseflag = 1
                subgroupTotal -= accountDetails["curbal"]
                accountTotal -= accountDetails["curbal"]
            if accountDetails["curbal"] != 0:
                accounts.append(
                    {
                        "groupAccname": account["accountname"],
                        "amount": "%.2f" % (accountTotal),
                        "groupAcccode": account["accountcode"],
                        "subgroupof": groupcode,
                        "accountof": subgroup["groupcode"],
                        "groupAccflag": 2,
                        "advflag": adverseflag,
                    }
                )
        groupWiseTotal += subgroupTotal
        groupAccSubgroup.append(
            {
                "groupAccname": subgroup["groupname"],
                "amount": "%.2f" % (subgroupTotal),
                "groupAcccode": subgroup["groupcode"],
                "subgroupof": groupcode,
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        groupAccSubgroup += accounts

    applicationsTotal += groupWiseTotal
    abalanceSheet.append(
        {
            "groupAccname": "Investments",
            "amount": "%.2f" % (groupWiseTotal),
            "groupAcccode": groupcode,
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )
    abalanceSheet += groupAccSubgroup

    # Calculate grouptotal for group "Current Assets"
    groupWiseTotal = 0.00
    accountcodeData = con.execute(
        "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Assets') order by accountname;"
        % (orgcode, orgcode)
    )
    accountCodes = accountcodeData.fetchall()
    subgroupDataRow = con.execute(
        "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Current Assets');"
        % (orgcode, orgcode)
    )
    subgroupData = subgroupDataRow.fetchall()
    groupCode = con.execute(
        "select groupcode from groupsubgroups where (orgcode=%d and groupname='Current Assets');"
        % (orgcode)
    )
    groupcode = groupCode.fetchone()["groupcode"]
    groupAccSubgroup = []

    for accountRow in accountCodes:
        accountTotal = 0.00
        adverseflag = 0
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Dr":
            groupWiseTotal += accountDetails["curbal"]
            accountTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
            adverseflag = 1
            accountTotal -= accountDetails["curbal"]
            groupWiseTotal -= accountDetails["curbal"]
        groupAccSubgroup.append(
            {
                "groupAccname": accountRow["accountname"],
                "amount": "%.2f" % (accountTotal),
                "groupAcccode": accountRow["accountcode"],
                "subgroupof": "",
                "accountof": groupcode,
                "groupAccflag": 1,
                "advflag": adverseflag,
            }
        )
    # loop over the subgroups of current assets
    for subgroup in subgroupData:
        subgroupTotal = 0.00
        accounts = []
        subgroupAccDataRow = con.execute(
            "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
            % (orgcode, subgroup["groupcode"])
        )
        subgroupAccData = subgroupAccDataRow.fetchall()
        for account in subgroupAccData:
            accountTotal = 0.00
            adverseflag = 0
            accountDetails = calculateBalance(
                con,
                account["accountcode"],
                financialStart,
                calculatefrom,
                calculateTo,
            )
            if accountDetails["baltype"] == "Dr":
                subgroupTotal += accountDetails["curbal"]
                accountTotal += accountDetails["curbal"]
            if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
                adverseflag = 1
                subgroupTotal -= accountDetails["curbal"]
                accountTotal -= accountDetails["curbal"]
            if accountDetails["curbal"] != 0:
                accounts.append(
                    {
                        "groupAccname": account["accountname"],
                        "amount": "%.2f" % (accountTotal),
                        "groupAcccode": account["accountcode"],
                        "subgroupof": groupcode,
                        "accountof": subgroup["groupcode"],
                        "groupAccflag": 2,
                        "advflag": adverseflag,
                    }
                )
        groupWiseTotal += subgroupTotal
        # calculate the inventory
        if subgroup["groupname"] == "Inventory":
            subgroupTotal = closingStockVal
        groupAccSubgroup.append(
            {
                "groupAccname": subgroup["groupname"],
                "amount": "%.2f" % (subgroupTotal),
                "groupAcccode": subgroup["groupcode"],
                "subgroupof": groupcode,
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        # TODO: check if accname is inventory and if it is, make the amount as closing stock value
        groupAccSubgroup += accounts
        # print(subgroup["groupname"])

    applicationsTotal += groupWiseTotal
    abalanceSheet.append(
        {
            "groupAccname": "Current Assets",
            "amount": "%.2f" % (groupWiseTotal + closingStockVal),
            "groupAcccode": groupcode,
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )
    abalanceSheet += groupAccSubgroup

    # Calculate grouptotal for group Loans(Asset)
    groupWiseTotal = 0.00
    accountcodeData = con.execute(
        "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Asset)') order by accountname;"
        % (orgcode, orgcode)
    )
    accountCodes = accountcodeData.fetchall()
    subgroupDataRow = con.execute(
        "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Loans(Asset)');"
        % (orgcode, orgcode)
    )
    subgroupData = subgroupDataRow.fetchall()
    groupCode = con.execute(
        "select groupcode from groupsubgroups where (orgcode=%d and groupname='Loans(Asset)');"
        % (orgcode)
    )
    groupcode = groupCode.fetchone()["groupcode"]
    groupAccSubgroup = []

    for accountRow in accountCodes:
        accountTotal = 0.00
        adverseflag = 0
        accountDetails = calculateBalance(
            con,
            accountRow["accountcode"],
            financialStart,
            calculatefrom,
            calculateTo,
        )
        if accountDetails["baltype"] == "Dr":
            groupWiseTotal += accountDetails["curbal"]
            accountTotal += accountDetails["curbal"]
        if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
            adverseflag = 1
            accountTotal -= accountDetails["curbal"]
            groupWiseTotal -= accountDetails["curbal"]
        groupAccSubgroup.append(
            {
                "groupAccname": accountRow["accountname"],
                "amount": "%.2f" % (accountTotal),
                "groupAcccode": accountRow["accountcode"],
                "subgroupof": "",
                "accountof": groupcode,
                "groupAccflag": 1,
                "advflag": adverseflag,
            }
        )

    for subgroup in subgroupData:
        subgroupTotal = 0.00
        accounts = []
        subgroupAccDataRow = con.execute(
            "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
            % (orgcode, subgroup["groupcode"])
        )
        subgroupAccData = subgroupAccDataRow.fetchall()
        for account in subgroupAccData:
            accountTotal = 0.00
            adverseflag = 0
            accountDetails = calculateBalance(
                con,
                account["accountcode"],
                financialStart,
                calculatefrom,
                calculateTo,
            )
            if accountDetails["baltype"] == "Dr":
                subgroupTotal += accountDetails["curbal"]
                accountTotal += accountDetails["curbal"]
            if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
                adverseflag = 1
                subgroupTotal -= accountDetails["curbal"]
                accountTotal -= accountDetails["curbal"]
            if accountDetails["curbal"] != 0:
                accounts.append(
                    {
                        "groupAccname": account["accountname"],
                        "amount": "%.2f" % (accountTotal),
                        "groupAcccode": account["accountcode"],
                        "subgroupof": groupcode,
                        "accountof": subgroup["groupcode"],
                        "groupAccflag": 2,
                        "advflag": adverseflag,
                    }
                )
        groupWiseTotal += subgroupTotal
        groupAccSubgroup.append(
            {
                "groupAccname": subgroup["groupname"],
                "amount": "%.2f" % (subgroupTotal),
                "groupAcccode": subgroup["groupcode"],
                "subgroupof": groupcode,
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        groupAccSubgroup += accounts

    applicationsTotal += groupWiseTotal
    abalanceSheet.append(
        {
            "groupAccname": "Loans(Asset)",
            "amount": "%.2f" % (groupWiseTotal),
            "groupAcccode": groupcode,
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )
    abalanceSheet += groupAccSubgroup

    if orgtype == "Profit Making":
        # Calculate grouptotal for group "Miscellaneous Expenses(Asset)"
        groupWiseTotal = 0.00
        accountcodeData = con.execute(
            "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Miscellaneous Expenses(Asset)') order by accountname;"
            % (orgcode, orgcode)
        )
        accountCodes = accountcodeData.fetchall()
        subgroupDataRow = con.execute(
            "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Miscellaneous Expenses(Asset)');"
            % (orgcode, orgcode)
        )
        subgroupData = subgroupDataRow.fetchall()
        groupCode = con.execute(
            "select groupcode from groupsubgroups where (orgcode=%d and groupname='Miscellaneous Expenses(Asset)');"
            % (orgcode)
        )
        groupcode = groupCode.fetchone()["groupcode"]
        groupAccSubgroup = []

        for accountRow in accountCodes:
            accountTotal = 0.00
            adverseflag = 0
            accountDetails = calculateBalance(
                con,
                accountRow["accountcode"],
                financialStart,
                calculatefrom,
                calculateTo,
            )
            if accountDetails["baltype"] == "Dr":
                groupWiseTotal += accountDetails["curbal"]
                accountTotal += accountDetails["curbal"]
            if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
                adverseflag = 1
                accountTotal -= accountDetails["curbal"]
                groupWiseTotal -= accountDetails["curbal"]
            groupAccSubgroup.append(
                {
                    "groupAccname": accountRow["accountname"],
                    "amount": "%.2f" % (accountTotal),
                    "groupAcccode": accountRow["accountcode"],
                    "subgroupof": "",
                    "accountof": groupcode,
                    "groupAccflag": 1,
                    "advflag": adverseflag,
                }
            )

        for subgroup in subgroupData:
            subgroupTotal = 0.00
            accounts = []
            subgroupAccDataRow = con.execute(
                "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                % (orgcode, subgroup["groupcode"])
            )
            subgroupAccData = subgroupAccDataRow.fetchall()
            for account in subgroupAccData:
                accountTotal = 0.00
                adverseflag = 0
                accountDetails = calculateBalance(
                    con,
                    account["accountcode"],
                    financialStart,
                    calculatefrom,
                    calculateTo,
                )
                if accountDetails["baltype"] == "Dr":
                    subgroupTotal += accountDetails["curbal"]
                    accountTotal += accountDetails["curbal"]
                if accountDetails["baltype"] == "Cr" and accountDetails["curbal"] != 0:
                    adverseflag = 1
                    subgroupTotal -= accountDetails["curbal"]
                    accountTotal -= accountDetails["curbal"]
                if accountDetails["curbal"] != 0:
                    accounts.append(
                        {
                            "groupAccname": account["accountname"],
                            "amount": "%.2f" % (accountTotal),
                            "groupAcccode": account["accountcode"],
                            "subgroupof": groupcode,
                            "accountof": subgroup["groupcode"],
                            "groupAccflag": 2,
                            "advflag": adverseflag,
                        }
                    )
            groupWiseTotal += subgroupTotal
            groupAccSubgroup.append(
                {
                    "groupAccname": subgroup["groupname"],
                    "amount": "%.2f" % (subgroupTotal),
                    "groupAcccode": subgroup["groupcode"],
                    "subgroupof": groupcode,
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )
            groupAccSubgroup += accounts

        applicationsTotal += groupWiseTotal
        abalanceSheet.append(
            {
                "groupAccname": "Miscellaneous Expenses(Asset)",
                "amount": "%.2f" % (groupWiseTotal),
                "groupAcccode": groupcode,
                "subgroupof": "",
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        abalanceSheet += groupAccSubgroup

    abalanceSheet.append(
        {
            "groupAccname": "Total",
            "amount": "%.2f" % (applicationsTotal),
            "groupAcccode": "",
            "subgroupof": "",
            "accountof": "",
            "groupAccflag": "",
            "advflag": "",
        }
    )
    # append the closing stock value as well
    sourcesTotal = round(sourcesTotal + closingStockVal, 2) 
    applicationsTotal = round(applicationsTotal, 2)
    difference = abs(sourcesTotal - applicationsTotal)

    if sourcesTotal > applicationsTotal:
        abalanceSheet.append(
            {
                "groupAccname": "Difference",
                "amount": "%.2f" % (difference),
                "groupAcccode": "",
                "subgroupof": "",
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        abalanceSheet.append(
            {
                "groupAccname": "Total",
                "amount": "%.2f" % (sourcesTotal),
                "groupAcccode": "",
                "subgroupof": "",
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
    if applicationsTotal > sourcesTotal:
        sbalanceSheet.append(
            {
                "groupAccname": "Difference",
                "amount": "%.2f" % (difference),
                "groupAcccode": "",
                "subgroupof": "",
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )
        sbalanceSheet.append(
            {
                "groupAccname": "Total",
                "amount": "%.2f" % (applicationsTotal),
                "groupAcccode": "",
                "subgroupof": "",
                "accountof": "",
                "groupAccflag": "",
                "advflag": "",
            }
        )

    if balancetype == 1:
        if orgtype == "Profit Making":
            if applicationsTotal > sourcesTotal and profit == 0:
                abalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
            if sourcesTotal > applicationsTotal and profit == 0:
                sbalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
                sbalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
                sbalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
            if applicationsTotal > sourcesTotal and profit != 0:
                abalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
                abalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
            if sourcesTotal > applicationsTotal and profit != 0:
                sbalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
                sbalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
            if difference == 0 and profit == 0:
                sbalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
            if difference == 0 and profit != 0:
                emptyno = 0
        if orgtype == "Not For Profit":
            if applicationsTotal > sourcesTotal and profit == 0:
                abalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
                abalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
            if sourcesTotal > applicationsTotal and profit == 0:
                sbalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
                sbalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
            if applicationsTotal > sourcesTotal and profit != 0:
                abalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
                abalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
                abalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
            if sourcesTotal > applicationsTotal and profit != 0:
                sbalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )
            if difference == 0 and profit == 0:
                emptyno = 0
            if difference == 0 and profit != 0:
                abalanceSheet.insert(
                    -1,
                    {
                        "groupAccname": "",
                        "amount": "",
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    },
                )

    return {"leftlist": sbalanceSheet, "rightlist": abalanceSheet}


def calculateBalance(con, accountCode, financialStart, calculateFrom, calculateTo):
    """
    purpose:
    This is a private method which will return
    *groupname for the provided account
    *opening balance for the range
    *opening balance type
    *closing balance for the selected range
    *closing balance type
    *Total Dr for the range
    * total Cr for the range.
    Input parameters are:
    *Orgcode
    *accountname
    *financialfrom
    *calculatefrom
    *calculateto

    first we will get the groupname for the provided account.
    note that the given account may be associated with a subgroup for which we must get the group.
    Then we get the opening balance and if it is not 0 then decide if it is a Dr or Cr balance based on the group.
    Then the Total Dr and Cr is calculated.
    If the calculate from is ahead of financial start, then the entire process is repeated.
    This function is called by all reports in this resource.
    we will be initializing all function level variables here.
    """
    groupName = ""
    openingBalance = 0.00
    balanceBrought = 0.00
    currentBalance = 0.00
    ttlCrBalance = 0.00
    ttlDrBalance = 0.00
    openingBalanceType = ""
    ttlDrUptoFrom = 0.00
    ttlCrUptoFrom = 0.00
    balType = ""
    groupData = con.execute(
        "select groupname from groupsubgroups where subgroupof is null and groupcode = (select groupcode from accounts where accountcode = %d) or groupcode = (select subgroupof from groupsubgroups where groupcode = (select groupcode from accounts where accountcode = %d));"
        % (int(accountCode), int(accountCode))
    )
    groupRecord = groupData.fetchone()
    groupName = groupRecord["groupname"]
    # now similarly we will get the opening balance for this account.

    obData = con.execute(
        select([accounts.c.openingbal]).where(accounts.c.accountcode == accountCode)
    )
    ob = obData.fetchone()
    openingBalance = float(ob["openingbal"])
    financialStart = str(financialStart)
    calculateFrom = str(calculateFrom)
    financialYearStartDate = datetime.strptime(financialStart, "%Y-%m-%d")
    calculateFromDate = datetime.strptime(calculateFrom, "%Y-%m-%d")
    calculateToDate = datetime.strptime(calculateTo, "%Y-%m-%d")
    if financialYearStartDate == calculateFromDate:
        if openingBalance == 0:
            balanceBrought = 0

        if openingBalance < 0 and (
            groupName == "Current Assets"
            or groupName == "Fixed Assets"
            or groupName == "Investments"
            or groupName == "Loans(Asset)"
            or groupName == "Miscellaneous Expenses(Asset)"
        ):
            balanceBrought = abs(openingBalance)
            openingBalanceType = "Cr"
            balType = "Cr"

        if openingBalance > 0 and (
            groupName == "Current Assets"
            or groupName == "Fixed Assets"
            or groupName == "Investments"
            or groupName == "Loans(Asset)"
            or groupName == "Miscellaneous Expenses(Asset)"
        ):
            balanceBrought = openingBalance
            openingBalanceType = "Dr"
            balType = "Dr"

        if openingBalance < 0 and (
            groupName == "Corpus"
            or groupName == "Capital"
            or groupName == "Current Liabilities"
            or groupName == "Loans(Liability)"
            or groupName == "Reserves"
        ):
            balanceBrought = abs(openingBalance)
            openingBalanceType = "Dr"
            balType = "Dr"

        if openingBalance > 0 and (
            groupName == "Corpus"
            or groupName == "Capital"
            or groupName == "Current Liabilities"
            or groupName == "Loans(Liability)"
            or groupName == "Reserves"
        ):
            balanceBrought = openingBalance
            openingBalanceType = "Cr"
            balType = "Cr"
    else:
        tdrfrm = con.execute(
            "select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s'"
            % (
                int(accountCode),
                financialStart,
                calculateFrom,
            )
        )
        tcrfrm = con.execute(
            "select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate < '%s'"
            % (int(accountCode), financialStart, calculateFrom)
        )
        tdrRow = tdrfrm.fetchone()
        tcrRow = tcrfrm.fetchone()
        ttlCrUptoFrom = tcrRow["total"]
        ttlDrUptoFrom = tdrRow["total"]
        if ttlCrUptoFrom == None:
            ttlCrUptoFrom = 0.00
        if ttlDrUptoFrom == None:
            ttlDrUptoFrom = 0.00

        if openingBalance == 0:
            balanceBrought = 0.00
        if openingBalance < 0 and (
            groupName == "Current Assets"
            or groupName == "Fixed Assets"
            or groupName == "Investments"
            or groupName == "Loans(Asset)"
            or groupName == "Miscellaneous Expenses(Asset)"
        ):
            ttlCrUptoFrom = ttlCrUptoFrom + abs(openingBalance)
        if openingBalance > 0 and (
            groupName == "Current Assets"
            or groupName == "Fixed Assets"
            or groupName == "Investments"
            or groupName == "Loans(Asset)"
            or groupName == "Miscellaneous Expenses(Asset)"
        ):
            ttlDrUptoFrom = ttlDrUptoFrom + openingBalance
        if openingBalance < 0 and (
            groupName == "Corpus"
            or groupName == "Capital"
            or groupName == "Current Liabilities"
            or groupName == "Loans(Liability)"
            or groupName == "Reserves"
        ):
            ttlDrUptoFrom = ttlDrUptoFrom + abs(openingBalance)
        if openingBalance > 0 and (
            groupName == "Corpus"
            or groupName == "Capital"
            or groupName == "Current Liabilities"
            or groupName == "Loans(Liability)"
            or groupName == "Reserves"
        ):
            ttlCrUptoFrom = ttlCrUptoFrom + openingBalance
        if ttlDrUptoFrom > ttlCrUptoFrom:
            balanceBrought = ttlDrUptoFrom - ttlCrUptoFrom
            balType = "Dr"
            openingBalanceType = "Dr"
        if ttlCrUptoFrom > ttlDrUptoFrom:
            balanceBrought = ttlCrUptoFrom - ttlDrUptoFrom
            balType = "Cr"
            openingBalanceType = "Cr"
    tdrfrm = con.execute(
        "select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s'"
        % (int(accountCode), calculateFrom, calculateTo)
    )
    tdrRow = tdrfrm.fetchone()
    tcrfrm = con.execute(
        "select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s'"
        % (int(accountCode), calculateFrom, calculateTo)
    )
    tcrRow = tcrfrm.fetchone()
    ttlDrBalance = tdrRow["total"]
    ttlCrBalance = tcrRow["total"]
    if ttlCrBalance == None:
        ttlCrBalance = 0.00
    if ttlDrBalance == None:
        ttlDrBalance = 0.00
    if balType == "Dr":
        ttlDrBalance = ttlDrBalance + float(balanceBrought)
    if balType == "Cr":
        ttlCrBalance = ttlCrBalance + float(balanceBrought)
    if ttlDrBalance > ttlCrBalance:
        currentBalance = ttlDrBalance - ttlCrBalance
        balType = "Dr"
    if ttlCrBalance > ttlDrBalance:
        currentBalance = ttlCrBalance - ttlDrBalance
        balType = "Cr"
    # print("=== calculate balance ===")
    # print(ttlCrBalance)
    # print(ttlDrBalance)
    return {
        "balbrought": float(balanceBrought),
        "curbal": float(currentBalance),
        "totalcrbal": float(ttlCrBalance),
        "totaldrbal": float(ttlDrBalance),
        "baltype": balType,
        "openbaltype": openingBalanceType,
        "grpname": groupName,
    }


def billwiseEntryLedger(con, orgcode, vouchercode, invid, drcrid):
    try:
        dcinfo = ""
        if invid == None:
            billdetl = con.execute(
                "select invid, adjamount from billwise where vouchercode = %d and orgcode =%d"
                % (vouchercode, orgcode)
            )
            billDetails = billdetl.fetchall()
            if len(billDetails) != 0:
                inno = "Invoice Nos.:"
                cmno = "Cash Memo Nos.:"
                for inv in billDetails:
                    invno = con.execute(
                        "select invoiceno, icflag from invoice where invid = %d and orgcode = %d"
                        % (inv["invid"], orgcode)
                    )
                    invinfo = invno.fetchone()
                    if invinfo["icflag"] == 9:
                        inno += (
                            str(invinfo["invoiceno"])
                            + ":"
                            + str(inv["adjamount"])
                            + ","
                        )
                        dcinfo = inno
                    else:
                        cmno += (
                            str(invinfo["invoiceno"])
                            + ":"
                            + str(inv["adjamount"])
                            + ","
                        )
                        dcinfo = cmno
        else:
            invno = con.execute(
                "select  invoiceno, icflag from invoice where invid = %d and orgcode = %d"
                % (invid, orgcode)
            )
            invinfo = invno.fetchone()
            if invinfo["icflag"] == 9:
                dcinfo = "Invoice No.:" + str(invinfo["invoiceno"])
            else:
                dcinfo = "Cash Memo No.:" + str(invinfo["invoiceno"])
        if drcrid != None:
            drcrno = con.execute(
                "select drcrno, dctypeflag from drcr where drcrid = %d and orgcode = %d"
                % (drcrid, orgcode)
            )
            drcrinfo = drcrno.fetchone()
            if drcrinfo["dctypeflag"] == 3:
                dcinfo = "Credit note no.:" + str(drcrinfo["drcrno"])
            else:
                dcinfo = "Dedit note no.:" + str(drcrinfo["drcrno"])
        return dcinfo
    except:
        return {"gkstatus": enumdict["ConnectionFailed"]}


def stockonhandfun(orgcode, productCode, endDate):
    try:
        con = eng.connect()
        stockReport = []
        totalinward = 0.00
        totaloutward = 0.00
        if productCode != "all":
            openingStockResult = con.execute(
                select(
                    [
                        product.c.openingstock,
                        product.c.productdesc,
                        product.c.productcode,
                        product.c.gsflag,
                    ]
                ).where(
                    and_(
                        product.c.productcode == productCode,
                        product.c.gsflag == 7,
                        product.c.orgcode == orgcode,
                    )
                )
            )
            osRow = openingStockResult.fetchone()
            openingStock = osRow["openingstock"]
            prodName = osRow["productdesc"]
            prodCode = osRow["productcode"]
            gsflag = osRow["gsflag"]
            stockRecords = con.execute(
                select([stock])
                .where(
                    and_(
                        stock.c.productcode == productCode,
                        stock.c.orgcode == orgcode,
                        or_(
                            stock.c.dcinvtnflag != 20,
                            stock.c.dcinvtnflag != 40,
                            stock.c.dcinvtnflag != 30,
                            stock.c.dcinvtnflag != 90,
                        ),
                    )
                )
                .order_by(stock.c.stockdate)
            )
            stockData = stockRecords.fetchall()
            totalinward = totalinward + float(openingStock)
            for finalRow in stockData:
                if finalRow["dcinvtnflag"] == 3 or finalRow["dcinvtnflag"] == 9:
                    countresult = con.execute(
                        select(
                            [
                                invoice.c.invoicedate,
                                invoice.c.invoiceno,
                                invoice.c.custid,
                            ]
                        ).where(
                            and_(
                                invoice.c.invoicedate <= endDate,
                                invoice.c.invid == finalRow["dcinvtnid"],
                            )
                        )
                    )
                    if countresult.rowcount == 1:
                        countrow = countresult.fetchone()
                        custdata = con.execute(
                            select([customerandsupplier.c.custname]).where(
                                customerandsupplier.c.custid == countrow["custid"]
                            )
                        )
                        custrow = custdata.fetchone()
                        if custrow != None:
                            custnamedata = custrow["custname"]
                        else:
                            custnamedata = "Cash Memo"
                        if finalRow["inout"] == 9:
                            openingStock = float(openingStock) + float(finalRow["qty"])
                            totalinward = float(totalinward) + float(finalRow["qty"])
                        if finalRow["inout"] == 15:
                            openingStock = float(openingStock) - float(finalRow["qty"])
                            totaloutward = float(totaloutward) + float(finalRow["qty"])
                if finalRow["dcinvtnflag"] == 4:
                    countresult = con.execute(
                        select(
                            [delchal.c.dcdate, delchal.c.dcno, delchal.c.custid]
                        ).where(
                            and_(
                                delchal.c.dcdate <= endDate,
                                delchal.c.dcid == finalRow["dcinvtnid"],
                            )
                        )
                    )
                    if countresult.rowcount == 1:
                        countrow = countresult.fetchone()
                        custdata = con.execute(
                            select([customerandsupplier.c.custname]).where(
                                customerandsupplier.c.custid == countrow["custid"]
                            )
                        )
                        custrow = custdata.fetchone()
                        dcinvresult = con.execute(
                            select([dcinv.c.invid]).where(
                                dcinv.c.dcid == finalRow["dcinvtnid"]
                            )
                        )
                        if dcinvresult.rowcount == 1:
                            dcinvrow = dcinvresult.fetchone()
                            invresult = con.execute(
                                select([invoice.c.invoiceno]).where(
                                    invoice.c.invid == dcinvrow["invid"]
                                )
                            )
                            """ No need to check if invresult has rowcount 1 since it must be 1 """
                            invrow = invresult.fetchone()
                            trntype = "delchal&invoice"
                        else:
                            dcinvrow = {"invid": ""}
                            invrow = {"invoiceno": ""}
                            trntype = "delchal"
                        if finalRow["inout"] == 9:
                            openingStock = float(openingStock) + float(finalRow["qty"])
                            totalinward = float(totalinward) + float(finalRow["qty"])
                        if finalRow["inout"] == 15:
                            openingStock = float(openingStock) - float(finalRow["qty"])
                            totaloutward = float(totaloutward) + float(finalRow["qty"])
                if finalRow["dcinvtnflag"] == 18:
                    if finalRow["inout"] == 9:
                        openingStock = float(openingStock) + float(finalRow["qty"])
                        totalinward = float(totalinward) + float(finalRow["qty"])
                    if finalRow["inout"] == 15:
                        openingStock = float(openingStock) - float(finalRow["qty"])
                        totaloutward = float(totaloutward) + float(finalRow["qty"])
                if finalRow["dcinvtnflag"] == 7:
                    countresult = con.execute(
                        select([func.count(drcr.c.drcrid).label("dc")]).where(
                            and_(
                                drcr.c.drcrdate <= endDate,
                                drcr.c.drcrid == finalRow["dcinvtnid"],
                            )
                        )
                    )
                    countrow = countresult.fetchone()
                    if countrow["dc"] == 1:
                        if finalRow["inout"] == 9:
                            openingStock = float(openingStock) + float(finalRow["qty"])
                            totalinward = float(totalinward) + float(finalRow["qty"])
                        if finalRow["inout"] == 15:
                            openingStock = float(openingStock) - float(finalRow["qty"])
                            totaloutward = float(totaloutward) + float(finalRow["qty"])
            stockReport.append(
                {
                    "srno": 1,
                    "productname": prodName,
                    "productcode": prodCode,
                    "totalinwardqty": "%.2f" % float(totalinward),
                    "totaloutwardqty": "%.2f" % float(totaloutward),
                    "balance": "%.2f" % float(openingStock),
                    "goid": finalRow["goid"],
                    "gsflag": gsflag,

                }
            )
            con.close()
            return {"gkstatus": enumdict["Success"], "gkresult": stockReport}
        if productCode == "all":
            products = con.execute(
                select(
                    [
                        product.c.openingstock,
                        product.c.productcode,
                        product.c.productdesc,
                    ]
                ).where(and_(product.c.orgcode == orgcode, product.c.gsflag == 7))
            )
            prodDesc = products.fetchall()
            srno = 1
            for row in prodDesc:
                totalinward = 0.00
                totaloutward = 0.00
                openingStock = row["openingstock"]
                productCd = row["productcode"]
                prodName = row["productdesc"]
                stockRecords = con.execute(
                    select([stock]).where(
                        and_(
                            stock.c.productcode == productCd,
                            stock.c.orgcode == orgcode,
                            or_(
                                stock.c.dcinvtnflag != 20,
                                stock.c.dcinvtnflag != 40,
                                stock.c.dcinvtnflag != 30,
                                stock.c.dcinvtnflag != 90,
                            ),
                        )
                    )
                )
                stockData = stockRecords.fetchall()
                totalinward = totalinward + float(openingStock)
                for finalRow in stockData:
                    if finalRow["dcinvtnflag"] == 3 or finalRow["dcinvtnflag"] == 9:
                        countresult = con.execute(
                            select(
                                [
                                    invoice.c.invoicedate,
                                    invoice.c.invoiceno,
                                    invoice.c.custid,
                                ]
                            ).where(
                                and_(
                                    invoice.c.invoicedate <= endDate,
                                    invoice.c.invid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            custdata = con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == countrow["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            if custrow != None:
                                custnamedata = custrow["custname"]
                            else:
                                custnamedata = "Cash Memo"
                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                    if finalRow["dcinvtnflag"] == 4:
                        countresult = con.execute(
                            select(
                                [delchal.c.dcdate, delchal.c.dcno, delchal.c.custid]
                            ).where(
                                and_(
                                    delchal.c.dcdate <= endDate,
                                    delchal.c.dcid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            custdata = con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == countrow["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            dcinvresult = con.execute(
                                select([dcinv.c.invid]).where(
                                    dcinv.c.dcid == finalRow["dcinvtnid"]
                                )
                            )
                            if dcinvresult.rowcount == 1:
                                dcinvrow = dcinvresult.fetchone()
                                invresult = con.execute(
                                    select([invoice.c.invoiceno]).where(
                                        invoice.c.invid == dcinvrow["invid"]
                                    )
                                )
                                """ No need to check if invresult has rowcount 1 since it must be 1 """
                                invrow = invresult.fetchone()
                                trntype = "delchal&invoice"
                            else:
                                dcinvrow = {"invid": ""}
                                invrow = {"invoiceno": ""}
                                trntype = "delchal"
                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                    if finalRow["dcinvtnflag"] == 18:
                        if finalRow["inout"] == 9:
                            openingStock = float(openingStock) + float(finalRow["qty"])
                            totalinward = float(totalinward) + float(finalRow["qty"])
                        if finalRow["inout"] == 15:
                            openingStock = float(openingStock) - float(finalRow["qty"])
                            totaloutward = float(totaloutward) + float(finalRow["qty"])
                    if finalRow["dcinvtnflag"] == 7:
                        countresult = con.execute(
                            select([func.count(drcr.c.drcrid).label("dc")]).where(
                                and_(
                                    drcr.c.drcrdate <= endDate,
                                    drcr.c.drcrid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        countrow = countresult.fetchone()
                        if countrow["dc"] == 1:
                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                stockReport.append(
                    {
                        "srno": srno,
                        "productname": prodName,
                        "productcode": productCd,
                        "totalinwardqty": "%.2f" % float(totalinward),
                        "totaloutwardqty": "%.2f" % float(totaloutward),
                        "balance": "%.2f" % float(openingStock),
                        "goid": finalRow["goid"],
                    }
                )
                srno = srno + 1
        con.close()
        return {"gkresult": stockReport}

    except Exception as e:
        logging.warn(e)
        return {"gkstatus": enumdict["ConnectionFailed"]}


def calculateOpeningStockValue(con, orgcode):
    try:
        # product table contains both product & service entries, filter only products
        productList = con.execute(
            select([product.c.productcode, product.c.productdesc]).where(
                and_(product.c.orgcode == orgcode, product.c.gsflag == 7)
            )
        ).fetchall()

        godownList = con.execute(
            select([godown.c.goid, godown.c.goname]).where(godown.c.orgcode == orgcode)
        ).fetchall()

        opStock = {"total": 0, "products": {}}
        for productItem in productList:
            prodOpStock = {"total": 0, "godowns": {}}
            if productItem["productcode"]:
                for godownItem in godownList:
                    if godownItem["goid"]:
                        openingStockQuery = con.execute(
                            select(
                                [goprod.c.goopeningstock, goprod.c.openingstockvalue]
                            ).where(
                                and_(
                                    goprod.c.productcode == productItem["productcode"],
                                    goprod.c.goid == godownItem["goid"],
                                    goprod.c.orgcode == orgcode,
                                )
                            )
                        )
                        if openingStockQuery.rowcount:
                            openingStock = openingStockQuery.fetchone()
                            if openingStock["goopeningstock"] != 0:
                                rate = (
                                    openingStock["openingstockvalue"]
                                    / openingStock["goopeningstock"]
                                )
                                # stockOnHand.append(
                                #     {
                                #         "qty": float(openingStock["goopeningstock"]),
                                #         "rate": float(rate),
                                #     }
                                # )
                                # print(stockOnHand)
                                prodOpStock["total"] += float(
                                    openingStock["openingstockvalue"]
                                )
                                if float(openingStock["openingstockvalue"]):
                                    prodOpStock["godowns"][
                                        godownItem["goname"]
                                    ] = float(openingStock["openingstockvalue"])
            opStock["total"] += prodOpStock["total"]
            opStock["products"][productItem["productdesc"]] = (
                0 if not prodOpStock["total"] else prodOpStock
            )
        opStock["total"] = round(opStock["total"], 2)
        return opStock
    except:
        print(traceback.format_exc())
        return {"total": 0, "products": {}}


def calculateClosingStockValue(con, orgcode, endDate):
    try:
        # product table contains both products & services, we fetch only products
        productList = con.execute(
            select([product.c.productcode, product.c.productdesc]).where(
                and_(
                product.c.orgcode == orgcode, product.c.gsflag == 7)
            )
        ).fetchall()

        godownList = con.execute(
            select([godown.c.goid, godown.c.goname]).where(godown.c.orgcode == orgcode)
        ).fetchall()

        closingStock = {"total": 0, "products": {}}
        # loop over all products
        for productItem in productList:
            prodClosingStock = {"total": 0, "godowns": {}}
            if productItem["productcode"]:
                for godownItem in godownList:
                    if godownItem["goid"]:
                        godownStockValue = calculateStockValue(
                            con,
                            orgcode,
                            endDate,
                            productItem["productcode"],
                            godownItem["goid"],
                        )
                        prodClosingStock["total"] += godownStockValue
                        if godownStockValue:
                            prodClosingStock["godowns"][
                                godownItem["goname"]
                            ] = godownStockValue
            closingStock["total"] += prodClosingStock["total"]
            closingStock["products"][productItem["productdesc"]] = (
                0 if not prodClosingStock["total"] else prodClosingStock
            )

        closingStock["total"] = round(closingStock["total"], 2)

        return closingStock
    except:
        print(traceback.format_exc())
        return {"total": 0, "products": {}}


def calculateStockValue(con, orgcode, endDate, productCode, godownCode):
    """
    Note: Preform the below steps for a product in a godown

    Algorithm
    step1: stockInHand = []
    step2: Get the opening stock qty and value from goprod table and push the same into stockInHand array.
    step3: Get all the stock table entries for the product in a godown
    step4: Loop through all the stock data:
            if trn == invoice/ cash memo/ delivery note:
            if purchase:
                stockInHand.append({qty: trn.qty, rate: trn.rate})
            else if sale:
                stockInHand[0][qty] -= trn.qty
    step5: Loop through the stockInHand arr:
            valueOnHand += float(item["qty"]) * float(item["rate"])
    """
    try:
        stockOnHand = []

        # opening stock
        openingStockQuery = con.execute(
            select([goprod.c.goopeningstock, goprod.c.openingstockvalue]).where(
                and_(
                    goprod.c.productcode == productCode,
                    goprod.c.goid == godownCode,
                    goprod.c.orgcode == orgcode,
                )
            )
        )

        if openingStockQuery.rowcount:
            openingStock = openingStockQuery.fetchone()
            if openingStock["goopeningstock"] != 0:
                rate = (
                    openingStock["openingstockvalue"] / openingStock["goopeningstock"]
                )
                stockOnHand.append(
                    {"qty": float(openingStock["goopeningstock"]), "rate": float(rate)}
                )
                print(stockOnHand)

        print(endDate)
        # stock sale and purchase data
        stockList = con.execute(
            select(
                [
                    stock.c.inout,
                    stock.c.rate,
                    stock.c.qty,
                    stock.c.dcinvtnid,
                    stock.c.dcinvtnflag,
                ]
            )
            .where(
                and_(
                    stock.c.orgcode == orgcode,
                    stock.c.productcode == productCode,
                    stock.c.goid == godownCode,
                )
            )
            .order_by(stock.c.stockdate, stock.c.stockid)
        ).fetchall()
        # print(len(stockList))

        for item in stockList:
            # print(item["qty"])
            trnId = item["dcinvtnid"]
            trnFlag = item["dcinvtnflag"]

            proceed = True
            stockIn = item["inout"] == 9

            if trnFlag == 4:  # avoid unlinked delchal
                linkCount = con.execute(
                    select([func.count(dcinv.c.invid)]).where(
                        and_(dcinv.c.dcid == trnId, dcinv.c.orgcode == orgcode)
                    )
                ).scalar()
                # print("linkcount = %d"%(linkCount))
                # some delivery challans wont be linked to invoices, so avoid them here
                if linkCount <= 0:
                    proceed = False
            if proceed:
                # update stockOnHand based on FIFO
                if stockIn:  # purchase or stock in
                    stockLen = len(stockOnHand)
                    if stockLen:
                        lastStock = stockOnHand[stockLen - 1]
                        if float(lastStock["qty"]) < 0 and float(
                            lastStock["rate"]
                        ) == float(
                            item["rate"]
                        ):  # case where sale or stock out has happened before any purchase or stock in
                            lastStock["qty"] = float(lastStock["qty"]) + float(
                                item["qty"]
                            )
                            continue
                    stockOnHand.append({"rate": item["rate"], "qty": item["qty"]})
                else:  # sale or stock out
                    # print("==============soh=============")
                    # print(stockOnHand)
                    stockLen = len(stockOnHand)

                    if stockLen:
                        stockOnHand[0]["qty"] = float(stockOnHand[0]["qty"]) - float(
                            item["qty"]
                        )

                        extraQty = stockOnHand[0]["qty"]

                        if extraQty <= 0:
                            extraQty *= -1
                            while extraQty:
                                stockOnHand.pop(0)
                                if extraQty == 0:
                                    break
                                if len(stockOnHand) > 0:
                                    if float(stockOnHand[0]["qty"]) > 0:
                                        stockOnHand[0]["qty"] = (
                                            float(stockOnHand[0]["qty"]) - extraQty
                                        )
                                        extraQty = stockOnHand[0]["qty"]
                                        if extraQty >= 0:
                                            break
                                        else:
                                            extraQty *= -1
                                    else:
                                        # if the qty is negative (stock out happened before stock in), then the remaining negative will also be added to it
                                        stockOnHand[0]["qty"] = (
                                            float(stockOnHand[0]["qty"]) - extraQty
                                        )
                                        break
                                else:
                                    stockOnHand.append(
                                        {"rate": item["rate"], "qty": -1 * extraQty}
                                    )
                                    break
                    else:
                        stockOnHand.append(
                            {"rate": item["rate"], "qty": -1 * item["qty"]}
                        )
                # print(stockOnHand)
        valueOnHand = 0
        # print("Stock value calculation")
        for item in stockOnHand:
            valueOnHand += float(item["qty"]) * float(item["rate"])
            # print(valueOnHand)
        return round(valueOnHand, 2)
    except:
        print(traceback.format_exc())
        return -1


def godownwisestockonhandfun(
    con, orgcode, startDate, endDate, stocktype, productCode, godownCode
):
    try:
        con = eng.connect()
        stockReport = []
        totalinward = 0.00
        totaloutward = 0.00
        openingStock = 0.00
        if stocktype == "pg":
            productCode = productCode
            godownCode = godownCode
            goopeningStockResult = con.execute(
                select([goprod.c.goopeningstock]).where(
                    and_(
                        goprod.c.productcode == productCode,
                        goprod.c.goid == godownCode,
                        goprod.c.orgcode == orgcode,
                    )
                )
            )
            gosRow = goopeningStockResult.fetchone()
            if gosRow != None:
                gopeningStock = gosRow["goopeningstock"]
            else:
                gopeningStock = 0.00
            stockRecords = con.execute(
                select([stock])
                .where(
                    and_(
                        stock.c.productcode == productCode,
                        stock.c.goid == godownCode,
                        stock.c.orgcode == orgcode,
                        or_(
                            stock.c.dcinvtnflag != 40,
                            stock.c.dcinvtnflag != 30,
                            stock.c.dcinvtnflag != 90,
                        ),
                    )
                )
                .order_by(stock.c.stockdate)
            )
            stockData = stockRecords.fetchall()
            ysData = con.execute(
                select([organisation.c.yearstart]).where(
                    organisation.c.orgcode == orgcode
                )
            )
            ysRow = ysData.fetchone()
            yearStart = datetime.strptime(str(ysRow["yearstart"]), "%Y-%m-%d")
            if not startDate:
                startDate = yearStart
            totalinward = totalinward + float(gopeningStock)
            for finalRow in stockData:
                if finalRow["dcinvtnflag"] == 4:
                    # Delivery note
                    countresult = con.execute(
                        select(
                            [delchal.c.dcdate, delchal.c.dcno, delchal.c.custid]
                        ).where(
                            and_(
                                delchal.c.dcdate <= endDate,
                                delchal.c.dcid == finalRow["dcinvtnid"],
                            )
                        )
                    )
                    if countresult.rowcount == 1:
                        countrow = countresult.fetchone()
                        custdata = con.execute(
                            select([customerandsupplier.c.custname]).where(
                                customerandsupplier.c.custid == countrow["custid"]
                            )
                        )
                        custrow = custdata.fetchone()
                        dcinvresult = con.execute(
                            select([dcinv.c.invid]).where(
                                dcinv.c.dcid == finalRow["dcinvtnid"]
                            )
                        )
                        if dcinvresult.rowcount == 1:
                            dcinvrow = dcinvresult.fetchone()
                            invresult = con.execute(
                                select([invoice.c.invoiceno]).where(
                                    invoice.c.invid == dcinvrow["invid"]
                                )
                            )
                            """ No need to check if invresult has rowcount 1 since it must be 1 """
                            invrow = invresult.fetchone()
                            trntype = "delchal&invoice"
                        else:
                            dcinvrow = {"invid": ""}
                            invrow = {"invoiceno": ""}
                            trntype = "delcha"
                        if finalRow["inout"] == 9:
                            gopeningStock = float(gopeningStock) + float(
                                finalRow["qty"]
                            )
                            totalinward = float(totalinward) + float(finalRow["qty"])
                        if finalRow["inout"] == 15:
                            gopeningStock = float(gopeningStock) - float(
                                finalRow["qty"]
                            )
                            totaloutward = float(totaloutward) + float(finalRow["qty"])
                if finalRow["dcinvtnflag"] == 20:
                    # Transfer Note
                    countresult = con.execute(
                        select(
                            [
                                transfernote.c.transfernotedate,
                                transfernote.c.transfernoteno,
                            ]
                        ).where(
                            and_(
                                transfernote.c.transfernotedate <= endDate,
                                transfernote.c.transfernoteid == finalRow["dcinvtnid"],
                            )
                        )
                    )
                    if countresult.rowcount == 1:
                        countrow = countresult.fetchone()
                        if finalRow["inout"] == 9:
                            gopeningStock = float(gopeningStock) + float(
                                finalRow["qty"]
                            )
                            totalinward = float(totalinward) + float(finalRow["qty"])
                        if finalRow["inout"] == 15:
                            gopeningStock = float(gopeningStock) - float(
                                finalRow["qty"]
                            )
                            totaloutward = float(totaloutward) + float(finalRow["qty"])
                if finalRow["dcinvtnflag"] == 18:
                    # Rejection Note
                    if finalRow["inout"] == 9:
                        gopeningStock = float(gopeningStock) + float(finalRow["qty"])
                        totalinward = float(totalinward) + float(finalRow["qty"])
                    if finalRow["inout"] == 15:
                        gopeningStock = float(gopeningStock) - float(finalRow["qty"])
                        totaloutward = float(totaloutward) + float(finalRow["qty"])
                if finalRow["dcinvtnflag"] == 7:
                    # Debite Credit Note
                    countresult = con.execute(
                        select([func.count(drcr.c.drcrid).label("dc")]).where(
                            and_(
                                drcr.c.drcrdate >= yearStart,
                                drcr.c.drcrdate <= endDate,
                                drcr.c.drcrid == finalRow["dcinvtnid"],
                            )
                        )
                    )
                    countrow = countresult.fetchone()
                    if countrow["dc"] == 1:
                        if finalRow["inout"] == 9:
                            gopeningStock = float(gopeningStock) + float(
                                finalRow["qty"]
                            )
                            totalinward = float(totalinward) + float(finalRow["qty"])
                        if finalRow["inout"] == 15:
                            gopeningStock = float(gopeningStock) - float(
                                finalRow["qty"]
                            )
                            totaloutward = float(totaloutward) + float(finalRow["qty"])
            stockReport.append(
                {
                    "srno": 1,
                    "totalinwardqty": "%.2f" % float(totalinward),
                    "totaloutwardqty": "%.2f" % float(totaloutward),
                    "balance": "%.2f" % float(gopeningStock),
                }
            )
            return stockReport
        if stocktype == "pag":
            productCode = productCode
            products = con.execute(
                select([product.c.productdesc]).where(
                    and_(
                        product.c.productcode == productCode,
                        product.c.orgcode == orgcode,
                    )
                )
            )
            prodDesc = products.fetchone()
            goopeningStockResult = con.execute(
                select([goprod.c.goopeningstock, goprod.c.goid]).where(
                    and_(
                        goprod.c.productcode == productCode, goprod.c.orgcode == orgcode
                    )
                )
            )
            gosRow = goopeningStockResult.fetchall()
            srno = 1
            for row in gosRow:
                totalinward = 0.00
                totaloutward = 0.00
                openingStock = 0.00
                if row["goopeningstock"] != None:
                    gopeningStock = row["goopeningstock"]
                else:
                    gopeningStock = 0.00
                godowns = con.execute(
                    select([godown.c.goname]).where(
                        and_(godown.c.goid == row["goid"], godown.c.orgcode == orgcode)
                    )
                )
                goName = godowns.fetchone()
                gn = goName["goname"]
                stockRecords = con.execute(
                    select([stock])
                    .where(
                        and_(
                            stock.c.productcode == productCode,
                            stock.c.goid == row["goid"],
                            stock.c.orgcode == orgcode,
                            or_(
                                stock.c.dcinvtnflag != 40,
                                stock.c.dcinvtnflag != 30,
                                stock.c.dcinvtnflag != 90,
                            ),
                        )
                    )
                    .order_by(stock.c.stockdate)
                )
                stockData = stockRecords.fetchall()
                totalinward = totalinward + float(gopeningStock)
                for finalRow in stockData:
                    if finalRow["dcinvtnflag"] == 4:
                        countresult = con.execute(
                            select(
                                [delchal.c.dcdate, delchal.c.dcno, delchal.c.custid]
                            ).where(
                                and_(
                                    delchal.c.dcdate <= endDate,
                                    delchal.c.dcid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            custdata = con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == countrow["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            dcinvresult = con.execute(
                                select([dcinv.c.invid]).where(
                                    dcinv.c.dcid == finalRow["dcinvtnid"]
                                )
                            )
                            if dcinvresult.rowcount == 1:
                                dcinvrow = dcinvresult.fetchone()
                                invresult = con.execute(
                                    select([invoice.c.invoiceno]).where(
                                        invoice.c.invid == dcinvrow["invid"]
                                    )
                                )
                                """ No need to check if invresult has rowcount 1 since it must be 1 """
                                invrow = invresult.fetchone()
                                trntype = "delchal&invoice"
                            else:
                                dcinvrow = {"invid": ""}
                                invrow = {"invoiceno": ""}
                                trntype = "delcha"
                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                    if finalRow["dcinvtnflag"] == 20:
                        countresult = con.execute(
                            select(
                                [
                                    transfernote.c.transfernotedate,
                                    transfernote.c.transfernoteno,
                                ]
                            ).where(
                                and_(
                                    transfernote.c.transfernotedate <= endDate,
                                    transfernote.c.transfernoteid
                                    == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                    if finalRow["dcinvtnflag"] == 18:
                        if finalRow["inout"] == 9:
                            gopeningStock = float(gopeningStock) + float(
                                finalRow["qty"]
                            )
                            totalinward = float(totalinward) + float(finalRow["qty"])
                        if finalRow["inout"] == 15:
                            gopeningStock = float(gopeningStock) - float(
                                finalRow["qty"]
                            )
                            totaloutward = float(totaloutward) + float(finalRow["qty"])
                    if finalRow["dcinvtnflag"] == 7:
                        countresult = con.execute(
                            select([func.count(drcr.c.drcrid).label("dc")]).where(
                                and_(
                                    drcr.c.drcrdate >= yearStart,
                                    drcr.c.drcrdate < startDate,
                                    drcr.c.drcrid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        countrow = countresult.fetchone()
                        if countrow["dc"] == 1:
                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                stockReport.append(
                    {
                        "srno": srno,
                        "productname": prodDesc["productdesc"],
                        "godown": gn,
                        "totalinwardqty": "%.2f" % float(totalinward),
                        "totaloutwardqty": "%.2f" % float(totaloutward),
                        "balance": "%.2f" % float(gopeningStock),
                    }
                )
                srno = srno + 1
            return stockReport
    except:
        # print(traceback.format_exc())
        return {"gkstatus": enumdict["ConnectionFailed"]}


# TODO: methods calculateProfitLossValue and calculateProfitLossPerProduct perform the same activities as calculateStockValue and calculateClosingStockValue.
# only the code to calculate profit and loss difference is extra. If possible merge the two to a generic method
def calculateProfitLossValue(con, orgcode, endDate):
    try:
        productList = con.execute(
            select([product.c.productcode, product.c.productdesc]).where(
                product.c.orgcode == orgcode
            )
        ).fetchall()

        godownList = con.execute(
            select([godown.c.goid, godown.c.goname]).where(godown.c.orgcode == orgcode)
        ).fetchall()

        plBuffer = {"total": 0, "products": {}}

        for productItem in productList:
            prodClosingStock = {"total": 0, "godowns": {}}
            if productItem["productcode"]:
                for godownItem in godownList:
                    if godownItem["goid"]:
                        godownStockValue = calculateProfitLossPerProduct(
                            con,
                            orgcode,
                            endDate,
                            productItem["productcode"],
                            godownItem["goid"],
                        )
                        prodClosingStock["total"] += godownStockValue
                        if godownStockValue:
                            prodClosingStock["godowns"][
                                godownItem["goname"]
                            ] = godownStockValue
            plBuffer["total"] += prodClosingStock["total"]
            plBuffer["products"][productItem["productdesc"]] = (
                0 if not prodClosingStock["total"] else prodClosingStock
            )

        plBuffer["total"] = round(plBuffer["total"], 2)

        return plBuffer
    except:
        print(traceback.format_exc())
        return {"total": 0, "products": {}}


def calculateProfitLossPerProduct(con, orgcode, endDate, productCode, godownCode):
    """
    Note: Preform the below steps for a product in a godown

    Algorithm
    step1: stockInHand = []
    step2: Get the opening stock qty and value from goprod table and push the same into stockInHand array.
    step3: Get all the stock table entries for the product in a godown
    step4: Loop through all the stock data:
            if trn == invoice/ cash memo/ delivery note:
            if purchase:
                stockInHand.append({qty: trn.qty, rate: trn.rate})
            else if sale:
                stockInHand[0][qty] -= trn.qty
    step5: Loop through the stockInHand arr:
            valueOnHand += float(item["qty"]) * float(item["rate"])
    """
    try:
        stockOnHand = []
        priceDiff = 0

        # opening stock
        openingStockQuery = con.execute(
            select([goprod.c.goopeningstock, goprod.c.openingstockvalue]).where(
                and_(
                    goprod.c.productcode == productCode,
                    goprod.c.goid == godownCode,
                    goprod.c.orgcode == orgcode,
                )
            )
        )

        if openingStockQuery.rowcount:
            openingStock = openingStockQuery.fetchone()
            if openingStock["goopeningstock"] != 0:
                rate = (
                    openingStock["openingstockvalue"] / openingStock["goopeningstock"]
                )
                stockOnHand.append(
                    {"qty": float(openingStock["goopeningstock"]), "rate": float(rate)}
                )

        # stock sale and purchase data
        stockList = con.execute(
            select(
                [
                    stock.c.inout,
                    stock.c.rate,
                    stock.c.qty,
                    stock.c.dcinvtnid,
                    stock.c.dcinvtnflag,
                ]
            )
            .where(
                and_(
                    stock.c.orgcode == orgcode,
                    stock.c.productcode == productCode,
                    stock.c.goid == godownCode,
                    stock.c.stockdate <= endDate,
                )
            )
            .order_by(stock.c.stockdate, stock.c.stockid)
        ).fetchall()
        # print(len(stockList))

        for item in stockList:
            # print(item)
            trnId = item["dcinvtnid"]
            trnFlag = item["dcinvtnflag"]

            proceed = True
            stockIn = item["inout"] == 9

            if trnFlag == 4:  # avoid unlinked delchal
                linkCount = con.execute(
                    select([func.count(dcinv.c.invid)]).where(
                        and_(dcinv.c.dcid == trnId, dcinv.c.orgcode == orgcode)
                    )
                ).scalar()
                # print("linkcount = %d"%(linkCount))
                # some delivery challans wont be linked to invoices, so avoid them here
                if linkCount <= 0:
                    proceed = False
            if proceed:
                # update stockOnHand based on FIFO
                if stockIn:  # purchase or stock in
                    stockLen = len(stockOnHand)
                    if stockLen:
                        lastStock = stockOnHand[stockLen - 1]
                        if float(lastStock["qty"]) < 0 and float(
                            lastStock["rate"]
                        ) == float(
                            item["rate"]
                        ):  # case where sale or stock out has happened before any purchase or stock in
                            lastStock["qty"] = float(lastStock["qty"]) + float(
                                item["qty"]
                            )
                            continue
                    stockOnHand.append({"rate": item["rate"], "qty": item["qty"]})
                else:  # sale or stock out
                    # print("==============soh=============")
                    # print(stockOnHand)
                    stockLen = len(stockOnHand)

                    if stockLen:
                        priceDiff += (float(item["qty"]) * float(item["rate"])) - (
                            float(item["qty"]) * float(stockOnHand[0]["rate"])
                        )
                        # if float(stockOnHand[0]["qty"]) > float(item["qty"]):
                        #     )
                        # else:
                        #     priceDiff = float(item[0]["qty"]) * float(
                        #         stockOnHand[0]["rate"]
                        #     )

                        stockOnHand[0]["qty"] = float(stockOnHand[0]["qty"]) - float(
                            item["qty"]
                        )

                        extraQty = stockOnHand[0]["qty"]
                        # if extraQty < 0, items sold > items purchased
                        if extraQty <= 0:
                            extraQty *= -1
                            while extraQty:
                                stockOnHand.pop(0)
                                if extraQty == 0:
                                    break
                                if len(stockOnHand) > 0:
                                    if float(stockOnHand[0]["qty"]) > 0:
                                        stockOnHand[0]["qty"] = (
                                            float(stockOnHand[0]["qty"]) - extraQty
                                        )
                                        extraQty = stockOnHand[0]["qty"]
                                        if extraQty >= 0:
                                            break
                                        else:
                                            extraQty *= -1
                                    else:
                                        # if the qty is negative (stock out happened before stock in), then the remaining negative will also be added to it
                                        # In this case price diff need not be calculated
                                        stockOnHand[0]["qty"] = (
                                            float(stockOnHand[0]["qty"]) - extraQty
                                        )
                                        break
                                else:
                                    stockOnHand.append(
                                        {"rate": item["rate"], "qty": -1 * extraQty}
                                    )
                                    break
                    else:
                        stockOnHand.append(
                            {"rate": item["rate"], "qty": -1 * item["qty"]}
                        )
                # print(priceDiff)
        valueOnHand = 0
        for item in stockOnHand:
            valueOnHand += float(item["qty"]) * float(item["rate"])
            # print(valueOnHand)
        return round(priceDiff, 2)
    except:
        print(traceback.format_exc())
        return -1


@view_defaults(route_name="report", request_method="GET")
class api_reports(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    @view_config(route_name="ledger-monthly", renderer="json")
    def monthlyLedger(self):
        """
        Purpose:
        Gets the list of all months with their respective closing balance for the given account.
        takes accountcode as input parameter.
        description:
        This function is used to produce a monthly ledger report for a given account.
        This is a useful report from which the accountant can choose
        a month for which the entire ledger can be displayed.
        In this report just the closing balance at end of every month is displayed.
        Takes accountcode as input parameter.
        This function is called when type=monthlyledger is passed to the /reports url.
        accountcode is extracted from json_body from request.
        Orgcode is procured from the jwt header.
        The list returned is a grid containing set of dictionaries.
        For each month calculatebalance will be called to get the closing balnace for that range.
        each dictionary will have 2 keys with their respective values,
        month and balance will be the 2 key value pares.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                orgcode = authDetails["orgcode"]
                accountCode = self.request.params["accountcode"]
                accNameData = self.con.execute(
                    select([accounts.c.accountname]).where(
                        accounts.c.accountcode == accountCode
                    )
                )
                row = accNameData.fetchone()
                accname = row["accountname"]
                finStartData = self.con.execute(
                    select([organisation.c.yearstart]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                finRow = finStartData.fetchone()
                financialStart = finRow["yearstart"]
                finEndData = self.con.execute(
                    select([organisation.c.yearend]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                finEndrow = finEndData.fetchone()
                financialEnd = finEndrow["yearend"]
                monthCounter = 1
                startMonthDate = financialStart
                endMonthDate = date(
                    startMonthDate.year,
                    startMonthDate.month,
                    (calendar.monthrange(startMonthDate.year, startMonthDate.month)[1]),
                )
                monthlyBal = []
                while endMonthDate <= financialEnd:
                    count = self.con.execute(
                        "select count(vouchercode) as vcount from vouchers where voucherdate<='%s' and voucherdate>='%s' and orgcode='%d' and (drs ? '%s' or crs ? '%s') "
                        % (
                            endMonthDate,
                            startMonthDate,
                            orgcode,
                            accountCode,
                            accountCode,
                        )
                    )
                    count = count.fetchone()
                    countDr = self.con.execute(
                        "select count(vouchercode) as vcount from vouchers where voucherdate<='%s' and voucherdate>='%s' and orgcode='%d' and (drs ? '%s') "
                        % (endMonthDate, startMonthDate, orgcode, accountCode)
                    )
                    countDr = countDr.fetchone()
                    countCr = self.con.execute(
                        "select count(vouchercode) as vcount from vouchers where voucherdate<='%s' and voucherdate>='%s' and orgcode='%d' and (crs ? '%s') "
                        % (endMonthDate, startMonthDate, orgcode, accountCode)
                    )
                    countCr = countCr.fetchone()
                    countLock = self.con.execute(
                        "select count(vouchercode) as vcount from vouchers where voucherdate<='%s' and voucherdate>='%s' and orgcode='%d' and lockflag='t' and (drs ? '%s' or crs ? '%s') "
                        % (
                            endMonthDate,
                            startMonthDate,
                            orgcode,
                            accountCode,
                            accountCode,
                        )
                    )
                    countLock = countLock.fetchone()
                    adverseflag = 0
                    monthClBal = calculateBalance(
                        self.con,
                        accountCode,
                        str(financialStart),
                        str(financialStart),
                        str(endMonthDate),
                    )
                    if monthClBal["baltype"] == "Dr":
                        if (
                            monthClBal["grpname"] == "Corpus"
                            or monthClBal["grpname"] == "Capital"
                            or monthClBal["grpname"] == "Current Liabilities"
                            or monthClBal["grpname"] == "Loans(Liability)"
                            or monthClBal["grpname"] == "Reserves"
                            or monthClBal["grpname"] == "Indirect Income"
                            or monthClBal["grpname"] == "Direct Income"
                        ) and monthClBal["curbal"] != 0:
                            adverseflag = 1
                        clBal = {
                            "month": calendar.month_name[startMonthDate.month],
                            "Dr": "%.2f" % float(monthClBal["curbal"]),
                            "Cr": "",
                            "period": str(startMonthDate) + ":" + str(endMonthDate),
                            "vcount": count["vcount"],
                            "vcountDr": countDr["vcount"],
                            "vcountCr": countCr["vcount"],
                            "vcountLock": countLock["vcount"],
                            "advflag": adverseflag,
                        }
                        monthlyBal.append(clBal)
                    if monthClBal["baltype"] == "Cr":
                        if (
                            monthClBal["grpname"] == "Current Assets"
                            or monthClBal["grpname"] == "Fixed Assets"
                            or monthClBal["grpname"] == "Investments"
                            or monthClBal["grpname"] == "Loans(Asset)"
                            or monthClBal["grpname"] == "Miscellaneous Expenses(Asset)"
                            or monthClBal["grpname"] == "Indirect Expense"
                            or monthClBal["grpname"] == "Direct Expense"
                        ) and monthClBal["curbal"] != 0:
                            adverseflag = 1
                        clBal = {
                            "month": calendar.month_name[startMonthDate.month],
                            "Dr": "",
                            "Cr": "%.2f" % float(monthClBal["curbal"]),
                            "period": str(startMonthDate) + ":" + str(endMonthDate),
                            "vcount": count["vcount"],
                            "vcountDr": countDr["vcount"],
                            "vcountCr": countCr["vcount"],
                            "vcountLock": countLock["vcount"],
                            "advflag": adverseflag,
                        }
                        monthlyBal.append(clBal)
                    if monthClBal["baltype"] == "":
                        if (
                            monthClBal["grpname"] == "Corpus"
                            or monthClBal["grpname"] == "Capital"
                            or monthClBal["grpname"] == "Current Liabilities"
                            or monthClBal["grpname"] == "Loans(Liability)"
                            or monthClBal["grpname"] == "Reserves"
                            or monthClBal["grpname"] == "Indirect Income"
                            or monthClBal["grpname"] == "Direct Income"
                        ) and count["vcount"] != 0:
                            clBal = {
                                "month": calendar.month_name[startMonthDate.month],
                                "Dr": "",
                                "Cr": "%.2f" % float(monthClBal["curbal"]),
                                "period": str(startMonthDate) + ":" + str(endMonthDate),
                                "vcount": count["vcount"],
                                "vcountDr": countDr["vcount"],
                                "vcountCr": countCr["vcount"],
                                "vcountLock": countLock["vcount"],
                                "advflag": adverseflag,
                            }
                        if (
                            monthClBal["grpname"] == "Current Assets"
                            or monthClBal["grpname"] == "Fixed Assets"
                            or monthClBal["grpname"] == "Investments"
                            or monthClBal["grpname"] == "Loans(Asset)"
                            or monthClBal["grpname"] == "Miscellaneous Expenses(Asset)"
                            or monthClBal["grpname"] == "Indirect Expense"
                            or monthClBal["grpname"] == "Direct Expense"
                        ) and count["vcount"] != 0:
                            clBal = {
                                "month": calendar.month_name[startMonthDate.month],
                                "Dr": "%.2f" % float(monthClBal["curbal"]),
                                "Cr": "",
                                "period": str(startMonthDate) + ":" + str(endMonthDate),
                                "vcount": count["vcount"],
                                "vcountDr": countDr["vcount"],
                                "vcountCr": countCr["vcount"],
                                "vcountLock": countLock["vcount"],
                                "advflag": adverseflag,
                            }
                        if count["vcount"] == 0:
                            clBal = {
                                "month": calendar.month_name[startMonthDate.month],
                                "Dr": "",
                                "Cr": "",
                                "period": str(startMonthDate) + ":" + str(endMonthDate),
                                "vcount": count["vcount"],
                                "vcountDr": countDr["vcount"],
                                "vcountCr": countCr["vcount"],
                                "vcountLock": countLock["vcount"],
                                "advflag": adverseflag,
                            }
                        monthlyBal.append(clBal)
                    startMonthDate = date(
                        financialStart.year, financialStart.month, financialStart.day
                    ) + monthdelta(monthCounter)
                    endMonthDate = date(
                        startMonthDate.year,
                        startMonthDate.month,
                        calendar.monthrange(startMonthDate.year, startMonthDate.month)[
                            1
                        ],
                    )
                    monthCounter += 1
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": monthlyBal,
                    "accountcode": accountCode,
                    "accountname": accname,
                }

            except Exception as E:
                print(E)
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="ledger", renderer="json")
    def ledger(self):
        """
        Purpose:
        Creates a grid containing complete ledger.
        Takes calculatefrom,calculateto and accountcode.
        Returns success as status and the grid containing ledger.
        description:
        this function returns a grid containing ledger.
        The first row contains opening balance of the account.
        subsequent rows contain all the transactions for an account given it's account code.
        Further, it gives the closing balance at the end of all cr and dr transactions.
        in addition it also provides a flag to indicate if the balance is adverce.
        In addition to all this, there are 2 other columns containing running total Dr and Cr,
        this is used in Printing.
        If the closing balance is Dr then the amount will be shown at the cr side and other way round.
        Then finally grand total is displayed.
        This method is called when the report url is called with type=ledger request_param.
        The columns  in the grid include:
        *Date,Particular,voucher Number, Dr,Cr and balance at end of transaction.
        orderflag is checked in request params for sorting date in descending order.
        """

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                orgcode = authDetails["orgcode"]
                accountCode = self.request.params["accountcode"]
                calculateFrom = self.request.params["calculatefrom"]
                calculateTo = self.request.params["calculateto"]
                projectCode = self.request.params["projectcode"]
                financialStart = self.request.params["financialstart"]
                calbalDict = calculateBalance(
                    self.con, accountCode, financialStart, calculateFrom, calculateTo
                )
                vouchergrid = []
                bal = 0.00
                adverseflag = 0
                accnamerow = self.con.execute(
                    select([accounts.c.accountname]).where(
                        accounts.c.accountcode == int(accountCode)
                    )
                )
                accname = accnamerow.fetchone()
                headerrow = {
                    "accountname": "".join(accname),
                    "projectname": "",
                    "calculateto": datetime.strftime(
                        datetime.strptime(str(calculateTo), "%Y-%m-%d").date(),
                        "%d-%m-%Y",
                    ),
                    "calculatefrom": datetime.strftime(
                        datetime.strptime(str(calculateFrom), "%Y-%m-%d").date(),
                        "%d-%m-%Y",
                    ),
                }
                if projectCode != "":
                    prjnamerow = self.con.execute(
                        select([projects.c.projectname]).where(
                            projects.c.projectcode == int(projectCode)
                        )
                    )
                    prjname = prjnamerow.fetchone()
                    headerrow["projectname"] = "".join(prjname)

                if projectCode == "" and calbalDict["balbrought"] > 0:
                    openingrow = {
                        "vouchercode": "",
                        "vouchernumber": "",
                        "voucherdate": datetime.strftime(
                            datetime.strptime(str(calculateFrom), "%Y-%m-%d").date(),
                            "%d-%m-%Y",
                        ),
                        "balance": "",
                        "narration": "",
                        "status": "",
                        "vouchertype": "",
                        "advflag": "",
                    }
                    vfrom = datetime.strptime(str(calculateFrom), "%Y-%m-%d")
                    fstart = datetime.strptime(str(financialStart), "%Y-%m-%d")
                    if vfrom == fstart:
                        openingrow["particulars"] = [{"accountname": "Opening Balance"}]
                    if vfrom > fstart:
                        openingrow["particulars"] = [{"accountname": "Balance B/F"}]
                    if calbalDict["openbaltype"] == "Dr":
                        openingrow["Dr"] = "%.2f" % float(calbalDict["balbrought"])
                        openingrow["Cr"] = ""
                        bal = float(calbalDict["balbrought"])
                    if calbalDict["openbaltype"] == "Cr":
                        openingrow["Dr"] = ""
                        openingrow["Cr"] = "%.2f" % float(calbalDict["balbrought"])
                        bal = float(-calbalDict["balbrought"])
                    vouchergrid.append(openingrow)
                transactionsRecords = ""
                if projectCode == "":
                    if "orderflag" in self.request.params:
                        transactionsRecords = self.con.execute(
                            "select * from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s' or crs ? '%s') order by voucherdate DESC,vouchercode ;"
                            % (calculateFrom, calculateTo, accountCode, accountCode)
                        )
                    else:
                        transactionsRecords = self.con.execute(
                            "select * from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s' or crs ? '%s') order by voucherdate,vouchercode ;"
                            % (calculateFrom, calculateTo, accountCode, accountCode)
                        )
                else:
                    if "orderflag" in self.request.params:
                        transactionsRecords = self.con.execute(
                            "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode,invid,drcrid  from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and projectcode=%d and (drs ? '%s' or crs ? '%s') order by voucherdate DESC, vouchercode;"
                            % (
                                calculateFrom,
                                calculateTo,
                                int(projectCode),
                                accountCode,
                                accountCode,
                            )
                        )
                    else:
                        transactionsRecords = self.con.execute(
                            "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode,invid,drcrid  from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and projectcode=%d and (drs ? '%s' or crs ? '%s') order by voucherdate, vouchercode;"
                            % (
                                calculateFrom,
                                calculateTo,
                                int(projectCode),
                                accountCode,
                                accountCode,
                            )
                        )

                transactions = transactionsRecords.fetchall()

                crtotal = 0.00
                drtotal = 0.00
                for transaction in transactions:
                    ledgerRecord = {
                        "vouchercode": transaction["vouchercode"],
                        "vouchernumber": transaction["vouchernumber"],
                        "voucherdate": str(
                            transaction["voucherdate"].date().strftime("%d-%m-%Y")
                        ),
                        "narration": transaction["narration"],
                        "status": transaction["lockflag"],
                        "vouchertype": transaction["vouchertype"],
                        "advflag": "",
                    }
                    if accountCode in transaction["drs"]:
                        ledgerRecord["Dr"] = "%.2f" % float(
                            transaction["drs"][accountCode]
                        )
                        ledgerRecord["Cr"] = ""
                        drtotal += float(transaction["drs"][accountCode])
                        par = []
                        for cr in list(transaction["crs"].keys()):
                            accountnameRow = self.con.execute(
                                select([accounts.c.accountname]).where(
                                    accounts.c.accountcode == int(cr)
                                )
                            )
                            accountname = accountnameRow.fetchone()
                            if len(transaction["crs"]) > 1:
                                par.append(
                                    {
                                        "accountname": accountname["accountname"],
                                        "amount": transaction["crs"][cr],
                                    }
                                )
                            else:
                                par.append({"accountname": accountname["accountname"]})
                        ledgerRecord["particulars"] = par
                        bal = bal + float(transaction["drs"][accountCode])

                    if accountCode in transaction["crs"]:
                        ledgerRecord["Cr"] = "%.2f" % float(
                            transaction["crs"][accountCode]
                        )
                        ledgerRecord["Dr"] = ""
                        crtotal += float(transaction["crs"][accountCode])
                        par = []
                        for dr in list(transaction["drs"].keys()):
                            accountnameRow = self.con.execute(
                                select([accounts.c.accountname]).where(
                                    accounts.c.accountcode == int(dr)
                                )
                            )
                            accountname = accountnameRow.fetchone()
                            if len(transaction["drs"]) > 1:
                                par.append(
                                    {
                                        "accountname": accountname["accountname"],
                                        "amount": transaction["drs"][dr],
                                    }
                                )
                            else:
                                par.append({"accountname": accountname["accountname"]})
                        ledgerRecord["particulars"] = par
                        bal = bal - float(transaction["crs"][accountCode])
                    if bal > 0:
                        ledgerRecord["balance"] = "%.2f(Dr)" % (bal)
                    elif bal < 0:
                        ledgerRecord["balance"] = "%.2f(Cr)" % (abs(bal))
                    else:
                        ledgerRecord["balance"] = "%.2f" % (0.00)
                    ledgerRecord["ttlRunDr"] = "%.2f" % (drtotal)
                    ledgerRecord["ttlRunCr"] = "%.2f" % (crtotal)
                    # get related document details
                    dcinfo = billwiseEntryLedger(
                        self.con,
                        orgcode,
                        transaction["vouchercode"],
                        transaction["invid"],
                        transaction["drcrid"],
                    )
                    if dcinfo != "":
                        ledgerRecord["dcinfo"] = dcinfo
                    vouchergrid.append(ledgerRecord)

                if projectCode == "":
                    if calbalDict["openbaltype"] == "Cr":
                        calbalDict["totalcrbal"] -= calbalDict["balbrought"]
                    if calbalDict["openbaltype"] == "Dr":
                        calbalDict["totaldrbal"] -= calbalDict["balbrought"]
                    ledgerRecord = {
                        "vouchercode": "",
                        "vouchernumber": "",
                        "voucherdate": "",
                        "narration": "",
                        "Dr": "%.2f" % (calbalDict["totaldrbal"]),
                        "Cr": "%.2f" % (calbalDict["totalcrbal"]),
                        "particulars": [{"accountname": "Total of Transactions"}],
                        "balance": "",
                        "status": "",
                        "vouchertype": "",
                        "advflag": "",
                    }
                    vouchergrid.append(ledgerRecord)

                    if calbalDict["curbal"] != 0:
                        ledgerRecord = {
                            "vouchercode": "",
                            "vouchernumber": "",
                            "voucherdate": datetime.strftime(
                                datetime.strptime(str(calculateTo), "%Y-%m-%d").date(),
                                "%d-%m-%Y",
                            ),
                            "narration": "",
                            "particulars": [{"accountname": "Closing Balance C/F"}],
                            "balance": "",
                            "status": "",
                            "vouchertype": "",
                        }
                        if calbalDict["baltype"] == "Cr":
                            if (
                                calbalDict["grpname"] == "Current Assets"
                                or calbalDict["grpname"] == "Fixed Assets"
                                or calbalDict["grpname"] == "Investments"
                                or calbalDict["grpname"] == "Loans(Asset)"
                                or calbalDict["grpname"]
                                == "Miscellaneous Expenses(Asset)"
                            ) and calbalDict["curbal"] != 0:
                                adverseflag = 1
                            ledgerRecord["Dr"] = "%.2f" % (calbalDict["curbal"])
                            ledgerRecord["Cr"] = ""

                        if calbalDict["baltype"] == "Dr":
                            if (
                                calbalDict["grpname"] == "Corpus"
                                or calbalDict["grpname"] == "Capital"
                                or calbalDict["grpname"] == "Current Liabilities"
                                or calbalDict["grpname"] == "Loans(Liability)"
                                or calbalDict["grpname"] == "Reserves"
                            ) and calbalDict["curbal"] != 0:
                                adverseflag = 1
                            ledgerRecord["Cr"] = "%.2f" % (calbalDict["curbal"])
                            ledgerRecord["Dr"] = ""
                        ledgerRecord["advflag"] = adverseflag
                        vouchergrid.append(ledgerRecord)

                    if (
                        (calbalDict["curbal"] == 0 and calbalDict["balbrought"] != 0)
                        or calbalDict["curbal"] != 0
                        or calbalDict["balbrought"] != 0
                    ):
                        ledgerRecord = {
                            "vouchercode": "",
                            "vouchernumber": "",
                            "voucherdate": "",
                            "narration": "",
                            "particulars": [{"accountname": "Grand Total"}],
                            "balance": "",
                            "status": "",
                            "vouchertype": "",
                            "advflag": "",
                        }
                        if projectCode == "" and calbalDict["balbrought"] > 0:
                            if calbalDict["openbaltype"] == "Dr":
                                calbalDict["totaldrbal"] += float(
                                    calbalDict["balbrought"]
                                )

                            if calbalDict["openbaltype"] == "Cr":
                                calbalDict["totalcrbal"] += float(
                                    calbalDict["balbrought"]
                                )
                            if calbalDict["baltype"] == "Cr":
                                calbalDict["totaldrbal"] += float(calbalDict["curbal"])

                            if calbalDict["baltype"] == "Dr":
                                calbalDict["totalcrbal"] += float(calbalDict["curbal"])
                            ledgerRecord["Dr"] = "%.2f" % (calbalDict["totaldrbal"])
                            ledgerRecord["Cr"] = "%.2f" % (calbalDict["totaldrbal"])
                            vouchergrid.append(ledgerRecord)
                        else:
                            if calbalDict["totaldrbal"] > calbalDict["totalcrbal"]:
                                ledgerRecord["Dr"] = "%.2f" % (calbalDict["totaldrbal"])
                                ledgerRecord["Cr"] = "%.2f" % (calbalDict["totaldrbal"])

                            if calbalDict["totaldrbal"] < calbalDict["totalcrbal"]:
                                ledgerRecord["Dr"] = "%.2f" % (calbalDict["totalcrbal"])
                                ledgerRecord["Cr"] = "%.2f" % (calbalDict["totalcrbal"])
                            vouchergrid.append(ledgerRecord)
                else:
                    ledgerRecord = {
                        "vouchercode": "",
                        "vouchernumber": "",
                        "voucherdate": "",
                        "narration": "",
                        "Dr": "%.2f" % (drtotal),
                        "Cr": "%.2f" % (crtotal),
                        "particulars": [{"accountname": "Total of Transactions"}],
                        "balance": "",
                        "status": "",
                        "vouchertype": "",
                        "advflag": "",
                    }

                    vouchergrid.append(ledgerRecord)
                self.con.close()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": vouchergrid,
                    "userrole": urole["userrole"],
                    "ledgerheader": headerrow,
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="ledger-crdr", renderer="json")
    def crdrledger(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                ur = getUserRole(authDetails["userid"], authDetails["orgcode"])
                urole = ur["gkresult"]
                orgcode = authDetails["orgcode"]
                accountCode = self.request.params["accountcode"]
                side = self.request.params["side"]
                calculateFrom = self.request.params["calculatefrom"]
                calculateTo = self.request.params["calculateto"]
                projectCode = self.request.params["projectcode"]
                financialStart = self.request.params["financialstart"]
                vouchergrid = []
                bal = 0.00
                accnamerow = self.con.execute(
                    select([accounts.c.accountname]).where(
                        accounts.c.accountcode == int(accountCode)
                    )
                )
                accname = accnamerow.fetchone()
                headerrow = {
                    "accountname": accname["accountname"],
                    "projectname": "",
                    "calculateto": datetime.strftime(
                        datetime.strptime(str(calculateTo), "%Y-%m-%d").date(),
                        "%d-%m-%Y",
                    ),
                    "calculatefrom": datetime.strftime(
                        datetime.strptime(str(calculateFrom), "%Y-%m-%d").date(),
                        "%d-%m-%Y",
                    ),
                }
                if projectCode != "":
                    prjnamerow = self.con.execute(
                        select([projects.c.projectname]).where(
                            projects.c.projectcode == int(projectCode)
                        )
                    )
                    prjname = prjnamerow.fetchone()
                    headerrow["projectname"] = prjname["projectname"]
                if side == "dr":
                    if projectCode == "":
                        if "orderflag" in self.request.params:
                            transactionsRecords = self.con.execute(
                                "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode,invid,drcrid from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') order by voucherdate DESC;"
                                % (calculateFrom, calculateTo, accountCode)
                            )
                        else:
                            transactionsRecords = self.con.execute(
                                "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode,invid,drcrid from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (drs ? '%s') order by voucherdate;"
                                % (calculateFrom, calculateTo, accountCode)
                            )
                    else:
                        if "orderflag" in self.request.params:
                            transactionsRecords = self.con.execute(
                                "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode,invid,drcrid from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and projectcode=%d and (drs ? '%s') order by voucherdate DESC;"
                                % (
                                    calculateFrom,
                                    calculateTo,
                                    int(projectCode),
                                    accountCode,
                                )
                            )
                        else:
                            transactionsRecords = self.con.execute(
                                "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,orgcode,invid,drcrid from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and projectcode=%d and (drs ? '%s') order by voucherdate;"
                                % (
                                    calculateFrom,
                                    calculateTo,
                                    int(projectCode),
                                    accountCode,
                                )
                            )

                    transactions = transactionsRecords.fetchall()
                    for transaction in transactions:
                        ledgerRecord = {
                            "vouchercode": transaction["vouchercode"],
                            "vouchernumber": transaction["vouchernumber"],
                            "voucherdate": str(
                                transaction["voucherdate"].date().strftime("%d-%m-%Y")
                            ),
                            "narration": transaction["narration"],
                            "status": transaction["lockflag"],
                            "vouchertype": transaction["vouchertype"],
                        }
                        ledgerRecord["Dr"] = "%.2f" % float(
                            transaction["drs"][accountCode]
                        )
                        ledgerRecord["Cr"] = ""
                        par = []
                        for cr in list(transaction["crs"].keys()):
                            accountnameRow = self.con.execute(
                                select([accounts.c.accountname]).where(
                                    accounts.c.accountcode == int(cr)
                                )
                            )
                            accountname = accountnameRow.fetchone()
                            if len(transaction["crs"]) > 1:
                                par.append(
                                    {
                                        "accountname": accountname["accountname"],
                                        "amount": transaction["crs"][cr],
                                    }
                                )
                            else:
                                par.append({"accountname": accountname["accountname"]})
                        ledgerRecord["particulars"] = par
                        # get deatils of related documents
                        dcinfo = billwiseEntryLedger(
                            self.con,
                            orgcode,
                            transaction["vouchercode"],
                            transaction["invid"],
                            transaction["drcrid"],
                        )
                        if dcinfo != "":
                            ledgerRecord["dcinfo"] = dcinfo

                        vouchergrid.append(ledgerRecord)
                    self.con.close()
                    return {
                        "gkstatus": enumdict["Success"],
                        "gkresult": vouchergrid,
                        "userrole": urole["userrole"],
                        "ledgerheader": headerrow,
                    }

                if side == "cr":
                    if projectCode == "":
                        if "orderflag" in self.request.params:
                            transactionsRecords = self.con.execute(
                                "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,invid,drcrid,,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') order by voucherdate DESC;"
                                % (calculateFrom, calculateTo, accountCode)
                            )
                        else:
                            transactionsRecords = self.con.execute(
                                "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,invid,drcrid,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and (crs ? '%s') order by voucherdate;"
                                % (calculateFrom, calculateTo, accountCode)
                            )
                    else:
                        if "orderflag" in self.request.params:
                            transactionsRecords = self.con.execute(
                                "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,projectcode,invid,drcrid,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and projectcode=%d and (crs ? '%s') order by voucherdate DESC;"
                                % (
                                    calculateFrom,
                                    calculateTo,
                                    int(projectCode),
                                    accountCode,
                                )
                            )
                        else:
                            transactionsRecords = self.con.execute(
                                "select vouchercode,vouchernumber,voucherdate,narration,drs,crs,prjcrs,prjdrs,vouchertype,lockflag,delflag,invid,drcrid,projectcode,orgcode from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and projectcode=%d and (crs ? '%s') order by voucherdate;"
                                % (
                                    calculateFrom,
                                    calculateTo,
                                    int(projectCode),
                                    accountCode,
                                )
                            )
                    transactions = transactionsRecords.fetchall()
                    for transaction in transactions:
                        ledgerRecord = {
                            "vouchercode": transaction["vouchercode"],
                            "vouchernumber": transaction["vouchernumber"],
                            "voucherdate": str(
                                transaction["voucherdate"].date().strftime("%d-%m-%Y")
                            ),
                            "narration": transaction["narration"],
                            "status": transaction["lockflag"],
                            "vouchertype": transaction["vouchertype"],
                        }
                        ledgerRecord["Cr"] = "%.2f" % float(
                            transaction["crs"][accountCode]
                        )
                        ledgerRecord["Dr"] = ""
                        par = []
                        for dr in list(transaction["drs"].keys()):
                            accountnameRow = self.con.execute(
                                select([accounts.c.accountname]).where(
                                    accounts.c.accountcode == int(dr)
                                )
                            )
                            accountname = accountnameRow.fetchone()
                            if len(transaction["drs"]) > 1:
                                par.append(
                                    {
                                        "accountname": accountname["accountname"],
                                        "amount": transaction["drs"][dr],
                                    }
                                )
                            else:
                                par.append({"accountname": accountname["accountname"]})
                        ledgerRecord["particulars"] = par
                        # get documents details
                        dcinfo = billwiseEntryLedger(
                            self.con,
                            orgcode,
                            transaction["vouchercode"],
                            transaction["invid"],
                            transaction["drcrid"],
                        )
                        if dcinfo != "":
                            ledgerRecord["dcinfo"] = dcinfo

                        vouchergrid.append(ledgerRecord)
                    self.con.close()
                    return {
                        "gkstatus": enumdict["Success"],
                        "gkresult": vouchergrid,
                        "userrole": urole["userrole"],
                        "ledgerheader": headerrow,
                    }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="net-trial-balance", renderer="json")
    def netTrialBalance(self):
        """
        Purpose:
        Returns a grid containing net trial balance for all accounts started from financial start till the end date provided by the user.
        Description:
        This method has type=nettrialbalance as request_param in view_config.
        the method takes financial start and calculateto as parameters.
        Then it calls calculateBalance in a loop after retriving list of accountcode and account names.
        For every iteration financialstart is passed twice to calculateBalance because in trial balance start date is always the financial start.
        Then all dR balances and all Cr balances are added to get total balance for each side.
        Finally if balances are different then that difference is calculated and shown on the lower side followed by a row containing grand total.
        In addition to this data we have 2 other columns,
        Total Running total for Dr and Cr useful for printing.
        Same applies to the following methods in this class for gross and extended trial balances.
        All rows in the ntbGrid are dictionaries.
        """

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                accountData = self.con.execute(
                    select([accounts.c.accountcode, accounts.c.accountname])
                    .where(accounts.c.orgcode == authDetails["orgcode"])
                    .order_by(accounts.c.accountname)
                )
                accountRecords = accountData.fetchall()
                ntbGrid = []
                financialStart = self.request.params["financialstart"]
                calculateTo = self.request.params["calculateto"]
                srno = 0
                totalDr = 0.00
                totalCr = 0.00
                for account in accountRecords:
                    adverseflag = 0
                    calbalData = calculateBalance(
                        self.con,
                        account["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if calbalData["baltype"] == "":
                        continue
                    srno += 1
                    ntbRow = {
                        "accountcode": account["accountcode"],
                        "accountname": account["accountname"],
                        "groupname": calbalData["grpname"],
                        "srno": srno,
                    }
                    if calbalData["baltype"] == "Dr":
                        if (
                            calbalData["grpname"] == "Corpus"
                            or calbalData["grpname"] == "Capital"
                            or calbalData["grpname"] == "Current Liabilities"
                            or calbalData["grpname"] == "Loans(Liability)"
                            or calbalData["grpname"] == "Reserves"
                        ) and calbalData["curbal"] != 0:
                            adverseflag = 1
                        ntbRow["Dr"] = "%.2f" % (calbalData["curbal"])
                        ntbRow["Cr"] = ""
                        ntbRow["advflag"] = adverseflag
                        totalDr = totalDr + calbalData["curbal"]
                    if calbalData["baltype"] == "Cr":
                        if (
                            calbalData["grpname"] == "Current Assets"
                            or calbalData["grpname"] == "Fixed Assets"
                            or calbalData["grpname"] == "Investments"
                            or calbalData["grpname"] == "Loans(Asset)"
                            or calbalData["grpname"] == "Miscellaneous Expenses(Asset)"
                        ) and calbalData["curbal"] != 0:
                            adverseflag = 1
                        ntbRow["Dr"] = ""
                        ntbRow["Cr"] = "%.2f" % (calbalData["curbal"])
                        ntbRow["advflag"] = adverseflag
                        totalCr = totalCr + calbalData["curbal"]
                    ntbRow["ttlRunDr"] = "%.2f" % (totalDr)
                    ntbRow["ttlRunCr"] = "%.2f" % (totalCr)
                    ntbGrid.append(ntbRow)
                ntbGrid.append(
                    {
                        "accountcode": "",
                        "accountname": "Total",
                        "groupname": "",
                        "srno": "",
                        "Dr": "%.2f" % (totalDr),
                        "Cr": "%.2f" % (totalCr),
                        "advflag": "",
                    }
                )
                if totalDr > totalCr:
                    baldiff = totalDr - totalCr
                    ntbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "Difference in Trial balance",
                            "groupname": "",
                            "srno": "",
                            "Cr": "%.2f" % (baldiff),
                            "Dr": "",
                            "advflag": "",
                        }
                    )
                    ntbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "",
                            "groupname": "",
                            "srno": "",
                            "Cr": "%.2f" % (totalDr),
                            "Dr": "%.2f" % (totalDr),
                            "advflag": "",
                        }
                    )
                if totalDr < totalCr:
                    baldiff = totalCr - totalDr
                    ntbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "Difference in Trial balance",
                            "groupname": "",
                            "srno": "",
                            "Dr": "%.2f" % (baldiff),
                            "Cr": "",
                            "advflag": "",
                        }
                    )
                    ntbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "",
                            "groupname": "",
                            "srno": "",
                            "Cr": "%.2f" % (totalCr),
                            "Dr": "%.2f" % (totalCr),
                            "advflag": "",
                        }
                    )
                self.con.close()

                return {"gkstatus": enumdict["Success"], "gkresult": ntbGrid}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="gross-trial-balance", renderer="json")
    def grossTrialBalance(self):
        """
        Purpose:
        Returns a grid containing gross trial balance for all accounts started from financial start till the end date provided by the user.
        Description:
        This method has type=nettrialbalance as request_param in view_config.
        the method takes financial start and calculateto as parameters.
        Then it calls calculateBalance in a loop after retriving list of accountcode and account names.
        For every iteration financialstart is passed twice to calculateBalance because in trial balance start date is always the financial start.
        Then all dR balances and all Cr balances are added to get total balance for each side.
        Finally if balances are different then that difference is calculated and shown on the lower side followed by a row containing grand total.
        All rows in the ntbGrid are dictionaries.
        """

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                accountData = self.con.execute(
                    select([accounts.c.accountcode, accounts.c.accountname])
                    .where(accounts.c.orgcode == authDetails["orgcode"])
                    .order_by(accounts.c.accountname)
                )
                accountRecords = accountData.fetchall()
                gtbGrid = []
                financialStart = self.request.params["financialstart"]
                calculateTo = self.request.params["calculateto"]
                srno = 0
                totalDr = 0.00
                totalCr = 0.00
                for account in accountRecords:
                    adverseflag = 0
                    calbalData = calculateBalance(
                        self.con,
                        account["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if (
                        float(calbalData["totaldrbal"]) == 0
                        and float(calbalData["totalcrbal"]) == 0
                    ):
                        continue
                    srno += 1
                    if (
                        (calbalData["baltype"] == "Dr")
                        and (
                            calbalData["grpname"] == "Corpus"
                            or calbalData["grpname"] == "Capital"
                            or calbalData["grpname"] == "Current Liabilities"
                            or calbalData["grpname"] == "Loans(Liability)"
                            or calbalData["grpname"] == "Reserves"
                        )
                        and calbalData["curbal"] != 0
                    ):
                        adverseflag = 1
                    if (
                        (calbalData["baltype"] == "Cr")
                        and (
                            calbalData["grpname"] == "Current Assets"
                            or calbalData["grpname"] == "Fixed Assets"
                            or calbalData["grpname"] == "Investments"
                            or calbalData["grpname"] == "Loans(Asset)"
                            or calbalData["grpname"] == "Miscellaneous Expenses(Asset)"
                        )
                        and calbalData["curbal"] != 0
                    ):
                        adverseflag = 1
                    gtbRow = {
                        "accountcode": account["accountcode"],
                        "accountname": account["accountname"],
                        "groupname": calbalData["grpname"],
                        "Dr balance": "%.2f" % (calbalData["totaldrbal"]),
                        "Cr balance": "%.2f" % (calbalData["totalcrbal"]),
                        "srno": srno,
                        "advflag": adverseflag,
                    }
                    totalDr += calbalData["totaldrbal"]
                    totalCr += calbalData["totalcrbal"]
                    gtbRow["ttlRunDr"] = "%.2f" % (totalDr)
                    gtbRow["ttlRunCr"] = "%.2f" % (totalCr)
                    gtbGrid.append(gtbRow)
                gtbGrid.append(
                    {
                        "accountcode": "",
                        "accountname": "Total",
                        "groupname": "",
                        "Dr balance": "%.2f" % (totalDr),
                        "Cr balance": "%.2f" % (totalCr),
                        "srno": "",
                        "advflag": "",
                    }
                )
                if totalDr > totalCr:
                    baldiff = totalDr - totalCr
                    gtbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "Difference in Trial balance",
                            "groupname": "",
                            "srno": "",
                            "Cr balance": "%.2f" % (baldiff),
                            "Dr balance": "",
                            "advflag": "",
                        }
                    )
                    gtbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "",
                            "groupname": "",
                            "srno": "",
                            "Cr balance": "%.2f" % (totalDr),
                            "Dr balance": "%.2f" % (totalDr),
                            "advflag": "",
                        }
                    )
                if totalDr < totalCr:
                    baldiff = totalCr - totalDr
                    gtbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "Difference in Trial balance",
                            "groupname": "",
                            "srno": "",
                            "Dr balance": "%.2f" % (baldiff),
                            "Cr balance": "",
                            "advflag": "",
                        }
                    )
                    gtbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "",
                            "groupname": "",
                            "srno": "",
                            "Cr balance": "%.2f" % (totalCr),
                            "Dr balance": "%.2f" % (totalCr),
                            "advflag": "",
                        }
                    )
                self.con.close()

                return {"gkstatus": enumdict["Success"], "gkresult": gtbGrid}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="extended-trial-balance", renderer="json")
    def extendedTrialBalance(self):
        """
        Purpose:
        Returns a grid containing extended trial balance for all accounts started from financial start till the end date provided by the user.
        Description:
        This method has type=nettrialbalance as request_param in view_config.
        the method takes financial start and calculateto as parameters.
        Then it calls calculateBalance in a loop after retriving list of accountcode and account names.
        For every iteration financialstart is passed twice to calculateBalance because in trial balance start date is always the financial start.
        Then all dR balances and all Cr balances are added to get total balance for each side.
        After this all closing balances are added either on Dr or Cr side depending on the baltype.
        Finally if balances are different then that difference is calculated and shown on the lower side followed by a row containing grand total.
        All rows in the extbGrid are dictionaries.
        """

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                accountData = self.con.execute(
                    select([accounts.c.accountcode, accounts.c.accountname])
                    .where(accounts.c.orgcode == authDetails["orgcode"])
                    .order_by(accounts.c.accountname)
                )
                accountRecords = accountData.fetchall()
                extbGrid = []
                financialStart = self.request.params["financialstart"]
                calculateTo = self.request.params["calculateto"]
                srno = 0
                totalDr = 0.00
                totalCr = 0.00
                totalDrBal = 0.00
                totalCrBal = 0.00
                difftb = 0.00
                for account in accountRecords:
                    adverseflag = 0
                    calbalData = calculateBalance(
                        self.con,
                        account["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if (
                        float(calbalData["balbrought"]) == 0
                        and float(calbalData["totaldrbal"]) == 0
                        and float(calbalData["totalcrbal"]) == 0
                    ):
                        continue
                    srno += 1
                    if calbalData["openbaltype"] == "Cr":
                        calbalData["totalcrbal"] -= calbalData["balbrought"]
                    if calbalData["openbaltype"] == "Dr":
                        calbalData["totaldrbal"] -= calbalData["balbrought"]
                    extbrow = {
                        "accountcode": account["accountcode"],
                        "accountname": account["accountname"],
                        "groupname": calbalData["grpname"],
                        "totaldr": "%.2f" % (calbalData["totaldrbal"]),
                        "totalcr": "%.2f" % (calbalData["totalcrbal"]),
                        "srno": srno,
                    }
                    if calbalData["balbrought"] > 0:
                        extbrow["openingbalance"] = "%.2f(%s)" % (
                            calbalData["balbrought"],
                            calbalData["openbaltype"],
                        )
                    else:
                        extbrow["openingbalance"] = "0.00"
                    totalDr += calbalData["totaldrbal"]
                    totalCr += calbalData["totalcrbal"]
                    if calbalData["baltype"] == "Dr":
                        if (
                            calbalData["grpname"] == "Corpus"
                            or calbalData["grpname"] == "Capital"
                            or calbalData["grpname"] == "Current Liabilities"
                            or calbalData["grpname"] == "Loans(Liability)"
                            or calbalData["grpname"] == "Reserves"
                        ) and calbalData["curbal"] != 0:
                            adverseflag = 1
                        extbrow["curbaldr"] = "%.2f" % (calbalData["curbal"])
                        extbrow["curbalcr"] = ""
                        totalDrBal += calbalData["curbal"]
                    if calbalData["baltype"] == "Cr":
                        if (
                            calbalData["grpname"] == "Current Assets"
                            or calbalData["grpname"] == "Fixed Assets"
                            or calbalData["grpname"] == "Investments"
                            or calbalData["grpname"] == "Loans(Asset)"
                            or calbalData["grpname"] == "Miscellaneous Expenses(Asset)"
                        ) and calbalData["curbal"] != 0:
                            adverseflag = 1
                        extbrow["curbaldr"] = ""
                        extbrow["curbalcr"] = "%.2f" % (calbalData["curbal"])
                        totalCrBal += calbalData["curbal"]
                    if calbalData["baltype"] == "":
                        extbrow["curbaldr"] = ""
                        extbrow["curbalcr"] = ""
                    extbrow["ttlRunDr"] = "%.2f" % (totalDrBal)
                    extbrow["ttlRunCr"] = "%.2f" % (totalCrBal)
                    extbrow["advflag"] = adverseflag
                    extbGrid.append(extbrow)
                extbrow = {
                    "accountcode": "",
                    "accountname": "Total",
                    "groupname": "",
                    "openingbalance": "",
                    "totaldr": "%.2f" % (totalDr),
                    "totalcr": "%.2f" % (totalCr),
                    "curbaldr": "%.2f" % (totalDrBal),
                    "curbalcr": "%.2f" % (totalCrBal),
                    "srno": "",
                    "advflag": "",
                }
                extbGrid.append(extbrow)

                if totalDrBal > totalCrBal:
                    extbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "Difference in Trial Balance",
                            "groupname": "",
                            "openingbalance": "",
                            "totaldr": "",
                            "totalcr": "",
                            "srno": "",
                            "curbalcr": "%.2f" % (totalDrBal - totalCrBal),
                            "curbaldr": "",
                            "advflag": "",
                        }
                    )
                    extbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "",
                            "groupname": "",
                            "openingbalance": "",
                            "totaldr": "",
                            "totalcr": "",
                            "curbaldr": "%.2f" % (totalDrBal),
                            "curbalcr": "%.2f" % (totalDrBal),
                            "srno": "",
                            "advflag": "",
                        }
                    )
                if totalCrBal > totalDrBal:
                    extbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "Difference in Trial Balance",
                            "groupname": "",
                            "openingbalance": "",
                            "totaldr": "",
                            "totalcr": "",
                            "srno": "",
                            "curbaldr": "%.2f" % (totalCrBal - totalDrBal),
                            "curbalcr": "",
                            "advflag": "",
                        }
                    )
                    extbGrid.append(
                        {
                            "accountcode": "",
                            "accountname": "",
                            "groupname": "",
                            "openingbalance": "",
                            "totaldr": "",
                            "totalcr": "",
                            "curbaldr": "%.2f" % (totalCrBal),
                            "curbalcr": "%.2f" % (totalCrBal),
                            "srno": "",
                            "advflag": "",
                        }
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": extbGrid}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=cashflow", renderer="json")
    def cashflow(self):
        """
        Purpose:
        Returns a grid containing opening and closing balances of those accounts under the group of Cash or Bank
        and also the total receipt and total payment (Cr and Dr) for the time period of theses accounts
        Description:
        This method has type=cashflow as request_param in view_config.
        the method takes financial start, calculatefrom and calculateto as parameters.
        then it fetches all the accountcodes, their opening balances and accountnames from the database which are under the group of Cash or Bank
        then a loop is ran for all these accounts and in the loop, the calculateBalance function is caaled for all these accounts
        if the balbrought!=0 (balbrought returned from calculateBalance, this also becomes the opening balance for the period) then the dictionary containing accountdetails and balbrought amount is appended to the "receiptcf" list.
        the balbrought amount is added or subtracted from the "rctotal" depending upon its openbaltype
        if the curbal!=0 (curbal returned from calculateBalance, this also becomes the closing balance for the period) then a dictionary containing the accountdetails and curbal amount is appended to the "closinggrid" list
        the curbal amount is added or subtracted from the "pytotal" depending upon its baltype
        then, all the vouchers (Except contra and journal) are fetched from the database which contain these accountcodes in either their crs or drs
        then a loop is ran for the accountcodes of the above fetched voucher crs to find the total receipts in the particular account. the same is done with drs to find the total payment done from that account.
        then the dictionary containing the accountdetails along total receipts is appended in the "rctransactionsgrid" list and the dictionary containing accountdetails along with the total payments are appended in the "paymentcf" list
        totalrunningreceipt (ttlRunDr) and totalrunningpayments(ttlRunCr) are calculated and added in the list for printing purpose.
        then these lists are joined to receiptcf & closing grid accordingly and returned as rcgkresult & pygkresult
        """

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                calculateFrom = self.request.params["calculatefrom"]
                calculateTo = self.request.params["calculateto"]
                financialStart = self.request.params["financialstart"]
                cbAccountsData = self.con.execute(
                    "select accountcode, openingbal, accountname from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Bank','Cash')) order by accountname"
                    % (authDetails["orgcode"], authDetails["orgcode"])
                )
                cbAccounts = cbAccountsData.fetchall()
                receiptcf = []
                paymentcf = []
                rctransactionsgrid = []
                closinggrid = []
                rcaccountcodes = []
                pyaccountcodes = []
                bankcodes = []
                rctotal = 0.00
                pytotal = 0.00
                ttlRunDr = 0.00
                ttlRunCr = 0.00
                vfrom = datetime.strptime(str(calculateFrom), "%Y-%m-%d")
                fstart = datetime.strptime(str(financialStart), "%Y-%m-%d")
                if vfrom == fstart:
                    receiptcf.append(
                        {
                            "toby": "To",
                            "particulars": "Opening balance",
                            "amount": "",
                            "accountcode": "",
                            "ttlRunDr": "",
                        }
                    )
                if vfrom > fstart:
                    receiptcf.append(
                        {
                            "toby": "To",
                            "particulars": "Balance B/F",
                            "amount": "",
                            "accountcode": "",
                            "ttlRunDr": "",
                        }
                    )
                for cbAccount in cbAccounts:
                    bankcodes.append(str(cbAccount["accountcode"]))
                closinggrid.append(
                    {
                        "toby": "By",
                        "particulars": "Closing balance",
                        "amount": "",
                        "accountcode": "",
                        "ttlRunCr": "",
                    }
                )
                for cbAccount in cbAccounts:
                    opacc = calculateBalance(
                        self.con,
                        cbAccount["accountcode"],
                        financialStart,
                        calculateFrom,
                        calculateTo,
                    )
                    if opacc["balbrought"] != 0.00:
                        if opacc["openbaltype"] == "Dr":
                            receiptcf.append(
                                {
                                    "toby": "",
                                    "particulars": "".join(cbAccount["accountname"]),
                                    "amount": "%.2f" % float(opacc["balbrought"]),
                                    "accountcode": cbAccount["accountcode"],
                                    "ttlRunDr": "",
                                }
                            )
                            rctotal += float(opacc["balbrought"])
                        if opacc["openbaltype"] == "Cr":
                            receiptcf.append(
                                {
                                    "toby": "",
                                    "particulars": "".join(cbAccount["accountname"]),
                                    "amount": "-" + "%.2f" % float(opacc["balbrought"]),
                                    "accountcode": cbAccount["accountcode"],
                                    "ttlRunDr": "",
                                }
                            )
                            rctotal -= float(opacc["balbrought"])
                    if opacc["curbal"] != 0.00:
                        if opacc["baltype"] == "Dr":
                            closinggrid.append(
                                {
                                    "toby": "",
                                    "particulars": "".join(cbAccount["accountname"]),
                                    "amount": "%.2f" % float(opacc["curbal"]),
                                    "accountcode": cbAccount["accountcode"],
                                    "ttlRunCr": "",
                                }
                            )
                            pytotal += float(opacc["curbal"])
                        if opacc["baltype"] == "Cr":
                            closinggrid.append(
                                {
                                    "toby": "",
                                    "particulars": "".join(cbAccount["accountname"]),
                                    "amount": "-" + "%.2f" % float(opacc["curbal"]),
                                    "accountcode": cbAccount["accountcode"],
                                    "ttlRunCr": "",
                                }
                            )
                            pytotal -= float(opacc["curbal"])
                    transactionsRecords = self.con.execute(
                        "select crs,drs from vouchers where voucherdate >= '%s'  and voucherdate <= '%s' and vouchertype not in ('contra','journal') and (drs ? '%s' or crs ? '%s');"
                        % (
                            calculateFrom,
                            calculateTo,
                            cbAccount["accountcode"],
                            cbAccount["accountcode"],
                        )
                    )
                    transactions = transactionsRecords.fetchall()
                    for transaction in transactions:
                        for cr in transaction["crs"]:
                            if cr not in rcaccountcodes and int(cr) != int(
                                cbAccount["accountcode"]
                            ):
                                rcaccountcodes.append(cr)
                                crresult = self.con.execute(
                                    "select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and vouchertype not in ('contra','journal') and (drs ?| array%s);"
                                    % (
                                        int(cr),
                                        financialStart,
                                        calculateTo,
                                        str(bankcodes),
                                    )
                                )
                                crresultRow = crresult.fetchone()
                                rcaccountname = self.con.execute(
                                    "select accountname from accounts where accountcode=%d"
                                    % (int(cr))
                                )
                                rcacc = "".join(rcaccountname.fetchone())
                                if crresultRow["total"] != None:
                                    ttlRunDr += float(crresultRow["total"])
                                    rctransactionsgrid.append(
                                        {
                                            "toby": "To",
                                            "particulars": rcacc,
                                            "amount": "%.2f"
                                            % float(crresultRow["total"]),
                                            "accountcode": int(cr),
                                            "ttlRunDr": ttlRunDr,
                                        }
                                    )
                                    rctotal += float(crresultRow["total"])
                        for dr in transaction["drs"]:
                            if dr not in pyaccountcodes and int(dr) != int(
                                cbAccount["accountcode"]
                            ):
                                pyaccountcodes.append(dr)
                                drresult = self.con.execute(
                                    "select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and vouchertype not in ('contra','journal') and (crs ?| array%s)"
                                    % (
                                        int(dr),
                                        financialStart,
                                        calculateTo,
                                        str(bankcodes),
                                    )
                                )
                                drresultRow = drresult.fetchone()
                                pyaccountname = self.con.execute(
                                    "select accountname from accounts where accountcode=%d"
                                    % (int(dr))
                                )
                                pyacc = "".join(pyaccountname.fetchone())
                                if drresultRow["total"] != None:
                                    ttlRunCr += float(drresultRow["total"])
                                    paymentcf.append(
                                        {
                                            "toby": "By",
                                            "particulars": pyacc,
                                            "amount": "%.2f"
                                            % float(drresultRow["total"]),
                                            "accountcode": int(dr),
                                            "ttlRunCr": ttlRunCr,
                                        }
                                    )
                                    pytotal += float(drresultRow["total"])

                receiptcf.extend(rctransactionsgrid)
                paymentcf.extend(closinggrid)
                if len(receiptcf) > len(paymentcf):
                    emptyno = len(receiptcf) - len(paymentcf)
                    for i in range(0, emptyno):
                        paymentcf.append(
                            {
                                "toby": "",
                                "particulars": "",
                                "amount": ".",
                                "accountcode": "",
                                "ttlRunCr": "",
                            }
                        )
                if len(receiptcf) < len(paymentcf):
                    emptyno = len(paymentcf) - len(receiptcf)
                    for i in range(0, emptyno):
                        receiptcf.append(
                            {
                                "toby": "",
                                "particulars": "",
                                "amount": ".",
                                "accountcode": "",
                                "ttlRunDr": "",
                            }
                        )
                receiptcf.append(
                    {
                        "toby": "",
                        "particulars": "Total",
                        "amount": "%.2f" % float(rctotal),
                        "accountcode": "",
                        "ttlRunDr": "",
                    }
                )
                paymentcf.append(
                    {
                        "toby": "",
                        "particulars": "Total",
                        "amount": "%.2f" % float(pytotal),
                        "accountcode": "",
                        "ttlRunCr": "",
                    }
                )
                self.con.close()

                return {
                    "gkstatus": enumdict["Success"],
                    "rcgkresult": receiptcf,
                    "pygkresult": paymentcf,
                }
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=projectstatement", renderer="json")
    def projectStatement(self):
        """
        Purpose:
        Returns a grid containing extended trial balance for all accounts started from financial start till the end date provided by the user.
        Description:
        This method has type=nettrialbalance as request_param in view_config.
        the method takes financial start and calculateto as parameters.
        Then it calls calculateBalance in a loop after retriving list of accountcode and account names.
        For every iteration financialstart is passed twice to calculateBalance because in trial balance start date is always the financial start.
        Then all dR balances and all Cr balances are added to get total balance for each side.
        After this all closing balances are added either on Dr or Cr side depending on the baltype.
        Finally if balances are different then that difference is calculated and shown on the lower side followed by a row containing grand total.
        In addition there will be running Cr and Dr totals for printing purpose.
        All rows in the extbGrid are dictionaries.
        """

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                calculateTo = self.request.params["calculateto"]
                financialStart = self.request.params["financialstart"]
                projectCode = self.request.params["projectcode"]
                totalDr = 0.00
                totalCr = 0.00
                grpaccsdata = self.con.execute(
                    "select accountcode , accountname, groupcode from accounts where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and groupcode in (select groupcode from groupsubgroups where orgcode = %d and (groupname in ('Direct Expense','Direct Income','Indirect Expense','Indirect Income') or groupname in (select groupname from groupsubgroups where subgroupof in (select groupcode from groupsubgroups where groupname in ('Direct Expense','Direct Income','Indirect Expense','Indirect Income')and orgcode = %d))))) order by accountname"
                    % (
                        authDetails["orgcode"],
                        authDetails["orgcode"],
                        authDetails["orgcode"],
                        authDetails["orgcode"],
                    )
                )
                grpaccs = grpaccsdata.fetchall()

                srno = 1
                projectStatement = []
                for accountRow in grpaccs:
                    statementRow = {}
                    g = gkdb.groupsubgroups.alias("g")
                    sg = gkdb.groupsubgroups.alias("sg")

                    group = self.con.execute(
                        select(
                            [
                                (g.c.groupcode).label("groupcode"),
                                (g.c.groupname).label("groupname"),
                                (sg.c.groupcode).label("subgroupcode"),
                                (sg.c.groupname).label("subgroupname"),
                            ]
                        ).where(
                            or_(
                                and_(
                                    g.c.groupcode == int(accountRow["groupcode"]),
                                    g.c.subgroupof == null(),
                                    sg.c.groupcode == int(accountRow["groupcode"]),
                                    sg.c.subgroupof == null(),
                                ),
                                and_(
                                    g.c.groupcode == sg.c.subgroupof,
                                    sg.c.groupcode == int(accountRow["groupcode"]),
                                ),
                            )
                        )
                    )
                    groupRow = group.fetchone()

                    drresult = self.con.execute(
                        "select sum(cast(drs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and projectcode=%d"
                        % (
                            int(accountRow["accountcode"]),
                            financialStart,
                            calculateTo,
                            int(projectCode),
                        )
                    )
                    drresultRow = drresult.fetchone()
                    crresult = self.con.execute(
                        "select sum(cast(crs->>'%d' as float)) as total from vouchers where delflag = false and voucherdate >='%s' and voucherdate <= '%s' and projectcode=%d"
                        % (
                            int(accountRow["accountcode"]),
                            financialStart,
                            calculateTo,
                            int(projectCode),
                        )
                    )
                    crresultRow = crresult.fetchone()
                    if groupRow["groupname"] == groupRow["subgroupname"]:
                        statementRow = {
                            "srno": srno,
                            "accountcode": accountRow["accountcode"],
                            "accountname": accountRow["accountname"],
                            "groupname": groupRow["groupname"],
                            "subgroupname": "",
                            "totalout": "%.2f" % float(totalDr),
                            "totalin": "%.2f" % float(totalCr),
                        }
                    else:
                        statementRow = {
                            "srno": srno,
                            "accountcode": accountRow["accountcode"],
                            "accountname": accountRow["accountname"],
                            "groupname": groupRow["groupname"],
                            "subgroupname": groupRow["subgroupname"],
                            "totalout": "%.2f" % float(totalDr),
                            "totalin": "%.2f" % float(totalCr),
                        }
                    if drresultRow["total"] == None:
                        statementRow["totalout"] = "%.2f" % float(0.00)
                    else:
                        statementRow["totalout"] = "%.2f" % float(drresultRow["total"])
                        totalDr = totalDr + drresultRow["total"]
                    if crresultRow["total"] == None:
                        statementRow["totalin"] = "%.2f" % float(0.00)
                    else:
                        statementRow["totalin"] = "%.2f" % float(crresultRow["total"])
                        totalCr = totalCr + crresultRow["total"]
                    if (
                        float(statementRow["totalout"]) == 0
                        and float(statementRow["totalin"]) == 0
                    ):
                        continue
                    srno = srno + 1
                    statementRow["ttlRunDr"] = "%.2f" % (totalDr)
                    statementRow["ttlRunCr"] = "%.2f" % (totalCr)
                    projectStatement.append(statementRow)
                projectStatement.append(
                    {
                        "srno": "",
                        "accountcode": "",
                        "accountname": "",
                        "groupname": "Total",
                        "subgroupname": "",
                        "totalout": "%.2f" % float(totalDr),
                        "totalin": "%.2f" % float(totalCr),
                    }
                )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": projectStatement}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="balance-sheet", renderer="json")
    def balanceSheet(self):
        """
        Purpose:
        Gets the list of groups and their respective balances
        takes organisation code and end date as input parameter
        Description:
        This function is used to generate balance sheet for a given organisation and the given time period.
        This function takes orgcode and end date as the input parameters
        This function is called when the type=balancesheet is passed to the /report url.
        orgcode is extracted from the header
        end date is extracted from the request_params
        The accountcode is extracted from the database under  groupcode for groups relevent to balance sheet
        the  groupbalance will be initialized to 0.0 for each group.
        this accountcode is sent to the calculateBalance function along with financialstart, calculateTo
        the function will return the closing balance related to each account which will be later added or subtracted according to the accounting rules from the group balance
        Then the subgroups and their respective accounts will be fetched from the database and the detail will be sent to the calculatBalance function which will return the curbal.
        the amount will be added or subtracted from the subgroup balance accordingly.
        the above steps will be executed in loop to calculate balances of all subgroups.
        these balances will be added/subtracted from the group balance accordingly.
        the above statements will be running in a loop for each group.
        Later all the group balances for sources and application will be added
        the difference in the amounts of sourcetotal and applicationtotal will be found
        the function will return the gkstatus and gkresult which contains a list of dictionaries where every dictionary represents a row with two key-value pairs each representing columns

        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        try:
            self.con = eng.connect()
            balanceSheet = getBalanceSheet(
                self.con,
                authDetails["orgcode"],
                self.request.params["calculateto"],
                self.request.params["calculatefrom"],
                int(self.request.params["baltype"]),
            )
            self.con.close()
            return {
                "gkstatus": enumdict["Success"],
                "gkresult": balanceSheet,
            }

        except:
            self.con.close()
            return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=conventionalbalancesheet", renderer="json")
    def conventionalbalanceSheet(self):
        """
        Purpose:
        Gets the list of groups and their respective balances
        takes organisation code and end date as input parameter
        Description:
        This function is used to generate balance sheet for a given organisation and the given time period.
        This function takes orgcode and end date as the input parameters
        This function is called when the type=conventionalbalancesheet is passed to the /report url.
        orgcode is extracted from the header
        end date is extracted from the request_params
        The accountcode is extracted from the database under  groupcode for groups relevent to balance sheet (meaning all groups except income and expence groups).
        the  groupbalance will be initialized to 0.0 for each group.
        this accountcode is sent to the calculateBalance function along with financialstart, calculateTo
        the function will return the closing balance related to each account which will be later added or subtracted according to the accounting rules from the group balance
        the above statements will be running in a loop for each group.
        Later all the group balances for sources and application will be added
        the difference in the amounts of sourcetotal and applicationtotal will be found
        the function will return the gkstatus and gkresult which contains a list of dictionaries where every dictionary represents a row with two key-value pairs each representing columns
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                orgcode = authDetails["orgcode"]
                financialstart = self.con.execute(
                    "select yearstart, orgtype from organisation where orgcode = %d"
                    % int(orgcode)
                )
                financialstartRow = financialstart.fetchone()
                financialStart = financialstartRow["yearstart"]
                orgtype = financialstartRow["orgtype"]
                calculateTo = self.request.params["calculateto"]
                calculateTo = calculateTo
                balanceSheet = []
                sourcegroupWiseTotal = 0.00
                applicationgroupWiseTotal = 0.00
                sourcesTotal = 0.00
                applicationsTotal = 0.00
                difference = 0.00
                balanceSheet.append(
                    {
                        "sourcesgroupname": "Sources:",
                        "sourceamount": "",
                        "appgroupname": "Applications:",
                        "applicationamount": "",
                    }
                )
                capital_Corpus = ""
                if orgtype == "Profit Making":
                    capital_Corpus = "Capital"
                if orgtype == "Not For Profit":
                    capital_Corpus = "Corpus"

                # Calculate grouptotal for group Capital/Corpus
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = '%s' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = '%s'));"
                    % (orgcode, orgcode, capital_Corpus, orgcode, capital_Corpus)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        sourcegroupWiseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Dr":
                        sourcegroupWiseTotal -= accountDetails["curbal"]
                sourcesTotal += sourcegroupWiseTotal

                # Calculate grouptotal for group "Fixed Assets"
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Fixed Assets' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Fixed Assets'));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        applicationgroupWiseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Cr":
                        applicationgroupWiseTotal -= accountDetails["curbal"]
                applicationsTotal += applicationgroupWiseTotal
                balanceSheet.append(
                    {
                        "sourcesgroupname": capital_Corpus,
                        "sourceamount": "%.2f" % (sourcegroupWiseTotal),
                        "appgroupname": "Fixed Assets",
                        "applicationamount": "%.2f" % (applicationgroupWiseTotal),
                    }
                )

                # Calculate grouptotal for group Loans(Liability)
                sourcegroupWiseTotal = 0.00
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Liability)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Loans(Liability)'));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        sourcegroupWiseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Dr":
                        sourcegroupWiseTotal -= accountDetails["curbal"]
                sourcesTotal += sourcegroupWiseTotal

                # Calculate grouptotal for group "Investments"
                applicationgroupWiseTotal = 0.00
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Investments' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Investments'));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        applicationgroupWiseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Cr":
                        applicationgroupWiseTotal -= accountDetails["curbal"]
                applicationsTotal += applicationgroupWiseTotal
                balanceSheet.append(
                    {
                        "sourcesgroupname": "Loans(Liability)",
                        "sourceamount": "%.2f" % (sourcegroupWiseTotal),
                        "appgroupname": "Investments",
                        "applicationamount": "%.2f" % (applicationgroupWiseTotal),
                    }
                )

                # Calculate grouptotal for group Current Liabilities
                sourcegroupWiseTotal = 0.00
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Liabilities' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Current Liabilities'));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        sourcegroupWiseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Dr":
                        sourcegroupWiseTotal -= accountDetails["curbal"]
                sourcesTotal += sourcegroupWiseTotal

                # Calculate grouptotal for group "Current Assets"
                applicationgroupWiseTotal = 0.00
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Assets' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Current Assets'));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        applicationgroupWiseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Cr":
                        applicationgroupWiseTotal -= accountDetails["curbal"]
                applicationsTotal += applicationgroupWiseTotal
                balanceSheet.append(
                    {
                        "sourcesgroupname": "Current Liabilities",
                        "sourceamount": "%.2f" % (sourcegroupWiseTotal),
                        "appgroupname": "Current Assets",
                        "applicationamount": "%.2f" % (applicationgroupWiseTotal),
                    }
                )

                # Calculate grouptotal for group "Reserves"
                sourcegroupWiseTotal = 0.00
                incomeTotal = 0.00
                expenseTotal = 0.00
                # Calculate all income(Direct and Indirect Income)
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Income','Indirect Income') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Income','Indirect Income')));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        incomeTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Dr":
                        incomeTotal -= accountDetails["curbal"]

                # Calculate all expense(Direct and Indirect Expense)
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Expense','Indirect Expense') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Indirect Expense')));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        expenseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Cr":
                        expenseTotal -= accountDetails["curbal"]

                # Calculate total of all accounts in Reserves (except Direct and Indirect Income, Expense)
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Reserves' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Reserves'));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        sourcegroupWiseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Dr":
                        sourcegroupWiseTotal -= accountDetails["curbal"]

                # Calculate Profit/Loss for the year
                profit = 0.00

                if expenseTotal > incomeTotal:
                    profit = expenseTotal - incomeTotal
                    sourcegroupWiseTotal -= profit
                if expenseTotal < incomeTotal:
                    profit = incomeTotal - expenseTotal
                    sourcegroupWiseTotal += profit

                sourcesTotal += sourcegroupWiseTotal

                # Calculate grouptotal for group Loans(Asset)
                applicationgroupWiseTotal = 0.00
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Asset)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Loans(Asset)'));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        applicationgroupWiseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Cr":
                        applicationgroupWiseTotal -= accountDetails["curbal"]
                applicationsTotal += applicationgroupWiseTotal
                balanceSheet.append(
                    {
                        "sourcesgroupname": "Reserves",
                        "sourceamount": "%.2f" % (sourcegroupWiseTotal),
                        "appgroupname": "Loans(Asset)",
                        "applicationamount": "%.2f" % (applicationgroupWiseTotal),
                    }
                )

                # Calculate grouptotal for group "Miscellaneous Expenses(Asset)"
                applicationgroupWiseTotal = 0.00
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname = 'Miscellaneous Expenses(Asset)' or subgroupof = (select groupcode from groupsubgroups where orgcode = %d and groupname = 'Miscellaneous Expenses(Asset)'));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        applicationgroupWiseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Cr":
                        applicationgroupWiseTotal -= accountDetails["curbal"]
                applicationsTotal += applicationgroupWiseTotal

                if expenseTotal > incomeTotal:
                    balanceSheet.append(
                        {
                            "sourcesgroupname": "Loss for the Year:",
                            "sourceamount": "%.2f" % (profit),
                            "appgroupname": "Miscellaneous Expenses(Asset)",
                            "applicationamount": "%.2f" % (applicationgroupWiseTotal),
                        }
                    )
                if expenseTotal < incomeTotal:
                    balanceSheet.append(
                        {
                            "sourcesgroupname": "Profit for the Year",
                            "sourceamount": "%.2f" % (profit),
                            "appgroupname": "Miscellaneous Expenses(Asset)",
                            "applicationamount": "%.2f" % (applicationgroupWiseTotal),
                        }
                    )
                if expenseTotal == incomeTotal:
                    balanceSheet.append(
                        {
                            "sourcesgroupname": "",
                            "sourceamount": "",
                            "appgroupname": "Miscellaneous Expenses(Asset)",
                            "applicationamount": "%.2f" % (applicationgroupWiseTotal),
                        }
                    )

                # Total of Sources and Applications
                balanceSheet.append(
                    {
                        "sourcesgroupname": "Total",
                        "sourceamount": "%.2f" % (sourcesTotal),
                        "appgroupname": "Total",
                        "applicationamount": "%.2f" % (applicationsTotal),
                    }
                )

                # Difference
                difference = abs(sourcesTotal - applicationsTotal)
                balanceSheet.append(
                    {
                        "sourcesgroupname": "Difference",
                        "sourceamount": "%.2f" % (difference),
                        "appgroupname": "",
                        "applicationamount": "",
                    }
                )
                return balanceSheet
                self.con.close()
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=consolidatedbalancesheet", renderer="json")
    def consolidatedbalanceSheet(self):
        """
        Purpose:
        Gets the list of groups and their respective balances
        takes organisations code and end date as input parameter
        Description:
        This function is used to generate consolidated balance sheet for a given organisations and the given time period.
        This function takes orgcode and end date as the input parameters
        This function is called and type=consolidatedbalancesheet is passed to the /report url.
        orgcode is extracted from the header
        end date is extracted from the request_params
        The accountcode is extracted from the database under  groupcode for groups relevent to balance sheet (meaning all groups except income and expence groups).
        the  groupbalance will be initialized to 0.0 for each group.
        this accountcode is sent to the calculateBalance function along with financialstart, calculateTo
        the function will return the closing balance related to each account which will be later added or subtracted according to the accounting rules from the group balance
        the above statements will be running in a loop for each group.
        Later all the group balances for sources and application will be added
        the difference in the amounts of sourcetotal and applicationtotal will be found
        the function will return the gkstatus and gkresult which contains a list of dictionaries where every dictionary represents a row with two key-value pairs each representing columns
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            # try:
            self.con = eng.connect()
            orgcode = authDetails["orgcode"]
            orgtype = self.request.params["orgtype"]
            financialStart = self.request.params["financialStart"]
            calculateTo = self.request.params["calculateto"]
            data = self.request.json_body
            orgs = data["listoforg"]
            sbalanceSheet = []
            abalanceSheet = []
            sourcesTotal = 0.00
            applicationsTotal = 0.00
            difference = 0.00
            sourcesTotal1 = 0.00
            applicationsTotal1 = 0.00
            sbalanceSheet.append(
                {
                    "groupAccname": "Sources:",
                    "amount": "",
                    "groupAcccode": "",
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )
            capital_Corpus = ""
            if orgtype == "Profit Making":
                capital_Corpus = "Capital"
            if orgtype == "Not For Profit":
                capital_Corpus = "Corpus"
            groupWiseTotal = 0.00

            # Calculate grouptotal for group Capital/Corpus
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = '%s') order by accountname;"
                    % (orgcode, orgcode, capital_Corpus)
                )
                accountCodes = accountcodeData.fetchall()
                subgroupDataRow = self.con.execute(
                    "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='%s');"
                    % (orgcode, orgcode, capital_Corpus)
                )
                subgroupData = subgroupDataRow.fetchall()
                groupCode = self.con.execute(
                    "select groupcode from groupsubgroups where (orgcode=%d and groupname='%s');"
                    % (orgcode, capital_Corpus)
                )
                groupcode = groupCode.fetchone()["groupcode"]
                groupAccSubgroup = []

                for accountRow in accountCodes:
                    accountTotal = 0.00
                    adverseflag = 0
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        groupWiseTotal += accountDetails["curbal"]
                        accountTotal += accountDetails["curbal"]
                    if (
                        accountDetails["baltype"] == "Dr"
                        and accountDetails["curbal"] != 0
                    ):
                        adverseflag = 1
                        accountTotal -= accountDetails["curbal"]
                        groupWiseTotal -= accountDetails["curbal"]

                for subgroup in subgroupData:
                    subgroupTotal = 0.00
                    accounts = []
                    subgroupAccDataRow = self.con.execute(
                        "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                        % (orgcode, subgroup["groupcode"])
                    )
                    subgroupAccData = subgroupAccDataRow.fetchall()
                    for account in subgroupAccData:
                        accountTotal = 0.00
                        adverseflag = 0
                        accountDetails = calculateBalance(
                            self.con,
                            account["accountcode"],
                            financialStart,
                            financialStart,
                            calculateTo,
                        )
                        if accountDetails["baltype"] == "Cr":
                            subgroupTotal += accountDetails["curbal"]
                            accountTotal += accountDetails["curbal"]
                        if (
                            accountDetails["baltype"] == "Dr"
                            and accountDetails["curbal"] != 0
                        ):
                            adverseflag = 1
                            subgroupTotal -= accountDetails["curbal"]
                            accountTotal -= accountDetails["curbal"]
                        if accountDetails["curbal"] != 0:
                            dummy = 0
                            # accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
                    groupWiseTotal += subgroupTotal
                    # groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
                    groupAccSubgroup += accounts
                sourcesTotal += groupWiseTotal
            sbalanceSheet.append(
                {
                    "groupAccname": capital_Corpus,
                    "amount": "%.2f" % (groupWiseTotal),
                    "groupAcccode": groupcode,
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )
            sourcesTotal1 += groupWiseTotal
            sbalanceSheet += groupAccSubgroup

            # Calculate grouptotal for group Loans(Liability)
            groupWiseTotal = 0.00
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Liability)') order by accountname;"
                    % (orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                subgroupDataRow = self.con.execute(
                    "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Loans(Liability)');"
                    % (orgcode, orgcode)
                )
                subgroupData = subgroupDataRow.fetchall()
                groupCode = self.con.execute(
                    "select groupcode from groupsubgroups where (orgcode=%d and groupname='Loans(Liability)');"
                    % (orgcode)
                )
                groupcode = groupCode.fetchone()["groupcode"]
                groupAccSubgroup = []

                for accountRow in accountCodes:
                    accountTotal = 0.00
                    adverseflag = 0
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        groupWiseTotal += accountDetails["curbal"]
                        accountTotal += accountDetails["curbal"]
                    if (
                        accountDetails["baltype"] == "Dr"
                        and accountDetails["curbal"] != 0
                    ):
                        adverseflag = 1
                        accountTotal -= accountDetails["curbal"]
                        groupWiseTotal -= accountDetails["curbal"]
                    groupAccSubgroup.append(
                        {
                            "groupAccname": accountRow["accountname"],
                            "amount": "%.2f" % (accountTotal),
                            "groupAcccode": accountRow["accountcode"],
                            "subgroupof": "",
                            "accountof": groupcode,
                            "groupAccflag": 1,
                            "advflag": adverseflag,
                        }
                    )

                for subgroup in subgroupData:
                    subgroupTotal = 0.00
                    accounts = []
                    subgroupAccDataRow = self.con.execute(
                        "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                        % (orgcode, subgroup["groupcode"])
                    )
                    subgroupAccData = subgroupAccDataRow.fetchall()
                    for account in subgroupAccData:
                        accountTotal = 0.00
                        adverseflag = 0
                        accountDetails = calculateBalance(
                            self.con,
                            account["accountcode"],
                            financialStart,
                            financialStart,
                            calculateTo,
                        )
                        if accountDetails["baltype"] == "Cr":
                            subgroupTotal += accountDetails["curbal"]
                            accountTotal += accountDetails["curbal"]
                        if (
                            accountDetails["baltype"] == "Dr"
                            and accountDetails["curbal"] != 0
                        ):
                            adverseflag = 1
                            subgroupTotal -= accountDetails["curbal"]
                            accountTotal -= accountDetails["curbal"]
                        if accountDetails["curbal"] != 0:
                            dummy = 0
                            # accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
                    groupWiseTotal += subgroupTotal
                    # groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
                    groupAccSubgroup += accounts

                sourcesTotal += groupWiseTotal
            sbalanceSheet.append(
                {
                    "groupAccname": "Loans(Liability)",
                    "amount": "%.2f" % (groupWiseTotal),
                    "groupAcccode": groupcode,
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )
            sourcesTotal1 += groupWiseTotal
            sbalanceSheet += groupAccSubgroup

            # Calculate grouptotal for group Current Liabilities
            groupWiseTotal = 0.00
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Liabilities') order by accountname;"
                    % (orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                subgroupDataRow = self.con.execute(
                    "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Current Liabilities');"
                    % (orgcode, orgcode)
                )
                subgroupData = subgroupDataRow.fetchall()
                groupCode = self.con.execute(
                    "select groupcode from groupsubgroups where (orgcode=%d and groupname='Current Liabilities');"
                    % (orgcode)
                )
                groupcode = groupCode.fetchone()["groupcode"]
                groupAccSubgroup = []

                for accountRow in accountCodes:
                    accountTotal = 0.00
                    adverseflag = 0
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        groupWiseTotal += accountDetails["curbal"]
                        accountTotal += accountDetails["curbal"]
                    if (
                        accountDetails["baltype"] == "Dr"
                        and accountDetails["curbal"] != 0
                    ):
                        adverseflag = 1
                        accountTotal -= accountDetails["curbal"]
                        groupWiseTotal -= accountDetails["curbal"]

                for subgroup in subgroupData:
                    subgroupTotal = 0.00
                    accounts = []
                    subgroupAccDataRow = self.con.execute(
                        "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                        % (orgcode, subgroup["groupcode"])
                    )
                    subgroupAccData = subgroupAccDataRow.fetchall()
                    for account in subgroupAccData:
                        accountTotal = 0.00
                        adverseflag = 0
                        accountDetails = calculateBalance(
                            self.con,
                            account["accountcode"],
                            financialStart,
                            financialStart,
                            calculateTo,
                        )
                        if accountDetails["baltype"] == "Cr":
                            subgroupTotal += accountDetails["curbal"]
                            accountTotal += accountDetails["curbal"]
                        if (
                            accountDetails["baltype"] == "Dr"
                            and accountDetails["curbal"] != 0
                        ):
                            adverseflag = 1
                            subgroupTotal -= accountDetails["curbal"]
                            accountTotal -= accountDetails["curbal"]
                        if accountDetails["curbal"] != 0:
                            dummy = 0
                            # accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
                    groupWiseTotal += subgroupTotal
                    # groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
                    groupAccSubgroup += accounts

                sourcesTotal += groupWiseTotal
            sbalanceSheet.append(
                {
                    "groupAccname": "Current Liabilities",
                    "amount": "%.2f" % (groupWiseTotal),
                    "groupAcccode": groupcode,
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )
            sourcesTotal1 += groupWiseTotal
            sbalanceSheet += groupAccSubgroup

            # Calculate grouptotal for group "Reserves"
            groupWiseTotal = 0.00
            incomeTotal = 0.00
            expenseTotal = 0.00
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Reserves') order by accountname;"
                    % (orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                subgroupDataRow = self.con.execute(
                    "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Reserves');"
                    % (orgcode, orgcode)
                )
                subgroupData = subgroupDataRow.fetchall()
                groupCode = self.con.execute(
                    "select groupcode from groupsubgroups where (orgcode=%d and groupname='Reserves');"
                    % (orgcode)
                )
                groupcode = groupCode.fetchone()["groupcode"]
                groupAccSubgroup = []

                for accountRow in accountCodes:
                    accountTotal = 0.00
                    adverseflag = 0
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        groupWiseTotal += accountDetails["curbal"]
                        accountTotal += accountDetails["curbal"]
                    if (
                        accountDetails["baltype"] == "Dr"
                        and accountDetails["curbal"] != 0
                    ):
                        adverseflag = 1
                        accountTotal -= accountDetails["curbal"]
                        groupWiseTotal -= accountDetails["curbal"]

                for subgroup in subgroupData:
                    subgroupTotal = 0.00
                    accounts = []
                    subgroupAccDataRow = self.con.execute(
                        "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                        % (orgcode, subgroup["groupcode"])
                    )
                    subgroupAccData = subgroupAccDataRow.fetchall()
                    for account in subgroupAccData:
                        accountTotal = 0.00
                        adverseflag = 0
                        accountDetails = calculateBalance(
                            self.con,
                            account["accountcode"],
                            financialStart,
                            financialStart,
                            calculateTo,
                        )
                        if accountDetails["baltype"] == "Cr":
                            subgroupTotal += accountDetails["curbal"]
                            accountTotal += accountDetails["curbal"]
                        if (
                            accountDetails["baltype"] == "Dr"
                            and accountDetails["curbal"] != 0
                        ):
                            adverseflag = 1
                            subgroupTotal -= accountDetails["curbal"]
                            accountTotal -= accountDetails["curbal"]
                        if accountDetails["curbal"] != 0:
                            dummy = 0
                            # accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
                    groupWiseTotal += subgroupTotal
            # groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
            groupAccSubgroup += accounts

            # Calculate all income(Direct and Indirect Income)
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Income','Indirect Income') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Income','Indirect Income')));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Cr":
                        incomeTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Dr":
                        incomeTotal -= accountDetails["curbal"]

            # Calculate all expense(Direct and Indirect Expense)
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode from accounts where orgcode = %d and groupcode in(select groupcode from groupsubgroups where orgcode =%d and groupname in ('Direct Expense','Indirect Expense') or subgroupof in (select groupcode from groupsubgroups where orgcode = %d and groupname in ('Direct Expense','Indirect Expense')));"
                    % (orgcode, orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                for accountRow in accountCodes:
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        expenseTotal += accountDetails["curbal"]
                    if accountDetails["baltype"] == "Cr":
                        expenseTotal -= accountDetails["curbal"]

            # Calculate Profit/Loss for the year
            profit = 0
            if expenseTotal > incomeTotal:
                profit = expenseTotal - incomeTotal
                groupWiseTotal -= profit
                sbalanceSheet.append(
                    {
                        "groupAccname": "Reserves",
                        "amount": "%.2f" % (groupWiseTotal),
                        "groupAcccode": groupcode,
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    }
                )
                if orgtype == "Profit Making":
                    sbalanceSheet.append(
                        {
                            "groupAccname": "Loss for the Year:",
                            "amount": "%.2f" % (profit),
                            "groupAcccode": "",
                            "subgroupof": groupcode,
                            "accountof": "",
                            "groupAccflag": 2,
                            "advflag": "",
                        }
                    )
                else:
                    sbalanceSheet.append(
                        {
                            "groupAccname": "Deficit for the Year:",
                            "amount": "%.2f" % (profit),
                            "groupAcccode": "",
                            "subgroupof": groupcode,
                            "accountof": "",
                            "groupAccflag": 2,
                            "advflag": "",
                        }
                    )

            if expenseTotal < incomeTotal:
                profit = incomeTotal - expenseTotal
                groupWiseTotal += profit
                sbalanceSheet.append(
                    {
                        "groupAccname": "Reserves",
                        "amount": "%.2f" % (groupWiseTotal),
                        "groupAcccode": groupcode,
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    }
                )
                if orgtype == "Profit Making":
                    sbalanceSheet.append(
                        {
                            "groupAccname": "Profit for the Year:",
                            "amount": "%.2f" % (profit),
                            "groupAcccode": "",
                            "subgroupof": groupcode,
                            "accountof": "",
                            "groupAccflag": 2,
                            "advflag": "",
                        }
                    )
                else:
                    sbalanceSheet.append(
                        {
                            "groupAccname": "Surplus for the Year:",
                            "amount": "%.2f" % (profit),
                            "groupAcccode": "",
                            "subgroupof": groupcode,
                            "accountof": "",
                            "groupAccflag": 2,
                            "advflag": "",
                        }
                    )
            if expenseTotal == incomeTotal:
                sbalanceSheet.append(
                    {
                        "groupAccname": "Reserves",
                        "amount": "%.2f" % (groupWiseTotal),
                        "groupAcccode": groupcode,
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    }
                )

            sbalanceSheet += groupAccSubgroup
            sourcesTotal += groupWiseTotal
            sourcesTotal1 += groupWiseTotal
            sbalanceSheet.append(
                {
                    "groupAccname": "Total",
                    "amount": "%.2f" % (sourcesTotal1),
                    "groupAcccode": "",
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )

            # Applications:
            abalanceSheet.append(
                {
                    "groupAccname": "Applications:",
                    "amount": "",
                    "groupAcccode": "",
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )

            # Calculate grouptotal for group "Fixed Assets"
            groupWiseTotal = 0.00
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Fixed Assets') order by accountname;"
                    % (orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                subgroupDataRow = self.con.execute(
                    "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Fixed Assets');"
                    % (orgcode, orgcode)
                )
                subgroupData = subgroupDataRow.fetchall()
                groupCode = self.con.execute(
                    "select groupcode from groupsubgroups where (orgcode=%d and groupname='Fixed Assets');"
                    % (orgcode)
                )
                groupcode = groupCode.fetchone()["groupcode"]
                groupAccSubgroup = []

                for accountRow in accountCodes:
                    accountTotal = 0.00
                    adverseflag = 0
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        groupWiseTotal += accountDetails["curbal"]
                        accountTotal += accountDetails["curbal"]
                    if (
                        accountDetails["baltype"] == "Cr"
                        and accountDetails["curbal"] != 0
                    ):
                        adverseflag = 1
                        accountTotal -= accountDetails["curbal"]
                        groupWiseTotal -= accountDetails["curbal"]

                for subgroup in subgroupData:
                    subgroupTotal = 0.00
                    accounts = []
                    subgroupAccDataRow = self.con.execute(
                        "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                        % (orgcode, subgroup["groupcode"])
                    )
                    subgroupAccData = subgroupAccDataRow.fetchall()

                    for account in subgroupAccData:
                        accountTotal = 0.00
                        adverseflag = 0
                        accountDetails = calculateBalance(
                            self.con,
                            account["accountcode"],
                            financialStart,
                            financialStart,
                            calculateTo,
                        )
                        if accountDetails["baltype"] == "Dr":
                            subgroupTotal += accountDetails["curbal"]
                            accountTotal += accountDetails["curbal"]
                        if (
                            accountDetails["baltype"] == "Cr"
                            and accountDetails["curbal"] != 0
                        ):
                            adverseflag = 1
                            subgroupTotal -= accountDetails["curbal"]
                            accountTotal -= accountDetails["curbal"]
                        if accountDetails["curbal"] != 0:
                            dummy = 0
                            # accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2,"advflag":adverseflag})
                    groupWiseTotal += subgroupTotal
                    # groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"","advflag":""})
                    groupAccSubgroup += accounts

                applicationsTotal += groupWiseTotal
            abalanceSheet.append(
                {
                    "groupAccname": "Fixed Assets",
                    "amount": "%.2f" % (groupWiseTotal),
                    "groupAcccode": groupcode,
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )
            applicationsTotal1 += groupWiseTotal
            abalanceSheet += groupAccSubgroup

            # Calculate grouptotal for group "Investments"
            groupWiseTotal = 0.00
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Investments') order by accountname;"
                    % (orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                subgroupDataRow = self.con.execute(
                    "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Investments');"
                    % (orgcode, orgcode)
                )
                subgroupData = subgroupDataRow.fetchall()
                groupCode = self.con.execute(
                    "select groupcode from groupsubgroups where (orgcode=%d and groupname='Investments');"
                    % (orgcode)
                )
                groupcode = groupCode.fetchone()["groupcode"]
                groupAccSubgroup = []

                for accountRow in accountCodes:
                    accountTotal = 0.00
                    adverseflag = 0
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        groupWiseTotal += accountDetails["curbal"]
                        accountTotal += accountDetails["curbal"]
                    if (
                        accountDetails["baltype"] == "Cr"
                        and accountDetails["curbal"] != 0
                    ):
                        adverseflag = 1
                        accountTotal -= accountDetails["curbal"]
                        groupWiseTotal -= accountDetails["curbal"]

                for subgroup in subgroupData:
                    subgroupTotal = 0.00
                    accounts = []
                    subgroupAccDataRow = self.con.execute(
                        "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                        % (orgcode, subgroup["groupcode"])
                    )
                    subgroupAccData = subgroupAccDataRow.fetchall()
                    for account in subgroupAccData:
                        accountTotal = 0.00
                        adverseflag = 0
                        accountDetails = calculateBalance(
                            self.con,
                            account["accountcode"],
                            financialStart,
                            financialStart,
                            calculateTo,
                        )
                        if accountDetails["baltype"] == "Dr":
                            subgroupTotal += accountDetails["curbal"]
                            accountTotal += accountDetails["curbal"]
                        if (
                            accountDetails["baltype"] == "Cr"
                            and accountDetails["curbal"] != 0
                        ):
                            adverseflag = 1
                            subgroupTotal -= accountDetails["curbal"]
                            accountTotal -= accountDetails["curbal"]
                        if accountDetails["curbal"] != 0:
                            dummy = 0
                            # accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
                    groupWiseTotal += subgroupTotal
                    # groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"","advflag":""})
                    groupAccSubgroup += accounts

                applicationsTotal += groupWiseTotal
            abalanceSheet.append(
                {
                    "groupAccname": "Investments",
                    "amount": "%.2f" % (groupWiseTotal),
                    "groupAcccode": groupcode,
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )
            applicationsTotal1 += groupWiseTotal
            abalanceSheet += groupAccSubgroup

            # Calculate grouptotal for group "Current Assets"
            groupWiseTotal = 0.00
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Current Assets') order by accountname;"
                    % (orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                subgroupDataRow = self.con.execute(
                    "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Current Assets');"
                    % (orgcode, orgcode)
                )
                subgroupData = subgroupDataRow.fetchall()
                groupCode = self.con.execute(
                    "select groupcode from groupsubgroups where (orgcode=%d and groupname='Current Assets');"
                    % (orgcode)
                )
                groupcode = groupCode.fetchone()["groupcode"]
                groupAccSubgroup = []

                for accountRow in accountCodes:
                    accountTotal = 0.00
                    adverseflag = 0
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        groupWiseTotal += accountDetails["curbal"]
                        accountTotal += accountDetails["curbal"]
                    if (
                        accountDetails["baltype"] == "Cr"
                        and accountDetails["curbal"] != 0
                    ):
                        adverseflag = 1
                        accountTotal -= accountDetails["curbal"]
                        groupWiseTotal -= accountDetails["curbal"]

                for subgroup in subgroupData:
                    subgroupTotal = 0.00
                    accounts = []
                    subgroupAccDataRow = self.con.execute(
                        "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                        % (orgcode, subgroup["groupcode"])
                    )
                    subgroupAccData = subgroupAccDataRow.fetchall()
                    for account in subgroupAccData:
                        accountTotal = 0.00
                        adverseflag = 0
                        accountDetails = calculateBalance(
                            self.con,
                            account["accountcode"],
                            financialStart,
                            financialStart,
                            calculateTo,
                        )
                        if accountDetails["baltype"] == "Dr":
                            subgroupTotal += accountDetails["curbal"]
                            accountTotal += accountDetails["curbal"]
                        if (
                            accountDetails["baltype"] == "Cr"
                            and accountDetails["curbal"] != 0
                        ):
                            adverseflag = 1
                            subgroupTotal -= accountDetails["curbal"]
                            accountTotal -= accountDetails["curbal"]
                        if accountDetails["curbal"] != 0:
                            dummy = 0
                            # accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
                    groupWiseTotal += subgroupTotal
                    # groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"","advflag":""})
                    groupAccSubgroup += accounts

                applicationsTotal += groupWiseTotal
            abalanceSheet.append(
                {
                    "groupAccname": "Current Assets",
                    "amount": "%.2f" % (groupWiseTotal),
                    "groupAcccode": groupcode,
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )
            applicationsTotal1 += groupWiseTotal
            abalanceSheet += groupAccSubgroup

            # Calculate grouptotal for group Loans(Asset)
            groupWiseTotal = 0.00
            for i in orgs:
                orgcode = int(i)
                accountcodeData = self.con.execute(
                    "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Loans(Asset)') order by accountname;"
                    % (orgcode, orgcode)
                )
                accountCodes = accountcodeData.fetchall()
                subgroupDataRow = self.con.execute(
                    "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Loans(Asset)');"
                    % (orgcode, orgcode)
                )
                subgroupData = subgroupDataRow.fetchall()
                groupCode = self.con.execute(
                    "select groupcode from groupsubgroups where (orgcode=%d and groupname='Loans(Asset)');"
                    % (orgcode)
                )
                groupcode = groupCode.fetchone()["groupcode"]
                groupAccSubgroup = []

                for accountRow in accountCodes:
                    accountTotal = 0.00
                    adverseflag = 0
                    accountDetails = calculateBalance(
                        self.con,
                        accountRow["accountcode"],
                        financialStart,
                        financialStart,
                        calculateTo,
                    )
                    if accountDetails["baltype"] == "Dr":
                        groupWiseTotal += accountDetails["curbal"]
                        accountTotal += accountDetails["curbal"]
                    if (
                        accountDetails["baltype"] == "Cr"
                        and accountDetails["curbal"] != 0
                    ):
                        adverseflag = 1
                        accountTotal -= accountDetails["curbal"]
                        groupWiseTotal -= accountDetails["curbal"]

                for subgroup in subgroupData:
                    subgroupTotal = 0.00
                    accounts = []
                    subgroupAccDataRow = self.con.execute(
                        "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                        % (orgcode, subgroup["groupcode"])
                    )
                    subgroupAccData = subgroupAccDataRow.fetchall()
                    for account in subgroupAccData:
                        accountTotal = 0.00
                        adverseflag = 0
                        accountDetails = calculateBalance(
                            self.con,
                            account["accountcode"],
                            financialStart,
                            financialStart,
                            calculateTo,
                        )
                        if accountDetails["baltype"] == "Dr":
                            subgroupTotal += accountDetails["curbal"]
                            accountTotal += accountDetails["curbal"]
                        if (
                            accountDetails["baltype"] == "Cr"
                            and accountDetails["curbal"] != 0
                        ):
                            adverseflag = 1
                            subgroupTotal -= accountDetails["curbal"]
                            accountTotal -= accountDetails["curbal"]
                        if accountDetails["curbal"] != 0:
                            dummy = 0
                            # accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag":adverseflag})
                    groupWiseTotal += subgroupTotal
                    # groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"", "advflag":""})
                    groupAccSubgroup += accounts

                applicationsTotal += groupWiseTotal
            abalanceSheet.append(
                {
                    "groupAccname": "Loans(Asset)",
                    "amount": "%.2f" % (groupWiseTotal),
                    "groupAcccode": groupcode,
                    "subgroupof": "",
                    "accountof": "",
                    "groupAccflag": "",
                    "advflag": "",
                }
            )
            applicationsTotal1 += groupWiseTotal
            abalanceSheet += groupAccSubgroup

            if orgtype == "Profit Making":
                # Calculate grouptotal for group "Miscellaneous Expenses(Asset)"
                groupWiseTotal = 0.00
                for i in orgs:
                    orgcode = int(i)
                    accountcodeData = self.con.execute(
                        "select accountcode, accountname from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where orgcode =%d and groupname = 'Miscellaneous Expenses(Asset)') order by accountname;"
                        % (orgcode, orgcode)
                    )
                    accountCodes = accountcodeData.fetchall()
                    subgroupDataRow = self.con.execute(
                        "select groupcode, groupname  from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where orgcode = %d and subgroupof is null and groupname ='Miscellaneous Expenses(Asset)');"
                        % (orgcode, orgcode)
                    )
                    subgroupData = subgroupDataRow.fetchall()
                    groupCode = self.con.execute(
                        "select groupcode from groupsubgroups where (orgcode=%d and groupname='Miscellaneous Expenses(Asset)');"
                        % (orgcode)
                    )
                    groupcode = groupCode.fetchone()["groupcode"]
                    groupAccSubgroup = []

                    for accountRow in accountCodes:
                        accountTotal = 0.00
                        adverseflag = 0
                        accountDetails = calculateBalance(
                            self.con,
                            accountRow["accountcode"],
                            financialStart,
                            financialStart,
                            calculateTo,
                        )
                        if accountDetails["baltype"] == "Dr":
                            groupWiseTotal += accountDetails["curbal"]
                            accountTotal += accountDetails["curbal"]
                        if (
                            accountDetails["baltype"] == "Cr"
                            and accountDetails["curbal"] != 0
                        ):
                            adverseflag = 1
                            accountTotal -= accountDetails["curbal"]
                            groupWiseTotal -= accountDetails["curbal"]

                    for subgroup in subgroupData:
                        subgroupTotal = 0.00
                        accounts = []
                        subgroupAccDataRow = self.con.execute(
                            "select accountcode, accountname from accounts where orgcode = %d and groupcode = %d order by accountname"
                            % (orgcode, subgroup["groupcode"])
                        )
                        subgroupAccData = subgroupAccDataRow.fetchall()
                        for account in subgroupAccData:
                            accountTotal = 0.00
                            adverseflag = 0
                            accountDetails = calculateBalance(
                                self.con,
                                account["accountcode"],
                                financialStart,
                                financialStart,
                                calculateTo,
                            )
                            if accountDetails["baltype"] == "Dr":
                                subgroupTotal += accountDetails["curbal"]
                                accountTotal += accountDetails["curbal"]
                            if (
                                accountDetails["baltype"] == "Cr"
                                and accountDetails["curbal"] != 0
                            ):
                                adverseflag = 1
                                subgroupTotal -= accountDetails["curbal"]
                                accountTotal -= accountDetails["curbal"]
                            if accountDetails["curbal"] != 0:
                                dummy = 0
                                # accounts.append({"groupAccname":account["accountname"],"amount":"%.2f"%(accountTotal), "groupAcccode":account["accountcode"],"subgroupof":groupcode , "accountof":subgroup["groupcode"], "groupAccflag":2, "advflag": adverseflag})
                        groupWiseTotal += subgroupTotal
                        # groupAccSubgroup.append({"groupAccname":subgroup["groupname"],"amount":"%.2f"%(subgroupTotal), "groupAcccode":subgroup["groupcode"],"subgroupof":groupcode , "accountof":"", "groupAccflag":"","advflag":""})
                        groupAccSubgroup += accounts

                    applicationsTotal += groupWiseTotal
                abalanceSheet.append(
                    {
                        "groupAccname": "Miscellaneous Expenses(Asset)",
                        "amount": "%.2f" % (groupWiseTotal),
                        "groupAcccode": groupcode,
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    }
                )
                applicationsTotal1 += groupWiseTotal
                abalanceSheet += groupAccSubgroup

                abalanceSheet.append(
                    {
                        "groupAccname": "Total",
                        "amount": "%.2f" % (applicationsTotal1),
                        "groupAcccode": "",
                        "subgroupof": "",
                        "accountof": "",
                        "groupAccflag": "",
                        "advflag": "",
                    }
                )

            self.con.close()
            return {
                "gkstatus": enumdict["Success"],
                "gkresult": {"leftlist": sbalanceSheet, "rightlist": abalanceSheet},
            }

        # except:
        # self.con.close()
        # return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(route_name="profit-loss", renderer="json")
    def profitLoss(self):
        """
        This method returns a grid containing the profit and loss statement of the organisation.
        The profit and loss statement has all the direct and indirect expenses and the direct and indirect incomes.
        If the incomes are greater than the expenses, the organisation is in profit
        Purpose:
        the method takes the orgcode and the calculateto as the input parameters and returns a grid containing the list of all accounts under the group of direct and indirect income and, direct and indirect expenses along with their respective balances. It also return the gross and net profit/loss made by the company.
        Description:
        the function generates the profit and loss statement of the organisation.
        this function is called when the type=profitloss is passed to the /report url.
        the orgcode is extracted from the header
        calculateTo date is extracted from the request_params
        the accounts and subgroups  under the groups direct income and direct expense are extracted from the database.
        then these codes are sent to the calculateBalance function which returns their current balances.
        the total of these balances give the gross profit/loss of the organisation.
        then the accounts and subgroups under the indirect income and indirect expense are extracted from the database.
        and sent to the calculateBalance function along with the financial start and the calculateto date.
        the total of balances of these accounts along with the gross profit/loss gives the net profit/loss of the organisation
        final dictionary will look like as follows : result = {"Direct Income":{"Direct Income Balance":value,"Subgrup Name":{"Account name":Balance,....,"balance":value},"account name":Balance,....}'''''Same for other groups ''''' }"Total":value, "Net Profit":Value}}
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            self.con = eng.connect()
            try:
                orgcode = authDetails["orgcode"]
                financialstart = self.con.execute(
                    "select orgtype from organisation where orgcode = %d" % int(orgcode)
                )
                financialstartRow = financialstart.fetchone()
                calculateFrom = self.request.params["calculatefrom"]
                orgtype = financialstartRow["orgtype"]
                calculateTo = self.request.params["calculateto"]
                result = {}
                # grsD = 0.00
                # income = 0.00
                # expense = 0.00
                # profit = ""
                # loss = ""
                # closingStockBal = 0.00
                directIncome = {}
                grpDIbalance = 0.00
                grpDI = 0.00  # Direct Income other than sales
                directExpense = {}
                grpDEbalance = 0.00
                grpDE = 0.00  # Direct Expense other than purchase
                indirectIncome = {}
                grpIIbalance = 0.00
                indirectExpense = {}
                grpIEbalance = 0.00

                # Calculate closing stock value
                result["Closing Stock"] = calculateClosingStockValue(
                    self.con, orgcode, calculateTo
                )
                # print("Profit Loss")
                # print(orgcode)
                # print(calculateTo)
                # Calculate opening stock value
                result["Opening Stock"] = calculateOpeningStockValue(self.con, orgcode)
                if orgtype == "Profit Making":
                    profit = "Profit"
                    loss = "Loss"
                    pnlAccountname = "Profit & Loss"
                if orgtype == "Not For Profit":
                    profit = "Surplus"
                    loss = "Deficit"
                    pnlAccountname = "Income & Expenditure"

                # Get all subgroups with their group code and group name under Group Direct Expense
                DESubGroupsData = self.con.execute(
                    "select groupcode,groupname from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where groupname = 'Direct Expense' and orgcode = %d)"
                    % (orgcode, orgcode)
                )
                DESubGroups = DESubGroupsData.fetchall()
                # print("Direct Expense sub groups")
                # print(DESubGroups)
                # now we have list of subgroups under Direct Expense.
                # We will loop through each and get list of their accounts.
                for DESub in DESubGroups:
                    # Start looping with the subgroup in hand,
                    # and get it's list of accounts.
                    DESubAccsData = self.con.execute(
                        select([accounts.c.accountcode, accounts.c.accountname]).where(
                            and_(
                                accounts.c.orgcode == orgcode,
                                accounts.c.groupcode == DESub["groupcode"],
                            )
                        )
                    )
                    if DESubAccsData.rowcount > 0:
                        DESubAccs = DESubAccsData.fetchall()
                        DESUBDict = {}
                        DESubBal = 0.00

                        for desubacc in DESubAccs:
                            calbalData = calculateBalance(
                                self.con,
                                desubacc["accountcode"],
                                calculateFrom,
                                calculateFrom,
                                calculateTo,
                            )
                            if calbalData["curbal"] == 0.00:
                                continue
                            if calbalData["baltype"] == "Dr":
                                DESUBDict[desubacc["accountname"]] = "%.2f" % (
                                    float(calbalData["curbal"])
                                )
                                DESubBal = DESubBal + float(calbalData["curbal"])
                            if calbalData["baltype"] == "Cr":
                                DESUBDict[desubacc["accountname"]] = "%.2f" % (
                                    -float(calbalData["curbal"])
                                )
                                DESubBal = DESubBal - float(calbalData["curbal"])
                        # This is balance of sub group
                        DESUBDict["balance"] = "%.2f" % (float(DESubBal))
                        # This is balance of main group
                        grpDEbalance = grpDEbalance + float(DESubBal)
                        if DESub["groupname"] != "Purchase":
                            grpDE = grpDE + float(DESubBal)
                        directExpense[DESub["groupname"]] = DESUBDict
                    else:
                        continue

                # Now consider those accounts which are directly created under Direct Expense group
                getDEAccData = self.con.execute(
                    "select accountname,accountcode from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where groupname = 'Direct Expense' and orgcode = %d)"
                    % (orgcode, orgcode)
                )
                if getDEAccData.rowcount > 0:
                    deAccData = getDEAccData.fetchall()
                    # print("Direct Expense Account data")
                    # print(deAccData)print("Balance Sheet")
                    # print(orgcode)
                    # print(calculateTo)
                    for deAcc in deAccData:
                        calbalData = calculateBalance(
                            self.con,
                            deAcc["accountcode"],
                            calculateFrom,
                            calculateFrom,
                            calculateTo,
                        )
                        if calbalData["curbal"] == 0.00:
                            continue
                        if calbalData["baltype"] == "Dr":
                            directExpense[deAcc["accountname"]] = "%.2f" % (
                                float(calbalData["curbal"])
                            )
                            grpDEbalance = grpDEbalance + float(calbalData["curbal"])
                            grpDE = grpDE + float(calbalData["curbal"])
                        if calbalData["baltype"] == "Cr":
                            directExpense[deAcc["accountname"]] = "%.2f" % (
                                -float(calbalData["curbal"])
                            )
                            grpDEbalance = grpDEbalance - float(calbalData["curbal"])
                            grpDE = grpDE - float(calbalData["curbal"])

                directExpense["direxpbal"] = "%.2f" % (float(grpDEbalance))
                result["Direct Expense"] = directExpense

                # Calculation for Direct Income
                # Same procedure as Direct Expense.
                DISubGroupsData = self.con.execute(
                    "select groupcode,groupname from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where groupname = 'Direct Income' and orgcode = %d)"
                    % (orgcode, orgcode)
                )
                DISubGroups = DISubGroupsData.fetchall()
                # now we have list of subgroups under Direct Income.
                # We will loop through each and get list of their accounts.
                for DISub in DISubGroups:
                    # Start looping with the subgroup in hand,
                    # and get it's list of accounts.
                    DISubAccsData = self.con.execute(
                        select([accounts.c.accountcode, accounts.c.accountname]).where(
                            and_(
                                accounts.c.orgcode == orgcode,
                                accounts.c.groupcode == DISub["groupcode"],
                            )
                        )
                    )
                    if DISubAccsData.rowcount > 0:
                        DISubAccs = DISubAccsData.fetchall()
                        DISUBDict = {}
                        DISubBal = 0.00
                        # print("Direct Income Sub Acc")
                        # print(DISubAccs)
                        for disubacc in DISubAccs:
                            calbalData = calculateBalance(
                                self.con,
                                disubacc["accountcode"],
                                calculateFrom,
                                calculateFrom,
                                calculateTo,
                            )
                            # print(calbalData["curbal"])
                            if calbalData["curbal"] == 0.00:
                                continue
                            if calbalData["baltype"] == "Cr":
                                DISUBDict[disubacc["accountname"]] = "%.2f" % (
                                    float(calbalData["curbal"])
                                )
                                DISubBal = DISubBal + float(calbalData["curbal"])
                            if calbalData["baltype"] == "Dr":
                                DISUBDict[disubacc["accountname"]] = "%.2f" % (
                                    -float(calbalData["curbal"])
                                )
                                DISubBal = DISubBal - float(calbalData["curbal"])

                        # This is balance of sub group
                        DISUBDict["balance"] = "%.2f" % (float(DISubBal))
                        # This is balance of main group
                        grpDIbalance = grpDIbalance + float(DISubBal)
                        if DISub["groupname"] != "Sales":
                            grpDI = grpDI + float(DISubBal)
                        directIncome[DISub["groupname"]] = DISUBDict

                getDIAccData = self.con.execute(
                    "select accountname,accountcode from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where groupname = 'Direct Income' and orgcode = %d)"
                    % (orgcode, orgcode)
                )
                if getDIAccData.rowcount > 0:
                    diAccData = getDIAccData.fetchall()
                    for diAcc in diAccData:
                        print(diAcc["accountname"])
                        if diAcc["accountname"] != pnlAccountname:
                            calbalData = calculateBalance(
                                self.con,
                                diAcc["accountcode"],
                                calculateFrom,
                                calculateFrom,
                                calculateTo,
                            )
                            if calbalData["curbal"] == 0.00:
                                continue
                            if calbalData["baltype"] == "Cr":
                                directIncome[diAcc["accountname"]] = "%.2f" % (
                                    float(calbalData["curbal"])
                                )
                                grpDIbalance = grpDIbalance + float(
                                    calbalData["curbal"]
                                )
                                grpDI = grpDI + float(calbalData["curbal"])
                            if calbalData["baltype"] == "Dr":
                                directIncome[diAcc["accountname"]] = "%.2f" % (
                                    -float(calbalData["curbal"])
                                )
                                grpDIbalance = grpDIbalance - float(
                                    calbalData["curbal"]
                                )
                                grpDI = grpDI - float(calbalData["curbal"])
                        # else:
                        #     csAccountcode = self.con.execute(
                        #         "select accountcode from accounts where orgcode=%d and accountname='Closing Stock'"
                        #         % (orgcode)
                        #     )
                        #     csAccountcodeRow = csAccountcode.fetchone()
                        #     calbalData = calculateBalance(
                        #         self.con,
                        #         csAccountcodeRow["accountcode"],
                        #         calculateFrom,
                        #         calculateFrom,
                        #         calculateTo,
                        #     )
                        #     result["Closing Stock"] = "%.2f" % (
                        #         float(calbalData["curbal"])
                        #     )
                        #     closingStockBal = float(calbalData["curbal"])

                directIncome["dirincmbal"] = "%.2f" % (float(grpDIbalance))
                result["Direct Income"] = directIncome

                saleCost = (
                    result["Opening Stock"]["total"]
                    + grpDEbalance
                    - result["Closing Stock"]["total"]
                )
                # sale =
                # if saleCost < grpDEbalance:
                #     grsD = grpDEbalance - saleCost
                #     result["grossprofitcf"] = "%.2f" % (float(grsD))
                #     result["totalD"] = "%.2f" % (float(grpDEbalance))
                # else:
                #     grsD = saleCost - grpDEbalance
                #     result["grosslosscf"] = "%.2f" % (float(grsD))
                #     result["totalD"] = "%.2f" % (float(saleCost))
                # if grpDIbalance > grpDEbalance:
                #     grsD = grpDIbalance - grpDEbalance
                #     result["grossprofitcf"] = "%.2f" % (float(grsD))
                #     result["totalD"] = "%.2f" % (float(grpDIbalance))
                # else:
                #     grsD = grpDEbalance - grpDIbalance
                #     result["grosslosscf"] = "%.2f" % (float(grsD))
                #     result["totalD"] = "%.2f" % (float(grpDEbalance))

                priceDiff = calculateProfitLossValue(self.con, orgcode, calculateTo)
                grossDiff = priceDiff["total"] + grpDI - grpDE

                if grossDiff >= 0:
                    result["grossprofitcf"] = "%.2f" % (float(grossDiff))
                else:
                    result["grosslosscf"] = "%.2f" % (-1 * float(grossDiff))

                """ ################   Indirect Income & Indirect Expense  ################ """
                # Get all subgroups with their group code and group name under Group Indirect Expense
                IESubGroupsData = self.con.execute(
                    "select groupcode,groupname from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where groupname = 'Indirect Expense' and orgcode = %d)"
                    % (orgcode, orgcode)
                )
                IESubGroups = IESubGroupsData.fetchall()
                for IESub in IESubGroups:
                    # Start looping with the subgroup in hand,
                    # and get it's list of accounts.
                    IESubAccsData = self.con.execute(
                        select([accounts.c.accountcode, accounts.c.accountname]).where(
                            and_(
                                accounts.c.orgcode == orgcode,
                                accounts.c.groupcode == IESub["groupcode"],
                            )
                        )
                    )
                    if IESubAccsData.rowcount > 0:
                        IESubAccs = IESubAccsData.fetchall()
                        IESUBDict = {}
                        IESubBal = 0.00
                        for iesubacc in IESubAccs:
                            calbalData = calculateBalance(
                                self.con,
                                iesubacc["accountcode"],
                                calculateFrom,
                                calculateFrom,
                                calculateTo,
                            )
                            if calbalData["curbal"] == 0.00:
                                continue
                            if calbalData["baltype"] == "Dr":
                                IESUBDict[iesubacc["accountname"]] = "%.2f" % (
                                    float(calbalData["curbal"])
                                )
                                IESubBal = IESubBal + float(calbalData["curbal"])
                            if calbalData["baltype"] == "Cr":
                                IESUBDict[iesubacc["accountname"]] = "%.2f" % (
                                    -float(calbalData["curbal"])
                                )
                                IESubBal = IESubBal - float(calbalData["curbal"])
                        # This is balance of sub group
                        IESUBDict["balance"] = "%.2f" % (float(IESubBal))
                        # This is balance of main group
                        grpIEbalance = grpIEbalance + float(IESubBal)
                        indirectExpense[IESub["groupname"]] = IESUBDict
                    else:
                        continue

                # Now consider those accounts which are directly created under Direct Expense group
                getIEAccData = self.con.execute(
                    "select accountname,accountcode from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where groupname = 'Indirect Expense' and orgcode = %d)"
                    % (orgcode, orgcode)
                )
                if getIEAccData.rowcount > 0:
                    ieAccData = getIEAccData.fetchall()
                    for ieAcc in ieAccData:
                        calbalData = calculateBalance(
                            self.con,
                            ieAcc["accountcode"],
                            calculateFrom,
                            calculateFrom,
                            calculateTo,
                        )
                        if calbalData["curbal"] == 0.00:
                            continue
                        if calbalData["baltype"] == "Dr":
                            indirectExpense[ieAcc["accountname"]] = "%.2f" % (
                                float(calbalData["curbal"])
                            )
                            grpIEbalance = grpIEbalance + float(calbalData["curbal"])
                        if calbalData["baltype"] == "Cr":
                            indirectExpense[ieAcc["accountname"]] = "%.2f" % (
                                -float(calbalData["curbal"])
                            )
                            grpIEbalance = grpIEbalance - float(calbalData["curbal"])
                indirectExpense["indirexpbal"] = "%.2f" % (float(grpIEbalance))
                result["Indirect Expense"] = indirectExpense

                # Calculation for Indirect Income
                # Same procedure as Direct Expense.
                IISubGroupsData = self.con.execute(
                    "select groupcode,groupname from groupsubgroups where orgcode = %d and subgroupof = (select groupcode from groupsubgroups where groupname = 'Indirect Income' and orgcode = %d)"
                    % (orgcode, orgcode)
                )
                IISubGroups = IISubGroupsData.fetchall()
                # now we have list of subgroups under Indirect Income.
                # We will loop through each and get list of their accounts.
                for IISub in IISubGroups:
                    # Start looping with the subgroup in hand,
                    # and get it's list of accounts.
                    IISubAccsData = self.con.execute(
                        select([accounts.c.accountcode, accounts.c.accountname]).where(
                            and_(
                                accounts.c.orgcode == orgcode,
                                accounts.c.groupcode == IISub["groupcode"],
                            )
                        )
                    )
                    if IISubAccsData.rowcount > 0:
                        IISubAccs = IISubAccsData.fetchall()
                        IISUBDict = {}
                        IISubBal = 0.00

                        for iisubacc in IISubAccs:
                            calbalData = calculateBalance(
                                self.con,
                                iisubacc["accountcode"],
                                calculateFrom,
                                calculateFrom,
                                calculateTo,
                            )
                            if calbalData["curbal"] == 0.00:
                                continue
                            if calbalData["baltype"] == "Cr":
                                IISUBDict[disubacc["accountname"]] = "%.2f" % (
                                    float(calbalData["curbal"])
                                )
                                IISubBal = IISubBal + float(calbalData["curbal"])
                            if calbalData["baltype"] == "Dr":
                                IISUBDict[disubacc["accountname"]] = "%.2f" % (
                                    -float(calbalData["curbal"])
                                )
                                IISubBal = IISubBal - float(calbalData["curbal"])

                        # This is balance of sub group
                        IISUBDict["balance"] = "%.2f" % (float(IISubBal))
                        # This is balance of main group
                        grpIIbalance = grpIIbalance + float(IISubBal)
                        indirectIncome[IISub["groupname"]] = IISUBDict

                getIIAccData = self.con.execute(
                    "select accountname,accountcode from accounts where orgcode = %d and groupcode = (select groupcode from groupsubgroups where groupname = 'Indirect Income' and orgcode = %d)"
                    % (orgcode, orgcode)
                )
                if getDIAccData.rowcount > 0:
                    iiAccData = getIIAccData.fetchall()
                    for iiAcc in iiAccData:
                        calbalData = calculateBalance(
                            self.con,
                            iiAcc["accountcode"],
                            calculateFrom,
                            calculateFrom,
                            calculateTo,
                        )
                        if calbalData["curbal"] == 0.00:
                            continue
                        if calbalData["baltype"] == "Cr":
                            indirectIncome[iiAcc["accountname"]] = "%.2f" % (
                                float(calbalData["curbal"])
                            )
                            grpIIbalance = grpIIbalance + float(calbalData["curbal"])
                        if calbalData["baltype"] == "Dr":
                            indirectIncome[iiAcc["accountname"]] = "%.2f" % (
                                -float(calbalData["curbal"])
                            )
                            grpIIbalance = grpIIbalance - float(calbalData["curbal"])

                indirectIncome["indirincmbal"] = "%.2f" % (float(grpIIbalance))
                result["Indirect Income"] = indirectIncome

                # Calculate difference between Indirect Income & Indirect Expense.
                grsI = grpIIbalance - grpIEbalance

                # Calculate Profit and Loss
                if "grossprofitcf" in result:
                    result["netprofit"] = "%.2f" % (
                        float(result["grossprofitcf"])
                        + float(grpIIbalance)
                        - float(grpIEbalance)
                    )
                    result["Total"] = "%.2f" % (
                        float(result["netprofit"]) + float(grpIEbalance)
                    )
                else:
                    result["netloss"] = "%.2f" % (
                        float(result["grosslosscf"])
                        + float(grpIIbalance)
                        - float(grpIEbalance)
                    )
                    result["Total"] = "%.2f" % (
                        float(result["netloss"]) + float(grpIEbalance)
                    )

                # income = grpDIbalance + grpIIbalance + closingStockBal
                # net profit = grossprofit + indirectincome - grpIEbalance
                # income = grpDIbalance + grpIIbalance + result["Closing Stock"]["total"]
                # expense = grpDEbalance + grpIEbalance
                # if income > expense:
                #     netProfit = income - expense
                #     result["netprofit"] = "%.2f" % (float(netProfit))
                #     result["Total"] = "%.2f" % (float(income))
                # else:
                #     netLoss = expense - income
                #     result["netloss"] = "%.2f" % (float(netLoss))
                #     result["Total"] = "%.2f" % (float(expense))

                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": result}

            except:
                print(traceback.format_exc())
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=deletedvoucher", renderer="json")
    def getdeletedVoucher(self):
        """
        this function is called when type=deletedvoucher is passed to the url /report
        it returns a grid containing details of all the deleted vouchers
        it first checks the userrole then fetches the data from voucherbin puts into a list.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            # try:
            self.con = eng.connect()
            orgcode = authDetails["orgcode"]
            orgcode = int(orgcode)
            userRoleData = getUserRole(authDetails["userid"], authDetails["orgcode"])
            userrole = userRoleData["gkresult"]["userrole"]
            vouchers = []
            if userrole == -1 or userrole == 0:
                if "orderflag" in self.request.params:
                    voucherRow = self.con.execute(
                        select([voucherbin])
                        .where(voucherbin.c.orgcode == orgcode)
                        .order_by(
                            desc(voucherbin.c.voucherdate), voucherbin.c.vouchercode
                        )
                    )
                else:
                    voucherRow = self.con.execute(
                        select([voucherbin])
                        .where(voucherbin.c.orgcode == orgcode)
                        .order_by(voucherbin.c.voucherdate, voucherbin.c.vouchercode)
                    )
                voucherData = voucherRow.fetchall()
                for voucher in voucherData:
                    vouchers.append(
                        {
                            "vouchercode": voucher["vouchercode"],
                            "vouchernumber": voucher["vouchernumber"],
                            "voucherdate": datetime.strftime(
                                voucher["voucherdate"], "%d-%m-%Y"
                            ),
                            "narration": voucher["narration"],
                            "drs": voucher["drs"],
                            "crs": voucher["crs"],
                            "vouchertype": voucher["vouchertype"],
                            "projectname": voucher["projectname"],
                        }
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": vouchers}
            else:
                self.con.close()
                return {"gkstatus": enumdict["BadPrivilege"]}
        # except:
        #    self.con.close()
        #    return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(request_param="type=stockreport", renderer="json")
    def stockReport(self):
        """
        Purpose:
        Return the structured data grid of stock report for given product.
        Input will be productcode,startdate,enddate.
        orgcode will be taken from header and startdate and enddate of fianancial year taken from organisation table .
        returns a list of dictionaries where every dictionary will be one row.
        description:
        This function returns the complete stock report,
        including opening stock every inward and outward quantity and running balance for every transaction along with transaction type.
        at the end we get total inward and outward quantity.
        This report will be on the basis of productcode, startdate and enddate given from the client.
        The orgcode is taken from the header.
        The report will query database to get all in and out records for the given product where the dcinvtn flag is not 20.
        For every iteration of this list with a for loop we will find out the date of transaction from the delchal or invoice table depending on the flag being 4 or 9.
        Cash memo is in the invoice table so even 3 will qualify.
        Then we wil find the customer or supplyer name on the basis of given data.
        Note that if the startdate is same as the yearstart of the organisation then opening stock can be directly taken from the product table.
        if it is later than the startyear then we will have to come to the closing balance of the day before startdate given by client and use it as the opening balance.
        The row will be represented in this grid with every key denoting a column.
        The columns (keys) will be,
        date,particulars,invoice/dcno, transaction type (invoice /delchal),inward quantity,outward quantity ,total inward quantity , total outwrd quanity and balance.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                orgcode = authDetails["orgcode"]
                productCode = self.request.params["productcode"]
                startDate = datetime.strptime(
                    str(self.request.params["startdate"]), "%Y-%m-%d"
                )
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stockReport = []
                totalinward = 0.00
                totaloutward = 0.00
                openingStockResult = self.con.execute(
                    select([product.c.openingstock]).where(
                        and_(
                            product.c.productcode == productCode,
                            product.c.orgcode == orgcode,
                        )
                    )
                )
                osRow = openingStockResult.fetchone()
                openingStock = osRow["openingstock"]
                stockRecords = self.con.execute(
                    select([stock])
                    .where(
                        and_(
                            stock.c.productcode == productCode,
                            stock.c.orgcode == orgcode,
                            or_(
                                stock.c.dcinvtnflag != 20,
                                stock.c.dcinvtnflag != 40,
                                stock.c.dcinvtnflag != 30,
                                stock.c.dcinvtnflag != 90,
                            ),
                        )
                    )
                    .order_by(stock.c.stockdate)
                )
                stockData = stockRecords.fetchall()
                ysData = self.con.execute(
                    select([organisation.c.yearstart]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                ysRow = ysData.fetchone()
                yearStart = datetime.strptime(str(ysRow["yearstart"]), "%Y-%m-%d")
                enData = self.con.execute(
                    select([organisation.c.yearend]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                enRow = enData.fetchone()
                yearend = datetime.strptime(str(enRow["yearend"]), "%Y-%m-%d")
                if startDate > yearStart:
                    for stockRow in stockData:
                        if stockRow["dcinvtnflag"] == 3 or stockRow["dcinvtnflag"] == 9:
                            countresult = self.con.execute(
                                select(
                                    [func.count(invoice.c.invid).label("inv")]
                                ).where(
                                    and_(
                                        invoice.c.invoicedate >= yearStart,
                                        invoice.c.invoicedate < startDate,
                                        invoice.c.invid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["inv"] == 1:
                                if stockRow["inout"] == 9:
                                    openingStock = float(openingStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    openingStock = float(openingStock) - float(
                                        stockRow["qty"]
                                    )
                        if stockRow["dcinvtnflag"] == 4:
                            countresult = self.con.execute(
                                select([func.count(delchal.c.dcid).label("dc")]).where(
                                    and_(
                                        delchal.c.dcdate >= yearStart,
                                        delchal.c.dcdate < startDate,
                                        delchal.c.dcid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["dc"] == 1:
                                if stockRow["inout"] == 9:
                                    openingStock = float(openingStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    openingStock = float(openingStock) - float(
                                        stockRow["qty"]
                                    )
                        if stockRow["dcinvtnflag"] == 18:
                            if stockRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    stockRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    stockRow["qty"]
                                )
                            if stockRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    stockRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    stockRow["qty"]
                                )
                        if stockRow["dcinvtnflag"] == 7:
                            countresult = self.con.execute(
                                select([func.count(drcr.c.drcrid).label("dc")]).where(
                                    and_(
                                        drcr.c.drcrdate >= yearStart,
                                        drcr.c.drcrdate < startDate,
                                        drcr.c.drcrid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["dc"] == 1:
                                if stockRow["inout"] == 9:
                                    openingStock = float(openingStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    openingStock = float(openingStock) - float(
                                        stockRow["qty"]
                                    )
                stockReport.append(
                    {
                        "date": "",
                        "particulars": "opening stock",
                        "trntype": "",
                        "dcid": "",
                        "dcno": "",
                        "drcrno": "",
                        "drcrid": "",
                        "invid": "",
                        "invno": "",
                        "rnid": "",
                        "rnno": "",
                        "inward": "%.2f" % float(openingStock),
                    }
                )
                totalinward = totalinward + float(openingStock)
                for finalRow in stockData:
                    if finalRow["dcinvtnflag"] == 3 or finalRow["dcinvtnflag"] == 9:
                        countresult = self.con.execute(
                            select(
                                [
                                    invoice.c.invoicedate,
                                    invoice.c.invoiceno,
                                    invoice.c.custid,
                                ]
                            ).where(
                                and_(
                                    invoice.c.invoicedate >= startDate,
                                    invoice.c.invoicedate <= endDate,
                                    invoice.c.invid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()

                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == countrow["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            if custrow != None:
                                custnamedata = custrow["custname"]
                            else:
                                custnamedata = "Cash Memo"
                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["invoicedate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custnamedata,
                                        "trntype": "invoice",
                                        "dcid": "",
                                        "dcno": "",
                                        "drcrno": "",
                                        "drcrid": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": finalRow["dcinvtnid"],
                                        "invno": countrow["invoiceno"],
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["invoicedate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custnamedata,
                                        "trntype": "invoice",
                                        "dcid": "",
                                        "dcno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": finalRow["dcinvtnid"],
                                        "invno": countrow["invoiceno"],
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )

                    if finalRow["dcinvtnflag"] == 4:
                        countresult = self.con.execute(
                            select(
                                [delchal.c.dcdate, delchal.c.dcno, delchal.c.custid]
                            ).where(
                                and_(
                                    delchal.c.dcdate >= startDate,
                                    delchal.c.dcdate <= endDate,
                                    delchal.c.dcid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()

                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == countrow["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            dcinvresult = self.con.execute(
                                select([dcinv.c.invid]).where(
                                    dcinv.c.dcid == finalRow["dcinvtnid"]
                                )
                            )
                            if dcinvresult.rowcount == 1:
                                dcinvrow = dcinvresult.fetchone()
                                invresult = self.con.execute(
                                    select(
                                        [invoice.c.invoiceno, invoice.c.icflag]
                                    ).where(invoice.c.invid == dcinvrow["invid"])
                                )
                                """ No need to check if invresult has rowcount 1 since it must be 1 """
                                invrow = invresult.fetchone()
                                trntype = "delchal&invoice"
                            else:
                                dcinvrow = {"invid": ""}
                                invrow = {"invoiceno": "", "icflag": ""}
                                trntype = "delchal"

                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["dcdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "dcid": finalRow["dcinvtnid"],
                                        "dcno": countrow["dcno"],
                                        "drcrno": "",
                                        "drcrid": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": dcinvrow["invid"],
                                        "invno": invrow["invoiceno"],
                                        "icflag": invrow["icflag"],
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["dcdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "dcid": finalRow["dcinvtnid"],
                                        "dcno": countrow["dcno"],
                                        "drcrno": "",
                                        "drcrid": "",
                                        "invid": dcinvrow["invid"],
                                        "invno": invrow["invoiceno"],
                                        "icflag": invrow["icflag"],
                                        "rnid": "",
                                        "rnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )

                    if finalRow["dcinvtnflag"] == 18:
                        countresult = self.con.execute(
                            select(
                                [
                                    rejectionnote.c.rndate,
                                    rejectionnote.c.rnno,
                                    rejectionnote.c.dcid,
                                    rejectionnote.c.invid,
                                ]
                            ).where(
                                and_(
                                    rejectionnote.c.rndate >= startDate,
                                    rejectionnote.c.rndate <= endDate,
                                    rejectionnote.c.rnid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            if countrow["dcid"] != None:
                                custdata = self.con.execute(
                                    select([customerandsupplier.c.custname]).where(
                                        customerandsupplier.c.custid
                                        == (
                                            select([delchal.c.custid]).where(
                                                delchal.c.dcid == countrow["dcid"]
                                            )
                                        )
                                    )
                                )
                            elif countrow["invid"] != None:
                                custdata = self.con.execute(
                                    select([customerandsupplier.c.custname]).where(
                                        customerandsupplier.c.custid
                                        == (
                                            select([invoice.c.custid]).where(
                                                invoice.c.invid == countrow["invid"]
                                            )
                                        )
                                    )
                                )
                            custrow = custdata.fetchone()
                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["rndate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": "Rejection Note",
                                        "rnid": finalRow["dcinvtnid"],
                                        "rnno": countrow["rnno"],
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["rndate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": "Rejection Note",
                                        "rnid": finalRow["dcinvtnid"],
                                        "rnno": countrow["rnno"],
                                        "dcno": "",
                                        "drcrno": "",
                                        "drcrid": "",
                                        "invid": "",
                                        "invno": "",
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                    if finalRow["dcinvtnflag"] == 7:
                        countresult = self.con.execute(
                            select(
                                [
                                    drcr.c.drcrdate,
                                    drcr.c.drcrno,
                                    drcr.c.invid,
                                    drcr.c.dctypeflag,
                                ]
                            ).where(
                                and_(
                                    drcr.c.drcrdate >= startDate,
                                    drcr.c.drcrdate <= endDate,
                                    drcr.c.drcrid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            drcrinvdata = self.con.execute(
                                select([invoice.c.custid]).where(
                                    invoice.c.invid == countrow["invid"]
                                )
                            )
                            drcrinv = drcrinvdata.fetchone()
                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == drcrinv["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            if int(countrow["dctypeflag"] == 3):
                                trntype = "Credit Note"
                            else:
                                trntype = "Debit Note"
                            if finalRow["inout"] == 9:
                                openingStock = float(openingStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["drcrdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "drcrid": finalRow["dcinvtnid"],
                                        "drcrno": countrow["drcrno"],
                                        "dcno": "",
                                        "dcid": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": "",
                                        "invno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                openingStock = float(openingStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["drcrdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "drcrid": finalRow["dcinvtnid"],
                                        "drcrno": countrow["drcrno"],
                                        "dcid": "",
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(openingStock),
                                    }
                                )

                stockReport.append(
                    {
                        "date": "",
                        "particulars": "Total",
                        "dcid": "",
                        "dcno": "",
                        "invid": "",
                        "invno": "",
                        "rnid": "",
                        "rnno": "",
                        "drcrno": "",
                        "drcrid": "",
                        "trntype": "",
                        "totalinwardqty": "%.2f" % float(totalinward),
                        "totaloutwardqty": "%.2f" % float(totaloutward),
                    }
                )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": stockReport}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="product-register", renderer="json")
    def godownStockReport(self):
        """
        Purpose:
        Return the structured data grid of stock report for given product.
        Input will be productcode,startdate,enddate and goid.
        orgcode will be taken from header and startdate and enddate of fianancial year taken from organisation table .
        returns a list of dictionaries where every dictionary will be one row.
        description:
        This function returns the complete stock report,
        including opening stock every inward and outward quantity and running balance for every transaction along with transaction type for a selected product and godown.
        at the end we get total inward and outward quantity.
        This report will be on the basis of productcode, startdate and enddate given from the client.
        The orgcode is taken from the header.
        The report will query database to get all in and out records for the given product where the dcinvtn flag is not 20.
        For every iteration of this list with a for loop we will find out the date of transaction from the delchal or invoice table depending on the flag being 4 or 9.
        Cash memo is in the invoice table so even 3 will qualify.
        Then we wil find the customer or supplyer name on the basis of given data.
        Note that if the startdate is same as the yearstart of the organisation then opening stock can be directly taken from the product table.
        if it is later than the startyear then we will have to come to the closing balance of the day before startdate given by client and use it as the opening balance.
        The row will be represented in this grid with every key denoting a column.
        The columns (keys) will be,
        date,particulars,invoice/dcno, transaction type (invoice /delchal),inward quantity,outward quantity ,total inward quantity , total outwrd quanity and balance.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                orgcode = authDetails["orgcode"]
                productCode = self.request.params["productcode"]
                godownCode = self.request.params["goid"]
                startDate = datetime.strptime(
                    str(self.request.params["startdate"]), "%Y-%m-%d"
                )
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stockReport = []
                totalinward = 0.00
                totaloutward = 0.00
                openingStock = 0.00
                goopeningStockResult = self.con.execute(
                    select([goprod.c.goopeningstock]).where(
                        and_(
                            goprod.c.productcode == productCode,
                            goprod.c.goid == godownCode,
                            goprod.c.orgcode == orgcode,
                        )
                    )
                )
                gosRow = goopeningStockResult.fetchone()
                if gosRow != None:
                    gopeningStock = gosRow["goopeningstock"]
                else:
                    gopeningStock = 0.00
                stockRecords = self.con.execute(
                    select([stock])
                    .where(
                        and_(
                            stock.c.productcode == productCode,
                            stock.c.goid == godownCode,
                            stock.c.orgcode == orgcode,
                            or_(
                                stock.c.dcinvtnflag != 40,
                                stock.c.dcinvtnflag != 30,
                                stock.c.dcinvtnflag != 90,
                            ),
                        )
                    )
                    .order_by(stock.c.stockdate)
                )
                stockData = stockRecords.fetchall()
                ysData = self.con.execute(
                    select([organisation.c.yearstart]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                ysRow = ysData.fetchone()
                yearStart = datetime.strptime(str(ysRow["yearstart"]), "%Y-%m-%d")
                enData = self.con.execute(
                    select([organisation.c.yearend]).where(
                        organisation.c.orgcode == orgcode
                    )
                )
                enRow = enData.fetchone()
                yearend = datetime.strptime(str(enRow["yearend"]), "%Y-%m-%d")
                if startDate > yearStart:
                    for stockRow in stockData:
                        if stockRow["dcinvtnflag"] == 4:
                            # delivery note
                            countresult = self.con.execute(
                                select([func.count(delchal.c.dcid).label("dc")]).where(
                                    and_(
                                        delchal.c.dcdate >= yearStart,
                                        delchal.c.dcdate < startDate,
                                        delchal.c.dcid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["dc"] == 1:
                                if stockRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        stockRow["qty"]
                                    )
                        if stockRow["dcinvtnflag"] == 20:
                            # transfer note
                            countresult = self.con.execute(
                                select(
                                    [
                                        func.count(transfernote.c.transfernoteid).label(
                                            "tn"
                                        )
                                    ]
                                ).where(
                                    and_(
                                        transfernote.c.transfernotedate >= yearStart,
                                        transfernote.c.transfernotedate < startDate,
                                        transfernote.c.transfernoteid
                                        == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["tn"] == 1:
                                if stockRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        stockRow["qty"]
                                    )
                        if stockRow["dcinvtnflag"] == 18:
                            # Rejection Note
                            if stockRow["inout"] == 9:
                                gopeningstock = float(gopeningstock) + float(
                                    stockRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    stockRow["qty"]
                                )
                            if stockRow["inout"] == 15:
                                gopeningstock = float(gopeningstock) - float(
                                    stockRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    stockRow["qty"]
                                )
                        if stockRow["dcinvtnflag"] == 7:
                            # Debit Credit Note
                            countresult = self.con.execute(
                                select([func.count(drcr.c.drcrid).label("dc")]).where(
                                    and_(
                                        drcr.c.drcrdate >= yearStart,
                                        drcr.c.drcrdate < startDate,
                                        drcr.c.drcrid == stockRow["dcinvtnid"],
                                    )
                                )
                            )
                            countrow = countresult.fetchone()
                            if countrow["dc"] == 1:
                                if stockRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        stockRow["qty"]
                                    )
                                if stockRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        stockRow["qty"]
                                    )
                stockReport.append(
                    {
                        "date": "",
                        "particulars": "opening stock",
                        "trntype": "",
                        "dcid": "",
                        "dcno": "",
                        "invid": "",
                        "invno": "",
                        "tnid": "",
                        "tnno": "",
                        "rnid": "",
                        "rnno": "",
                        "inward": "%.2f" % float(gopeningStock),
                    }
                )
                totalinward = totalinward + float(gopeningStock)

                for finalRow in stockData:
                    if finalRow["dcinvtnflag"] == 4:
                        countresult = self.con.execute(
                            select(
                                [delchal.c.dcdate, delchal.c.dcno, delchal.c.custid]
                            ).where(
                                and_(
                                    delchal.c.dcdate >= startDate,
                                    delchal.c.dcdate <= endDate,
                                    delchal.c.dcid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == countrow["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            dcinvresult = self.con.execute(
                                select([dcinv.c.invid]).where(
                                    dcinv.c.dcid == finalRow["dcinvtnid"]
                                )
                            )
                            if dcinvresult.rowcount == 1:
                                dcinvrow = dcinvresult.fetchone()
                                invresult = self.con.execute(
                                    select(
                                        [invoice.c.invoiceno, invoice.c.icflag]
                                    ).where(invoice.c.invid == dcinvrow["invid"])
                                )
                                """ No need to check if invresult has rowcount 1 since it must be 1 """
                                invrow = invresult.fetchone()
                                trntype = "delchal&invoice"
                            else:
                                dcinvrow = {"invid": ""}
                                invrow = {"invoiceno": "", "icflag": ""}
                                trntype = "delchal"

                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["dcdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "dcid": finalRow["dcinvtnid"],
                                        "dcno": countrow["dcno"],
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": dcinvrow["invid"],
                                        "invno": invrow["invoiceno"],
                                        "icflag": invrow["icflag"],
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["dcdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "dcid": finalRow["dcinvtnid"],
                                        "dcno": countrow["dcno"],
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": dcinvrow["invid"],
                                        "invno": invrow["invoiceno"],
                                        "icflag": invrow["icflag"],
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                    if finalRow["dcinvtnflag"] == 20:
                        countresult = self.con.execute(
                            select(
                                [
                                    transfernote.c.transfernotedate,
                                    transfernote.c.transfernoteno,
                                ]
                            ).where(
                                and_(
                                    transfernote.c.transfernotedate >= startDate,
                                    transfernote.c.transfernotedate <= endDate,
                                    transfernote.c.transfernoteid
                                    == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(
                                                    countrow["transfernotedate"].date()
                                                ),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": "",
                                        "trntype": "transfer note",
                                        "dcid": "",
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "tnid": finalRow["dcinvtnid"],
                                        "tnno": countrow["transfernoteno"],
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(
                                                    countrow["transfernotedate"].date()
                                                ),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": "",
                                        "trntype": "transfer note",
                                        "dcid": "",
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "tnid": finalRow["dcinvtnid"],
                                        "tnno": countrow["transfernoteno"],
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )

                    if finalRow["dcinvtnflag"] == 18:
                        countresult = self.con.execute(
                            select(
                                [
                                    rejectionnote.c.rndate,
                                    rejectionnote.c.rnno,
                                    rejectionnote.c.dcid,
                                    rejectionnote.c.invid,
                                ]
                            ).where(
                                and_(
                                    rejectionnote.c.rndate >= startDate,
                                    rejectionnote.c.rndate <= endDate,
                                    rejectionnote.c.rnid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            if countrow["dcid"] != None:
                                custdata = self.con.execute(
                                    select([customerandsupplier.c.custname]).where(
                                        customerandsupplier.c.custid
                                        == (
                                            select([delchal.c.custid]).where(
                                                delchal.c.dcid == countrow["dcid"]
                                            )
                                        )
                                    )
                                )
                            elif countrow["invid"] != None:
                                custdata = self.con.execute(
                                    select([customerandsupplier.c.custname]).where(
                                        customerandsupplier.c.custid
                                        == (
                                            select([invoice.c.custid]).where(
                                                invoice.c.invid == countrow["invid"]
                                            )
                                        )
                                    )
                                )
                            custrow = custdata.fetchone()
                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["rndate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": "Rejection Note",
                                        "rnid": finalRow["dcinvtnid"],
                                        "rnno": countrow["rnno"],
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )
                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["rndate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": "Rejection Note",
                                        "rnid": finalRow["dcinvtnid"],
                                        "rnno": countrow["rnno"],
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "tnid": "",
                                        "tnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                    if finalRow["dcinvtnflag"] == 7:
                        countresult = self.con.execute(
                            select(
                                [
                                    drcr.c.drcrdate,
                                    drcr.c.drcrno,
                                    drcr.c.invid,
                                    drcr.c.dctypeflag,
                                ]
                            ).where(
                                and_(
                                    drcr.c.drcrdate >= startDate,
                                    drcr.c.drcrdate <= endDate,
                                    drcr.c.drcrid == finalRow["dcinvtnid"],
                                )
                            )
                        )
                        if countresult.rowcount == 1:
                            countrow = countresult.fetchone()
                            drcrinvdata = self.con.execute(
                                select([invoice.c.custid]).where(
                                    invoice.c.invid == countrow["invid"]
                                )
                            )
                            drcrinv = drcrinvdata.fetchone()
                            custdata = self.con.execute(
                                select([customerandsupplier.c.custname]).where(
                                    customerandsupplier.c.custid == drcrinv["custid"]
                                )
                            )
                            custrow = custdata.fetchone()
                            if int(countrow["dctypeflag"] == 3):
                                trntype = "Credit Note"
                            else:
                                trntype = "Debit Note"
                            if finalRow["inout"] == 9:
                                gopeningStock = float(gopeningStock) + float(
                                    finalRow["qty"]
                                )
                                totalinward = float(totalinward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["drcrdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "drcrid": finalRow["dcinvtnid"],
                                        "drcrno": countrow["drcrno"],
                                        "dcno": "",
                                        "dcid": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "invid": "",
                                        "invno": "",
                                        "inwardqty": "%.2f" % float(finalRow["qty"]),
                                        "outwardqty": "",
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )
                            if finalRow["inout"] == 15:
                                gopeningStock = float(gopeningStock) - float(
                                    finalRow["qty"]
                                )
                                totaloutward = float(totaloutward) + float(
                                    finalRow["qty"]
                                )

                                stockReport.append(
                                    {
                                        "date": datetime.strftime(
                                            datetime.strptime(
                                                str(countrow["drcrdate"].date()),
                                                "%Y-%m-%d",
                                            ).date(),
                                            "%d-%m-%Y",
                                        ),
                                        "particulars": custrow["custname"],
                                        "trntype": trntype,
                                        "drcrid": finalRow["dcinvtnid"],
                                        "drcrno": countrow["drcrno"],
                                        "dcid": "",
                                        "dcno": "",
                                        "invid": "",
                                        "invno": "",
                                        "rnid": "",
                                        "rnno": "",
                                        "inwardqty": "",
                                        "outwardqty": "%.2f" % float(finalRow["qty"]),
                                        "balance": "%.2f" % float(gopeningStock),
                                    }
                                )

                stockReport.append(
                    {
                        "date": "",
                        "particulars": "Total",
                        "dcid": "",
                        "dcno": "",
                        "invid": "",
                        "invno": "",
                        "rnid": "",
                        "rnno": "",
                        "tnid": "",
                        "tnno": "",
                        "trntype": "",
                        "totalinwardqty": "%.2f" % float(totalinward),
                        "totaloutwardqty": "%.2f" % float(totaloutward),
                    }
                )
                return {"gkstatus": enumdict["Success"], "gkresult": stockReport}

                self.con.close()
            except:
                print(traceback.format_exc())
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="stockonhandreport", renderer="json")
    def stockOnHandReport(self):
        """
        Purpose:
        Return the structured data grid of stock report for given product.
        Input will be productcode,startdate,enddate.
        orgcode will be taken from header and enddate
        returns a list of dictionaries where every dictionary will be one row.
        description:
        This function returns the complete stock report,
        including opening stock every inward and outward quantity and running balance for every transaction along with transaction type.
        at the end we get total inward and outward quantity.
        This report will be on the basis of productcode, startdate and enddate given from the client.
        The orgcode is taken from the header.
        The report will query database to get all in and out records for the given product where the dcinvtn flag is not 20.
        For every iteration of this list with a for loop we will find out the date of transaction from the delchal or invoice table depending on the flag being 4 or 9.
        Cash memo is in the invoice table so even 3 will qualify.
        Then we wil find the customer or supplyer name on the basis of given data.
        Note that if the startdate is same as the yearstart of the organisation then opening stock can be directly taken from the product table.
        if it is later than the startyear then we will have to come to the closing balance of the day before startdate given by client and use it as the opening balance.
        The row will be represented in this grid with every key denoting a column.
        The columns (keys) will be,
        date,particulars,invoice/dcno, transaction type (invoice /delchal),inward quantity,outward quantity ,total inward quantity , total outwrd quanity and balance.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                orgcode = authDetails["orgcode"]
                productCode = self.request.params["productcode"]
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stockresult = stockonhandfun(orgcode, productCode, endDate)
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": stockresult["gkresult"],
                }
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="godownwisestockforgodownincharge", renderer="json")
    def godownwisestockforgodownincharge(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()

                orgcode = authDetails["orgcode"]

                startDate = ""

                if "startdate" in self.request.params:
                    startDate = datetime.strptime(
                        str(self.request.params["startdate"]), "%Y-%m-%d"
                    )

                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stocktype = self.request.params["type"]
                godownCode = int(self.request.params["goid"])

                prodcode = self.con.execute(
                    "select productcode as productcode from goprod where goid=%d and orgcode=%d"
                    % (godownCode, orgcode)
                )
                prodcodelist = prodcode.fetchall()

                if prodcodelist == None:
                    return {"gkstatus": enumdict["Success"], "gkresult": prodcodelist}
                else:
                    stocklist = []
                    prodcodedesclist = []
                    for productcode in prodcodelist:
                        productCode = productcode["productcode"]
                        result = godownwisestockonhandfun(
                            self.con,
                            orgcode,
                            startDate,
                            endDate,
                            stocktype,
                            productCode,
                            godownCode,
                        )
                        resultlist = result[0]["prodid"] = productCode
                        stocklist.append(result[0])

                    allprodstocklist = sorted(
                        stocklist, key=lambda x: float(x["balance"])
                    )[0:5]
                    for prodcode in allprodstocklist:
                        proddesc = self.con.execute(
                            "select productdesc as proddesc from product where productcode=%d"
                            % (prodcode["prodid"])
                        )
                        proddesclist = proddesc.fetchone()
                        prodcodedesclist.append(
                            {
                                "prodcode": prodcode["prodid"],
                                "proddesc": proddesclist["proddesc"],
                            }
                        )
                    self.con.close()
                    return {
                        "gkstatus": enumdict["Success"],
                        "gkresult": allprodstocklist,
                        "proddesclist": prodcodedesclist,
                    }
            except Exception as e:
                logging.warn(e)
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="godownwise_stock_value", renderer="json")
    def godownwise_stock_value(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()

                orgcode = authDetails["orgcode"]

                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                godownCode = int(self.request.params["goid"])
                productCode = int(self.request.params["productcode"])

                valueOnHand = calculateStockValue(
                    self.con, orgcode, endDate, productCode, godownCode
                )
                self.con.close()

                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": valueOnHand,
                }
            except:
                print(traceback.format_exc())
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="godownwisestockonhand", renderer="json")
    def godownStockHReport(self):
        """
        Purpose:
        Return the structured data grid of godown wise stock on hand report for given product.
        Input will be productcode,enddate and goid(for specific godown) also type(mention at last).
        orgcode will be taken from header .
        returns a list of dictionaries where every dictionary will be one row.
        description:
        This function returns the complete godown wise stock on hand report,
        including opening stock every inward and outward quantity and running balance  for  selected product and godown.
        at the end we get total inward and outward quantity and balance.
        godownwise opening stock can be taken from goprod table . and godown name can be taken from godown
        The report will query database to get all in and out records for the given product where the dcinvtn flag 4 & 20.
        For every iteration of this list with a for loop we will find out the date of transaction from the delchal or transfernote table depending on the flag being 4 or 20.
        closing balance of the day before startdate given by client and use it as the opening balance.
        The row will be represented in this grid with every key denoting a column.
        The columns (keys) will be,
        total inward quantity , total outwrd quanity and balance , product name ,godownname.

        *product and godown = pg
        *all product and all godown = apag
        *all product and single godown = apg
        *product and all godown = pag
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            self.con = eng.connect()
            try:
                #
                orgcode = authDetails["orgcode"]
                startDate = ""

                if "startdate" in self.request.params:
                    startDate = datetime.strptime(
                        str(self.request.params["startdate"]), "%Y-%m-%d"
                    )
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stocktype = self.request.params["type"]
                productCode = (
                    self.request.params["productcode"]
                    if "productcode" in self.request.params
                    else ""
                )

                if stocktype in ["pg", "apg"]:
                    godownCode = self.request.params["goid"]
                else:
                    godownCode = 0

                result = []
                if stocktype == "apg":
                    prows = self.con.execute(
                        select([product.c.productcode, product.c.productdesc]).where(
                            and_(
                                product.c.orgcode == orgcode,
                            )
                        )
                    )
                    products = prows.fetchall()
                    pmap = {}
                    for prod in products:
                        pmap[prod["productcode"]] = prod["productdesc"]

                    # gpc - godown product code
                    gpcrows = self.con.execute(
                        select([goprod.c.productcode]).where(
                            and_(
                                goprod.c.goid == godownCode,
                                goprod.c.orgcode == orgcode,
                            )
                        )
                    )
                    gpcodes = gpcrows.fetchall()
                    for gpcode in gpcodes:
                        pcode = gpcode["productcode"]
                        temp = godownwisestockonhandfun(
                            self.con,
                            orgcode,
                            startDate,
                            endDate,
                            "pg",
                            pcode,
                            godownCode,
                        )
                        if len(temp):
                            temp[0]["srno"] = len(result) + 1
                            temp[0]["productcode"] = pcode
                            temp[0]["productname"] = pmap[pcode]
                            result.append(temp[0])
                else:
                    result = godownwisestockonhandfun(
                        self.con,
                        orgcode,
                        startDate,
                        endDate,
                        stocktype,
                        productCode,
                        godownCode,
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": result}
            except Exception as e:
                # print(traceback.format_exc())
                # print(e)
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=categorywisestockonhand", renderer="json")
    def categorywiseStockOnHandReport(self):
        """
        Purpose:
        Return the structured data grid of stock report for all products in given category.
        Input will be categorycodecode, enddate.
        orgcode will be taken from header
        returns a list of dictionaries where every dictionary will be one row.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                goid = self.request.params["goid"]
                subcategorycode = self.request.params["subcategorycode"]
                speccode = self.request.params["speccode"]
                orgcode = authDetails["orgcode"]
                categorycode = self.request.params["categorycode"]
                endDate = datetime.strptime(
                    str(self.request.params["enddate"]), "%Y-%m-%d"
                )
                stockReport = []
                totalinward = 0.00
                totaloutward = 0.00
                """get its subcategories as well"""
                catdata = []
                # when there is some subcategory then get all N level categories of this category.
                if subcategorycode != "all":
                    catdata.append(int(subcategorycode))
                    for ccode in catdata:
                        result = self.con.execute(
                            select([categorysubcategories.c.categorycode]).where(
                                and_(
                                    categorysubcategories.c.orgcode == orgcode,
                                    categorysubcategories.c.subcategoryof == ccode,
                                )
                            )
                        )
                        result = result.fetchall()
                        for cat in result:
                            catdata.append(cat[0])
                # when subcategory is not there get all N level categories of main category.
                else:
                    catdata.append(int(categorycode))
                    for ccode in catdata:
                        result = self.con.execute(
                            select([categorysubcategories.c.categorycode]).where(
                                and_(
                                    categorysubcategories.c.orgcode == orgcode,
                                    categorysubcategories.c.subcategoryof == ccode,
                                )
                            )
                        )
                        result = result.fetchall()
                        for cat in result:
                            catdata.append(cat[0])
                # if godown wise report selected
                if goid != "-1" and goid != "all":
                    products = self.con.execute(
                        select(
                            [
                                goprod.c.goopeningstock.label("openingstock"),
                                product.c.productcode,
                                product.c.productdesc,
                            ]
                        ).where(
                            and_(
                                product.c.orgcode == orgcode,
                                goprod.c.orgcode == orgcode,
                                goprod.c.goid == int(goid),
                                product.c.productcode == goprod.c.productcode,
                                product.c.categorycode.in_(catdata),
                            )
                        )
                    )
                    prodDesc = products.fetchall()
                    srno = 1
                    for row in prodDesc:
                        totalinwardgo = 0.00
                        totaloutwardgo = 0.00
                        gopeningStock = row["openingstock"]
                        stockRecords = self.con.execute(
                            select([stock])
                            .where(
                                and_(
                                    stock.c.productcode == row["productcode"],
                                    stock.c.goid == int(goid),
                                    stock.c.orgcode == orgcode,
                                    or_(
                                        stock.c.dcinvtnflag != 40,
                                        stock.c.dcinvtnflag != 30,
                                        stock.c.dcinvtnflag != 90,
                                    ),
                                )
                            )
                            .order_by(stock.c.stockdate)
                        )
                        stockData = stockRecords.fetchall()
                        ysData = self.con.execute(
                            select([organisation.c.yearstart]).where(
                                organisation.c.orgcode == orgcode
                            )
                        )
                        ysRow = ysData.fetchone()
                        yearStart = datetime.strptime(
                            str(ysRow["yearstart"]), "%Y-%m-%d"
                        )
                        totalinwardgo = totalinwardgo + float(gopeningStock)
                        for finalRow in stockData:
                            if finalRow["dcinvtnflag"] == 4:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            delchal.c.dcdate,
                                            delchal.c.dcno,
                                            delchal.c.custid,
                                        ]
                                    ).where(
                                        and_(
                                            delchal.c.dcdate <= endDate,
                                            delchal.c.dcid == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    custdata = self.con.execute(
                                        select([customerandsupplier.c.custname]).where(
                                            customerandsupplier.c.custid
                                            == countrow["custid"]
                                        )
                                    )
                                    custrow = custdata.fetchone()
                                    dcinvresult = self.con.execute(
                                        select([dcinv.c.invid]).where(
                                            dcinv.c.dcid == finalRow["dcinvtnid"]
                                        )
                                    )
                                    if dcinvresult.rowcount == 1:
                                        dcinvrow = dcinvresult.fetchone()
                                        invresult = self.con.execute(
                                            select([invoice.c.invoiceno]).where(
                                                invoice.c.invid == dcinvrow["invid"]
                                            )
                                        )
                                        """ No need to check if invresult has rowcount 1 since it must be 1 """
                                        invrow = invresult.fetchone()
                                        trntype = "delchal&invoice"
                                    else:
                                        dcinvrow = {"invid": ""}
                                        invrow = {"invoiceno": ""}
                                        trntype = "delchal"
                                    if finalRow["inout"] == 9:
                                        gopeningStock = float(gopeningStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinwardgo = float(totalinwardgo) + float(
                                            finalRow["qty"]
                                        )

                                    if finalRow["inout"] == 15:
                                        gopeningStock = float(gopeningStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutward = float(totaloutwardgo) + float(
                                            finalRow["qty"]
                                        )
                            if finalRow["dcinvtnflag"] == 20:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            transfernote.c.transfernotedate,
                                            transfernote.c.transfernoteno,
                                        ]
                                    ).where(
                                        and_(
                                            transfernote.c.transfernotedate <= endDate,
                                            transfernote.c.transfernoteid
                                            == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    if finalRow["inout"] == 9:
                                        gopeningStock = float(gopeningStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinwardgo = float(totalinwardgo) + float(
                                            finalRow["qty"]
                                        )

                                    if finalRow["inout"] == 15:
                                        gopeningStock = float(gopeningStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutwardgo = float(totaloutwardgo) + float(
                                            finalRow["qty"]
                                        )
                            if finalRow["dcinvtnflag"] == 18:
                                if finalRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        finalRow["qty"]
                                    )
                                    totalinward = float(totalinward) + float(
                                        finalRow["qty"]
                                    )
                                if finalRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        finalRow["qty"]
                                    )
                                    totaloutward = float(totaloutward) + float(
                                        finalRow["qty"]
                                    )
                        stockReport.append(
                            {
                                "srno": srno,
                                "productname": row["productdesc"],
                                "totalinwardqty": "%.2f" % float(totalinwardgo),
                                "totaloutwardqty": "%.2f" % float(totaloutwardgo),
                                "balance": "%.2f" % float(gopeningStock),
                            }
                        )
                        srno += 1
                    self.con.close()
                    return {"gkstatus": enumdict["Success"], "gkresult": stockReport}
                # if godown wise report selected but all godowns selected
                elif goid == "all":
                    products = self.con.execute(
                        select(
                            [
                                goprod.c.goopeningstock.label("openingstock"),
                                goprod.c.goid,
                                product.c.productcode,
                                product.c.productdesc,
                            ]
                        ).where(
                            and_(
                                product.c.orgcode == orgcode,
                                goprod.c.orgcode == orgcode,
                                product.c.productcode == goprod.c.productcode,
                                product.c.categorycode.in_(catdata),
                            )
                        )
                    )
                    prodDesc = products.fetchall()
                    srno = 1
                    for row in prodDesc:
                        totalinwardgo = 0.00
                        totaloutwardgo = 0.00
                        gopeningStock = row["openingstock"]
                        godowns = self.con.execute(
                            select([godown.c.goname]).where(
                                and_(
                                    godown.c.goid == row["goid"],
                                    godown.c.orgcode == orgcode,
                                )
                            )
                        )
                        stockRecords = self.con.execute(
                            select([stock])
                            .where(
                                and_(
                                    stock.c.productcode == row["productcode"],
                                    stock.c.goid == int(row["goid"]),
                                    stock.c.orgcode == orgcode,
                                    or_(
                                        stock.c.dcinvtnflag != 40,
                                        stock.c.dcinvtnflag != 30,
                                        stock.c.dcinvtnflag != 90,
                                    ),
                                )
                            )
                            .order_by(stock.c.stockdate)
                        )
                        stockData = stockRecords.fetchall()
                        ysData = self.con.execute(
                            select([organisation.c.yearstart]).where(
                                organisation.c.orgcode == orgcode
                            )
                        )
                        ysRow = ysData.fetchone()
                        yearStart = datetime.strptime(
                            str(ysRow["yearstart"]), "%Y-%m-%d"
                        )
                        totalinwardgo = totalinwardgo + float(gopeningStock)
                        for finalRow in stockData:
                            if finalRow["dcinvtnflag"] == 4:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            delchal.c.dcdate,
                                            delchal.c.dcno,
                                            delchal.c.custid,
                                        ]
                                    ).where(
                                        and_(
                                            delchal.c.dcdate <= endDate,
                                            delchal.c.dcid == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    custdata = self.con.execute(
                                        select([customerandsupplier.c.custname]).where(
                                            customerandsupplier.c.custid
                                            == countrow["custid"]
                                        )
                                    )
                                    custrow = custdata.fetchone()
                                    dcinvresult = self.con.execute(
                                        select([dcinv.c.invid]).where(
                                            dcinv.c.dcid == finalRow["dcinvtnid"]
                                        )
                                    )
                                    if dcinvresult.rowcount == 1:
                                        dcinvrow = dcinvresult.fetchone()
                                        invresult = self.con.execute(
                                            select([invoice.c.invoiceno]).where(
                                                invoice.c.invid == dcinvrow["invid"]
                                            )
                                        )
                                        """ No need to check if invresult has rowcount 1 since it must be 1 """
                                        invrow = invresult.fetchone()
                                        trntype = "delchal&invoice"
                                    else:
                                        dcinvrow = {"invid": ""}
                                        invrow = {"invoiceno": ""}
                                        trntype = "delchal"
                                    if finalRow["inout"] == 9:
                                        gopeningStock = float(gopeningStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinwardgo = float(totalinwardgo) + float(
                                            finalRow["qty"]
                                        )

                                    if finalRow["inout"] == 15:
                                        gopeningStock = float(gopeningStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutward = float(totaloutwardgo) + float(
                                            finalRow["qty"]
                                        )
                            if finalRow["dcinvtnflag"] == 20:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            transfernote.c.transfernotedate,
                                            transfernote.c.transfernoteno,
                                        ]
                                    ).where(
                                        and_(
                                            transfernote.c.transfernotedate <= endDate,
                                            transfernote.c.transfernoteid
                                            == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    if finalRow["inout"] == 9:
                                        gopeningStock = float(gopeningStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinwardgo = float(totalinwardgo) + float(
                                            finalRow["qty"]
                                        )

                                    if finalRow["inout"] == 15:
                                        gopeningStock = float(gopeningStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutwardgo = float(totaloutwardgo) + float(
                                            finalRow["qty"]
                                        )

                            if finalRow["dcinvtnflag"] == 18:
                                if finalRow["inout"] == 9:
                                    gopeningStock = float(gopeningStock) + float(
                                        finalRow["qty"]
                                    )
                                    totalinward = float(totalinward) + float(
                                        finalRow["qty"]
                                    )
                                if finalRow["inout"] == 15:
                                    gopeningStock = float(gopeningStock) - float(
                                        finalRow["qty"]
                                    )
                                    totaloutward = float(totaloutward) + float(
                                        finalRow["qty"]
                                    )
                        stockReport.append(
                            {
                                "srno": srno,
                                "productname": row["productdesc"],
                                "godown": godowns.fetchone()["goname"],
                                "totalinwardqty": "%.2f" % float(totalinwardgo),
                                "totaloutwardqty": "%.2f" % float(totaloutwardgo),
                                "balance": "%.2f" % float(gopeningStock),
                            }
                        )
                        srno += 1
                    self.con.close()
                    return {"gkstatus": enumdict["Success"], "gkresult": stockReport}
                # No godown selected just categorywise stock on hand report
                else:
                    products = self.con.execute(
                        select(
                            [
                                product.c.openingstock,
                                product.c.productcode,
                                product.c.productdesc,
                            ]
                        ).where(
                            and_(
                                product.c.orgcode == orgcode,
                                product.c.categorycode.in_(catdata),
                            )
                        )
                    )
                    prodDesc = products.fetchall()
                    srno = 1
                    for row in prodDesc:
                        totalinward = 0.00
                        totaloutward = 0.00
                        openingStock = row["openingstock"]
                        productCd = row["productcode"]
                        prodName = row["productdesc"]
                        if goid != "-1" and goid != "all":
                            stockRecords = self.con.execute(
                                select([stock])
                                .where(
                                    and_(
                                        stock.c.productcode == productCd,
                                        stock.c.goid == int(goid),
                                        stock.c.orgcode == orgcode,
                                        or_(
                                            stock.c.dcinvtnflag != 40,
                                            stock.c.dcinvtnflag != 30,
                                            stock.c.dcinvtnflag != 90,
                                        ),
                                    )
                                )
                                .order_by(stock.c.stockdate)
                            )
                        else:
                            stockRecords = self.con.execute(
                                select([stock]).where(
                                    and_(
                                        stock.c.productcode == productCd,
                                        stock.c.orgcode == orgcode,
                                        or_(
                                            stock.c.dcinvtnflag != 20,
                                            stock.c.dcinvtnflag != 40,
                                            stock.c.dcinvtnflag != 30,
                                            stock.c.dcinvtnflag != 90,
                                        ),
                                    )
                                )
                            )
                        stockData = stockRecords.fetchall()
                        totalinward = totalinward + float(openingStock)
                        for finalRow in stockData:
                            if (
                                finalRow["dcinvtnflag"] == 3
                                or finalRow["dcinvtnflag"] == 9
                            ):
                                countresult = self.con.execute(
                                    select(
                                        [
                                            invoice.c.invoicedate,
                                            invoice.c.invoiceno,
                                            invoice.c.custid,
                                        ]
                                    ).where(
                                        and_(
                                            invoice.c.invoicedate <= endDate,
                                            invoice.c.invid == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    custdata = self.con.execute(
                                        select([customerandsupplier.c.custname]).where(
                                            customerandsupplier.c.custid
                                            == countrow["custid"]
                                        )
                                    )
                                    custrow = custdata.fetchone()
                                    if custrow != None:
                                        custnamedata = custrow["custname"]
                                    else:
                                        custnamedata = "Cash Memo"
                                    if finalRow["inout"] == 9:
                                        openingStock = float(openingStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinward = float(totalinward) + float(
                                            finalRow["qty"]
                                        )
                                    if finalRow["inout"] == 15:
                                        openingStock = float(openingStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutward = float(totaloutward) + float(
                                            finalRow["qty"]
                                        )

                            if finalRow["dcinvtnflag"] == 4:
                                countresult = self.con.execute(
                                    select(
                                        [
                                            delchal.c.dcdate,
                                            delchal.c.dcno,
                                            delchal.c.custid,
                                        ]
                                    ).where(
                                        and_(
                                            delchal.c.dcdate <= endDate,
                                            delchal.c.dcid == finalRow["dcinvtnid"],
                                        )
                                    )
                                )
                                if countresult.rowcount == 1:
                                    countrow = countresult.fetchone()
                                    custdata = self.con.execute(
                                        select([customerandsupplier.c.custname]).where(
                                            customerandsupplier.c.custid
                                            == countrow["custid"]
                                        )
                                    )
                                    custrow = custdata.fetchone()
                                    dcinvresult = self.con.execute(
                                        select([dcinv.c.invid]).where(
                                            dcinv.c.dcid == finalRow["dcinvtnid"]
                                        )
                                    )
                                    if dcinvresult.rowcount == 1:
                                        dcinvrow = dcinvresult.fetchone()
                                        invresult = self.con.execute(
                                            select([invoice.c.invoiceno]).where(
                                                invoice.c.invid == dcinvrow["invid"]
                                            )
                                        )
                                        """ No need to check if invresult has rowcount 1 since it must be 1 """
                                        invrow = invresult.fetchone()
                                        trntype = "delchal&invoice"
                                    else:
                                        dcinvrow = {"invid": ""}
                                        invrow = {"invoiceno": ""}
                                        trntype = "delchal"
                                    if finalRow["inout"] == 9:
                                        openingStock = float(openingStock) + float(
                                            finalRow["qty"]
                                        )
                                        totalinward = float(totalinward) + float(
                                            finalRow["qty"]
                                        )
                                    if finalRow["inout"] == 15:
                                        openingStock = float(openingStock) - float(
                                            finalRow["qty"]
                                        )
                                        totaloutward = float(totaloutward) + float(
                                            finalRow["qty"]
                                        )

                            if finalRow["dcinvtnflag"] == 18:
                                if finalRow["inout"] == 9:
                                    openingStock = float(openingStock) + float(
                                        finalRow["qty"]
                                    )
                                    totalinward = float(totalinward) + float(
                                        finalRow["qty"]
                                    )
                                if finalRow["inout"] == 15:
                                    openingStock = float(openingStock) - float(
                                        finalRow["qty"]
                                    )
                                    totaloutward = float(totaloutward) + float(
                                        finalRow["qty"]
                                    )

                        stockReport.append(
                            {
                                "srno": srno,
                                "productname": prodName,
                                "totalinwardqty": "%.2f" % float(totalinward),
                                "totaloutwardqty": "%.2f" % float(totaloutward),
                                "balance": "%.2f" % float(openingStock),
                            }
                        )
                        srno = srno + 1
                    return {"gkstatus": enumdict["Success"], "gkresult": stockReport}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="type=closingbalance", renderer="json")
    def closingBalance(self):
        """
        Purpose: returns the current balance and balance type for the given account as per the current date.
        description:
        This function takes the startedate and enddate (date of transaction) as well as accountcode.
        Returns the balance as on that date with the baltype.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                accountCode = self.request.params["accountcode"]
                financialStart = self.request.params["financialstart"]
                calculateTo = self.request.params["calculateto"]
                calbalData = calculateBalance(
                    self.con, accountCode, financialStart, financialStart, calculateTo
                )
                if calbalData["curbal"] == 0:
                    currentBalance = "%.2f" % float(calbalData["curbal"])
                else:
                    currentBalance = "%.2f (%s)" % (
                        float(calbalData["curbal"]),
                        calbalData["baltype"],
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": currentBalance}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=logbyorg", renderer="json")
    def logByOrg(self):
        """
        purpose: returns complete log statement for an organisation.
        Date range is taken from calculatefrom and calculateto.
        description:
        This function returns entire log statement for a given organisation.
        Date range is taken from client and orgcode from authdetails.
        Date sorted according to orderflag.
        If request params has orderflag then date sorted in descending order otherwise in ascending order.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                if "orderflag" in self.request.params:
                    result = self.con.execute(
                        select([log])
                        .where(
                            and_(
                                log.c.orgcode == authDetails["orgcode"],
                                log.c.time >= self.request.params["calculatefrom"],
                                log.c.time <= self.request.params["calculateto"],
                            )
                        )
                        .order_by(desc(log.c.time))
                    )
                else:
                    result = self.con.execute(
                        select([log])
                        .where(
                            and_(
                                log.c.orgcode == authDetails["orgcode"],
                                log.c.time >= self.request.params["calculatefrom"],
                                log.c.time <= self.request.params["calculateto"],
                            )
                        )
                        .order_by(log.c.time)
                    )
                logdata = []
                ROLES = {
                    -1: "Admin",
                    0: "Manager",
                    1: "Operator",
                    2: "Internal Auditor",
                    3: "Godown In Charge",
                }
                for row in result:
                    rowuser = self.con.execute(
                        "select username, orgs->'%s'->'userrole' as userrole from gkusers where userid = %d"
                        % (str(authDetails["orgcode"]), int(row["userid"]))
                    ).fetchone()
                    userrole = ROLES[rowuser["userrole"]]
                    logdata.append(
                        {
                            "logid": row["logid"],
                            "time": datetime.strftime(row["time"], "%d-%m-%Y"),
                            "activity": row["activity"],
                            "userid": row["userid"],
                            "username": rowuser["username"] + "(" + userrole + ")",
                        }
                    )

                return {"gkstatus": enumdict["Success"], "gkresult": logdata}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="type=logbyuser", renderer="json")
    def logByUser(self):
        """
        This function is the replica of the previous one except the log here is for a particular user.
        All parameter are same with the addition of userid."""
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                if "orderflag" in self.request.params:
                    result = self.con.execute(
                        select([log])
                        .where(
                            and_(
                                log.c.userid == self.request.params["userid"],
                                log.c.orgcode == authDetails["orgcode"],
                                log.c.time >= self.request.params["calculatefrom"],
                                log.c.time <= self.request.params["calculateto"],
                            )
                        )
                        .order_by(desc(log.c.time))
                    )
                else:
                    result = self.con.execute(
                        select([log])
                        .where(
                            and_(
                                log.c.userid == self.request.params["userid"],
                                log.c.orgcode == authDetails["orgcode"],
                                log.c.time >= self.request.params["calculatefrom"],
                                log.c.time <= self.request.params["calculateto"],
                            )
                        )
                        .order_by(log.c.time)
                    )
                logdata = []
                for row in result:
                    logdata.append(
                        {
                            "logid": row["logid"],
                            "time": datetime.strftime(row["time"], "%d-%m-%Y"),
                            "activity": row["activity"],
                        }
                    )
                return {"gkstatus": enumdict["Success"], "gkresult": logdata}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="type=del_unbilled", renderer="json")
    def unbilled_deliveries(self):
        """
        purpose:
        presents a list of deliverys which are unbilled  There are exceptions which should be excluded.
        free replacement or sample are those which are excluded.
                Token is the only required input.
                We also require Orgcode, but it is extracted from the token itself.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                orgcode = authDetails["orgcode"]
                if "inputdate" in self.request.params:
                    dataset = {
                        "inputdate": self.request.params["inputdate"],
                        "del_unbilled_type": self.request.params["del_unbilled_type"],
                    }
                else:
                    dataset = self.request.json_body
                inout = self.request.params["inout"]
                inputdate = dataset["inputdate"]
                del_unbilled_type = dataset["del_unbilled_type"]
                new_inputdate = dataset["inputdate"]
                new_inputdate = datetime.strptime(new_inputdate, "%Y-%m-%d")
                dc_unbilled = []
                # Adding the query here only, which will select the dcids either with "delivery-out" type or "delivery-in".
                if inout == "i":  # in
                    # distinct clause must be added to the query.
                    # delchal dcdate need to be added into select clause, since it is mentioned in order_by clause.
                    if del_unbilled_type == "0":
                        alldcids = self.con.execute(
                            select([delchal.c.dcid, delchal.c.dcdate])
                            .distinct()
                            .where(
                                and_(
                                    delchal.c.orgcode == orgcode,
                                    delchal.c.dcdate <= new_inputdate,
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 9,
                                    delchal.c.dcid == stock.c.dcinvtnid,
                                )
                            )
                            .order_by(delchal.c.dcdate)
                        )
                    else:
                        alldcids = self.con.execute(
                            select([delchal.c.dcid, delchal.c.dcdate])
                            .distinct()
                            .where(
                                and_(
                                    delchal.c.orgcode == orgcode,
                                    delchal.c.dcflag == int(del_unbilled_type),
                                    delchal.c.dcdate <= new_inputdate,
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 9,
                                    delchal.c.dcid == stock.c.dcinvtnid,
                                )
                            )
                            .order_by(delchal.c.dcdate)
                        )
                if inout == "o":  # out
                    # distinct clause must be added to the query.
                    # delchal dcdate need to be added into select clause, since it is mentioned in order_by clause.
                    if del_unbilled_type == "0":
                        alldcids = self.con.execute(
                            select([delchal.c.dcid, delchal.c.dcdate])
                            .distinct()
                            .where(
                                and_(
                                    delchal.c.orgcode == orgcode,
                                    delchal.c.dcdate <= new_inputdate,
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 15,
                                    delchal.c.dcid == stock.c.dcinvtnid,
                                )
                            )
                            .order_by(delchal.c.dcdate)
                        )
                    else:
                        alldcids = self.con.execute(
                            select([delchal.c.dcid, delchal.c.dcdate])
                            .distinct()
                            .where(
                                and_(
                                    delchal.c.orgcode == orgcode,
                                    delchal.c.dcflag == int(del_unbilled_type),
                                    delchal.c.dcdate <= new_inputdate,
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 15,
                                    delchal.c.dcid == stock.c.dcinvtnid,
                                )
                            )
                            .order_by(delchal.c.dcdate)
                        )
                alldcids = alldcids.fetchall()
                dcResult = []
                # ********* What if multiple delchals are covered by single invoice?*******************
                i = 0
                while i < len(alldcids):
                    dcid = alldcids[i]
                    invidresult = self.con.execute(
                        select([dcinv.c.invid]).where(
                            and_(
                                dcid[0] == dcinv.c.dcid,
                                dcinv.c.orgcode == orgcode,
                                invoice.c.orgcode == orgcode,
                                invoice.c.invid == dcinv.c.invid,
                                invoice.c.invoicedate <= new_inputdate,
                            )
                        )
                    )
                    invidresult = invidresult.fetchall()
                    if len(invidresult) == 0:
                        pass
                    else:
                        # invid's will be distinct only. So no problem to explicitly applying distinct clause.
                        if inout == "i":  # in
                            dcprodresult = self.con.execute(
                                select([stock.c.productcode, stock.c.qty]).where(
                                    and_(
                                        stock.c.orgcode == orgcode,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 9,
                                        dcid[0] == stock.c.dcinvtnid,
                                    )
                                )
                            )
                        if inout == "o":  # out
                            dcprodresult = self.con.execute(
                                select([stock.c.productcode, stock.c.qty]).where(
                                    and_(
                                        stock.c.orgcode == orgcode,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 15,
                                        dcid[0] == stock.c.dcinvtnid,
                                    )
                                )
                            )
                        dcprodresult = dcprodresult.fetchall()
                        # I am assuming :productcode must be distinct. So, I haven't applied distinct construct.
                        # what if dcprodresult or invprodresult is empty?
                        invprodresult = []
                        for invid in invidresult:
                            temp = self.con.execute(
                                select([invoice.c.contents]).where(
                                    and_(
                                        invoice.c.orgcode == orgcode,
                                        invid == invoice.c.invid,
                                    )
                                )
                            )
                            temp = temp.fetchall()
                            # Below two lines are intentionally repeated. It's not a mistake.
                            temp = temp[0]
                            temp = temp[0]
                            invprodresult.append(temp)
                        # Now we have to compare the two results: dcprodresult and invprodresult
                        # I assume that the delchal must have at most only one entry for a particular product. If not, then it's a bug and needs to be rectified.
                        # But, in case of invprodresult, there can be more than one productcodes mentioned. This is because, with one delchal, there can be many invoices linked.
                        matchedproducts = []
                        remainingproducts = {}
                        for eachitem in dcprodresult:
                            # dcprodresult is a list of tuples. eachitem is one such tuple.
                            for eachinvoice in invprodresult:
                                # invprodresult is a list of dictionaries. eachinvoice is one such dictionary.
                                for eachproductcode in list(eachinvoice.keys()):
                                    # eachitem[0] is unique. It's not repeated.
                                    dcprodcode = eachitem[0]
                                    if int(dcprodcode) == int(
                                        eachproductcode
                                    ):  # why do we need to convert these into string to compare?
                                        # this means that the product in delchal matches with the product in invoice
                                        # now we will check its quantity
                                        invqty = list(
                                            eachinvoice[eachproductcode].values()
                                        )[0]
                                        dcqty = eachitem[1]
                                        if float(dcqty) == float(
                                            invqty
                                        ):  # conversion of datatypes to compatible ones is very important when comparing them.
                                            # this means the quantity of current individual product is matched exactly
                                            matchedproducts.append(int(eachproductcode))
                                        elif float(dcqty) > float(invqty):
                                            # this means current invoice has not billed the whole product quantity.
                                            if dcprodcode in list(
                                                remainingproducts.keys()
                                            ):
                                                if float(dcqty) == (
                                                    float(remainingproducts[dcprodcode])
                                                    + float(invqty)
                                                ):
                                                    matchedproducts.append(
                                                        int(eachproductcode)
                                                    )
                                                    # whether we use eachproductcode or dcprodcode, doesn't matter. Because, both values are the same here.
                                                    del remainingproducts[
                                                        int(eachproductcode)
                                                    ]
                                                else:
                                                    # It must not be the case that below addition is greater than dcqty.
                                                    remainingproducts[
                                                        dcprodcode
                                                    ] = float(
                                                        remainingproducts[dcprodcode]
                                                    ) + float(
                                                        invqty
                                                    )
                                            else:
                                                remainingproducts.update(
                                                    {dcprodcode: float(invqty)}
                                                )
                                        else:
                                            # "dcqty < invqty" should never happen.
                                            # It could happen when multiple delivery chalans have only one invoice.
                                            pass

                        # changing previous logic..
                        if len(matchedproducts) == len(dcprodresult):
                            # Now we have got the delchals, for which invoices are also sent completely.
                            alldcids.remove(dcid)
                            i -= 1
                    i += 1
                    pass

                for eachdcid in alldcids:
                    if inout == "i":  # in
                        # check if current dcid has godown name or it's None. Accordingly, our query should be changed.
                        tmpresult = self.con.execute(
                            select([stock.c.goid])
                            .distinct()
                            .where(
                                and_(
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 9,
                                    stock.c.dcinvtnid == eachdcid[0],
                                )
                            )
                        )
                        tmpresult = tmpresult.fetchone()
                        if tmpresult[0] == None:
                            singledcResult = self.con.execute(
                                select(
                                    [
                                        delchal.c.dcid,
                                        delchal.c.dcno,
                                        delchal.c.dcdate,
                                        delchal.c.dcflag,
                                        customerandsupplier.c.custname,
                                    ]
                                )
                                .distinct()
                                .where(
                                    and_(
                                        delchal.c.orgcode == orgcode,
                                        customerandsupplier.c.orgcode == orgcode,
                                        eachdcid[0] == delchal.c.dcid,
                                        delchal.c.custid
                                        == customerandsupplier.c.custid,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 9,
                                        eachdcid[0] == stock.c.dcinvtnid,
                                    )
                                )
                            )
                        else:
                            singledcResult = self.con.execute(
                                select(
                                    [
                                        delchal.c.dcid,
                                        delchal.c.dcno,
                                        delchal.c.dcdate,
                                        delchal.c.dcflag,
                                        customerandsupplier.c.custname,
                                        godown.c.goname,
                                    ]
                                )
                                .distinct()
                                .where(
                                    and_(
                                        delchal.c.orgcode == orgcode,
                                        customerandsupplier.c.orgcode == orgcode,
                                        godown.c.orgcode == orgcode,
                                        eachdcid[0] == delchal.c.dcid,
                                        delchal.c.custid
                                        == customerandsupplier.c.custid,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 9,
                                        eachdcid[0] == stock.c.dcinvtnid,
                                        stock.c.goid == godown.c.goid,
                                    )
                                )
                            )
                    if inout == "o":  # out
                        # check if current dcid has godown name or it's None. Accordingly, our query should be changed.
                        tmpresult = self.con.execute(
                            select([stock.c.goid])
                            .distinct()
                            .where(
                                and_(
                                    stock.c.orgcode == orgcode,
                                    stock.c.dcinvtnflag == 4,
                                    stock.c.inout == 15,
                                    stock.c.dcinvtnid == eachdcid[0],
                                )
                            )
                        )
                        tmpresult = tmpresult.fetchone()
                        if tmpresult[0] == None:
                            singledcResult = self.con.execute(
                                select(
                                    [
                                        delchal.c.dcid,
                                        delchal.c.dcno,
                                        delchal.c.dcdate,
                                        delchal.c.dcflag,
                                        customerandsupplier.c.custname,
                                    ]
                                )
                                .distinct()
                                .where(
                                    and_(
                                        delchal.c.orgcode == orgcode,
                                        customerandsupplier.c.orgcode == orgcode,
                                        eachdcid[0] == delchal.c.dcid,
                                        delchal.c.custid
                                        == customerandsupplier.c.custid,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 15,
                                        eachdcid[0] == stock.c.dcinvtnid,
                                    )
                                )
                            )
                        else:
                            singledcResult = self.con.execute(
                                select(
                                    [
                                        delchal.c.dcid,
                                        delchal.c.dcno,
                                        delchal.c.dcdate,
                                        delchal.c.dcflag,
                                        customerandsupplier.c.custname,
                                        godown.c.goname,
                                    ]
                                )
                                .distinct()
                                .where(
                                    and_(
                                        delchal.c.orgcode == orgcode,
                                        customerandsupplier.c.orgcode == orgcode,
                                        godown.c.orgcode == orgcode,
                                        eachdcid[0] == delchal.c.dcid,
                                        delchal.c.custid
                                        == customerandsupplier.c.custid,
                                        stock.c.dcinvtnflag == 4,
                                        stock.c.inout == 15,
                                        eachdcid[0] == stock.c.dcinvtnid,
                                        stock.c.goid == godown.c.goid,
                                    )
                                )
                            )
                    singledcResult = singledcResult.fetchone()
                    dcResult.append(singledcResult)

                temp_dict = {}
                srno = 1
                for row in dcResult:
                    # if (row["dcdate"].year < inputdate.year) or (row["dcdate"].year == inputdate.year and row["dcdate"].month < inputdate.month) or (row["dcdate"].year == inputdate.year and row["dcdate"].month == inputdate.month and row["dcdate"].day <= inputdate.day):
                    temp_dict = {
                        "dcid": row["dcid"],
                        "srno": srno,
                        "dcno": row["dcno"],
                        "dcdate": datetime.strftime(row["dcdate"], "%d-%m-%Y"),
                        "dcflag": row["dcflag"],
                        "custname": row["custname"],
                    }

                    canceldelchal = 1
                    exist_dcinv = self.con.execute(
                        "select count(dcid) as dccount from dcinv where dcid=%d and orgcode=%d"
                        % (row["dcid"], authDetails["orgcode"])
                    )
                    existDcinv = exist_dcinv.fetchone()
                    if existDcinv["dccount"] > 0:
                        canceldelchal = 0
                    temp_dict["canceldelchal"] = canceldelchal

                    if "goname" in list(row.keys()):
                        temp_dict["goname"] = row["goname"]
                    else:
                        temp_dict["goname"] = None
                    if temp_dict["dcflag"] == 1:
                        temp_dict["dcflag"] = "Approval"
                    elif temp_dict["dcflag"] == 3:
                        temp_dict["dcflag"] = "Consignment"
                    elif temp_dict["dcflag"] == 4:
                        temp_dict["dcflag"] = "Sale"
                    elif temp_dict["dcflag"] == 16:
                        temp_dict["dcflag"] = "Purchase"
                    elif temp_dict["dcflag"] == 19:
                        # We don't have to consider sample.
                        temp_dict["dcflag"] = "Sample"
                    elif temp_dict["dcflag"] == 6:
                        # we ignore this as well
                        temp_dict["dcflag"] = "Free Replacement"
                    else:
                        temp_dict["dcflag"] = "Bad Input"
                    if (
                        temp_dict["dcflag"] != "Sample"
                        and temp_dict["dcflag"] != "Free Replacement"
                    ):
                        dc_unbilled.append(temp_dict)
                        srno += 1
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": dc_unbilled}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(route_name="registers", renderer="json")
    def register(self):
        """
        purpose: Takes input: i.e. either sales/purchase register and time period.
        Returns a dictionary of all matched invoices.
        description:
        This function is used to see sales or purchase register of organisation.
        It means the total purchase and sales of different products. Also its amount,
        tax, etc.
        orderflag is checked in request params for sorting date in descending order.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                """This is a list of dictionaries. Each dictionary contains details of an invoice, like-invoiceno, invdate,
                customer or supllier name, TIN, then total amount of invoice in rs then different tax rates and their respective amounts
                """
                spdata = []
                """taxcolumns is a list, which contains all possible rates of tax which are there in invoices"""
                taxcolumns = []
                # sales register(flag = 0)
                if int(self.request.params["flag"]) == 0:
                    if "orderflag" in self.request.params:
                        invquery = self.con.execute(
                            "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax,cess ,freeqty, sourcestate,  taxstate, taxflag, discount, icflag from invoice where orgcode=%d AND inoutflag = 15 AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate DESC"
                            # "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax,cess ,freeqty, sourcestate,  taxstate, taxflag, discount, icflag from invoice where orgcode=%d AND custid IN (select custid from customerandsupplier where orgcode=%d AND csflag=3) AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate DESC"
                            % (
                                authDetails["orgcode"],
                                datetime.strptime(
                                    str(self.request.params["calculatefrom"]),
                                    "%d-%m-%Y",
                                ).strftime("%Y-%m-%d"),
                                datetime.strptime(
                                    str(self.request.params["calculateto"]), "%d-%m-%Y"
                                ).strftime("%Y-%m-%d"),
                            )
                        )
                    else:
                        invquery = self.con.execute(
                            "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax,cess ,freeqty, sourcestate,  taxstate, taxflag, discount, icflag from invoice where orgcode=%d AND inoutflag = 15 AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate"
                            # "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax,cess ,freeqty, sourcestate,  taxstate, taxflag, discount, icflag from invoice where orgcode=%d AND custid IN (select custid from customerandsupplier where orgcode=%d AND csflag=3) AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate"
                            % (
                                authDetails["orgcode"],
                                datetime.strptime(
                                    str(self.request.params["calculatefrom"]),
                                    "%d-%m-%Y",
                                ).strftime("%Y-%m-%d"),
                                datetime.strptime(
                                    str(self.request.params["calculateto"]), "%d-%m-%Y"
                                ).strftime("%Y-%m-%d"),
                            )
                        )

                # purchase register(flag = 1)
                elif int(self.request.params["flag"]) == 1:
                    if "orderflag" in self.request.params:
                        invquery = self.con.execute(
                            "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax, cess,freeqty, taxstate, sourcestate, taxflag, discount, icflag from invoice where orgcode=%d AND inoutflag = 9 AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate DESC"
                            # "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax, cess,freeqty, taxstate, sourcestate, taxflag, discount, icflag from invoice where orgcode=%d AND custid IN (select custid from customerandsupplier where orgcode=%d AND csflag=19) AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate DESC"
                            % (
                                authDetails["orgcode"],
                                datetime.strptime(
                                    str(self.request.params["calculatefrom"]),
                                    "%d-%m-%Y",
                                ).strftime("%Y-%m-%d"),
                                datetime.strptime(
                                    str(self.request.params["calculateto"]), "%d-%m-%Y"
                                ).strftime("%Y-%m-%d"),
                            )
                        )
                    else:
                        invquery = self.con.execute(
                            "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax, cess,freeqty, taxstate, sourcestate, taxflag, discount, icflag from invoice where orgcode=%d AND inoutflag = 9 AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate"
                            # "select invid, invoiceno, invoicedate, custid, invoicetotal, contents, tax, cess,freeqty, taxstate, sourcestate, taxflag, discount, icflag from invoice where orgcode=%d AND custid IN (select custid from customerandsupplier where orgcode=%d AND csflag=19) AND invoicedate >= '%s' AND invoicedate <= '%s' order by invoicedate"
                            % (
                                authDetails["orgcode"],
                                datetime.strptime(
                                    str(self.request.params["calculatefrom"]),
                                    "%d-%m-%Y",
                                ).strftime("%Y-%m-%d"),
                                datetime.strptime(
                                    str(self.request.params["calculateto"]), "%d-%m-%Y"
                                ).strftime("%Y-%m-%d"),
                            )
                        )

                srno = 1
                """This totalrow dictionary is used for very last row of report which contains sum of all columns in report"""
                totalrow = {
                    "grossamount": "0.00",
                    "taxfree": "0.00",
                    "tax": {},
                    "taxamount": {},
                }
                # for each invoice
                result = invquery.fetchall()
                for row in result:
                    try:
                        custdata = self.con.execute(
                            select(
                                [
                                    customerandsupplier.c.custname,
                                    customerandsupplier.c.csflag,
                                    customerandsupplier.c.custtan,
                                    customerandsupplier.c.gstin,
                                ]
                            ).where(customerandsupplier.c.custid == row["custid"])
                        )
                        rowcust = custdata.fetchone()
                        if not rowcust:
                            rowcust = {
                                "custname": "",
                                "custtan": "",
                                "gstin": None,
                                "csflag": "",
                            }
                        invoicedata = {
                            "srno": srno,
                            "invid": row["invid"],
                            "invoiceno": row["invoiceno"],
                            "invoicedate": datetime.strftime(
                                row["invoicedate"], "%d-%m-%Y"
                            ),
                            "customername": rowcust["custname"],
                            "customertin": rowcust["custtan"],
                            "grossamount": "%.2f" % row["invoicetotal"],
                            "taxfree": "0.00",
                            "tax": "",
                            "taxamount": "",
                            "icflag": row["icflag"],
                        }

                        taxname = ""
                        disc = row["discount"]
                        # Decide tax type from taxflag
                        if int(row["taxflag"]) == 22:
                            taxname = "% VAT"

                        if int(row["taxflag"]) == 7:
                            destinationstate = row["taxstate"]
                            destinationStateCode = getStateCode(
                                row["taxstate"], self.con
                            )["statecode"]
                            sourcestate = row["sourcestate"]
                            sourceStateCode = getStateCode(
                                row["sourcestate"], self.con
                            )["statecode"]
                            # Gst has 2 types of tax Inter State(IGST) & Intra state(SGST & CGST).
                            if destinationstate != sourcestate:
                                taxname = "% IGST "
                            if destinationstate == sourcestate:
                                taxname = "% SGST"
                            # Get GSTIN on the basis of Customer / Supplier role.
                            if rowcust["gstin"] != None:
                                invoicedata["custgstin"] = ""
                                if int(rowcust["csflag"]) == 3:
                                    try:
                                        if (
                                            str(destinationStateCode)
                                            not in rowcust["gstin"]
                                        ):
                                            stcode = "0" + str(destinationStateCode)
                                            if stcode in rowcust["gstin"]:
                                                invoicedata["custgstin"] = rowcust[
                                                    "gstin"
                                                ][stcode]
                                        else:
                                            invoicedata["custgstin"] = rowcust["gstin"][
                                                str(destinationStateCode)
                                            ]
                                    except:
                                        invoicedata["custgstin"] = ""
                                else:
                                    try:
                                        if str(sourceStateCode) not in rowcust["gstin"]:
                                            stcode = "0" + str(sourceStateCode)
                                            if stcode in rowcust["gstin"]:
                                                invoicedata["custgstin"] = rowcust[
                                                    "gstin"
                                                ][stcode]
                                        else:
                                            invoicedata["custgstin"] = rowcust["gstin"][
                                                str(sourceStateCode)
                                            ]
                                    except:
                                        invoicedata["custgstin"] = ""

                        # Calculate total grossamount of all invoices.
                        totalrow["grossamount"] = "%.2f" % (
                            float(totalrow["grossamount"])
                            + float("%.2f" % row["invoicetotal"])
                        )
                        qty = 0.00
                        ppu = 0.00
                        # taxrate and cessrate are in percentage
                        taxrate = 0.00
                        cessrate = 0.00
                        # taxamount is net amount for some tax rate. eg. 2% tax on 200rs. This 200rs is taxamount, i.e. Taxable amount
                        taxamount = 0.00
                        """This taxdata dictionary has key as taxrate and value as amount of tax to be paid on this rate. eg. {"2.00": "2.80"}"""
                        taxdata = {}
                        """This taxamountdata dictionary has key as taxrate and value as Net amount on which tax to be paid. eg. {"2.00": "140.00"}"""
                        taxamountdata = {}
                        """for each product in invoice.
                        row["contents"] is JSONB which has format like this - {"22": {"20.00": "2"}, "61": {"100.00": "1"}} where 22 and 61 is productcode, {"20.00": "2"}
                        here 20.00 is price per unit and quantity is 2.
                        The other JSONB field in each invoice is row["tax"]. Its format is {"22": "2.00", "61": "2.00"}. Here, 22 and 61 are products and 2.00 is tax applied on those products, similarly for CESS {"22":"0.05"} where 22 is productcode snd 0.05 is cess rate"""

                        for pc in row["contents"].keys():
                            if not pc:
                                continue
                            discamt = 0.00
                            taxrate = float(row["tax"][pc])
                            if disc != None:
                                discamt = float(disc[pc])
                            else:
                                discamt = 0.00
                            for pcprice in row["contents"][pc].keys():
                                ppu = pcprice

                                gspc = self.con.execute(
                                    select([product.c.gsflag]).where(
                                        product.c.productcode == pc
                                    )
                                )
                                flag = gspc.fetchone()
                                # Check for product & service.
                                # In case of service quantity is not present.
                                if int(flag["gsflag"]) == 7:
                                    qty = float(row["contents"][pc][pcprice])
                                    # Taxable value of a product is calculated as (Price per unit * Quantity) - Discount
                                    taxamount = (float(ppu) * float(qty)) - float(
                                        discamt
                                    )
                                else:
                                    # Taxable value for service.
                                    taxamount = float(ppu) - float(discamt)
                            # There is a possibility of tax free product or service. This needs to be mention seperately.
                            # For this condition tax is saved as 0.00 in tax field of invoice.
                            if taxrate == 0.00:
                                invoicedata["taxfree"] = "%.2f" % (
                                    (
                                        float("%.2f" % float(invoicedata["taxfree"]))
                                        + taxamount
                                    )
                                )
                                totalrow["taxfree"] = "%.2f" % (
                                    float(totalrow["taxfree"]) + taxamount
                                )
                                continue
                            """if taxrate appears in this invoice then update invoice tax and taxamount for that rate Otherwise create new entries in respective dictionaries of that invoice"""
                            # When tax type is IGST or VAT.
                            if taxrate != 0.00:
                                if taxname != "% SGST":
                                    taxnames = "%.2f" % taxrate + taxname
                                    if str(taxnames) in taxdata:
                                        taxdata[taxnames] = "%.2f" % (
                                            float(taxdata[taxnames]) + taxamount
                                        )
                                        taxamountdata[taxnames] = "%.2f" % (
                                            float(taxamountdata[taxnames])
                                            + taxamount * float(taxrate) / 100.00
                                        )
                                    else:
                                        taxdata.update({taxnames: "%.2f" % taxamount})
                                        taxamountdata.update(
                                            {
                                                taxnames: "%.2f"
                                                % (taxamount * float(taxrate) / 100.00)
                                            }
                                        )

                                    """if new taxrate appears(in all invoices), ie. we found this rate for the first time then add this column to taxcolumns and also create new entries in tax & taxamount dictionaries Otherwise update existing data"""
                                    if taxnames not in taxcolumns:
                                        taxcolumns.append(taxnames)
                                        totalrow["taxamount"].update(
                                            {
                                                taxnames: "%.2f"
                                                % float(taxamountdata[taxnames])
                                            }
                                        )
                                        totalrow["tax"].update(
                                            {taxnames: "%.2f" % taxamount}
                                        )
                                    else:
                                        totalrow["taxamount"][taxnames] = "%.2f" % (
                                            float(totalrow["taxamount"][taxnames])
                                            + float(taxamount * float(taxrate) / 100.00)
                                        )
                                        totalrow["tax"][taxnames] = "%.2f" % (
                                            float(totalrow["tax"][taxnames]) + taxamount
                                        )

                                # when tax type is SGST & CGST , Tax rate needs to be diveded by 2.
                                if taxname == "% SGST":
                                    taxrate = taxrate / 2
                                    sgstTax = "%.2f" % taxrate + "% SGST"
                                    cgstTax = "%.2f" % taxrate + "% CGST"
                                    if sgstTax in taxdata:
                                        taxdata[sgstTax] = "%.2f" % (
                                            float(taxdata[sgstTax]) + taxamount
                                        )
                                        taxamountdata[sgstTax] = "%.2f" % (
                                            float(taxamountdata[sgstTax])
                                            + taxamount * float(taxrate) / 100.00
                                        )

                                    else:
                                        taxdata.update({sgstTax: "%.2f" % taxamount})
                                        taxamountdata.update(
                                            {
                                                sgstTax: "%.2f"
                                                % (taxamount * float(taxrate) / 100.00)
                                            }
                                        )

                                    if sgstTax not in taxcolumns:
                                        taxcolumns.append(sgstTax)
                                        totalrow["taxamount"].update(
                                            {
                                                sgstTax: "%.2f"
                                                % float(taxamountdata[sgstTax])
                                            }
                                        )
                                        totalrow["tax"].update(
                                            {sgstTax: "%.2f" % taxamount}
                                        )
                                    else:
                                        totalrow["taxamount"][sgstTax] = "%.2f" % (
                                            float(totalrow["taxamount"][sgstTax])
                                            + float(taxamount * float(taxrate) / 100.00)
                                        )
                                        totalrow["tax"][sgstTax] = "%.2f" % (
                                            float(totalrow["tax"][sgstTax]) + taxamount
                                        )

                                    if cgstTax in taxdata:
                                        taxdata[cgstTax] = "%.2f" % (
                                            float(taxdata[cgstTax]) + taxamount
                                        )
                                        taxamountdata[cgstTax] = "%.2f" % (
                                            float(taxamountdata[cgstTax])
                                            + taxamount * float(taxrate) / 100.00
                                        )

                                    else:
                                        taxdata.update({cgstTax: "%.2f" % taxamount})
                                        taxamountdata.update(
                                            {
                                                cgstTax: "%.2f"
                                                % (taxamount * float(taxrate) / 100.00)
                                            }
                                        )

                                    if cgstTax not in taxcolumns:
                                        taxcolumns.append(cgstTax)
                                        totalrow["taxamount"].update(
                                            {
                                                cgstTax: "%.2f"
                                                % float(taxamountdata[cgstTax])
                                            }
                                        )
                                        totalrow["tax"].update(
                                            {cgstTax: "%.2f" % taxamount}
                                        )
                                    else:
                                        totalrow["taxamount"][cgstTax] = "%.2f" % (
                                            float(totalrow["taxamount"][cgstTax])
                                            + float(taxamount * float(taxrate) / 100.00)
                                        )
                                        totalrow["tax"][cgstTax] = "%.2f" % (
                                            float(totalrow["tax"][cgstTax]) + taxamount
                                        )

                            if row["taxflag"] == 22:
                                continue

                            Cessname = ""
                            # Cess is a different type of TAX, only present in GST invoice.
                            if row["cess"] != None:
                                cessrate = "%.2f" % float(row["cess"][pc])
                                Cessname = str(cessrate) + "% CESS"
                                if cessrate != "0.00":
                                    if str(Cessname) in taxdata:
                                        taxdata[Cessname] = "%.2f" % (
                                            float(taxdata[Cessname]) + taxamount
                                        )
                                        taxamountdata[Cessname] = "%.2f" % (
                                            float(taxamountdata[Cessname])
                                            + taxamount * float(cessrate) / 100.00
                                        )
                                    else:
                                        taxdata.update({Cessname: "%.2f" % taxamount})
                                        taxamountdata.update(
                                            {
                                                Cessname: "%.2f"
                                                % (taxamount * float(cessrate) / 100.00)
                                            }
                                        )

                                    if Cessname not in taxcolumns:
                                        taxcolumns.append(Cessname)
                                        totalrow["taxamount"].update(
                                            {
                                                Cessname: "%.2f"
                                                % float(taxamountdata[Cessname])
                                            }
                                        )
                                        totalrow["tax"].update(
                                            {Cessname: "%.2f" % taxamount}
                                        )
                                    else:
                                        totalrow["taxamount"][Cessname] = "%.2f" % (
                                            float(totalrow["taxamount"][Cessname])
                                            + float(
                                                taxamount * float(cessrate) / 100.00
                                            )
                                        )
                                        totalrow["tax"][Cessname] = "%.2f" % (
                                            float(totalrow["tax"][Cessname]) + taxamount
                                        )

                        invoicedata["tax"] = taxdata
                        invoicedata["taxamount"] = taxamountdata
                        spdata.append(invoicedata)
                        srno += 1
                    except:
                        print(traceback.format_exc())
                        pass

                taxcolumns.sort()
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": spdata,
                    "totalrow": totalrow,
                    "taxcolumns": taxcolumns,
                }

            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="type=GSTCalc", renderer="json")
    def GSTCalc(self):
        """
        Purpose:
        takes list of accounts for CGST,SGST,IGST and CESS at Input and Output side,
        Returns list of accounts with their closing balances.
        Description:
        This API will return list of all accounts for input and output side created by the user for GST calculation.
        The function takes json_body which will have 8 key: value pares.
        Each  key denoting the tax and value will be list of accounts.
        The keys of this json_body will be as follows.
        * CGSTIn,
        * CGSTOut,
        * SGSTIn,
        * SGSTOut,
        * IGSTIn,
        * IGSTOut,
        * CESSIn,
        * CESSOut.
        Function will also need the range for which calculatBalance is to be called for getting actual balances.
        The function will loop through every list getting closing balance for all the accounts.
        Then it will sum up all the balances for that list.
        Then it will compare total in amount with total out amount and will decide if it is payable or carried forward.
        Following code will return a dictionary which will have structure like  gstDict = {"cgstin":{"accname":calculated balance,...,"to        talCGSTIn":value},"cgstout":{"accname":calculatebalance ,...,"totalCGSTOut":value},.....,"cgstpayable":value,"sgstpayable":value,        ....,"cgstcrdfwd":value,"sgstcrdfwd":value,.....}
        """

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                # check if data is supplied as json or url params
                try:
                    dataset = self.request.json_body
                except:
                    dataset = self.request.params

                stateD = dataset["statename"]
                # Get abbreviation of state
                stateA = self.con.execute(
                    select([state.c.abbreviation]).where(state.c.statename == stateD)
                )
                stateABV = stateA.fetchone()
                # Retrived individual data from dictionary
                startDate = dataset["startdate"]
                endDate = dataset["enddate"]
                result = self.con.execute(
                    select([organisation.c.yearstart]).where(
                        organisation.c.orgcode == authDetails["orgcode"]
                    )
                )
                fStart = result.fetchone()
                financialStart = fStart["yearstart"]

                # get list of accountCodes for each type of taxes for their input and output taxes.
                grp = self.con.execute(
                    select([groupsubgroups.c.groupcode]).where(
                        and_(
                            groupsubgroups.c.groupname == "Duties & Taxes",
                            groupsubgroups.c.orgcode == authDetails["orgcode"],
                        )
                    )
                )
                grpCode = grp.fetchone()

                # Create string which has taxname with state abbreviation for selecting accounts
                Cgstin = "CGSTIN_" + stateABV["abbreviation"]
                cgstout = "CGSTOUT_" + stateABV["abbreviation"]
                sgstin = "SGSTIN_" + stateABV["abbreviation"]
                sgstout = "SGSTOUT_" + stateABV["abbreviation"]
                igstin = "IGSTIN_" + stateABV["abbreviation"]
                igstout = "IGSTOUT_" + stateABV["abbreviation"]
                cessin = "CESSIN_" + stateABV["abbreviation"]
                cessout = "CESSOUT_" + stateABV["abbreviation"]

                # Declare public variables to store total
                totalCGSTIn = 0.00
                totalCGSTOut = 0.00
                totalSGSTOut = 0.00
                totalSGSTIn = 0.00
                totalSGSTOut = 0.00
                totalIGSTIn = 0.00
                totalIGSTOut = 0.00
                totalCESSIn = 0.00
                totalCESSOut = 0.00
                # These variables are to store Payable and carried forward amount
                cgstPayable = 0.00
                cgstCrdFwd = 0.00
                sgstPayable = 0.00
                sgstCrdFwd = 0.00
                igstPayable = 0.00
                igstCrdFwd = 0.00
                cessPayable = 0.00
                cessCrdFwd = 0.00
                gstDict = {}

                cIN = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(Cgstin + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                CGSTIn = cIN.fetchall()
                cgstin = {}
                if CGSTIn != None:
                    for cin in CGSTIn:
                        calbalData = calculateBalance(
                            self.con,
                            cin["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        # fill dictionary with account name and its balance.
                        cgstin[cin["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        # calculate total cgst in amount by adding balance of each account in every iteration.
                        totalCGSTIn = totalCGSTIn + calbalData["curbal"]
                # Populate dictionary to be returned with cgstin and total values
                gstDict["cgstin"] = cgstin
                gstDict["totalCGSTIn"] = "%.2f" % (float(totalCGSTIn))

                cOUT = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(cgstout + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                CGSTOut = cOUT.fetchall()
                cgstout = {}
                if CGSTOut != None:
                    for cout in CGSTOut:
                        calbalData = calculateBalance(
                            self.con,
                            cout["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        cgstout[cout["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalCGSTOut = totalCGSTOut + calbalData["curbal"]
                gstDict["cgstout"] = cgstout
                gstDict["totalCGSTOut"] = "%.2f" % (float(totalCGSTOut))

                # calculate carried forward amount or payable.
                if totalCGSTIn > totalCGSTOut:
                    cgstCrdFwd = totalCGSTIn - totalCGSTOut
                    gstDict["cgstcrdfwd"] = "%.2f" % (float(cgstCrdFwd))
                else:
                    cgstPayable = totalCGSTOut - totalCGSTIn
                    gstDict["cgstpayable"] = "%.2f" % (float(cgstPayable))

                # For state tax
                sIN = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(sgstin + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                SGSTIn = sIN.fetchall()
                sgstin = {}
                if SGSTIn != None:
                    for sin in SGSTIn:
                        calbalData = calculateBalance(
                            self.con,
                            sin["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        sgstin[sin["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalSGSTIn = totalSGSTIn + calbalData["curbal"]
                    # Populate dictionary to be returned with cgstin and total values
                    gstDict["sgstin"] = sgstin
                    gstDict["totalSGSTIn"] = "%.2f" % (float(totalSGSTIn))

                sOUT = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(sgstout + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                SGSTOut = sOUT.fetchall()
                sgstout = {}
                if SGSTOut != None:
                    for sout in SGSTOut:
                        calbalData = calculateBalance(
                            self.con,
                            sout["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        sgstout[sout["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalSGSTOut = totalSGSTOut + calbalData["curbal"]
                gstDict["sgstout"] = sgstout
                gstDict["totalSGSTOut"] = "%.2f" % (float(totalSGSTOut))

                # calculate carried forward amount or payable.
                if totalSGSTIn > totalSGSTOut:
                    sgstCrdFwd = totalSGSTIn - totalSGSTOut
                    gstDict["sgstcrdfwd"] = "%.2f" % (float(sgstCrdFwd))
                else:
                    sgstPayable = totalSGSTOut - totalSGSTIn
                    gstDict["sgstpayable"] = "%.2f" % (float(sgstPayable))

                # For Inter state tax

                iIN = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(igstin + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                IGSTIn = iIN.fetchall()
                igstin = {}
                if IGSTIn != None:
                    for iin in IGSTIn:
                        calbalData = calculateBalance(
                            self.con,
                            iin["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        igstin[iin["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalIGSTIn = totalIGSTIn + calbalData["curbal"]
                gstDict["igstin"] = igstin
                gstDict["totalIGSTIn"] = "%.2f" % (float(totalIGSTIn))

                iOUT = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(igstout + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                IGSTOut = iOUT.fetchall()
                igstout = {}
                if IGSTOut != None:
                    for iout in IGSTOut:
                        calbalData = calculateBalance(
                            self.con,
                            iout["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        igstout[iout["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalIGSTOut = totalIGSTOut + calbalData["curbal"]
                gstDict["igstout"] = igstout
                gstDict["totalIGSTOut"] = "%.2f" % (float(totalIGSTOut))

                # calculate carried forward amount or payable.
                if totalIGSTIn > totalIGSTOut:
                    igstCrdFwd = totalIGSTIn - totalIGSTOut
                    gstDict["IgstCrdFwd"] = "%.2f" % (float(igstCrdFwd))
                else:
                    igstPayable = totalIGSTOut - totalIGSTIn
                    gstDict["IgstPayable"] = "%.2f" % (float(igstPayable))

                # For cess tax
                csIN = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(cessin + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                CESSIn = csIN.fetchall()
                cssin = {}
                if CESSIn != None:
                    for csin in CESSIn:
                        calbalData = calculateBalance(
                            self.con,
                            csin["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        cssin[csin["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalCESSIn = totalCESSIn + calbalData["curbal"]
                gstDict["cessin"] = cssin
                gstDict["totalCESSIn"] = "%.2f" % (float(totalCESSIn))

                csOUT = self.con.execute(
                    select([accounts.c.accountname, accounts.c.accountcode]).where(
                        and_(
                            accounts.c.accountname.like(cessout + "%"),
                            accounts.c.orgcode == authDetails["orgcode"],
                            accounts.c.groupcode == grpCode["groupcode"],
                        )
                    )
                )
                CESSOut = csOUT.fetchall()
                cssout = {}
                if CESSOut != None:
                    for csout in CESSOut:
                        calbalData = calculateBalance(
                            self.con,
                            csout["accountcode"],
                            financialStart,
                            startDate,
                            endDate,
                        )
                        cssout[csout["accountname"]] = "%.2f" % (
                            float(calbalData["curbal"])
                        )
                        totalCESSOut = totalCESSOut + calbalData["curbal"]
                gstDict["cessout"] = cssout
                gstDict["totalCESSOut"] = "%.2f" % (float(totalCESSOut))

                # calculate carried forward amount or payable.
                if totalCESSIn > totalCESSOut:
                    cessCrdFwd = totalCESSIn - totalCESSOut
                    gstDict["cessCrdFwd"] = "%.2f" % (float(cessCrdFwd))
                else:
                    cessPayable = totalCESSOut - totalCESSIn
                    gstDict["cesspayable"] = "%.2f" % (float(cessPayable))

                return {"gkstatus": enumdict["Success"], "gkresult": gstDict}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
