
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

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
"Prajkta Patkar" <prajkta.patkar007@gmail.com>

"""

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models.gkdb import organisation,accounts,users,bankrecon,categorysubcategories,categoryspecs,customerandsupplier,dcinv,delchal,godown,goprod,groupsubgroups,invoice,projects,product,purchaseorder,transfernote,stock,tax,unitofmeasurement,vouchers,voucherbin
from sqlalchemy.sql import select
from datetime import datetime,date
from openpyxl import Workbook
from openpyxl.styles import Font
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result
import gkcore
import os
from sqlalchemy.sql.functions import func
import base64
import cPickle
from datetime import datetime
import tarfile
from tarfile import TarFile
import user

@view_defaults(route_name='backuprestore')
class api_backuprestore(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
		print "backup initialized"
		
	@view_config(request_method='GET',renderer='json',request_param='fulldb=1')
	def backupdatabase(self):
		""" This method backsup entire database with organisation.
		First it checks the user role if the user is admin then only user can do the backup					  """
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}

		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				user=self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				if userRole[0]==-1:
					os.system("pg_dump -a -Ft -t organisation -t groupsubgroups -t accounts -t users -t projects -t bankrecon -t customerandsupplier -t categorysubcategories -t categoryspecs -t unitofmeasurement -t product -t tax -t godown -t goprod -t purchaseorder -t delchal -t invoice -t dcinv -t stock -t transfernote -t vouchers -t voucherbin  gkdata -f /tmp/gkbackup.tar")
					backupfile = open("/tmp/gkbackup.tar","r")
					backup_str = base64.b64encode(backupfile.read())
					backupfile.close()
					return {"gkstatus":enumdict["Success"],"gkdata":backup_str}
				else:
					return {"gkstatus":  enumdict["BadPrivilege"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			finally:
				self.con.close()
				
	@view_config(request_method='GET',renderer='json',request_param='fulldb=0')
	def backuporg(self):
		""" Purpose:
		This function gives a backup of all data for an entire organisation for a given financial year.
		Returns a spreadsheet in encoded form with list of accounts under their groups or subgroups in the first sheet.
		and second sheet with all vouchers.
		description:
		this function will take orgcode and userid from the get request.
		Once this data is taken from the json_body the processing is done for that organisation.
		Firstly check for the user's role.  If it is admin then,
		Query to organisation table and get organisation name , yearstart and yearend ; Fill this data into first row. 
		First it gets the list of all main groups.
		Then a main loop runs through this list.
		For each iteration a cell is created with the current groupname in bold.
		after the cell is created,
		In this loop we first check if any accounts exist for the main group.
		if row count is > 0 for the select query,
		then a loop is run to add every account name one below the other in successive cells.
		The account name is in italics.
		now query for list of subgroup for this group. 
		then if there are subgroups for this group using groupcode in the select query,
		run a for loop.
		This means if the rowcount is more than 0 then a for loop is run for these subgroups.
		At the beginning of this subgroup loop the name of the subgroup is put exactly under the group if no accounts were directly in the group,
		Else the subgroup will be put under the cell containing the last account for the main group.
		Inside this for loop we check for the list of accounts.
		If there are accounts (check for row count after query ) then run another loop inside.
		All that this loop will do is to add account name in cells below the subgroup.
		Note that account names will be in italics.
		
		Once all accounts entries have been added to first sheet next sheet will be created for vouchers entries.
		Now query for vouchers details such as voucherdate , vouchernumber , vouchertype , narration ,crs and drs , projectcode.
		if rowcount > 0 , fetch all data which query has return.
		loop through data & Add data in the rows and columns accordingly.
		Format decided for adding data to the spreadsheet is as follows VoucherNumber ,Date, VoucherType , DebitAccount , Debit amount,CreditAccount , Credit amount ,Narration , Lockflag , Projectname; 
		Title for each field is mentioned in 1st row.
		Filling details(values) start from column 1 and fill up the columns upto column 10 of 2nd row respectively. Row counter will increase by 1 as soon as all details in current in row is filled up.
		To get accountname for creditaccount and debitaccount firstly get accountcode form dictionary crs and drs .
		query to accounts table using accountcode and retrieve accountname.
		For multiple crs and drs for each entry , Entries for accountname and amount will be added to immediate next row .
		Projectname can be find using projectcode. If project name exists project name will be added for that voucher entry else field will be blank.
		At last Save the file in xlsx format by giving suitable name.
		For better compression tar.bz2 file format is used.
		encode the compressed file using base64 encode format , now file has been converted into encoded string format, So that we can use it as value to JSON dictionary.
				
		"""
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				user=self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				if userRole[0]==-1:
					#create a workbook
					#open the book with one sheet.
					#then we will get list of all groups.
					gkwb = Workbook()
					accountList = gkwb.active
					accountList.title = "Account List"
					accountList.column_dimensions["A"].width = 100
					
					orgInfo = self.con.execute(select([organisation.c.orgname,organisation.c.orgtype,organisation.c.yearstart,organisation.c.yearend]).where(organisation.c.orgcode == authDetails["orgcode"] ))
					org = orgInfo.fetchone()
					t = accountList.cell(row=1,column=1,value= org["orgname"])
					t = accountList.cell(row=1,column=2,value= org["orgtype"])
					t = accountList.cell(row=1,column=3,value= str(org["yearstart"].strftime('%d-%m-%Y')))
					t = accountList.cell(row=1,column=4,value= str(org["yearend"].strftime('%d-%m-%Y')))
								
					mainGroups = self.con.execute(select([groupsubgroups.c.groupcode, groupsubgroups.c.groupname]).where(and_(groupsubgroups.c.orgcode == authDetails["orgcode"], groupsubgroups.c.subgroupof == None )))
					groups =  mainGroups.fetchall()
					cellCounter = 3
					for group in groups:
						#create first row with cell containing groupname.
						#make it bold style with font object and then go for it's accounts first.
						c = accountList.cell(row=cellCounter,column=1,value=group["groupname"])
						c.font = Font(name=c.font.name,bold=True)
						cellCounter = cellCounter + 1
						grpaccounts = self.con.execute(select([accounts.c.accountname]).where(and_(accounts.c.groupcode == group["groupcode"],accounts.c.orgcode == authDetails["orgcode"]) ))
						if grpaccounts.rowcount > 0:
							account = grpaccounts.fetchall()
							for acct in account:
								a = accountList.cell(row=cellCounter,column=1,value= acct["accountname"])
								a.font = Font(name=a.font.name,italic=True) 
								cellCounter = cellCounter + 1
						#search for subgroups existing for main group , create row with cell containing subgroup
						#then search for accounts existing for subgroup. and create new cell immediately under subgroup.
						subgrp = self.con.execute(select([groupsubgroups.c.groupcode, groupsubgroups.c.groupname]).where(and_(groupsubgroups.c.orgcode == authDetails["orgcode"], groupsubgroups.c.subgroupof ==group["groupcode"])))
						if subgrp.rowcount > 0:
							subgroup = subgrp.fetchall()
							for sg in subgroup:
								s = accountList.cell(row=cellCounter,column=1,value=sg["groupname"])
								cellCounter = cellCounter + 1
								grpaccounts = self.con.execute(select([accounts.c.accountname]).where(and_(accounts.c.groupcode == sg["groupcode"],accounts.c.orgcode == authDetails["orgcode"]) ))
								if grpaccounts.rowcount > 0:
									account = grpaccounts.fetchall()
									for acct in account:
										a = accountList.cell(row=cellCounter,column=1,value= acct["accountname"])
										a.font = Font(name=a.font.name,italic=True) 
										cellCounter = cellCounter + 1
										
					Vouchers = gkwb.create_sheet(title="Vouchers")
					voucher = self.con.execute(select([vouchers.c.vouchernumber,vouchers.c.voucherdate,vouchers.c.narration,vouchers.c.vouchertype,vouchers.c.drs,vouchers.c.crs,vouchers.c.lockflag,vouchers.c.projectcode]).where(vouchers.c.orgcode== authDetails["orgcode"]))
					
					Vouchers.column_dimensions["D"].width = 25 
					Vouchers.column_dimensions["F"].width = 25
					Vouchers.column_dimensions["H"].width = 20
					Vouchers.column_dimensions["J"].width = 20
					Vouchers.cell(row= 1,column=1,value= "VchNo")
					Vouchers.cell(row= 1,column=2,value= "Date")
					Vouchers.cell(row= 1,column=3,value= "VchType")
					Vouchers.cell(row= 1,column=4,value= "DrAcc")
					Vouchers.cell(row= 1,column=5,value= "DrAmt")
					Vouchers.cell(row= 1,column=6,value= "CrAcc")
					Vouchers.cell(row= 1,column=7,value= "CrAmt")
					Vouchers.cell(row= 1,column=8,value= "Narration")
					Vouchers.cell(row= 1,column=9,value= "Lockflag")
					Vouchers.cell(row= 1,column=10,value= "Project")
						
					rowcounter = 2	
					if voucher.rowcount > 0:
						voucherData = voucher.fetchall()
						for vch in voucherData:
							vn = Vouchers.cell(row= rowcounter,column=1,value=vch["vouchernumber"]) 
							vd =  Vouchers.cell(row= rowcounter,column=2,value= str(vch["voucherdate"].date().strftime('%d-%m-%Y'))) 
							vt =  Vouchers.cell(row= rowcounter,column=3,value=vch["vouchertype"])
							dr = vch["drs"]
							drcounter = rowcounter
							for draccno in dr.keys():
								draccname = self.con.execute(select([accounts.c.accountname]).where(and_(accounts.c.accountcode == draccno , accounts.c.orgcode == authDetails["orgcode"])))
								dracctname = draccname.fetchone()
								drAccName =  Vouchers.cell(row= drcounter,column=4,value=dracctname["accountname"])
								drValue = Vouchers.cell(row= drcounter,column=5,value= "%.2f"%float(dr[draccno]))
								drcounter = drcounter + 1
								
							cr = vch["crs"]
							crcounter = rowcounter
							for craccno in cr.keys():
								craccname = self.con.execute(select([accounts.c.accountname]).where(and_(accounts.c.accountcode == craccno,accounts.c.orgcode == authDetails["orgcode"])))
								cracctname = craccname.fetchone()
								crAccName = Vouchers.cell(row= crcounter,column=6,value=cracctname["accountname"])
								crvalue = Vouchers.cell(row= crcounter,column=7,value= "%.2f"%float(cr[craccno]))
								crcounter = crcounter + 1
							
							vnr = Vouchers.cell(row= rowcounter,column=8,value=vch["narration"])
							vl = Vouchers.cell(row= rowcounter,column=9,value=vch["lockflag"])
							prj = self.con.execute(select([projects.c.projectname]).where(and_(projects.c.projectcode == vch["projectcode"], projects.c.orgcode == authDetails["orgcode"])))
							prjname = prj.fetchone()
							if prjname != None:
								vp = Vouchers.cell(row= rowcounter,column=10,value=prjname["projectname"])
							else:
								vp = Vouchers.cell(row= rowcounter,column=10,value= " ")
							
							
							if drcounter >= rowcounter:
								rowcounter = drcounter + 1
							else :
								rowcounter = crcounter + 1
							
							
					gkwb.save(filename = "/tmp/GkExport.xlsx")
					cmp = tarfile.open("/tmp/GkOrgExport.tar.bz2","w:bz2")
					cmp.add("/tmp/GkExport.xlsx")
					cmp.close()
					os.system("rm /tmp/GkExport.xlsx")
					gkarch = open("GkOrgExport.tar.bz2","r")
					archData = base64.b64encode(gkarch.read())
					gkarch.close()

																
					return {"gkstatus":enumdict["Success"],"gkdata":archData}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			finally:
				self.con.close() 
				
				
	
	
	@view_config(request_method='POST',renderer='json')
	def Restoredatabase(self):
		""" This method restore entire database with organisation. 
		  First it checks the user role if the user is admin then only user can do the backup					  """
		try:
			self.con = eng.connect()
			orgcount = self.con.execute(select([func.count(organisation.c.orgcode).label('orgcount')]))
			countrow = orgcount.fetchone()
			if int(countrow["orgcount"]) > 0:
				return {"gkstatus":enumdict["ActionDisallowed"]}
			dataset = self.request.json_body
			datasource = dataset["datasource"]
			restore_str = base64.b64decode(datasource)
			restorefile = open("/tmp/restore.tar","w")
			restorefile.write(restore_str)
			restorefile.close()
			os.system("pg_restore -t organisation -t groupsubgroups -t accounts -t users -t projects -t bankrecon -t customerandsupplier -t categorysubcategories -t categoryspecs -t unitofmeasurement -t product -t tax -t godown -t goprod -t purchaseorder -t delchal -t invoice -t dcinv -t stock -t transfernote  -t vouchers -t voucherbin --dbname=gkdata  /tmp/restore.tar")
		
			return {"gkstatus":enumdict["Success"]}
		except:
			return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
				

	@view_config(request_method='POST',request_param='fulldb=0',renderer='json')
	def RestoreOrg(self):
		""" This method restore entire database with organisation.
		First it checks the user role if the user is admin then only user can do the backup					  """
		try:
			self.con = eng.connect()
			dataset = self.request.json_body
			datarestore = dataset["datarestore"]
			restore_data = base64.b64decode(datarestore)
			restorewrite_file=open("restoreOrg.tar.bz2","w")
			restorewrite_file.write(restore_data)
			restorewrite_file.close()
			os.system("tar jxf restoreOrg.tar.bz2")
			
			rOrg =open("backupdir/org.back","rb")
			pOrg = cPickle.load(rOrg)
			rOrg.close()
			rGsg =open("backupdir/gsg.back","rb")
			pGsg = cPickle.load(rGsg)
			rGsg.close()
			rAcc =open("backupdir/accounts.back","rb")
			pAccount = cPickle.load(rAcc)
			rAcc.close()
			rUsr =open("backupdir/users.back","rb")
			pUser = cPickle.load(rUsr)
			rUsr.close()
			rProj =open("backupdir/projects.back","rb")
			pProjects = cPickle.load(rProj)
			rProj.close()
			rBnkrcn =open("backupdir/bankrecon.back","rb")
			pBankrecon = cPickle.load(rBnkrcn)
			rBnkrcn.close()
			rCas =open("backupdir/customerandsupplier.back","rb")
			pCustomerandsupplier = cPickle.load(rCas)
			rCas.close()
			rCasb =open("backupdir/categorysubcategories.back","rb")
			pCategorysubcategories = cPickle.load(rCasb)
			rCasb.close()
			rCtspc =open("backupdir/categoryspecs.back","rb")
			pCategoryspecs = cPickle.load(rCtspc)
			rCasb.close()
			rUm =open("backupdir/unitofmeasurement.back","rb")
			pUnitofmeasurement = cPickle.load(rUm)
			rUm.close()
			rPod =open("backupdir/product.back","rb")
			pProduct = cPickle.load(rPod)
			rPod.close()
			rGo =open("backupdir/godown.back","rb")
			pGodown = cPickle.load(rGo)
			rGo.close()
			rGoprod =open("backupdir/goprod.back","rb")
			pGoprod = cPickle.load(rGoprod)
			rGoprod.close()
			rTx =open("backupdir/tax.back","rb")
			pTax = cPickle.load(rTx)
			rTx.close()
			rPo =open("backupdir/purchaseorder.back","rb")
			pPurchaseorder = cPickle.load(rPo)
			rPo.close()
			rDc =open("backupdir/delchal.back","rb")
			pDelchal = cPickle.load(rDc)
			rDc.close()
			rIv =open("backupdir/invoice.back","rb")
			pInvoice = cPickle.load(rIv)
			rIv.close()
			rDciv =open("backupdir/dcinv.back","rb")
			pDcinv = cPickle.load(rDciv)
			rDciv.close() 
			rStk =open("backupdir/stock.back","rb")
			pStock = cPickle.load(rStk)
			rStk.close()
			rTn =open("backupdir/transfernote.back","rb")
			pTransfernote = cPickle.load(rTn)
			rTn.close()
			rVouch =open("backupdir/vouchers.back","rb")
			pVoucher = cPickle.load(rVouch)
			rVouch.close()
			rVbn =open("backupdir/voucherbin.back","rb")
			pVoucherbin= cPickle.load(rVbn)
			rVbn.close()
			try:
				
				orgdata = pOrg[0]
				result = self.con.execute(organisation.insert(),[orgdata])
						
				organisationd = self.con.execute(select([organisation.c.orgcode]).where(and_(organisation.c.orgname==orgdata["orgname"],organisation.c.orgtype==orgdata["orgtype"],organisation.c.yearstart==orgdata["yearstart"],organisation.c.yearend==orgdata["yearend"])))
				orgrow = organisationd.fetchone()
				orgcode = orgrow["orgcode"]
				
				for row in pGsg:
					row["orgcode"] = orgcode
					if row["subgroupof"]== None:
						result = self.con.execute(groupsubgroups.insert(),[row])
					if row["subgroupof"]!= None:
						grpcode = self.con.execute(select([groupsubgroups.c.groupcode]).where(and_(groupsubgroups.c.groupname==row["subgroupof"],organisation.c.orgcode==orgcode)))
						grcdow = grpcode.fetchone()
						grpcode = grcdow["groupcode"]
						row["subgroupof"] = grpcode
						result = self.con.execute(groupsubgroups.insert(),[row])
					
				for row in pAccount:
					row["orgcode"] = orgcode
					grpcode = self.con.execute(select([groupsubgroups.c.groupcode]).where(and_(groupsubgroups.c.groupname==row["groupcode"],organisation.c.orgcode==orgcode)))
					grprow = grpcode.fetchone()
					row["groupcode"]= grcdow["groupcode"]
					result = self.con.execute(accounts.insert(),[row])
					
				for row in pUser:
					row["orgcode"] = orgcode
					result = self.con.execute(users.insert(),[row])
				for row in pProjects:
					row["orgcode"] = orgcode
					result = self.con.execute(projects.insert(),[row])
				
				for row in pCustomerandsupplier:
					row["orgcode"] = orgcode
					result = self.con.execute(customerandsupplier.insert(),[row])
				for row in pCategorysubcategories:
					row["orgcode"] = orgcode
					if row["subcategoryof"]==None:
						result = self.con.execute(categorysubcategories.insert(),[row])
					if row["subcategoryof"]!=None:
						catcode = self.con.execute(select([categorysubcategories.c.categorycode]).where(and_(categorysubcategories.c.categoryname==row["subcategoryof"],categorysubcategories.c.orgcode==orgcode)))
						catrow = catcode.fetchone()
						catscode = catrow["categorycode"]
						row["subcategoryof"] = catscode
						result = self.con.execute(groupsubgroups.insert(),[row])
								
				for row in pCategoryspecs:
					row["orgcode"] = orgcode
					categorydata = self.con.execute(select([categorysubcategories.c.categorycode]).where(and_(categorysubcategories.c.categoryname ==row["categorycode"], categorysubcategories.c.orgcode == orgcode)))
					ctrow = categorydata.fetchone()
					categorycodee = ctrow["categorycode"]
					row["categorycode"] = categorycodee
					result = self.con.execute(categoryspecs.insert(),[row])
					
				for row in pUnitofmeasurement:
					row["orgcode"] = orgcode
					result = self.con.execute(unitofmeasurement.insert(),[row])
				for row in pProduct:
					row["orgcode"] = orgcode
					try :
						result = self.con.execute(product.insert(),[row])
					except:
						self.con.execute("alter table product alter column productcode type bigint")
						self.con.execute("alter table goprod alter column productcode type bigint")
						self.con.execute("alter table stock alter column productcode type bigint")
						self.con.execute("alter table vouchers alter column vouchercode type bigint")
						self.con.execute("alter table bankrecon alter column vouchercode type bigint")
						
						categorydata = self.con.execute(select([categorysubcategories.c.categorycode]).where(and_(categorysubcategories.c.categoryname ==row["categorycode"], categorysubcategories.c.orgcode == orgcode)))
						ctrow = categorydata.fetchone()
						categorycodee = ctrow["categorycode"]
						row["categorycode"] = categorycodee
						uomdata = self.con.execute(select([unitofmeasurement.c.uomid]).where(and_(unitofmeasurement.c.unitname ==row["uomid"])))
						umrow = uomdata.fetchone()
						umcodee = umrow["uomid"]
						row["uomid"] = umcodee 
						result = self.con.execute(product.insert(),[row])
						
				for row in pGodown:
					row["orgcode"] = orgcode
					result = self.con.execute(godown.insert(),[row])
					
				for row in pGoprod:
					row["orgcode"] = orgcode
					godata = self.con.execute(select([godown.c.goid]).where(and_(godown.c.goname ==row["goid"],godown.c.orgcode == orgcode)))
					gorow = godata.fetchone()
					goidd= gorow ["goid"]
					row["goid"] = goidd
					productdata = self.con.execute(select([product.c.productcode]).where(and_(product.c.productdesc ==row["productcode"],product.c.orgcode == orgcode)))
					pdrow = productdata.fetchone()
					productcodee = pdrow["productcode"]
					row["productcode"] = productcodee
					
					result = self.con.execute(goprod.insert(),[row])
	
				for row in pTax:
					row["orgcode"] = orgcode
					if row["categorycode"]!= None:
						categorydata = self.con.execute(select([categorysubcategories.c.categorycode]).where(and_(categorysubcategories.c.categoryname ==row["categorycode"], categorysubcategories.c.orgcode == orgcode)))
						ctrow = categorydata.fetchone()
						categorycodee = ctrow["categorycode"]
						row["categorycode"] = categorycodee
						
					if row["productcode"]!= None:
						proddata = self.con.execute(select([product.c.productcode]).where(and_(product.c.productdesc ==row["categorycode"], product.c.orgcode == orgcode)))
						prodrow = proddata.fetchone()
						productcodee = prodrow["productcode"]
						row["productcode"] = productcodee
					result = self.con.execute(tax.insert(),[row])
				for row in pPurchaseorder:
					row["orgcode"] = orgcode
					csdata = self.con.execute(select([customerandsupplier.c.custid]).where(and_(customerandsupplier.c.custid ==row["csid"], customerandsupplier.c.orgcode == orgcode)))
					csrow = csdata.fetchone()
					custidd = csrow["custid"]
					row["csid"] = custidd
					result = self.con.execute(purchaseorder.insert(),[row])
				for row in pDelchal:
					row["orgcode"] = orgcode
					result = self.con.execute(delchal.insert(),[row])
				for row in pInvoice:
					row["orgcode"] = orgcode
					row["invoicetotal"]=100
					newcontent = {}
					content = row["contents"]
					for key in content:
							productcode = key
							value = content[key]
							prodname = self.con.execute(select([product.c.productcode]).where(and_(product.c.productdesc == productcode,product.c.orgcode==orgcode)))																					
							prodnamerow = prodname.fetchone()
							productcodee = prodnamerow ["productcode"]	
							newcontent[productcodee]= value
							row["contents"]= newcontent   
					
					if row["orderid"] != None:
						podata = self.con.execute(select([purchaseorder.c.orderid]).where(and_(purchaseorder.c.orderno ==row["orderid"],purchaseorder.c.orgcode == orgcode)))
						porow = podata.fetchone()
						orderidd= porow["orderid"]
						row["orderid"] = orderidd
								
					if row["custid"]!= None:
						csdata = self.con.execute(select([customerandsupplier.c.custid]).where(and_(customerandsupplier.c.custname == row["custid"], customerandsupplier.c.orgcode == orgcode)))
						csrow = csdata.fetchone()
						custidd = csrow["custid"]
						row["custid"] = custidd
					result = self.con.execute(invoice.insert(),[row])
					
				for row in pDcinv:
					row["orgcode"] = orgcode
					if row["dcid"] != None:
						dcdata = self.con.execute(select([delchal.c.dcid]).where(and_(delchal.c.dcno ==row["dcid"], delchal.c.orgcode == orgcode)))
						dcrow = dcdata.fetchone()
						dcidd = dcrow["dcid"]
						row["dcid"]= dcidd
						
					if row["invid"] !=None:
						invdata = self.con.execute(select([invoice.c.invid]).where(and_(invoice.c.invoiceno ==row["invid"], invoice.c.orgcode == orgcode)))
						inrow = invdata.fetchone()
						invidd = inrow["invid"]
						row["invid"]= invidd
					result = self.con.execute(dcinv.insert(),[row])
	   
				for row in pStock:
					row["orgcode"] = orgcode
					if row["goid"]!= None:
						godata = self.con.execute(select([godown.c.goid]).where(and_(godown.c.goname ==row["goid"],godown.c.orgcode == orgcode)))
						gorow = godata.fetchone()
						goidd= gorow ["goid"]
						row["goid"] = goidd
					result = self.con.execute(stock.insert(),[row]) 
				for row in pTransfernote:
					row["orgcode"] = orgcode
					godata = self.con.execute(select([godown.c.goid]).where(and_(godown.c.goname ==row["togodown"],godown.c.orgcode == orgcode)))
					gorow = godata.fetchone()
					goidd= gorow ["goid"]
					row["togodown"] = goidd
	
					result = self.con.execute(transfernote.insert(),[row])
				
				for row in pVoucher:
					row["orgcode"] = orgcode
					drs = row["drs"]
					crs = row["crs"]
					newdrs = {}
					newcrs = {}
	
					for key in drs:
						accnodr = key
						valuedr = drs[key]
					for key in crs:
						accnocr = key
						valuecr = crs[key]
	
					acccode = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname == accnodr,accounts.c.orgcode==orgcode)))																					
					accnamerow = acccode .fetchone()
					accountcodedr = accnamerow ["accountcode"]															
					acccode = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname == accnocr,accounts.c.orgcode==orgcode)))																					
					accnamerow = acccode.fetchone()
					accountcodecr = accnamerow ["accountcode"]
					newcrs[accountcodecr] = valuecr
					row["crs"]=newcrs
					newdrs[accountcodedr] = valuedr
					row["drs"]=newdrs
	
					result = self.con.execute(vouchers.insert(),[row])
				for row in pVoucherbin:
					row["orgcode"] = orgcode
					result = self.con.execute(voucherbin.insert(),[row])
				for row in pBankrecon:
					row["orgcode"] = orgcode
					acccode = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname == row["accountcode"],accounts.c.orgcode==orgcode)))																					
					accnamerow = acccode .fetchone()
					accountcodde = accnamerow ["accountcode"]															
					row["accountcode"]=accountcodde
					result = self.con.execute(bankrecon.insert(),[row])
					return {"gkstatus":enumdict["Success"]}
			except:
				  return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			
		finally:
			self.con.close()
					
					

					
			
		
		
		  

			
					
