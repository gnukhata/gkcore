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
"Survesh" <123survesh@gmail.com>
"Sai Karthik"<kskarthik@disroot.org>

"""

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models.gkdb import organisation, unitofmeasurement, product, goprod, stock, categorysubcategories
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
import gkcore
from gkcore.views.api_reports import getBalanceSheet
from gkcore.views.api_invoice import getInvoiceList
from datetime import datetime, date
from gkcore.views.api_user import getUserRole
from gkcore.views.api_godown import getusergodowns

# Spreadsheet libraries
import io
import openpyxl
from openpyxl.styles import Font, Alignment
from openpyxl.styles.colors import RED
from io import BytesIO

"""
    This API returns a spreadsheet in XLSX format of the desired report.
"""


@view_defaults(route_name="spreadsheet")
class api_spreadsheet(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print("Spreadsheet API initialized")

    """
        Returns the spreadsheet for Conventional Balancesheet
        In the Conventional format, capital and liabilities are shown on left side and assets on the right side.

        Params
            type            = conv_bal_sheet
            calculateto     = Calculate balance sheet to date (yyyy-mm-dd)
            calculatefrom   = Calculate balance sheet from date (yyyy-mm-dd)
            baltype         = balance sheet type
            orgname         = Organisation name
            fystart         = Financial start date (dd-mm-yyyy)
            fyend           = Financial end date (dd-mm-yyyy)
            orgtype         = Organisation type, profitable or not for profit
    """

    @view_config(
        request_method="GET", request_param="type=conv_bal_sheet", renderer="json"
    )
    def getConvBalSheet(self):
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
                calculateto = self.request.params["calculateto"]
                calculatefrom = self.request.params["calculatefrom"]
                balType = int(self.request.params["baltype"])
                fystart = str(self.request.params["fystart"])
                orgname = str(self.request.params["orgname"])
                fyend = str(self.request.params["fyend"])
                orgtype = str(self.request.params["orgtype"])
                result = getBalanceSheet(
                    self.con,
                    authDetails["orgcode"],
                    calculateto,
                    calculatefrom,
                    balType,
                )
                calculateto = calculateto[8:10] + calculateto[4:8] + calculateto[0:4]
                sources = result["leftlist"]
                applications = result["rightlist"]
                conventionalwb = openpyxl.Workbook()
                sheet = conventionalwb.active
                sheet.title = "Conventional Balance Sheet"
                sheet.column_dimensions["A"].width = 30
                sheet.column_dimensions["B"].width = 12
                sheet.column_dimensions["C"].width = 12
                sheet.column_dimensions["D"].width = 12
                sheet.column_dimensions["E"].width = 30
                sheet.column_dimensions["F"].width = 12
                sheet.column_dimensions["G"].width = 12
                sheet.column_dimensions["H"].width = 12
                sheet.merge_cells("A1:H2")
                sheet["A1"].font = Font(name="Liberation Serif", size="16", bold=True)
                sheet["A1"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                sheet["A1"] = orgname + " (FY: " + fystart + " to " + fyend + ")"
                sheet.merge_cells("A3:H3")
                if orgtype == "Profit Making":
                    sheet["A3"].font = Font(
                        name="Liberation Serif", size="14", bold=True
                    )
                    sheet["A3"].alignment = Alignment(
                        horizontal="center", vertical="center"
                    )
                    sheet["A3"] = (
                        "Conventional Balance Sheet from "
                        + calculatefrom
                        + " to "
                        + calculateto
                    )
                    sheet["A4"] = "Capital and Liabilities"
                    sheet["A4"].font = Font(
                        name="Liberation Serif", size="12", bold=True
                    )
                if orgtype == "Not For Profit":
                    sheet["A3"].font = Font(
                        name="Liberation Serif", size="14", bold=True
                    )
                    sheet["A3"].alignment = Alignment(
                        horizontal="center", vertical="center"
                    )
                    sheet["A3"] = (
                        "Conventional Statement of Affairs as on " + calculateto
                    )
                    sheet["A4"] = "Corpus and Liabilities"
                    sheet["A4"].font = Font(
                        name="Liberation Serif", size="12", bold=True
                    )
                sheet["D4"] = "Amount"
                sheet["D4"].alignment = Alignment(horizontal="right")
                sheet["D4"].font = Font(name="Liberation Serif", size="12", bold=True)
                sheet["E4"] = "Property and Assets"
                sheet["E4"].alignment = Alignment(horizontal="left")
                sheet["E4"].font = Font(name="Liberation Serif", size="12", bold=True)
                sheet["H4"] = "Amount"
                sheet["H4"].alignment = Alignment(horizontal="right")
                sheet["H4"].font = Font(name="Liberation Serif", size="12", bold=True)
                """ 
                """
                """ 
                Looping each dictionaries in list sources to store data in cells and apply styles.
                If the advflag = 1 then 'amount' will be displayed in 'RED' color
                """
                row = 4
                for record in sources:
                    if record["groupAccname"] != "":
                        if record["groupAccname"] != "Sources:":
                            if (
                                record["groupAccname"] == "Total"
                                or record["groupAccname"] == "Sources:"
                                or record["groupAccname"] == "Difference"
                            ):
                                sheet["A" + str(row)] = record["groupAccname"].upper()
                                sheet["A" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=True
                                )
                            elif (
                                record["groupAccflag"] == ""
                                and record["subgroupof"] != ""
                            ):
                                sheet["A" + str(row)] = (
                                    "            " + record["groupAccname"]
                                )
                                sheet["A" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=False
                                )
                            elif record["groupAccflag"] == 1:
                                sheet["A" + str(row)] = (
                                    "                        " + record["groupAccname"]
                                )
                                sheet["A" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=False
                                )
                            elif record["groupAccflag"] == 2:
                                sheet["A" + str(row)] = (
                                    "                        " + record["groupAccname"]
                                )
                                sheet["A" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=False
                                )
                            else:
                                sheet["A" + str(row)] = record["groupAccname"].upper()
                                sheet["A" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=False
                                )
                        if record["groupAccflag"] == 2 or record["groupAccflag"] == 1:
                            if record["advflag"] == 1:
                                sheet["B" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["B" + str(row)].number_format = "0.00"
                                sheet["B" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["B" + str(row)].font = Font(
                                    name="Liberation Serif",
                                    size="12",
                                    bold=True,
                                    color=RED,
                                )
                            else:
                                sheet["B" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["B" + str(row)].number_format = "0.00"
                                sheet["B" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["B" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=False
                                )
                        elif (
                            record["groupAccflag"] == "" and record["subgroupof"] != ""
                        ):
                            if record["advflag"] == 1:
                                sheet["C" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["C" + str(row)].number_format = "0.00"
                                sheet["C" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["C" + str(row)].font = Font(
                                    name="Liberation Serif",
                                    size="12",
                                    bold=True,
                                    color=RED,
                                )
                            else:
                                sheet["C" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["C" + str(row)].number_format = "0.00"
                                sheet["C" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["C" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=False
                                )
                        else:
                            if record["advflag"] == 1:
                                sheet["D" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["D" + str(row)].number_format = "0.00"
                                sheet["D" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["D" + str(row)].font = Font(
                                    name="Liberation Serif",
                                    size="12",
                                    bold=True,
                                    color=RED,
                                )
                            else:
                                if record["amount"] != "":
                                    sheet["D" + str(row)] = float(
                                        "%.2f" % float(record["amount"])
                                    )
                                    sheet["D" + str(row)].number_format = "0.00"
                                    sheet["D" + str(row)].alignment = Alignment(
                                        horizontal="right"
                                    )
                                    sheet["D" + str(row)].font = Font(
                                        name="Liberation Serif", size="12", bold=True
                                    )
                        row += 1
                """ 
                """
                """ 
                Looping each dictionaries in list applications to store data in cells and apply styles.
                If the advflag = 1 then 'amount' will be displayed in 'RED' color
                """
                row = 4
                for record in applications:
                    if record["groupAccname"] != "":
                        if record["groupAccname"] != "Applications:":
                            if (
                                record["groupAccname"] == "Total"
                                or record["groupAccname"] == "Sources:"
                                or record["groupAccname"] == "Difference"
                            ):
                                sheet["E" + str(row)] = record["groupAccname"].upper()
                                sheet["E" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=True
                                )
                            elif (
                                record["groupAccflag"] == ""
                                and record["subgroupof"] != ""
                            ):
                                sheet["E" + str(row)] = (
                                    "            " + record["groupAccname"]
                                )
                                sheet["E" + str(row)].font = Font(
                                    name="Liberation Serif", size="12"
                                )
                            elif record["groupAccflag"] == 1:
                                sheet["E" + str(row)] = (
                                    "                        " + record["groupAccname"]
                                )
                                sheet["E" + str(row)].font = Font(
                                    name="Liberation Serif", size="12"
                                )
                            elif record["groupAccflag"] == 2:
                                sheet["E" + str(row)] = (
                                    "                        " + record["groupAccname"]
                                )
                                sheet["E" + str(row)].font = Font(
                                    name="Liberation Serif", size="12"
                                )
                            else:
                                sheet["E" + str(row)] = record["groupAccname"].upper()
                                sheet["E" + str(row)].font = Font(
                                    name="Liberation Serif", size="12"
                                )

                        if record["groupAccflag"] == 2 or record["groupAccflag"] == 1:
                            if record["advflag"] == 1:
                                sheet["F" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["F" + str(row)].number_format = "0.00"
                                sheet["F" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["F" + str(row)].font = Font(
                                    name="Liberation Serif",
                                    size="12",
                                    bold=True,
                                    color=RED,
                                )
                            else:
                                sheet["F" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["F" + str(row)].number_format = "0.00"
                                sheet["F" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["F" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=False
                                )
                        elif (
                            record["groupAccflag"] == "" and record["subgroupof"] != ""
                        ):
                            if record["advflag"] == 1:
                                sheet["G" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["G" + str(row)].number_format = "0.00"
                                sheet["G" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["G" + str(row)].font = Font(
                                    name="Liberation Serif",
                                    size="12",
                                    bold=True,
                                    color=RED,
                                )
                            else:
                                sheet["G" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["G" + str(row)].number_format = "0.00"
                                sheet["G" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["G" + str(row)].font = Font(
                                    name="Liberation Serif", size="12", bold=False
                                )
                        else:
                            if record["advflag"] == 1:
                                sheet["H" + str(row)] = float(
                                    "%.2f" % float(record["amount"])
                                )
                                sheet["H" + str(row)].number_format = "0.00"
                                sheet["H" + str(row)].alignment = Alignment(
                                    horizontal="right"
                                )
                                sheet["H" + str(row)].font = Font(
                                    name="Liberation Serif",
                                    size="12",
                                    bold=True,
                                    color=RED,
                                )
                            else:
                                if record["amount"] != "":
                                    sheet["H" + str(row)] = float(
                                        "%.2f" % float(record["amount"])
                                    )
                                    sheet["H" + str(row)].number_format = "0.00"
                                    sheet["H" + str(row)].alignment = Alignment(
                                        horizontal="right"
                                    )
                                    sheet["H" + str(row)].font = Font(
                                        name="Liberation Serif", size="12", bold=True
                                    )
                        row += 1
                output = io.BytesIO()
                conventionalwb.save(output)
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
                #   print(e)
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}

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

    @view_config(
        request_method="GET", request_param="type=invoice_list", renderer="json"
    )
    def getInvoiceList(self):
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
                invoices = getInvoiceList(self.con, authDetails['orgcode'], self.request.params)
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
                sheet["A1"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                sheet["A1"] = orgname + " (FY: " + fystart + " to " + fyend + ")"
                sheet.merge_cells("A3:K3")
                sheet["A3"].font = Font(name="Liberation Serif", size="14", bold=True)
                sheet["A3"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
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
                    + datetime.strptime(
                        self.request.params["todate"], "%Y-%m-%d"
                    ).strftime("%d-%m-%Y")
                )

                sheet["A4"].font = Font(name="Liberation Serif", size="14", bold=True)
                sheet["A4"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
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

    """
    This function returns a list of products and services in the form of a spreadsheet.

    Params
        type    = products_list
        fystart = Financial start date (dd-mm-yyyy)
        fyend   = Financial end date (dd-mm-yyyy)
        orgname = Organisation name
    """

    @view_config(
        request_method="GET", request_param="type=products_list", renderer="json"
    )
    def getListofProductsSpreadsheet(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                orgdetails = self.con.execute(
                    select(
                        [
                            organisation.c.orgname,
                            organisation.c.yearstart,
                            organisation.c.yearend,
                        ]
                    ).where(organisation.c.orgcode == authDetails["orgcode"])
                )
                orgData = orgdetails.fetchone()
                gstorvatflag = 29
                date1 = "2017-07-01"
                gstdate = datetime.strptime(date1, "%Y-%m-%d")
                financialStart = datetime.strptime(
                    str(orgData["yearstart"]), "%Y-%m-%d"
                )
                financialEnd = datetime.strptime(str(orgData["yearend"]), "%Y-%m-%d")
                fystart = financialStart.strftime("%d-%m-%Y")
                fyend = financialEnd.strftime("%d-%m-%Y")
                orgname = orgData["orgname"]

                if gstdate > financialStart and gstdate > financialEnd:
                    gstorvatflag = 22
                elif gstdate > financialStart and gstdate <= financialEnd:
                    gstorvatflag = 29
                elif gstdate <= financialStart and gstdate <= financialEnd:
                    gstorvatflag = 7
                userrole = getUserRole(authDetails["userid"])
                gorole = userrole["gkresult"]
                if gorole["userrole"] == 3:
                    uId = getusergodowns(authDetails["userid"])
                    gid = []
                    for record1 in uId["gkresult"]:
                        gid.append(record1["goid"])
                    productCodes = []
                    for record2 in gid:
                        proCode = self.con.execute(
                            select([goprod.c.productcode]).where(
                                goprod.c.goid == record2
                            )
                        )
                        proCodes = proCode.fetchall()
                        for record3 in proCodes:
                            if record3["productcode"] not in productCodes:
                                productCodes.append(record3["productcode"])
                    results = []
                    for record4 in productCodes:
                        result = self.con.execute(
                            select(
                                [
                                    product.c.productcode,
                                    product.c.productdesc,
                                    product.c.categorycode,
                                    product.c.uomid,
                                    product.c.gsflag,
                                    product.c.prodsp,
                                    product.c.prodmrp,
                                ]
                            )
                            .where(
                                and_(
                                    product.c.orgcode == authDetails["orgcode"],
                                    product.c.productcode == record4,
                                )
                            )
                            .order_by(product.c.productdesc)
                        )
                        products = result.fetchone()
                        results.append(products)
                else:
                    invdc = 9
                    try:
                        invdc = int(self.request.params["invdc"])
                    except:
                        invdc = 9
                    if invdc == 4:
                        results = self.con.execute(
                            select(
                                [
                                    product.c.productcode,
                                    product.c.gsflag,
                                    product.c.productdesc,
                                    product.c.categorycode,
                                    product.c.uomid,
                                    product.c.prodsp,
                                    product.c.prodmrp,
                                ]
                            )
                            .where(
                                and_(
                                    product.c.orgcode == authDetails["orgcode"],
                                    product.c.gsflag == 7,
                                )
                            )
                            .order_by(product.c.productdesc)
                        )
                    if invdc == 9:
                        results = self.con.execute(
                            select(
                                [
                                    product.c.productcode,
                                    product.c.productdesc,
                                    product.c.gsflag,
                                    product.c.categorycode,
                                    product.c.uomid,
                                    product.c.prodsp,
                                    product.c.prodmrp,
                                ]
                            )
                            .where(product.c.orgcode == authDetails["orgcode"])
                            .order_by(product.c.productdesc)
                        )

                products = []
                srno = 1
                for productrow in results:
                    unitsofmeasurement = self.con.execute(
                        select([unitofmeasurement.c.unitname]).where(
                            unitofmeasurement.c.uomid == productrow["uomid"]
                        )
                    )
                    uom = unitsofmeasurement.fetchone()
                    if uom != None:
                        unitname = uom["unitname"]
                    else:
                        unitname = ""
                    if productrow["categorycode"] != None:
                        categories = self.con.execute(
                            select([categorysubcategories.c.categoryname]).where(
                                categorysubcategories.c.categorycode
                                == productrow["categorycode"]
                            )
                        )
                        category = categories.fetchone()
                        categoryname = category["categoryname"]
                    else:
                        categoryname = ""
                    if productrow["productcode"] != None:
                        openingStockResult = self.con.execute(
                            select([product.c.openingstock]).where(
                                product.c.productcode == productrow["productcode"]
                            )
                        )
                        osProductrow = openingStockResult.fetchone()
                        openingStock = osProductrow["openingstock"]
                        productstockin = self.con.execute(
                            select(
                                [func.sum(stock.c.qty).label("sumofins")]
                            ).where(
                                and_(
                                    stock.c.productcode
                                    == productrow["productcode"],
                                    stock.c.inout == 9,
                                )
                            )
                        )
                        stockinsum = productstockin.fetchone()
                        if stockinsum["sumofins"] != None:
                            openingStock = openingStock + stockinsum["sumofins"]
                        productstockout = self.con.execute(
                            select(
                                [func.sum(stock.c.qty).label("sumofouts")]
                            ).where(
                                and_(
                                    stock.c.productcode
                                    == productrow["productcode"],
                                    stock.c.inout == 15,
                                )
                            )
                        )
                        stockoutsum = productstockout.fetchone()
                        if stockoutsum["sumofouts"] != None:
                            openingStock = openingStock - stockoutsum["sumofouts"]
                    products.append(
                        {
                            "srno": srno,
                            "unitname": unitname,
                            "categoryname": categoryname,
                            "productcode": productrow["productcode"],
                            "productdesc": productrow["productdesc"],
                            "categorycode": productrow["categorycode"],
                            "productquantity": "%.2f" % float(openingStock),
                            "gsflag": productrow["gsflag"],
                        }
                    )
                    srno = srno + 1
                # A workbook is opened.
                productwb = openpyxl.Workbook()
                # The new sheet is the active sheet as no other sheet exists. It is set as value of variable - sheet.
                sheet = productwb.active
                # Title of the sheet and width of columns are set.
                sheet.title = "List of Products"
                sheet.column_dimensions["A"].width = 8
                sheet.column_dimensions["B"].width = 24
                sheet.column_dimensions["C"].width = 18
                sheet.column_dimensions["D"].width = 24
                sheet.column_dimensions["E"].width = 16
                # Cells of first two rows are merged to display organisation details properly.
                sheet.merge_cells("A1:E2")
                # Font and Alignment of cells are set. Each cell can be identified using the cell index - column name and row number.
                sheet["A1"].font = Font(name="Liberation Serif", size="16", bold=True)
                sheet["A1"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                # Organisation name and financial year are displayed.
                sheet["A1"] = orgname + " (FY: " + fystart + " to " + fyend + ")"
                sheet.merge_cells("A3:E3")
                sheet["A3"].font = Font(name="Liberation Serif", size="14", bold=True)
                sheet["A3"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                sheet["A3"] = "List of Products"
                sheet.merge_cells("A3:E3")
                sheet["A4"] = "Sr.No."
                if gstorvatflag == "22":
                    sheet["B4"] = "Product"
                    sheet["C4"] = "Category"
                    sheet["D4"] = "UOM"
                else:
                    sheet["B4"] = "Product/service"
                    sheet["C4"] = "Type"
                    sheet["D4"] = "Category"
                    sheet["E4"] = "Uom"
                titlerow = sheet.row_dimensions[4]
                titlerow.font = Font(name="Liberation Serif", size=12, bold=True)
                srno = 1
                if gstorvatflag == "22":
                    row = 5
                    for prodStock in products:
                        sheet["A" + str(row)] = srno
                        sheet["A" + str(row)].alignment = Alignment(horizontal="left")
                        sheet["A" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["B" + str(row)] = prodStock["productdesc"]
                        sheet["B" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)] = prodStock["categoryname"]
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["D" + str(row)] = prodStock["unitname"]
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        row += 1
                        srno += 1
                else:
                    row = 5
                    for prodStock in products:
                        sheet["A" + str(row)] = srno
                        sheet["A" + str(row)].alignment = Alignment(horizontal="left")
                        sheet["A" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["B" + str(row)] = prodStock["productdesc"]
                        sheet["B" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        if prodStock["gsflag"] == 7:
                            sheet["C" + str(row)] = "Product"
                            sheet["C" + str(row)].font = Font(
                                name="Liberation Serif", size="12", bold=False
                            )
                        else:
                            sheet["C" + str(row)] = "Service"
                            sheet["C" + str(row)].font = Font(
                                name="Liberation Serif", size="12", bold=False
                            )
                        sheet["D" + str(row)] = prodStock["categoryname"]
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["E" + str(row)] = prodStock["unitname"]
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        row += 1
                        srno += 1
                output = io.BytesIO()
                productwb.save(output)
                contents = output.getvalue()
                output.close()
                headerList = {
                    "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "Content-Length": len(contents),
                    "Content-Disposition": "attachment; filename=report.xlsx",
                    "X-Content-Type-Options": "nosniff",
                    "Set-Cookie": "fileDownload=true; path=/ [;HttpOnly]",
                }
                # headerList = {'Content-Type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ,'Content-Length': len(contents),'Content-Disposition': 'attachment; filename=report.xlsx','Set-Cookie':'fileDownload=true; path=/'}
                self.con.close()
                return Response(contents, headerlist=list(headerList.items()))
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
