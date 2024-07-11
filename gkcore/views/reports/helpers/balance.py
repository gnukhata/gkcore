from gkcore.models.gkdb import accounts
from sqlalchemy.sql import select
from datetime import datetime
from gkcore.views.reports.helpers.stock import (
    calculateOpeningStockValue,
    calculateClosingStockValue
)


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
