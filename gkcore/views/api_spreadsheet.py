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
from gkcore.models.gkdb import (
    organisation,
    unitofmeasurement,
    product,
    goprod,
    stock,
    categorysubcategories,
)
from sqlalchemy.sql import select
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
import requests
import json
from gkcore.views.spreadsheets import *

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
                            select([func.sum(stock.c.qty).label("sumofins")]).where(
                                and_(
                                    stock.c.productcode == productrow["productcode"],
                                    stock.c.inout == 9,
                                )
                            )
                        )
                        stockinsum = productstockin.fetchone()
                        if stockinsum["sumofins"] != None:
                            openingStock = openingStock + stockinsum["sumofins"]
                        productstockout = self.con.execute(
                            select([func.sum(stock.c.qty).label("sumofouts")]).where(
                                and_(
                                    stock.c.productcode == productrow["productcode"],
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

    @view_config(
        request_method="GET", request_param="type=stockreport", renderer="json"
    )
    def stockreport_spreadsheet(self):
        print("stock report")
        try:
            header = {"gktoken": self.request.headers["gktoken"]}
            godownflag = int(self.request.params["godownflag"])
            if godownflag == 1:
                goaddr = self.request.params["goaddr"]
                goid = int(self.request.params["goid"])
                goname = self.request.params["goname"]
            productcode = int(self.request.params["productcode"])
            calculatefrom = self.request.params["calculatefrom"]
            calculateto = self.request.params["calculateto"]
            scalculatefrom = datetime.strptime(calculatefrom, "%d-%m-%Y").strftime(
                "%Y-%m-%d"
            )
            scalculateto = datetime.strptime(calculateto, "%d-%m-%Y").strftime(
                "%Y-%m-%d"
            )
            productdesc = self.request.params["productdesc"]
            if godownflag > 0:
                subreq = Request.blank(
                    "/report?type=godownstockreport&productcode=%d&startdate=%s&enddate=%s&goid=%d&godownflag=%d"
                    % (productcode, scalculatefrom, scalculateto, goid, godownflag),
                    headers=header,
                )
                result = self.request.invoke_subrequest(subreq)
            else:
                subr = Request.blank(
                    "/report?type=stockreport&productcode=%d&startdate=%s&enddate=%s"
                    % (productcode, scalculatefrom, scalculateto),
                    headers=header,
                )
                result = self.request.invoke_subrequest(subr)
            result = json.loads(result.text)["gkresult"]
            fystart = datetime.strptime(
                self.request.params["fystart"], "%Y-%m-%d"
            ).strftime("%d-%m-%Y")
            fyend = str(self.request.params["fyend"])
            orgname = str(self.request.params["orgname"])
            # A workbook is opened.
            prowb = openpyxl.Workbook()
            # The new sheet is the active sheet as no other sheet exists. It is set as value of variable - sheet.
            sheet = prowb.active
            # Title of the sheet and width of columns are set.
            sheet.title = "Product Report"
            sheet.column_dimensions["A"].width = 10
            sheet.column_dimensions["B"].width = 18
            sheet.column_dimensions["C"].width = 22
            sheet.column_dimensions["D"].width = 18
            sheet.column_dimensions["E"].width = 14
            sheet.column_dimensions["F"].width = 14
            sheet.column_dimensions["G"].width = 14
            sheet.column_dimensions["H"].width = 14
            sheet.column_dimensions["I"].width = 14
            sheet.column_dimensions["J"].width = 14
            # Cells of first two rows are merged to display organisation details properly.
            sheet.merge_cells("A1:I2")
            # Name and Financial Year of organisation is fetched to be displayed on the first row.
            sheet["A1"].font = Font(name="Liberation Serif", size="16", bold=True)
            sheet["A1"].alignment = Alignment(horizontal="center", vertical="center")
            # Organisation name and financial year are displayed.
            sheet.merge_cells("A3:J3")
            sheet["A3"].font = Font(name="Liberation Serif", size="14", bold=True)
            sheet["A3"].alignment = Alignment(horizontal="center", vertical="center")
            sheet.merge_cells("A4:J4")
            sheet["A4"].font = Font(name="Liberation Serif", size="14", bold=True)
            sheet["A4"].alignment = Alignment(horizontal="center", vertical="center")
            trn = ""
            if godownflag > 0:
                sheet["A1"] = orgname + " (FY: " + fystart + " to " + fyend + ")"
                sheet["A3"] = (
                    "Godown Wise Product Report  (Period : "
                    + calculatefrom
                    + " to "
                    + calculateto
                    + ")"
                )
                sheet["A4"] = "Name of the Product: " + productdesc
                sheet.merge_cells("A5:J5")
                sheet["A5"].font = Font(name="Liberation Serif", size="14", bold=True)
                sheet["A5"] = (
                    "Name of the Godown : " + goname + ", Godown Address: " + goaddr
                )
                sheet["A6"] = "Date"
                sheet["B6"] = "Particulars"
                sheet["C6"] = "Document Type"
                sheet["D6"] = "Deli Note No."
                sheet["E6"] = "INV/DR/CR No."
                sheet["F6"] = "RN No."
                sheet["G6"] = "TN No."
                sheet["H6"] = "Inward"
                sheet["I6"] = "Outward"
                sheet["J6"] = "Balance"
                titlerow = sheet.row_dimensions[6]
                titlerow.font = Font(name="Liberation Serif", size=12, bold=True)
                titlerow.alignment = Alignment(horizontal="center", vertical="center")
                sheet["H6"].alignment = Alignment(horizontal="right")
                sheet["H6"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["I6"].alignment = Alignment(horizontal="right")
                sheet["I6"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["J6"].alignment = Alignment(horizontal="right")
                sheet["J6"].font = Font(name="Liberation Serif", size=12, bold=True)
                row = 7

                for stock in result:
                    if stock["trntype"] == "delchal":
                        trn = "Delivery Note"
                    if stock["trntype"] == "invoice":
                        trn = "Invoice "
                    if stock["trntype"] == "delchal&invoice":
                        trn = "Delivery Note & Invoice"
                    if stock["trntype"] == "transfer note":
                        trn = "Transfer Note "
                    if stock["trntype"] == "Rejection Note":
                        trn = "Rejection Note"
                    if stock["trntype"] == "Debit Note":
                        trn = "Debit Note"
                    if stock["trntype"] == "Credit Note":
                        trn = "Credit Note"

                    if (
                        stock["particulars"] == "opening stock"
                        and stock["dcno"] == ""
                        and stock["invno"] == ""
                        and stock["date"] == ""
                    ):
                        sheet["A" + str(row)] = ""
                        sheet["A" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["A" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["B" + str(row)] = stock["particulars"].title()
                        sheet["B" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)] = ""
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["D" + str(row)] = ""
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["D" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["E" + str(row)] = ""
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["E" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["F" + str(row)] = ""
                        sheet["F" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["F" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["G" + str(row)] = ""
                        sheet["G" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["G" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["H" + str(row)] = float("%.2f" % float(stock["inward"]))
                        sheet["H" + str(row)].number_format = "0.00"
                        sheet["H" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["H" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["I" + str(row)] = ""
                        sheet["I" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["I" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["J" + str(row)] = ""
                        sheet["J" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["J" + str(row)].alignment = Alignment(horizontal="right")
                    if (
                        stock["particulars"] != "Total"
                        and (
                            stock["dcno"] != ""
                            or stock["invno"] != ""
                            or stock["tnno"] != ""
                            or stock["rnno"] != ""
                        )
                        and stock["date"] != ""
                    ):

                        sheet["A" + str(row)] = stock["date"]
                        sheet["A" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["A" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["B" + str(row)] = stock["particulars"]
                        sheet["B" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)] = trn
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["D" + str(row)] = stock["dcno"]
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["D" + str(row)].alignment = Alignment(horizontal="center")
                        if stock["invno"] != "":

                            sheet["E" + str(row)] = stock["invno"]
                        elif "drcrno" in stock and stock["drcrno"] != "":

                            sheet["E" + str(row)] = stock["drcrno"]
                        else:

                            sheet["E" + str(row)] = ""
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["E" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["F" + str(row)] = stock["rnno"]
                        sheet["F" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["F" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["G" + str(row)] = stock["tnno"]
                        sheet["G" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["G" + str(row)].alignment = Alignment(horizontal="center")
                        if stock["inwardqty"] != "":

                            sheet["H" + str(row)] = float(
                                "%.2f" % float(stock["inwardqty"])
                            )
                            sheet["H" + str(row)].number_format = "0.00"
                            sheet["H" + str(row)].font = Font(
                                name="Liberation Serif", size="12", bold=False
                            )
                            sheet["H" + str(row)].alignment = Alignment(
                                horizontal="right"
                            )
                        if stock["outwardqty"] != "":

                            sheet["I" + str(row)] = float(
                                "%.2f" % float(stock["outwardqty"])
                            )
                            sheet["I" + str(row)].number_format = "0.00"
                            sheet["I" + str(row)].font = Font(
                                name="Liberation Serif", size="12", bold=False
                            )
                            sheet["I" + str(row)].alignment = Alignment(
                                horizontal="right"
                            )
                        sheet["J" + str(row)] = float("%.2f" % float(stock["balance"]))
                        sheet["J" + str(row)].number_format = "0.00"
                        sheet["J" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["J" + str(row)].alignment = Alignment(horizontal="right")
                    if (
                        stock["particulars"] == "Total"
                        and stock["dcno"] == ""
                        and stock["invno"] == ""
                        and stock["date"] == ""
                    ):

                        sheet["A" + str(row)] = ""
                        sheet["A" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["A" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["B" + str(row)] = stock["particulars"].title()
                        sheet["B" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)] = ""
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["D" + str(row)] = ""
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["D" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["E" + str(row)] = ""
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["E" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["F" + str(row)] = ""
                        sheet["F" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["F" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["G" + str(row)] = ""
                        sheet["G" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["G" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["H" + str(row)] = float(
                            "%.2f" % float(stock["totalinwardqty"])
                        )
                        sheet["H" + str(row)].number_format = "0.00"
                        sheet["H" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["H" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["I" + str(row)] = float(
                            "%.2f" % float(stock["totaloutwardqty"])
                        )
                        sheet["I" + str(row)].number_format = "0.00"
                        sheet["I" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["I" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["J" + str(row)] = ""
                        sheet["J" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["J" + str(row)].alignment = Alignment(horizontal="right")
                    row += 1
            else:
                sheet["A1"] = orgname + " (FY: " + fystart + " to " + fyend + ")"
                sheet["A3"] = (
                    "Product Report (Period : "
                    + calculatefrom
                    + " to "
                    + calculateto
                    + ")"
                )
                sheet["A4"] = "Name of the Product: " + productdesc
                sheet["A5"] = "Date"
                sheet["B5"] = "Particulars"
                sheet["C5"] = "Document Type"
                sheet["D5"] = "Deli Note No."
                sheet["E5"] = "INV/DR/CR No."
                sheet["F5"] = "RN No."
                sheet["G5"] = "Inward"
                sheet["H5"] = "Outward"
                sheet["I5"] = "Balance"
                titlerow = sheet.row_dimensions[5]
                titlerow.font = Font(name="Liberation Serif", size=12, bold=True)
                titlerow.alignment = Alignment(horizontal="center", vertical="center")
                sheet["G5"].alignment = Alignment(horizontal="right")
                sheet["G5"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["H5"].alignment = Alignment(horizontal="right")
                sheet["H5"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["I5"].alignment = Alignment(horizontal="right")
                sheet["I5"].font = Font(name="Liberation Serif", size=12, bold=True)
                row = 6

                for stock in result:
                    if stock["trntype"] == "delchal":
                        trn = "Delivery Note"
                    if stock["trntype"] == "invoice":
                        trn = "Invoice "
                    if stock["trntype"] == "delchal&invoice":
                        trn = "Delivery Note & Invoice"
                    if stock["trntype"] == "transfer note":
                        trn = "Transfer Note "
                    if stock["trntype"] == "Rejection Note":
                        trn = "Rejection Note"
                    if stock["trntype"] == "Debit Note":
                        trn = "Debit Note"
                    if stock["trntype"] == "Credit Note":
                        trn = "Credit Note"

                    if (
                        stock["particulars"] == "opening stock"
                        and stock["dcno"] == ""
                        and stock["invno"] == ""
                        and stock["date"] == ""
                    ):
                        sheet["A" + str(row)] = ""
                        sheet["A" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["A" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["B" + str(row)] = stock["particulars"].title()
                        sheet["B" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)] = ""
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["D" + str(row)] = ""
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["D" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["E" + str(row)] = ""
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["E" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["F" + str(row)] = ""
                        sheet["F" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["F" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["G" + str(row)] = float("%.2f" % float(stock["inward"]))
                        sheet["G" + str(row)].number_format = "0.00"
                        sheet["G" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["G" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["H" + str(row)] = ""
                        sheet["H" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["H" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["I" + str(row)] = ""
                        sheet["I" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["I" + str(row)].alignment = Alignment(horizontal="right")
                    if (
                        stock["particulars"] != "Total"
                        and (
                            stock["dcno"] != ""
                            or stock["invno"] != ""
                            or stock["rnid"] != ""
                            or stock["drcrno"] != ""
                        )
                        and stock["date"] != ""
                    ):
                        sheet["A" + str(row)] = stock["date"]
                        sheet["A" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["A" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["B" + str(row)] = stock["particulars"]
                        sheet["B" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )

                        sheet["C" + str(row)] = trn
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )

                        sheet["C" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["D" + str(row)] = stock["dcno"]
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["D" + str(row)].alignment = Alignment(horizontal="center")
                        if stock["invno"] != "":
                            sheet["E" + str(row)] = stock["invno"]
                        elif "drcrno" in stock and stock["drcrno"] != "":
                            sheet["E" + str(row)] = stock["drcrno"]
                        else:
                            sheet["E" + str(row)] = ""
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["E" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["F" + str(row)] = stock["rnno"]
                        sheet["F" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["F" + str(row)].alignment = Alignment(horizontal="right")
                        if stock["inwardqty"] != "":
                            sheet["G" + str(row)] = float(
                                "%.2f" % float(stock["inwardqty"])
                            )
                            sheet["G" + str(row)].number_format = "0.00"
                            sheet["G" + str(row)].font = Font(
                                name="Liberation Serif", size="12", bold=False
                            )
                            sheet["G" + str(row)].alignment = Alignment(
                                horizontal="right"
                            )
                        if stock["outwardqty"] != "":
                            sheet["H" + str(row)] = float(
                                "%.2f" % float(stock["outwardqty"])
                            )
                            sheet["H" + str(row)].number_format = "0.00"
                            sheet["H" + str(row)].font = Font(
                                name="Liberation Serif", size="12", bold=False
                            )
                            sheet["H" + str(row)].alignment = Alignment(
                                horizontal="right"
                            )
                        sheet["I" + str(row)] = float("%.2f" % float(stock["balance"]))
                        sheet["I" + str(row)].number_format = "0.00"
                        sheet["I" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["I" + str(row)].alignment = Alignment(horizontal="right")
                    if (
                        stock["particulars"] == "Total"
                        and stock["dcno"] == ""
                        and stock["invno"] == ""
                        and stock["date"] == ""
                    ):
                        sheet["A" + str(row)] = ""
                        sheet["A" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["A" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["B" + str(row)] = stock["particulars"].title()
                        sheet["B" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)] = ""
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["C" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["D" + str(row)] = ""
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["D" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["E" + str(row)] = ""
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["E" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["F" + str(row)] = ""
                        sheet["F" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["F" + str(row)].alignment = Alignment(horizontal="center")
                        sheet["G" + str(row)] = float(
                            "%.2f" % float(stock["totalinwardqty"])
                        )
                        sheet["G" + str(row)].number_format = "0.00"
                        sheet["G" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["G" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["H" + str(row)] = float(
                            "%.2f" % float(stock["totaloutwardqty"])
                        )
                        sheet["H" + str(row)].number_format = "0.00"
                        sheet["H" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["H" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["I" + str(row)] = ""
                        sheet["I" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        sheet["I" + str(row)].alignment = Alignment(horizontal="right")
                    row += 1
            output = io.BytesIO()
            prowb.save(output)
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

            return Response(contents, headerlist=list(headerList.items()))
        except Exception as e:
            print("exception:", e)
            return {"gkstatus": 3}

    @view_config(
        request_method="GET", request_param="type=trialbalance", renderer="json"
    )
    def print_trial_balance(self):
        """
        This function returns a spreadsheet form of Trial Balance Report.
        The spreadsheet in XLSX format is generated by the frontendend.
        """
        try:
            header = {"gktoken": self.request.headers["gktoken"]}
            orgname = self.request.params["orgname"]
            financialstart = self.request.params["fystart"]
            fyend = str(self.request.params["fyend"])
            startdate = self.request.params["fystart"]
            calculateto = self.request.params["calculateto"]
            trialbalancetype = int(self.request.params["trialbalancetype"])
            if trialbalancetype == 1:
                subreq = Request.blank(
                    "/report?type=nettrialbalance&calculateto=%s&financialstart=%s"
                    % (calculateto, financialstart),
                    headers=header,
                )
                result = self.request.invoke_subrequest(subreq)
            elif trialbalancetype == 2:
                subreq = Request.blank(
                    "/report?type=extendedtrialbalance&calculateto=%s&financialstart=%s"
                    % (calculateto, financialstart),
                    headers=header,
                )
                result = self.request.invoke_subrequest(subreq)
            elif trialbalancetype == 3:
                subreq = Request.blank(
                    "/report?type=extendedtrialbalance&calculateto=%s&financialstart=%s"
                    % (calculateto, financialstart),
                    headers=header,
                )
                result = self.request.invoke_subrequest(subreq)
            records = json.loads(result.text)["gkresult"]
            trialbalancewb = openpyxl.Workbook()
            sheet = trialbalancewb.active
            sheet.title = "Trial Balance of %s" % (str(orgname))
            # Condition for Net Trial Balance
            if trialbalancetype == 1:
                sheet.column_dimensions["A"].width = 8
                sheet.column_dimensions["B"].width = 20
                sheet.column_dimensions["C"].width = 14
                sheet.column_dimensions["D"].width = 16
                sheet.column_dimensions["E"].width = 22
                # Cells of first two rows are merged to display organisation details properly.
                sheet.merge_cells("A1:E2")
                # Name and Financial Year of organisation is fetched to be displayed on the first row.
                sheet["A1"].font = Font(name="Liberation Serif", size="16", bold=True)
                sheet["A1"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                # Organisation name and financial year are displayed.
                sheet["A1"] = (
                    orgname
                    + " (FY: "
                    + datetime.strptime(str(financialstart), "%Y-%m-%d").strftime(
                        "%d-%m-%Y"
                    )
                    + " to "
                    + fyend
                    + ")"
                )
                sheet.merge_cells("A3:F3")
                sheet["A3"].font = Font(name="Liberation Serif", size="14", bold=True)
                sheet["A3"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                sheet["A3"] = "Net Trial Balance for the period from %s to %s" % (
                    datetime.strptime(str(startdate), "%Y-%m-%d").strftime("%d-%m-%Y"),
                    datetime.strptime(str(calculateto), "%Y-%m-%d").strftime(
                        "%d-%m-%Y"
                    ),
                )
                sheet["A4"] = "Sr. No."
                sheet["B4"] = "Account Name"
                sheet["C4"] = "Debit"
                sheet["D4"] = "Credit"
                sheet["E4"] = "Group Name"
                titlerow = sheet.row_dimensions[4]
                titlerow.font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["C4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["D4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["E4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["c4"].alignment = Alignment(horizontal="right")
                sheet["D4"].alignment = Alignment(horizontal="right")
                sheet["E4"].alignment = Alignment(horizontal="center")
                row = 5
                for record in records:
                    sheet["A" + str(row)] = record["srno"]
                    sheet["A" + str(row)].alignment = Alignment(horizontal="left")
                    sheet["A" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    sheet["B" + str(row)] = record["accountname"]
                    sheet["B" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    if record["advflag"] == 1:
                        if record["Dr"] != "":
                            sheet["C" + str(row)] = float("%.2f" % float(record["Dr"]))
                            sheet["C" + str(row)].number_format = "0.00"
                            sheet["C" + str(row)].alignment = Alignment(
                                horizontal="right"
                            )
                            sheet["C" + str(row)].font = Font(
                                name="Liberation Serif", size="12", bold=True, color=RED
                            )
                        if record["Cr"] != "":
                            sheet["D" + str(row)] = float("%.2f" % float(record["Cr"]))
                            sheet["D" + str(row)].number_format = "0.00"
                        sheet["D" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=True, color=RED
                        )
                    else:
                        if record["Dr"] != "":
                            sheet["C" + str(row)] = float("%.2f" % float(record["Dr"]))
                            sheet["C" + str(row)].number_format = "0.00"
                        sheet["C" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        if record["Cr"] != "":
                            sheet["D" + str(row)] = float("%.2f" % float(record["Cr"]))
                            sheet["D" + str(row)].number_format = "0.00"
                        sheet["D" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                    sheet["E" + str(row)] = record["groupname"]
                    sheet["E" + str(row)].alignment = Alignment(horizontal="center")
                    sheet["E" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    row = row + 1
            # Condition for Gross Trial Balance
            elif trialbalancetype == 2:
                sheet.column_dimensions["A"].width = 8
                sheet.column_dimensions["B"].width = 20
                sheet.column_dimensions["C"].width = 18
                sheet.column_dimensions["D"].width = 18
                sheet.column_dimensions["E"].width = 20
                sheet.column_dimensions["F"].width = 20
                sheet.column_dimensions["G"].width = 20
                # Cells of first two rows are merged to display organisation details properly.
                sheet.merge_cells("A1:G2")
                # Name and Financial Year of organisation is fetched to be displayed on the first row.
                sheet["A1"].font = Font(name="Liberation Serif", size="16", bold=True)
                sheet["A1"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                # Organisation name and financial year are displayed.
                sheet["A1"] = (
                    orgname
                    + " (FY: "
                    + datetime.strptime(str(financialstart), "%Y-%m-%d").strftime(
                        "%d-%m-%Y"
                    )
                    + " to "
                    + fyend
                    + ")"
                )
                sheet.merge_cells("A3:G3")
                sheet["A3"].font = Font(name="Liberation Serif", size="14", bold=True)
                sheet["A3"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                sheet["A3"] = "Gross Trial Balance for the period from %s to %s" % (
                    datetime.strptime(str(startdate), "%Y-%m-%d").strftime("%d-%m-%Y"),
                    datetime.strptime(str(calculateto), "%Y-%m-%d").strftime(
                        "%d-%m-%Y"
                    ),
                )
                sheet["A4"] = "Sr. No. "
                sheet["B4"] = "Account Name"
                sheet["C4"] = "Debit"
                sheet["D4"] = "Credit"
                sheet["E4"] = "Dr Balance"
                sheet["F4"] = "Cr Balance"
                sheet["G4"] = "Group Name"
                titlerow = sheet.row_dimensions[4]
                titlerow.font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["C4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["D4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["E4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["F4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["G4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["c4"].alignment = Alignment(horizontal="right")
                sheet["D4"].alignment = Alignment(horizontal="right")
                sheet["E4"].alignment = Alignment(horizontal="right")
                sheet["F4"].alignment = Alignment(horizontal="right")
                sheet["G4"].alignment = Alignment(horizontal="center")
                row = 5
                for record in records:
                    sheet["A" + str(row)] = record["srno"]
                    sheet["A" + str(row)].alignment = Alignment(horizontal="center")
                    sheet["A" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    sheet["B" + str(row)] = record["accountname"]
                    sheet["B" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    if record["totaldr"] != "":
                        sheet["C" + str(row)] = float("%.2f" % float(record["totaldr"]))
                        sheet["C" + str(row)].number_format = "0.00"
                    sheet["C" + str(row)].alignment = Alignment(horizontal="right")
                    sheet["C" + str(row)].font = Font(
                        name="Liberation Serif", bold=False
                    )
                    if record["totalcr"] != "":
                        sheet["D" + str(row)] = float("%.2f" % float(record["totalcr"]))
                        sheet["D" + str(row)].number_format = "0.00"
                    sheet["D" + str(row)].alignment = Alignment(horizontal="right")
                    sheet["D" + str(row)].font = Font(
                        name="Liberation Serif", bold=False
                    )
                    if record["advflag"] == 1:
                        if record["curbaldr"] != "":
                            sheet["E" + str(row)] = float(
                                "%.2f" % float(record["curbaldr"])
                            )
                            sheet["E" + str(row)].number_format = "0.00"
                        sheet["E" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=True, color=RED
                        )
                        if record["curbalcr"] != "":
                            sheet["F" + str(row)] = float(
                                "%.2f" % float(record["curbalcr"])
                            )
                            sheet["F" + str(row)].number_format = "0.00"
                        sheet["F" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["F" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=True, color=RED
                        )
                    else:
                        if record["curbaldr"] != "":
                            sheet["E" + str(row)] = float(
                                "%.2f" % float(record["curbaldr"])
                            )
                            sheet["E" + str(row)].number_format = "0.00"
                        sheet["E" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        if record["curbalcr"] != "":
                            sheet["F" + str(row)] = float(
                                "%.2f" % float(record["curbalcr"])
                            )
                            sheet["F" + str(row)].number_format = "0.00"
                        sheet["F" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["F" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                    sheet["G" + str(row)] = record["groupname"]
                    sheet["G" + str(row)].alignment = Alignment(horizontal="center")
                    sheet["G" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    row = row + 1
            # Condition for Extended Trial Balance
            elif trialbalancetype == 3:
                sheet.column_dimensions["A"].width = 8
                sheet.column_dimensions["B"].width = 20
                sheet.column_dimensions["C"].width = 18
                sheet.column_dimensions["D"].width = 16
                sheet.column_dimensions["E"].width = 16
                sheet.column_dimensions["F"].width = 16
                sheet.column_dimensions["G"].width = 16
                sheet.column_dimensions["H"].width = 20
                # Cells of first two rows are merged to display organisation details properly.
                sheet.merge_cells("A1:H2")
                # Name and Financial Year of organisation is fetched to be displayed on the first row.
                sheet["A1"].font = Font(name="Liberation Serif", size="16", bold=True)
                sheet["A1"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                # Organisation name and financial year are displayed.
                sheet["A1"] = (
                    orgname
                    + " (FY: "
                    + datetime.strptime(str(financialstart), "%Y-%m-%d").strftime(
                        "%d-%m-%Y"
                    )
                    + " to "
                    + fyend
                    + ")"
                )
                sheet.merge_cells("A3:H3")
                sheet["A3"].font = Font(name="Liberation Serif", size="14", bold=True)
                sheet["A3"].alignment = Alignment(
                    horizontal="center", vertical="center"
                )
                sheet["A3"] = "Extended Trial Balance for the period from %s to %s" % (
                    datetime.strptime(str(startdate), "%Y-%m-%d").strftime("%d-%m-%Y"),
                    datetime.strptime(str(calculateto), "%Y-%m-%d").strftime(
                        "%d-%m-%Y"
                    ),
                )
                sheet["A4"] = "Sr. No. "
                sheet["B4"] = "Account Name"
                sheet["C4"] = "Opening Balance"
                sheet["D4"] = "Total Debit"
                sheet["E4"] = "Total Credit"
                sheet["F4"] = "Debit Balance"
                sheet["G4"] = "Credit Balance"
                sheet["H4"] = "Group Name"
                titlerow = sheet.row_dimensions[4]
                titlerow.font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["C4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["D4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["E4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["F4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["G4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["H4"].font = Font(name="Liberation Serif", size=12, bold=True)
                sheet["c4"].alignment = Alignment(horizontal="right")
                sheet["D4"].alignment = Alignment(horizontal="right")
                sheet["E4"].alignment = Alignment(horizontal="right")
                sheet["F4"].alignment = Alignment(horizontal="right")
                sheet["G4"].alignment = Alignment(horizontal="right")
                sheet["H4"].alignment = Alignment(horizontal="center")
                row = 5
                for record in records:
                    sheet["A" + str(row)] = record["srno"]
                    sheet["A" + str(row)].alignment = Alignment(horizontal="center")
                    sheet["A" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    sheet["B" + str(row)] = record["accountname"]
                    sheet["B" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    if record["openingbalance"] == "0.00":
                        sheet["C" + str(row)] = float(
                            "%.2f" % float(record["openingbalance"])
                        )
                        sheet["C" + str(row)].number_format = "0.00"
                        sheet["C" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                    else:
                        sheet["C" + str(row)] = record["openingbalance"]
                        sheet["C" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                    if record["totaldr"] != "":
                        sheet["D" + str(row)] = float("%.2f" % float(record["totaldr"]))
                        sheet["D" + str(row)].number_format = "0.00"
                        sheet["D" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["D" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                    if record["totalcr"] != "":
                        sheet["E" + str(row)] = float("%.2f" % float(record["totalcr"]))
                        sheet["E" + str(row)].number_format = "0.00"
                        sheet["E" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["E" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                    if record["advflag"] == 1:
                        if record["curbaldr"] != "":
                            sheet["F" + str(row)] = float(
                                "%.2f" % float(record["curbaldr"])
                            )
                            sheet["F" + str(row)].number_format = "0.00"
                            sheet["F" + str(row)].alignment = Alignment(
                                horizontal="right"
                            )
                            sheet["F" + str(row)].font = Font(
                                name="Liberation Serif", size="12", bold=True, color=RED
                            )
                        if record["curbalcr"] != "":
                            sheet["G" + str(row)] = float(
                                "%.2f" % float(record["curbalcr"])
                            )
                            sheet["G" + str(row)].number_format = "0.00"
                            sheet["G" + str(row)].alignment = Alignment(
                                horizontal="right"
                            )
                            sheet["G" + str(row)].font = Font(
                                name="Liberation Serif", size="12", bold=True, color=RED
                            )
                    else:
                        if record["curbaldr"] != "":
                            sheet["F" + str(row)] = float(
                                "%.2f" % float(record["curbaldr"])
                            )
                            sheet["F" + str(row)].number_format = "0.00"
                        sheet["F" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["F" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                        if record["curbalcr"] != "":
                            sheet["G" + str(row)] = float(
                                "%.2f" % float(record["curbalcr"])
                            )
                            sheet["G" + str(row)].number_format = "0.00"
                        sheet["G" + str(row)].alignment = Alignment(horizontal="right")
                        sheet["G" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                    sheet["H" + str(row)] = record["groupname"]
                    sheet["H" + str(row)].alignment = Alignment(horizontal="center")
                    sheet["H" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    row = row + 1
            output = io.BytesIO()
            trialbalancewb.save(output)
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

            return Response(contents, headerlist=list(headerList.items()))
        except:
            print("file not found")
            return {"gkstatus": 3}

    @view_config(request_method="GET", request_param="type=pslist", renderer="json")
    def product_service_list(self):

        """
        This function returns a spreadsheet form of List of Products Report.
        The spreadsheet in XLSX format is generated by the backend and sent in base64 encoded format.
        It is decoded and returned along with mime information.

        params:

        fystart = financial year beginning in yyyymmdd format
        fyend = financial year ending in yyyymmdd format
        orgname = organisation name
        """
        try:
            header = {"gktoken": self.request.headers["gktoken"]}
            subreq = Request.blank("/products", headers=header)
            # result = requests.get("http://127.0.0.1:6543/products", headers=header)
            result = self.request.invoke_subrequest(subreq)
            subreq2 = Request.blank("/products?tax=vatorgst", headers=header)
            result2 = self.request.invoke_subrequest(subreq2)
            # resultgstvat = resultgstvat.json()["gkresult"]
            resultgstvat = json.loads(result2.text)["gkresult"]
            result = json.loads(result.text)["gkresult"]
            fystart = str(self.request.params["fystart"])
            fyend = str(self.request.params["fyend"])
            orgname = str(self.request.params["orgname"])
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
            sheet["A1"].alignment = Alignment(horizontal="center", vertical="center")
            # Organisation name and financial year are displayed.
            sheet["A1"] = orgname + " (FY: " + fystart + " to " + fyend + ")"
            sheet.merge_cells("A3:E3")
            sheet["A3"].font = Font(name="Liberation Serif", size="14", bold=True)
            sheet["A3"].alignment = Alignment(horizontal="center", vertical="center")
            sheet["A3"] = "List of Products"
            sheet.merge_cells("A3:E3")
            sheet["A4"] = "Sr.No."
            if resultgstvat == "22":
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
            if resultgstvat == "22":
                row = 5
                for stock in result:
                    sheet["A" + str(row)] = srno
                    sheet["A" + str(row)].alignment = Alignment(horizontal="left")
                    sheet["A" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    sheet["B" + str(row)] = stock["productdesc"]
                    sheet["B" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    sheet["C" + str(row)] = stock["categoryname"]
                    sheet["C" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    sheet["D" + str(row)] = stock["unitname"]
                    sheet["D" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    row += 1
                    srno += 1
            else:
                row = 5
                for stock in result:
                    sheet["A" + str(row)] = srno
                    sheet["A" + str(row)].alignment = Alignment(horizontal="left")
                    sheet["A" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    sheet["B" + str(row)] = stock["productdesc"]
                    sheet["B" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    if stock["gsflag"] == 7:
                        sheet["C" + str(row)] = "Product"
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                    else:
                        sheet["C" + str(row)] = "Service"
                        sheet["C" + str(row)].font = Font(
                            name="Liberation Serif", size="12", bold=False
                        )
                    sheet["D" + str(row)] = stock["categoryname"]
                    sheet["D" + str(row)].font = Font(
                        name="Liberation Serif", size="12", bold=False
                    )
                    sheet["E" + str(row)] = stock["unitname"]
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
            return Response(contents, headerlist=list(headerList.items()))
        except:
            return {"gkstatus": 3}
