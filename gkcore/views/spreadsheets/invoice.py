from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck

# from gkcore.models.gkdb import (
#     organisation,
#     unitofmeasurement,
#     product,
#     goprod,
#     stock,
#     categorysubcategories,
# )
# from sqlalchemy.sql import select
# from sqlalchemy.engine.base import Connection
# from sqlalchemy import and_, func
# from pyramid.request import Request
from pyramid.response import Response

# from pyramid.view import view_defaults, view_config
# import gkcore
# from gkcore.views.api_reports import getBalanceSheet
from gkcore.views.api_invoice import getInvoiceList
from datetime import datetime

# from gkcore.views.api_user import getUserRole
# from gkcore.views.api_godown import getusergodowns

# Spreadsheet libraries
import io
import openpyxl
from openpyxl.styles import Font, Alignment

# from openpyxl.styles.colors import RED


def print_invoice_list(self):
    """
    This function returns a list of invoices in the form of a spreadsheet.

    Params
        type     = invoice_list
        flag     = 0 - all invoices, 1 - sale invoices, 2 - purchase invoices
        fromdate = Choose invoices from date (yyyy-mm-dd)
        todate   = Choose invoices to date (yyyy-mm-dd)
        fystart  = Financial start date (dd-mm-yyyy)
        fyend    = Financial end date (dd-mm-yyyy)
        orgname  = Organisation name
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

            # params fromdate and todate are required to fetch the invoices list
            fystart = str(self.request.params["fystart"])
            fyend = str(self.request.params["fyend"])
            orgname = str(self.request.params["orgname"])
            invflag = int(self.request.params["flag"])
            invoices = getInvoiceList(
                self.con, authDetails["orgcode"], self.request.params
            )
            invoicewb = openpyxl.Workbook()
            sheet = invoicewb.active
            sheet.column_dimensions["A"].width = 8
            sheet.column_dimensions["B"].width = 12
            sheet.column_dimensions["C"].width = 10
            sheet.column_dimensions["D"].width = 16
            sheet.column_dimensions["E"].width = 16
            sheet.column_dimensions["F"].width = 16
            sheet.column_dimensions["G"].width = 16
            sheet.column_dimensions["H"].width = 10
            sheet.column_dimensions["I"].width = 16
            sheet.merge_cells("A1:K2")
            sheet["A1"].font = Font(name="Liberation Serif", size="16", bold=True)
            sheet["A1"].alignment = Alignment(horizontal="center", vertical="center")
            sheet["A1"] = orgname + " (FY: " + fystart + " to " + fyend + ")"
            sheet.merge_cells("A3:K3")
            sheet["A3"].font = Font(name="Liberation Serif", size="14", bold=True)
            sheet["A3"].alignment = Alignment(horizontal="center", vertical="center")
            if invflag == 0:
                sheet.title = "List of All Invoices"
                sheet["A3"] = "List of All Invoices"
            elif invflag == 1:
                sheet.title = "List of Sales Invoices"
                sheet["A3"] = "List of Sales Invoices"
            elif invflag == 2:
                sheet.title = "List of Purchase Invoices"
                sheet["A3"] = "List of Purchase Invoices"
            sheet.merge_cells("A4:K4")
            sheet["A4"] = (
                "Period: "
                + datetime.strptime(
                    self.request.params["fromdate"], "%Y-%m-%d"
                ).strftime("%d-%m-%Y")
                + " to "
                + datetime.strptime(self.request.params["todate"], "%Y-%m-%d").strftime(
                    "%d-%m-%Y"
                )
            )

            sheet["A4"].font = Font(name="Liberation Serif", size="14", bold=True)
            sheet["A4"].alignment = Alignment(horizontal="center", vertical="center")
            sheet["A5"] = "Sr. No."
            sheet["B5"] = "INV No."
            sheet["C5"] = "INV Date"
            sheet["D5"] = "Deli. Note "
            if invflag == 0:
                sheet["E5"] = "Cust/Supp Name"
            elif invflag == 1:
                sheet["E5"] = "Customer Name"
            elif invflag == 2:
                sheet["E5"] = "Supplier Name"
            sheet["F5"] = "Gross Amt"
            sheet["G5"] = "Net Amt"
            sheet["H5"] = "Tax Amt"
            sheet["I5"] = "Godown"
            titlerow = sheet.row_dimensions[5]
            titlerow.font = Font(name="Liberation Serif", size=12, bold=True)
            sheet["A5"].alignment = Alignment(horizontal="center")
            sheet["B5"].alignment = Alignment(horizontal="center")
            sheet["C5"].alignment = Alignment(horizontal="center")
            sheet["D5"].alignment = Alignment(horizontal="center")
            sheet["E5"].alignment = Alignment(horizontal="center")
            sheet["F5"].alignment = Alignment(horizontal="right")
            sheet["G5"].alignment = Alignment(horizontal="right")
            sheet["H5"].alignment = Alignment(horizontal="right")
            sheet["I5"].alignment = Alignment(horizontal="center")
            sheet["A5"].font = Font(name="Liberation Serif", size=12, bold=True)
            sheet["B5"].font = Font(name="Liberation Serif", size=12, bold=True)
            sheet["C5"].font = Font(name="Liberation Serif", size=12, bold=True)
            sheet["D5"].font = Font(name="Liberation Serif", size=12, bold=True)
            sheet["E5"].font = Font(name="Liberation Serif", size=12, bold=True)
            sheet["F5"].font = Font(name="Liberation Serif", size=12, bold=True)
            sheet["G5"].font = Font(name="Liberation Serif", size=12, bold=True)
            sheet["H5"].font = Font(name="Liberation Serif", size=12, bold=True)
            sheet["I5"].font = Font(name="Liberation Serif", size=12, bold=True)
            row = 6
            # Looping each dictionaries in list result to store data in cells and apply styles.
            for sheetdata in invoices:
                sheet["A" + str(row)] = sheetdata["srno"]
                sheet["A" + str(row)].alignment = Alignment(horizontal="center")
                sheet["A" + str(row)].font = Font(
                    name="Liberation Serif", size="12", bold=False
                )
                sheet["B" + str(row)] = sheetdata["invoiceno"]
                sheet["B" + str(row)].alignment = Alignment(horizontal="center")
                sheet["B" + str(row)].font = Font(
                    name="Liberation Serif", size="12", bold=False
                )
                sheet["C" + str(row)] = sheetdata["invoicedate"]
                sheet["C" + str(row)].alignment = Alignment(horizontal="center")
                sheet["C" + str(row)].font = Font(
                    name="Liberation Serif", size="12", bold=False
                )
                if sheetdata["dcno"] != "" and sheetdata["dcdate"] != "":
                    sheet["D" + str(row)] = (
                        sheetdata["dcno"] + "," + sheetdata["dcdate"]
                    )
                    sheet["D" + str(row)].alignment = Alignment(horizontal="center")
                    sheet["D" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                sheet["E" + str(row)] = sheetdata["custname"]
                sheet["E" + str(row)].alignment = Alignment(horizontal="center")
                sheet["E" + str(row)].font = Font(
                    name="Liberation Serif", size="12", bold=False
                )
                sheet["F" + str(row)] = float("%.2f" % float(sheetdata["grossamt"]))
                sheet["F" + str(row)].number_format = "0.00"
                sheet["F" + str(row)].alignment = Alignment(horizontal="right")
                sheet["F" + str(row)].font = Font(
                    name="Liberation Serif", size="12", bold=False
                )
                sheet["G" + str(row)] = float("%.2f" % float(sheetdata["netamt"]))
                sheet["G" + str(row)].number_format = "0.00"
                sheet["G" + str(row)].alignment = Alignment(horizontal="right")
                sheet["G" + str(row)].font = Font(
                    name="Liberation Serif", size="12", bold=False
                )
                sheet["H" + str(row)] = float("%.2f" % float(sheetdata["taxamt"]))
                sheet["H" + str(row)].number_format = "0.00"
                sheet["H" + str(row)].alignment = Alignment(horizontal="right")
                sheet["H" + str(row)].font = Font(
                    name="Liberation Serif", size="12", bold=False
                )
                sheet["I" + str(row)] = sheetdata["godown"]
                sheet["I" + str(row)].alignment = Alignment(horizontal="center")
                sheet["I" + str(row)].font = Font(
                    name="Liberation Serif", size="12", bold=False
                )
                row = row + 1
            output = io.BytesIO()
            invoicewb.save(output)
            contents = output.getvalue()
            output.close()
            headerList = {
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "Content-Length": len(contents),
                "Content-Disposition": "attachment; filename=report.xlsx",
                "X-Content-Type-Options": "nosniff",
                "Set-Cookie": "fileDownload=true ;path=/ [;HttpOnly]",
            }
            # headerList = {'Content-Type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ,'Content-Length': len(contents),'Content-Disposition': 'attachment; filename=report.xlsx','Set-Cookie':'fileDownload=true ;path=/'}
            self.con.close()
            return Response(contents, headerlist=list(headerList.items()))
        except:
            self.con.close()
            return {"gkstatus": enumdict["ConnectionFailed"]}
