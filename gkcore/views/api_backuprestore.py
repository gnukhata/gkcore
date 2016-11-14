
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
from gkcore.models.gkdb import  organisation,accounts,users,bankrecon,categorysubcategories,customerandsupplier,dcinv,delchal,discrepancynote,godown,groupsubgroups,invoice,projects,product,purchaseorder,transfernote,stock,tax,unitofmeasurement,vouchers,voucherbin
from sqlalchemy.sql import select
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
					os.system("pg_dump -a -Ft -t organisation -t groupsubgroups -t accounts -t users -t projects -t bankrecon -t customerandsupplier -t categorysubcategories -t categoryspecs -t unitofmeasurement -t product -t tax -t godown -t purchaseorder -t delchal -t invoice -t dcinv -t stock -t transfernote -t discrepancynote -t vouchers -t voucherbin  gkdata -f /tmp/gkbackup.tar")
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
		""" This method backsup entire database for certain organisation.
		First it checks the user role if the user is admin then only user can do the backup					  """
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}

		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		else:
			#	try:
				self.con = eng.connect()
				user=self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				if userRole[0]==-1:
					newOrgCode = str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour) + str(datetime.now().minute) + str(datetime.now().second) + str(datetime.now().microsecond)
					newOrgCode = int(newOrgCode)

					
					organisation = self.con.execute(select([organisation]).where(organisation.c.orgcode==authDetails["orgcode"]))
					lstorganisation = []
					for row in organisation:
						lstorganisation.append({"orgcode":newOrgCode, "orgname":row["orgname"],"orgtype":row["orgtype"],"yearstart":row["yearstart"],"yearend":row["yearend"],"orgcity":row["orgcity"],"orgaddr":row["orgaddr"],"orgpincode":row["orgpincode"],"orgstate":row["orgstate"],"orgcountry":row["orgcountry"],"orgtelno":row["orgtelno"],"orgfax":row["orgfax"],"orgwebsite":row["orgwebsite"],"orgemail":row["orgemail"],"orgpan":row["orgpan"],"orgmvat":row["orgmvat"],"orgstax":row["orgstax"],"orgregno":row["orgregno"],"orgregdate":row["orgregdate"],"orgfcrano":row["orgfcrano"],"orgfcradate":row["orgfcradate"],"roflag":row["roflag"],"booksclosedflag":row["booksclosedflag"],"invflag":row["invflag"]})
					groupsubgroups = self.con.execute(select([groupsubgroups]).where(groupsubgroups.c.orgcode==authDetails["orgcode"]))
					lstgroupsubgroups = []
					for row in groupsubgroups:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstgroupsubgroups.append({"groupcode":newKey,"groupname":row["groupname"],"subgroupof":row["subgroupof"],"orgcode": newOrgCode})
					accounts = self.con.execute(select([accounts]).where(accounts.c.orgcode==authDetails["orgcode"]))
					lstaccounts = []
					for row in accounts:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstaccounts.append({"accountcode":newKey,"accountname":row["accountname"],"groupcode":row["groupcode"],"openingbal":row["openingbal"],"vouchercount":row["vouchercount"],"orgcode":newOrgCode})
					backupUsers = self.con.execute(select([users]).where(users.c.orgcode==authDetails["orgcode"]))
					lstusers = []
					for row in backupUsers:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstusers.append({"userid":newKey,"username":row["username"],"userpassword":row["userpassword"],"userrole":row["userrole"],"userquestion":row["userquestion"],"useranswer":row["useranswer"],"themename":row["themename"],"orgcode":newOrgCode})	
					projects = self.con.execute(select([projects]).where(projects.c.orgcode==authDetails["orgcode"]))
					lstprojects = []
					for row in projects:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstprojects.append({"projectcode":newKey,"projectname":row["projectname"],"sanctionedamount":row["sanctionedamount"],"orgcode":newOrgCode})
					bankrecon = self.con.execute(select([bankrecon]).where(bankrecon.c.orgcode==authDetails["orgcode"]))
					lstbankrecon = []
					for row in bankrecon:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstbankrecon.append({"reconcode":newKey,"vouchercode":row["vouchercode"],"accountcode":row["accountcode"],"clearancedate":row["clearancedate"],"memo":row["memo"],"orgcode":newOrgCode})
					customerandsupplier = self.con.execute((select([customerandsupplier]).where(customerandsupplier.c.orgcode==authDetails["orgcode"])))
					lstcustomerandsupplier = []
					for row in customerandsupplier:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstcustomerandsupplier.append({"custid":newKey,"custname":row["custname"],"custaddr":row["custaddr"],"custphone":row["custphone"],"custemail":["custemail"],"custfax":["custfax"],"custpan":row["custpan"],"custtan":row["custtan"],"custdoc":row["custdoc"],"csflag":row["csflag"],"state":row["state"],"orgcode":newOrgCode})
					categorysubcategories = self.con.execute(select([categorysubcategories]).where(categorysubcategories.c.orgcode==authDetails["orgcode"]))
					lstcategorysubcategories = []
					for row in categorysubcategories:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstcategorysubcategories.append({"categorycode":newKey,"categoryname":row["categoryname"],"subcategoryof":row["subcategoryof"],"orgcode":newOrgCode})	
					categoryspecs = self.con.execute(select([categorysubcategories]).where(categoryspecs.c.orgcode==authDetails["orgcode"]))
					lstcategoryspecs = []
					for row in categoryspecs:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstcategoryspecs.append({"spcode":newKey,"attrname":row["attrname"],"attrtype":row["attrtype"],"productcount":row["productcount"],"orgcode":newOrgCode})	
					unitofmeasurement = self.con.execute(select([unitofmeasurement]))
					lstunitofmeasurement = []
					for row in unitofmeasurement:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstunitofmeasurement.append({"uomid":newKey,"unitname":row["unitname"],"conversionrate":row["conversionrate"],"subunitof":row["subunitof"],"frequency":row["frequency"]})
					product = self.con.execute(select([product]).where(product.c.orgcode==authDetails["orgcode"]))
					lstproduct = []
					for row in product:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstproduct.append({"productcode":newKey,"productdesc":row["productdesc"],"specs":row["specs"],"categorycode":row["categorycode"],"uomid":row["uomid"],"orgcode":newOrgCode})	
					tax = self.con.execute(select([tax]).where(tax.c.orgcode==authDetails["orgcode"]))
					lsttax = []
					for row in tax:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lsttax.append({"taxid":newKey,"taxname":row["taxname"],"taxrate":row["taxrate"],"state":row["state"],"productcode":row["productcode"],"categorycode":row["categorycode"],"orgcode":newOrgCode})	
					godown = self.con.execute(select([godown]).where(godown.c.orgcode==authDetails["orgcode"]))
					lstgodown = []
					for row in godown:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstgodown.append({"goid":newKey,"goname":row["goname"],"goaddr":row["goaddr"],"gocontact":row["gocount"],"contactname":row["contactname"],"orgcode":newOrgCode})	
					purchaseorder = self.con.execute(select([purchaseorder]).where(purchaseorder.c.orgcode==authDetails["orgcode"]))
					lstpurchaseorder = []
					for row in purchaseorder:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstpurchaseorder.append({"orderid":newKey,"orderno": row["orderno"], "orderdate": datetime.strftime(row["orderdate"],'%d-%m-%Y'),"csid":row["csid"],"productdetails": row["productdetails"],"tax":row["tax"],"payterms":row["payterms"],"maxdate":row["maxdate"],"datedelivery":row["datedelivery"],"deliveryplaceaddr":row["deliveryplaceaddr"],"schedule":row["schedule"],"modeoftransport":row["modeoftransport"],"psflag":row["psflag"],"packaging":row["packaging"],"issuername":row["issuername"],"designation":row["designation"],"orgcode":newOrgCode})	
					delchal = self.con.execute(select([delchal]).where(delchal.c.orgcode==authDetails["orgcode"]))
					lstdelchal = []
					for row in delchal:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstdelchal.append({"dcid":newKey,"dcno":row["dcno"],"dcdate":row["dcdate"],"dcflag":row["dcflag"],"issureid":row["issuerid"],"issuerid":row["issuerid"],"custid:row":["custid"],"orderid":row["orderid"],"orgcode":newOrgCode})
					invoice = self.con.execute(select([invoice]).where(invoice.c.orgcode==authDetails["orgcode"]))
					lstinvoice = []
					for row in invoice:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstinvoice.append({"invid":newKey,"invoiceno":row["invoiceno"],"invoicedate":row["invoicedate"],"contents":row["contents"],"orderid":row["orderid"],"custid":row["custid"],"orgcode":newOrgCode})	
					dcinv = self.con.execute(select([dcinv]).where(dcinv.c.orgcode==authDetails["orgcode"]))
					lstdcinv = []
					for row in dcinv:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstdcinv.append({"dcinvid":newKey,"dcid":row["dcid"],"invid":row["invid"],"contents":row["contents"],"issuername":row["issuername"],"tax":row["tax"],"orderid":row["orderid"],"custid":row["custid"],"designation":row["designation"],"orgcode":newOrgCode})	
					stock = self.con.execute(select([stock]).where(stock.c.orgcode==authDetails["orgcode"]))
					lststock = []
					for row in stock:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lststock = stock.append({"stockid":newKey,"productcode":row["productcode"],"qty":row["qty"],"dcinvtnid":row["dcinvtnid"],"dcinvtnflag":row["dcinvtnflag"],"inout":row["inout"],"goid":row["goid"],"orgcode":newOrgCode})
					transfernote = self.con.execute(select([transfernote]).where(transfernote.c.orgcode==authDetails["orgcode"]))
					lsttransfernote = []
					for row in transfernote:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lsttransfernote.append({"transfernoteno":newKey,"transfernoteid": row["transfernoteid"], "transfernotedate":row["transfernotedate"],"transportationmode":row["transportationmode"],"nopkt":["nopkt"],"issuername":row["issuername"],"designation":row["designation"],"recieved":row["recieved"],"togodown":row["togodown"],"orgcode":newOrgCode})
					discrepancynote = self.con.execute(select([discrepancynote]).where(discrepancynote.c.orgcode==authDetails["orgcode"]))
					lstdiscrepancynote = []
					for row in discrepancynote:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstdiscrepancynote.append({"discrepancyid":newKey,"discrepancyno":row["discrepancyno"],"discrepancydate":row["discrepancydate"],"discrepancydetails":row["discrepancydetails"],"dcinvpotncode":row["dcinvpotncode"],"dcinvpotnflag":row["dcinvpotnflag"],"issuername":row["issuername"],"supplier":row["supplier"],"designation":row["designation"],"orgcode":newOrgCode})
					vouchers = self.con.execute(select([vouchers]).where(vouchers.c.orgcode==authDetails["orgcode"]))
					lstvouchers = []
					for row in vouchers:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstvouchers.append({"vouchercode":newKey,"vouchernumber":row["vouchernumber"],"voucherdate":row["voucherdate"],"entrydate":row["entrydate"],"narration":row["narration"],"drs":row["drs"],"crs":row["crs"],"prjdrs":row["prjdrs"],"prjcrs":row["prjcrs"],"attatchment":row["attatchment"],"attatchmentcount":row["attatchmentcount"],"vouchertype":row["vouchertype"],"lockflag":row["lockflag"],"delflag":row["delflag"],"projectcode":row["projectcode"],"orgcode":newOrgCode,"invid":row["invid"]})					
					voucherbin = self.con.execute((select([voucherbin]).where(voucherbin.c.orgcode==authDetails["orgcode"])))
					lstvoucherbin = []
					for row in voucherbin:
						curTime = datetime.now()
						newKey = str(curTime.year) + str(curTime.month) + str(curTime.day) + str(curTime.hour) + str(curTime.minute) + str(curTime.second) + str(curTime.microsecond)
						newKey = int(newKey)
						lstvoucherbin.append({"vouchercode":newKey,"vouchernumber":row["vouchernumber"],"voucherdate":row["voucherdate"],"narration":row["narration"],"drs":row["drs"],"crs":row["crs"],"vouchertype":row["vouchertype"],"projectname":row["projectname"],"orgcode":newOrgCode})
					os.system("mkdir ../../backupdir")
					orgFile = open("../../../../backupdir/org.back","w")
					success = cPickle.dump(lstorganisation,orgFile)
					orgFile.close()
					gsgFile = open("../../../../backupdir/gsg.back","w")
					success = cPickle.dump(lstgroupsubgroups,gsgFile)
					gsgFile.close()
					accFile = open("../../backupdir/accounts.back","w")
					success = cPickle.dump(lstaccounts,accFile)
					accFile.close()
					usersFile = open("../../../../backupdir/users.back","w")
					success = cPickle.dump(lstusers,usersFile)
					usersFile.close()
					projFile = open("../../../../backupdir/projects.back","w")
					success = cPickle.dump(lstprojects,projFile)
					projFile.close()
					bankreconFile = open("../../../../backupdir/bankrecon.back","w")
					success = cPickle.dump(lstbankrecon,bankreconFile)
					bankreconFile.close()
					customerandsupplierFile = open("../../../../backupdir/customerandsupplier.back","w")
					success = cPickle.dump(lstcustomerandsupplier,customerandsupplierFile)
					customerandsupplierFile.close()
					categorysubcategoriesFile = open("../../../../backupdir/categorysubcategories.back","w")
					success = cPickle.dump(lstcategorysubcategories,categorysubcategoriesFile)
					categorysubcategoriesFile.close()
					categoryspecsFile = open("../../../../backupdir/accounts.back","w")
					success = cPickle.dump(lstcategoryspecs,categoryspecsFile)
					categoryspecsFile.close()
					unitofmeasurementFile = open("../../../../backupdir/unitofmeasurement.back","w")
					success = cPickle.dump(lstunitofmeasurement,unitofmeasurementFile)
					unitofmeasurementFile.close()
					productFile = open("../../../../backupdir/product.back","w")
					success = cPickle.dump(lstproduct,productFile)
					productFile.close()
					godownFile = open("../../../../backupdir/godown.back","w")
					success = cPickle.dump(lstgodown,godownFile)
					godownFile.close()
					taxFile = open("../../../../backupdir/tax.back","w")
					success = cPickle.dump(lsttax,taxFile)
					taxFile.close()
					purchaseorderFile = open("../../backupdir/purchaseorder.back","w")
					success = cPickle.dump(lstpurchaseorder,purchaseorderFile)
					purchaseorderFile.close()
					delchalFile = open("../../backupdir/delchal.back","w")
					success = cPickle.dump(lstdelchal,delchalFile)
					delchalFile.close()
					invoiceFile = open("../../backupdir/invoice.back","w")
					success = cPickle.dump(lstinvoice,invoiceFile)
					invoiceFile.close()
					dcinvFile = open("../../backupdir/dcinv.back","w")
					success = cPickle.dump(lstdcinv,dcinvFile)
					dcinvFile.close()
					stockFile = open("../../backupdir/stock.back","w")
					success = cPickle.dump(lststock,stockFile)
					stockFile.close()
					transfernoteFile = open("../../backupdir/transfernote.back","w")
					success = cPickle.dump(lsttransfernote,transfernoteFile)
					transfernoteFile.close()
					discrepancynoteFile = open("../../backupdir/discrepancynote.back","w")
					success = cPickle.dump(lstdiscrepancynote,discrepancynoteFile)
					discrepancynoteFile.close()
					vouchersFile = open("../../backupdir/vouchers.back","w")
					success = cPickle.dump(lstvouchers,vouchersFile)
					vouchersFile.close()
					voucherbinFile = open("../../backupdir/voucherbin.back","w")
					success = cPickle.dump(lstvoucherbin,voucherbinFile)
					voucherbinFile.close()
					#return {"gkstatus":enumdict["Success"]}
			#except:
				#   return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
		# finally:
			#	print "end"

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
			os.system("pg_restore -t organisation -t groupsubgroups -t accounts -t users -t projects -t bankrecon -t customerandsupplier -t categorysubcategories -t categoryspecs -t unitofmeasurement -t product -t tax -t godown -t purchaseorder -t delchal -t invoice -t dcinv -t stock -t transfernote -t discrepancynote -t vouchers -t voucherbin --dbname=gkdata  /tmp/restore.tar")
		
			return {"gkstatus":enumdict["Success"]}
		except:
			return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			
				
			
					
