"""
This file is part of GNUKhata:A modular,robust and Free Accounting System.

License: AGPLv3

Contributors:
"Ankita Chakrabarti"<chakrabarti.ankita94@gmail.com>
"Sai Karthik"<kskarthik@disrot.org>

"""
from gkcore import eng, enumdict
from gkcore.utils import authCheck, gk_log
from gkcore.models.gkdb import accounts
from gkcore.views.reports.helpers.voucher import get_org_invoice_data
from sqlalchemy.sql import select
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
from pyramid.request import Request
from pyramid.view import view_defaults, view_config
import traceback  # for printing detailed exception logs
from gkcore.views.reports.helpers.stock import (
    calculateOpeningStockValue,
    calculateClosingStockValue,
)
from gkcore.views.reports.helpers.balance import calculateBalance
from gkcore.views.reports.helpers.profit_loss import calculateProfitLossValue


@view_defaults(request_method="GET")
class api_profit_loss(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
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
                service_invoice_data = get_org_invoice_data(
                    self.con, orgcode, calculateFrom, calculateTo, 19
                )

                priceDiff = calculateProfitLossValue(self.con, orgcode, calculateTo)
                grossDiff = priceDiff["total"] + grpDI - grpDE + service_invoice_data[1]

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


@view_defaults(route_name="profit-loss-new")
class pl(object):
    def __init__(self, request):
        self.request = Request
        self.request = request

    @view_config(request_method="GET", renderer="json")
    def calculate_profit_loss(self):
        # Check whether the user is registered & valid
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        auth_details = authCheck(token)

        if auth_details["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        current_orgcode = auth_details["orgcode"]

        params = dict()

        try:
            params["calculatefrom"] = self.request.params["calculatefrom"]
            params["calculateto"] = self.request.params["calculateto"]
        except Exception as e:
            gk_log("gkcore").warn(e)
            return {"gkstatus": enumdict["ConnectionFailed"]}

        final_result = dict()
        # calculate the opening & closing stock values
        final_result["opening_stock_value"] = calculateOpeningStockValue(
            eng.connect(), current_orgcode
        )

        final_result["closing_stock_value"] = calculateClosingStockValue(
            eng.connect(), current_orgcode, params["calculateto"]
        )
        return {"gkstatus": enumdict["Success"], "gkresult": final_result}
