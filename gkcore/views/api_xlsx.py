"""
Copyright (C) 2013, 2014, 2015, 2016, 2017 Digital Freedom Foundation
Copyright (C) 2017, 2018 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330.
"""

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc,alias, or_, func, desc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.sql.expression import null
from gkcore.models.meta import dbconnect
from gkcore.models.gkdb import  accounts, vouchers, groupsubgroups, projects, organisation, users, voucherbin,delchal,invoice,customerandsupplier,stock,product,transfernote,goprod, dcinv, log,godown, categorysubcategories, rejectionnote
from datetime import datetime, date
from monthdelta import monthdelta
from gkcore.models.meta import dbconnect
from sqlalchemy.sql.functions import func
from time import strftime, strptime
import openpyxl
from openpyxl.styles import Font, Alignment
import base64
import os


@view_config(request_method='GET', request_param="type=sprdsheet", renderer="json")
def spreadsheetForUserreport(self):
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
                 # A workbook is opened.
                userwb = openpyxl.Workbook()
                # A new sheet is created.
                userwb.create_sheet()
                # The new sheet is the active sheet as no other sheet exists. It is set as value of variable - sheet.
                sheet = userwb.active
                # Title of the sheet and width of columns are set.
                sheet.title = "List of Users"
                sheet.column_dimensions['A'].width = 8
                sheet.column_dimensions['B'].width = 18
                sheet.column_dimensions['C'].width = 14
                sheet.column_dimensions['D'].width = 24
                # Cells of first two rows are merged to display organisation details properly.
                sheet.merge_cells('A1:D2')
                # Name and Financial Year of organisation is fetched to be displayed on the first row.
                orgdata = self.con.execute(select([organisation.c.orgname, organisation.c.yearstart, organisation.c.yearend]).where(organisation.c.orgcode==authDetails["orgcode"]))
                orgdetails = orgdata.fetchone()
                
                # Font and Alignment of cells are set. Each cell can be identified using the cell index - column name and row number.
                sheet['A1'].font = Font(name='Liberation Serif',size='16',bold=True)
                sheet['A1'].alignment = Alignment(horizontal = 'center', vertical='center')
                # Organisation name and financial year are displayed.
                sheet['A1'] = orgdetails["orgname"] + ' (FY: ' + datetime.strftime(orgdetails["yearstart"],'%d-%m-%Y') + ' to ' + datetime.strftime(orgdetails["yearend"],'%d-%m-%Y') +')'
                sheet.merge_cells('A3:D3')
                sheet['A3'].font = Font(name='Liberation Serif',size='14',bold=True)
                sheet['A3'].alignment = Alignment(horizontal = 'center', vertical='center')
                sheet['A3'] = 'List of Unpaid Invoices'
                sheet.merge_cells('A4:D4')
                sheet['A4'] = 'Period: ' + str(self.request.params["startdate"]) + ' to ' + str(self.request.params["enddate"])
                sheet['A4'].font = Font(name='Liberation Serif',size='14',bold=True)
                sheet['A4'].alignment = Alignment(horizontal = 'center', vertical='center')
                sheet['A5'] = 'Sr. No. '
                sheet['B5'] = 'User Name'
                sheet['C5'] = 'User Role'
                sheet['D5'] = 'Associated Godown(s)'
                titlerow = sheet.row_dimensions[5]
                titlerow.font = Font(name='Liberation Serif',size=12,bold=True)
                 # Saving the xlsx file.
                userwb.save('report.xlsx')
                # Opening xlsx file in read only mode.
                reportxslx = open("report.xlsx","r")
                # Encoding xlsx file in base64 format.
                xlsxdata = base64.b64encode(reportxslx.read())
                # Closing file.
                reportxslx.close()
                os.remove("report.xlsx")
                return {"gkstatus":enumdict["Success"],"gkdata":xlsxdata}
            except:
                print "Spreadsheet not created."
                return {"gkstatus":3}
