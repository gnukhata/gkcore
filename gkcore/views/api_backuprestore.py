
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
from gkcore.models.gkdb import organisation,accounts,users,bankrecon,categorysubcategories,categoryspecs,customerandsupplier,dcinv,delchal,godown,groupsubgroups,invoice,projects,product,purchaseorder,transfernote,stock,tax,unitofmeasurement,vouchers,voucherbin
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
					os.system("pg_dump -a -Ft -t organisation -t groupsubgroups -t accounts -t users -t projects -t bankrecon -t customerandsupplier -t categorysubcategories -t categoryspecs -t unitofmeasurement -t product -t tax -t godown -t purchaseorder -t delchal -t invoice -t dcinv -t stock -t transfernote -t vouchers -t voucherbin  gkdata -f /tmp/gkbackup.tar")
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
	#		try:
				self.con = eng.connect()
				user=self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				if userRole[0]==-1:
					backupOrganisation = self.con.execute(select([organisation]).where(organisation.c.orgcode==authDetails["orgcode"]))
					lstorganisation = []
					for row in backupOrganisation:
						lstorganisation.append({ "orgname":row["orgname"],"orgtype":row["orgtype"],"yearstart":row["yearstart"],"yearend":row["yearend"],"orgcity":row["orgcity"],"orgaddr":row["orgaddr"],"orgpincode":row["orgpincode"],"orgstate":row["orgstate"],"orgcountry":row["orgcountry"],"orgtelno":row["orgtelno"],"orgfax":row["orgfax"],"orgwebsite":row["orgwebsite"],"orgemail":row["orgemail"],"orgpan":row["orgpan"],"orgmvat":row["orgmvat"],"orgstax":row["orgstax"],"orgregno":row["orgregno"],"orgregdate":row["orgregdate"],"orgfcrano":row["orgfcrano"],"orgfcradate":row["orgfcradate"],"roflag":row["roflag"],"booksclosedflag":row["booksclosedflag"],"invflag":row["invflag"]})
					backupGroupsubgroups = self.con.execute(select([groupsubgroups]).where(groupsubgroups.c.orgcode==authDetails["orgcode"]))
					lstgroupsubgroups = []
					for row in backupGroupsubgroups:
						grpname = None
						if row["subgroupof"] != None:
							grpnamedata = self.con.execute(select([groupsubgroups.c.groupname]).where(and_(groupsubgroups.c.groupcode ==row["subgroupof"], groupsubgroups.c.orgcode == authDetails["orgcode"])))
							grpnamerow = grpnamedata.fetchone()
							grpname = grpnamerow["groupname"]
						lstgroupsubgroups.append({"groupname":row["groupname"],"subgroupof":grpname})
					
					backupAccounts = self.con.execute(select([accounts]).where(accounts.c.orgcode==authDetails["orgcode"]))
					lstaccounts = []
					for row in backupAccounts:
						grpname = self.con.execute(select([groupsubgroups.c.groupname]).where(groupsubgroups.c.groupcode == row["groupcode"]))																				
						grpnamerow = grpname.fetchone()
						groupname = grpnamerow["groupname"]															
						lstaccounts.append({"accountname":row["accountname"],"groupcode":groupname,"openingbal":row["openingbal"],"vouchercount":row["vouchercount"]})
					
					backupUsers = self.con.execute(select([users]).where(users.c.orgcode==authDetails["orgcode"]))
					lstusers = []
					for row in backupUsers:
						lstusers.append({"username":row["username"],"userpassword":row["userpassword"],"userrole":row["userrole"],"userquestion":row["userquestion"],"useranswer":row["useranswer"],"themename":row["themename"]})
											
					backupProjects = self.con.execute(select([projects]).where(projects.c.orgcode==authDetails["orgcode"]))
					lstprojects = []
					for row in backupProjects:
						lstprojects.append({"projectname":row["projectname"],"sanctionedamount":row["sanctionedamount"]})
					
					backupCustomerandsupplier = self.con.execute((select([customerandsupplier]).where(customerandsupplier.c.orgcode==authDetails["orgcode"])))
					lstcustomerandsupplier = []
					for row in backupCustomerandsupplier:
						lstcustomerandsupplier.append({"custname":row["custname"],"custaddr":row["custaddr"],"custphone":row["custphone"],"custemail":row["custemail"],"custfax":row["custfax"],"custpan":row["custpan"],"custtan":row["custtan"],"custdoc":row["custdoc"],"csflag":row["csflag"],"state":row["state"]})
					
					backupCategorysubcategories = self.con.execute(select([categorysubcategories]).where(categorysubcategories.c.orgcode==authDetails["orgcode"]))
					lstcategorysubcategories = []
					for row in backupCategorysubcategories:
						subcategryof = None
						if row["subcategoryof"] != None:
							subcategorydata = self.con.execute(select([categorysubcategories.c.categoryname]).where(and_(categorysubcategories.c.categorycode ==row["subcategoryof"], categorysubcategories.c.orgcode == authDetails["orgcode"])))
							sbctorow = subcategorydata.fetchone()
							subcategryof = sbctorow["categoryname"]

						lstcategorysubcategories.append({"categoryname":row["categoryname"],"subcategoryof":subcategryof})	
					
					backupCategoryspecs = self.con.execute(select([categoryspecs]).where(categoryspecs.c.orgcode==authDetails["orgcode"]))
					lstcategoryspecs = []
					for row in backupCategoryspecs:
						categorydata = self.con.execute(select([categorysubcategories.c.categoryname]).where(and_(categorysubcategories.c.categorycode ==row["categorycode"], categorysubcategories.c.orgcode == authDetails["orgcode"])))
						ctrow = categorydata.fetchone()
						categoryname = ctrow["categoryname"]
						lstcategoryspecs.append({"attrname":row["attrname"],"attrtype":row["attrtype"],"productcount":row["productcount"],"categorycode":categoryname})	
					
					backupUnitofmeasurement = self.con.execute(select([unitofmeasurement]))
					lstunitofmeasurement = []
					for row in backupUnitofmeasurement:
						subunitof = None
						if row["subunitof"] != None:
							subunitdata = self.con.execute(select([unitofmeasurement.c.unitname]).where(and_(unitofmeasurement.c.uomid ==row["subunitof"], unitofmeasurement.c.orgcode == authDetails["orgcode"])))
							sbuntrow = subunitdata.fetchone()
							unitname = sbuntrow["unitname"]

						lstunitofmeasurement.append({"unitname":row["unitname"],"conversionrate":row["conversionrate"],"subunitof":subunitof ,"frequency":row["frequency"]})
					
					backupProduct = self.con.execute(select([product]).where(product.c.orgcode==authDetails["orgcode"]))
					lstproduct = []
					mapProd ={}
					for row in backupProduct:
						curtime = datetime.now()
						snewkey = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + str(curtime.microsecond)
						newkey = snewkey[0:19]
						newkey= int(newkey)
						mapProd[row["productcode"]] = newkey
						categorydata = self.con.execute(select([categorysubcategories.c.categoryname]).where(and_(categorysubcategories.c.categorycode ==row["categorycode"], categorysubcategories.c.orgcode == authDetails["orgcode"])))
						ctrow = categorydata.fetchone()
						categoryname = ctrow["categoryname"]
						unitdata = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid ==row["uomid"]))
						unitrow = unitdata.fetchone()
						unitname = unitrow ["unitname"]

						lstproduct.append({"productcode" : newkey,"productdesc":row["productdesc"],"specs":row["specs"],"categorycode":categoryname,"uomid":unitname,"openingstock":row["openingstock"]})	
					
					backupTax = self.con.execute(select([tax]).where(tax.c.orgcode==authDetails["orgcode"]))
					lsttax = []
					for row in backupTax:
						productcode = None
						categorycode = None

						if row["productcode"] != None:
							productdata = self.con.execute(select([product.c.productdesc]).where(and_(product.c.productcode ==row["productcode"], product.c.orgcode == authDetails["orgcode"])))
							productrow = productdata.fetchone()
							productdesc= productrow["productdesc"]
							
						if row["categorycode"]!= None:
							categorydata = self.con.execute(select([categorysubcategories.c.categoryname]).where(and_(categorysubcategories.c.categorycode ==row["categorycode"], categorysubcategories.c.orgcode == authDetails["orgcode"])))
							ctrow = categorydata.fetchone()
							categoryname = ctrow["categoryname"]
							
						lsttax.append({"taxname":row["taxname"],"taxrate":row["taxrate"],"state":row["state"],"productcode":productcode,"categorycode":categoryname})
							
					backupGodown = self.con.execute(select([godown]).where(godown.c.orgcode==authDetails["orgcode"]))
					lstgodown = []
					for row in backupGodown:
						lstgodown.append({"goname":row["goname"],"goaddr":row["goaddr"],"gocontact":row["gocontact"],"contactname":row["contactname"]})	
					
					backupPurchaseorder = self.con.execute(select([purchaseorder]).where(purchaseorder.c.orgcode==authDetails["orgcode"]))
					lstpurchaseorder = []
					for row in backupPurchaseorder:
						csdata = self.con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.custid ==row["csid"], customerandsupplier.c.orgcode == authDetails["orgcode"])))
						csrow = csdata.fetchone()
						custname = csrow["custname"]

						lstpurchaseorder.append({"orderno": row["orderno"], "orderdate":row["orderdate"],"csid":custname,"productdetails": row["productdetails"],"tax":row["tax"],"payterms":row["payterms"],"maxdate":row["maxdate"],"datedelivery":row["datedelivery"],"deliveryplaceaddr":row["deliveryplaceaddr"],"schedule":row["schedule"],"modeoftransport":row["modeoftransport"],"psflag":row["psflag"],"packaging":row["packaging"],"issuername":row["issuername"],"designation":row["designation"]})	
					
					backupDelchal = self.con.execute(select([delchal]).where(delchal.c.orgcode==authDetails["orgcode"]))
					lstdelchal = []
					
					for row in backupDelchal:
						custname = None
						orderno = None
						issuername = None
						if row["custid"] != None :
							csdata = self.con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.custid ==row["custid"], customerandsupplier.c.orgcode == authDetails["orgcode"])))
							csrow = csdata.fetchone()
							custname = csrow["custname"]
														
						if row["orderid"] != None :
							 podata = self.con.execute(select([purchaseorder.c.orderno]).where(and_(purchaseorder.c.orderid ==row["orderid"],purchaseorder.c.orgcode == authDetails["orgcode"])))
							 porow = podata.fetchone()
							 orderno= porow["orderno"]
							 
						if row["issuerid"] != None:
							 issuerdata = self.con.execute(select([users.c.username]).where(and_(users.c.userid ==row["issuerid"], users.c.orgcode == authDetails["orgcode"])))
							 isrow = issuerdata.fetchone()
							 issuername = isrow["username"]
							 
							 
						lstdelchal.append({"dcno":row["dcno"],"dcdate":row["dcdate"],"dcflag":row["dcflag"],"issuerid":issuername,"custid:":custname,"canceldate":row["canceldate"],"cancelflag":row["cancelflag"],"orderid":orderno})
					
					backupInvoice = self.con.execute(select([invoice]).where(invoice.c.orgcode==authDetails["orgcode"]))
					lstinvoice = []
					for row in backupInvoice:
						orderno = None
						custname = None
						newcontent = {}
						content = row["contents"]
						for key in content:
							productcode = key
							value = content[key]
							prodname = self.con.execute(select([product.c.productdesc]).where(and_(product.c.productcode == productcode,accounts.c.orgcode==authDetails["orgcode"])))																					
							prodnamerow = prodname.fetchone()
							productname = prodnamerow ["productdesc"]	
							newcontent[productname]= value	
																				
						if row["orderid"] != None:
							podata = self.con.execute(select([purchaseorder.c.orderno]).where(and_(purchaseorder.c.orderid ==row["orderid"],purchaseorder.c.orgcode == authDetails["orgcode"])))
							porow = podata.fetchone()
							orderno= porow["orderno"]
							
						if row["custid"]!= None:
							csdata = self.con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.custid == row["custid"], customerandsupplier.c.orgcode == authDetails["orgcode"])))
							csrow = csdata.fetchone()
							custname = csrow["custname"]
													
						lstinvoice.append({"invoiceno":row["invoiceno"],"invoicedate":row["invoicedate"],"contents":newcontent,"orderid":orderno,"custid":custname ,"issuername":row["issuername"],"designation":row["designation"],"tax":row["tax"],"taxstate":row["taxstate"],"icflag":row["icflag"],"canceldate":row["canceldate"],"cancelflag":row["cancelflag"]})
					  
					
					backupDcinv = self.con.execute(select([dcinv]).where(dcinv.c.orgcode==authDetails["orgcode"]))
					lstdcinv = []
					for row in backupDcinv:
						dcno = None
						invoiceno = None

						if row["dcid"] != None:
							dcdata = self.con.execute(select([delchal.c.dcno]).where(and_(delchal.c.dcid ==row["dcid"], delchal.c.orgcode == authDetails["orgcode"])))
							dcrow = dcdata.fetchone()
							dcno = dcrow["dcno"]
							
						if row["invid"] !=None:
							invdata = self.con.execute(select([invoice.c.invoiceno]).where(and_(invoice.c.invid ==row["invid"], invoice.c.orgcode == authDetails["orgcode"])))
							inrow = invdata.fetchone()
							invoiceno = inrow["invoiceno"]
							
						lstdcinv.append({"dcid":dcno,"invid":invoiceno})	
					
					backupStock = self.con.execute(select([stock]).where(stock.c.orgcode==authDetails["orgcode"]))
					lststock = []
					mapProd ={}
					for row in backupStock:
						curtime = datetime.now()
						snewkey = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + str(curtime.microsecond)
						newkey = snewkey[0:19]
						newkey= int(newkey)
						mapProd[row["productcode"]] = newkey
						if row["goid"]!= None:
							godata = self.con.execute(select([godown.c.goname]).where(and_(godown.c.goid ==row["goid"],godown.c.orgcode == authDetails["orgcode"])))
							gorow = godata.fetchone()
							goname= gorow ["goname"]
							
						
						lststock.append({"productcode":mapProd[row["productcode"]],"qty":row["qty"],"dcinvtnid":row["dcinvtnid"],"dcinvtnflag":row["dcinvtnflag"],"inout":row["inout"],"goid":goname})
					
					backupTransfernote = self.con.execute(select([transfernote]).where(transfernote.c.orgcode==authDetails["orgcode"]))
					lsttransfernote = []
					for row in backupTransfernote:
						godata = self.con.execute(select([godown.c.goname]).where(and_(godown.c.goid ==row["togodown"],godown.c.orgcode == authDetails["orgcode"])))
						gorow = godata.fetchone()
						goname= gorow ["goname"]
						lsttransfernote.append({"transfernoteno": row["transfernoteno"], "transfernotedate":row["transfernotedate"],"transportationmode":row["transportationmode"],"nopkt":row["nopkt"],"issuername":row["issuername"],"designation":row["designation"],"recieved":row["recieved"],"togodown":goname,"canceldate":row["canceldate"],"cancelfag":row["cancelflag"]})
					
					backupVouchers = self.con.execute(select([vouchers]).where(vouchers.c.orgcode==authDetails["orgcode"]))
					lstvouchers = []
					mapVouchers = {}
					for row in backupVouchers:
						newdrs = {}
						newcrs = {}
						curtime = datetime.now()
						snewkey = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + str(curtime.microsecond)
						newkey = snewkey[0:19]
						newkey= int(newkey)
						mapVouchers[row["vouchercode"]] = newkey
						drs = row["drs"]
						crs = row["crs"]
						for key in drs:
							accnodr = key
							valuedr = drs[key]
						for key in crs:
							accnocr = key
							valuecr = crs[key]

						accname = self.con.execute(select([accounts.c.accountname]).where(and_(accounts.c.accountcode == accnodr,accounts.c.orgcode==authDetails["orgcode"])))																					
						accnamerow = accname .fetchone()
						accountnamedr = accnamerow ["accountname"]															
						accname = self.con.execute(select([accounts.c.accountname]).where(and_(accounts.c.accountcode == accnocr,accounts.c.orgcode==authDetails["orgcode"])))																					
						accnamerow = accname .fetchone()
						accountnamecr = accnamerow ["accountname"]
						newcrs[accountnamecr] = valuecr
						newdrs[accountnamedr] = valuedr
						  
						lstvouchers.append({"vouchercode":mapVouchers[row["vouchercode"]],"vouchernumber":row["vouchernumber"],"voucherdate":row["voucherdate"],"invid":row["invid"],"entrydate":row["entrydate"],"narration":row["narration"],"drs":newdrs,"crs":newcrs,"prjdrs":row["prjdrs"],"prjcrs":row["prjcrs"],"attachment":row["attachment"],"attachmentcount":row["attachmentcount"],"vouchertype":row["vouchertype"],"lockflag":row["lockflag"],"delflag":row["delflag"],"projectcode":row["projectcode"]})					
						
					
					backupVoucherbin = self.con.execute((select([voucherbin]).where(voucherbin.c.orgcode==authDetails["orgcode"])))
					lstvoucherbin = []
					for row in backupVoucherbin:
						lstvoucherbin.append({"vouchernumber":row["vouchernumber"],"voucherdate":row["voucherdate"],"narration":row["narration"],"drs":row["drs"],"crs":row["crs"],"vouchertype":row["vouchertype"],"projectname":row["projectname"]})
					backupBankrecon = self.con.execute(select([bankrecon]).where(bankrecon.c.orgcode==authDetails["orgcode"]))
					lstbankrecon = []
					for row in backupBankrecon:
						curtime = datetime.now()
						snewkey = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + str(curtime.microsecond)
						newkey = snewkey[0:19]
						newkey= int(newkey)
						mapVouchers[row["vouchercode"]] = newkey
						accname = self.con.execute(select([accounts.c.accountname]).where(and_(accounts.c.accountcode == row["accountcode"],accounts.c.orgcode==authDetails["orgcode"])))																					
						accnamerow = accname .fetchone()
						accountname = accnamerow ["accountname"]															

						lstbankrecon.append({"vouchercode":mapVouchers[row["vouchercode"]],"accountcode":accountname,"clearancedate":row["clearancedate"],"memo":row["memo"]})
					os.system("mkdir backupdir")
					orgFile = open("backupdir/org.back","w")
					success = cPickle.dump(lstorganisation,orgFile)
					orgFile.close()
					gsgFile = open("backupdir/gsg.back","w")
					success = cPickle.dump(lstgroupsubgroups,gsgFile)
					gsgFile.close()
					accFile = open("backupdir/accounts.back","w")
					success = cPickle.dump(lstaccounts,accFile)
					accFile.close()
					usersFile = open("backupdir/users.back","w")
					success = cPickle.dump(lstusers,usersFile)
					usersFile.close()
					projFile = open("backupdir/projects.back","w")
					success = cPickle.dump(lstprojects,projFile)
					projFile.close()
					customerandsupplierFile = open("backupdir/customerandsupplier.back","w")
					success = cPickle.dump(lstcustomerandsupplier,customerandsupplierFile)
					customerandsupplierFile.close()
					categorysubcategoriesFile = open("backupdir/categorysubcategories.back","w")
					success = cPickle.dump(lstcategorysubcategories,categorysubcategoriesFile)
					categorysubcategoriesFile.close()
					categoryspecsFile = open("backupdir/categoryspecs.back","w")
					success = cPickle.dump(lstcategoryspecs,categoryspecsFile)
					categoryspecsFile.close()
					unitofmeasurementFile = open("backupdir/unitofmeasurement.back","w")
					success = cPickle.dump(lstunitofmeasurement,unitofmeasurementFile)
					unitofmeasurementFile.close()
					productFile = open("backupdir/product.back","w")
					success = cPickle.dump(lstproduct,productFile)
					productFile.close()
					godownFile = open("backupdir/godown.back","w")
					success = cPickle.dump(lstgodown,godownFile)
					godownFile.close()
					taxFile = open("backupdir/tax.back","w")
					success = cPickle.dump(lsttax,taxFile)
					taxFile.close()
					purchaseorderFile = open("backupdir/purchaseorder.back","w")
					success = cPickle.dump(lstpurchaseorder,purchaseorderFile)
					purchaseorderFile.close()
					delchalFile = open("backupdir/delchal.back","w")
					success = cPickle.dump(lstdelchal,delchalFile)
					delchalFile.close()
					invoiceFile = open("backupdir/invoice.back","w")
					success = cPickle.dump(lstinvoice,invoiceFile)
					invoiceFile.close()
					dcinvFile = open("backupdir/dcinv.back","w")
					success = cPickle.dump(lstdcinv,dcinvFile)
					dcinvFile.close()
					stockFile = open("backupdir/stock.back","w")
					success = cPickle.dump(lststock,stockFile)
					stockFile.close()
					transfernoteFile = open("backupdir/transfernote.back","w")
					success = cPickle.dump(lsttransfernote,transfernoteFile)
					transfernoteFile.close()
					vouchersFile = open("backupdir/vouchers.back","w")
					success = cPickle.dump(lstvouchers,vouchersFile)
					vouchersFile.close()
					voucherbinFile = open("backupdir/voucherbin.back","w")
					success = cPickle.dump(lstvoucherbin,voucherbinFile)
					voucherbinFile.close()
					bankreconFile = open("backupdir/bankrecon.back","w")
					success = cPickle.dump(lstbankrecon,bankreconFile)
					bankreconFile.close()

					cmp =   tarfile.open("gkbackup.tar.bz2","w:bz2")
					cmp.add("backupdir")
					cmp.close()
					#os.system("rm -rf backupdir")
					gkarch = open("gkbackup.tar.bz2","r")
					archData = base64.b64encode(gkarch.read())
					gkarch.close()
					#os.system("rm gkbackup.tar.bz2")
					return {"gkstatus":enumdict["Success"],"gkdata":archData}
	#		except:
	#			return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
	#		finally:
	#			self.con.close() """
				
				
	
	
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
			os.system("pg_restore -t organisation -t groupsubgroups -t accounts -t users -t projects -t bankrecon -t customerandsupplier -t categorysubcategories -t categoryspecs -t unitofmeasurement -t product -t tax -t godown -t purchaseorder -t delchal -t invoice -t dcinv -t stock -t transfernote  -t vouchers -t voucherbin --dbname=gkdata  /tmp/restore.tar")
		
			return {"gkstatus":enumdict["Success"]}
		except:
			return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
				

	@view_config(request_method='POST',request_param='fulldb=0',renderer='json')
	def RestoreOrg(self):
		""" This method restore entire database with organisation.
		First it checks the user role if the user is admin then only user can do the backup					  """
		#try:
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
		#print pOrg
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
			print "first attempt attempting to insert org data"
			orgdata = pOrg[0]
			#print orgdata
			result = self.con.execute(organisation.insert(),[orgdata])
			print result
					
			organisationd = self.con.execute(select([organisation.c.orgcode]).where(and_(organisation.c.orgname==orgdata["orgname"],organisation.c.orgtype==orgdata["orgtype"],organisation.c.yearstart==orgdata["yearstart"],organisation.c.yearend==orgdata["yearend"])))
			orgrow = organisationd.fetchone()
			orgcode = orgrow["orgcode"]
			print orgcode
			for row in pGsg:
				row["orgcode"] = orgcode
				if row["subgroupof"]== None:
					result = self.con.execute(groupsubgroups.insert(),[row])
				if row["subgroupof"]!= None:
					grpname = row["subgroupof"]
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
			for row in pCategoryspecs:
				row["orgcode"] = orgcode
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
					self.con.execute("alter table stock alter column productcode type bigint")
					self.con.execute("alter table vouchers alter column vouchercode type bigint")
					self.con.execute("alter table bankrecon alter column vouchercode type bigint")
					result = self.con.execute(product.insert(),[row])
			for row in pGodown:
				row["orgcode"] = orgcode
				result = self.con.execute(godown.insert(),[row])
			for row in pTax:
				row["orgcode"] = orgcode
				result = self.con.execute(tax.insert(),[row])
			for row in pPurchaseorder:
				row["orgcode"] = orgcode
				result = self.con.execute(purchaseorder.insert(),[row])
			for row in pDelchal:
				row["orgcode"] = orgcode
				result = self.con.execute(delchal.insert(),[row])
			for row in pInvoice:
				row["orgcode"] = orgcode
				result = self.con.execute(invoice.insert(),[row])
			for row in pDcinv:
				row["orgcode"] = orgcode
				result = self.con.execute(dcinv.insert(),[row])
			for row in pStock:
				row["orgcode"] = orgcode
				result = self.con.execute(stock.insert(),[row])
			for row in pTransfernote:
				row["orgcode"] = orgcode
				result = self.con.execute(transfernote.insert(),[row])
			
			for row in pVoucher:
				row["orgcode"] = orgcode
				result = self.con.execute(vouchers.insert(),[row])
			for row in pVoucherbin:
				row["orgcode"] = orgcode
				result = self.con.execute(voucherbin.insert(),[row])
			for row in pBankrecon:
				row["orgcode"] = orgcode
				result = self.con.execute(bankrecon.insert(),[row])
		finally:
				self.con.close()

		return {"gkstatus":enumdict["Success"]}
		#except:
			#return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}


			
					
