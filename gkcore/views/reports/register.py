from gkcore import eng, enumdict
from gkcore.utils import authCheck
from gkcore.views.api_invoice import getStateCode
from gkcore.models.gkdb import (
    organisation,
    delchal,
    invoice,
    customerandsupplier,
    stock,
    product,
    transfernote,
    goprod,
    dcinv,
    rejectionnote,
    drcr,
    godown,
    categorysubcategories,
)
from sqlalchemy.sql import select
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, or_
from pyramid.request import Request
from pyramid.view import view_defaults, view_config
from datetime import datetime
from sqlalchemy.sql.functions import func
import traceback  # for printing detailed exception logs
from gkcore.views.reports.helpers.stock import stockonhandfun


@view_defaults(request_method="GET")
class api_stock_register(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

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

    @view_config(route_name="stock-report", renderer="json")
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

    @view_config(route_name="stock-on-hand", renderer="json")
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

    @view_config(route_name="category-wise-stock-on-hand", renderer="json")
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
