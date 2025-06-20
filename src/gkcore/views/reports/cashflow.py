from gkcore import eng, enumdict
from gkcore.utils import authCheck
from sqlalchemy.sql.expression import text
from pyramid.request import Request
from pyramid.view import view_defaults, view_config
from datetime import datetime
from gkcore.views.reports.helpers.balance import calculateBalance


@view_defaults(route_name="cash-flow", request_method="GET")
class api_cashflow(object):
    def __init__(self, request):
        self.request = Request
        self.request = request

    @view_config(renderer="json")
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
        with eng.connect() as con:
            calculateFrom = self.request.params["calculatefrom"]
            calculateTo = self.request.params["calculateto"]
            financialStart = self.request.params["financialstart"]
            cbAccountsData = con.execute(
                text("select accountcode, openingbal, accountname from accounts where orgcode = :orgcode and groupcode in (select groupcode from groupsubgroups where orgcode = :orgcode and groupname in ('Bank','Cash')) order by accountname"),
                orgcode = authDetails["orgcode"],
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
                    con,
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
                transactionsRecords = con.execute(
                    text("select crs,drs from vouchers where voucherdate >= :voucherdate_from  and voucherdate <= :voucherdate_to and vouchertype not in ('contra') and (drs ? :drs or crs ? :crs);"),
                    voucherdate_from = calculateFrom,
                    voucherdate_to = calculateTo,
                    drs = str(cbAccount["accountcode"]),
                    crs = str(cbAccount["accountcode"]),
                )
                transactions = transactionsRecords.fetchall()
                for transaction in transactions:
                    for cr in transaction["crs"]:
                        if cr not in rcaccountcodes and int(cr) != int(
                            cbAccount["accountcode"]
                        ):
                            rcaccountcodes.append(cr)
                            crresult = con.execute(
                                text("select sum(cast(crs->>:cr as float)) as total from vouchers where delflag = false and voucherdate >= :voucherdate_from and voucherdate <= :voucherdate_to and vouchertype not in ('contra') and (drs ?| :bankcodes);"),
                                cr = cr,
                                voucherdate_from = financialStart,
                                voucherdate_to = calculateTo,
                                bankcodes = bankcodes,
                            )
                            crresultRow = crresult.fetchone()
                            rcaccountname = con.execute(
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
                            drresult = con.execute(
                                text("select sum(cast(drs->>:dr as float)) as total from vouchers where delflag = false and voucherdate >= :voucherdate_from and voucherdate <= :voucherdate_to and vouchertype not in ('contra') and (crs ?| :bankcodes);"),
                                dr = dr,
                                voucherdate_from = financialStart,
                                voucherdate_to = calculateTo,
                                bankcodes = bankcodes,
                            )
                            drresultRow = drresult.fetchone()
                            pyaccountname = con.execute(
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
            return {
                "gkstatus": enumdict["Success"],
                "gkresult":{
                    "rcgkresult": receiptcf,
                    "pygkresult": paymentcf,
                }
            }
