
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
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
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,


Contributors:
"Krishnakant Mane" <kkmane@riseup.net>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
'Prajkta Patkar'<prajakta@dff.org.in>
'Reshma Bhatwadekar'<reshma_b@riseup.net>
"Sanket Kolnoorkar"<Sanketf123@gmail.com>
'Aditya Shukla' <adityashukla9158.as@gmail.com>
'Pravin Dake' <pravindake24@gmail.com>

"""

from pyramid.view import view_defaults,  view_config
from gkcore.views.api_login import authCheck
from gkcore import eng, enumdict
from pyramid.request import Request
from gkcore.models import gkdb
from sqlalchemy.sql import select, distinct
from sqlalchemy import func, desc
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
import jwt
import gkcore
from gkcore.models.meta import dbconnect
from Crypto.PublicKey import RSA
from gkcore.models.gkdb import metadata
from gkcore.models.meta import inventoryMigration,addFields
from gkcore.views.api_invoice import getStateCode 
con= Connection

@view_defaults(route_name='organisations')
class api_organisation(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection

    @view_config(request_method='GET', renderer ='json')
    def getOrgs(self):
        try:
            self.con=eng.connect()
            result = self.con.execute(select([gkdb.organisation.c.orgname, gkdb.organisation.c.orgtype]).order_by(gkdb.organisation.c.orgname).distinct())
            orgs = []
            for row in result:
                orgs.append({"orgname":row["orgname"], "orgtype":row["orgtype"]})
                orgs.sort()
            self.con.close()
            return {"gkstatus":enumdict["Success"], "gkdata":orgs}
        except:
            self.con.close()
            return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(request_method='GET', request_param='type=orgcodelist', renderer='json' , route_name="organisations")
    def getsubOrgs(self):
        try:
            self.con=eng.connect()
            result = self.con.execute(select([gkdb.organisation.c.orgname, gkdb.organisation.c.orgtype,gkdb.organisation.c.orgcode,gkdb.organisation.c.yearstart,gkdb.organisation.c.yearend]).order_by(gkdb.organisation.c.orgcode))
            orgs = []
            for row in result:
                orgs.append({"orgname":row["orgname"], "orgtype":row["orgtype"], "orgcode":row["orgcode"], "yearstart":str(row["yearstart"]), "yearend":str(row["yearend"]) })
                orgs.sort()
            self.con.close()
            return {"gkstatus":enumdict["Success"], "gkdata":orgs}
        except:
            self.con.close()
            return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(route_name='orgyears', request_method='GET', renderer ='json')
    def getYears(self):
        try:
            self.con = eng.connect()
            result = self.con.execute(select([gkdb.organisation.c.yearstart, gkdb.organisation.c.yearend,gkdb.organisation.c.orgcode]).where(and_(gkdb.organisation.c.orgname==self.request.matchdict["orgname"], gkdb.organisation.c.orgtype == self.request.matchdict["orgtype"])).order_by(desc(gkdb.organisation.c.yearend)))
            years = []
            for row in result:
                years.append({"yearstart":str(row["yearstart"]), "yearend":str(row["yearend"]),"orgcode":row["orgcode"]})
            self.con.close()
            return {"gkstatus":enumdict["Success"],"gkdata":years}
        except:
            self.con.close()
            return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(request_method='POST',renderer='json')
    def postOrg(self):

        try:
            self.con = eng.connect()
            dataset = self.request.json_body
            orgdata = dataset["orgdetails"]
            userdata = dataset["userdetails"]
            result = self.con.execute(select([gkdb.signature]))
            sign = result.fetchone()
            if sign == None:
                key = RSA.generate(2560)
                privatekey = key.exportKey('PEM')
                sig = {"secretcode":privatekey}
                gkcore.secret = privatekey
                result = self.con.execute(gkdb.signature.insert(),[sig])
            elif len(sign["secretcode"]) <= 20:
                result = con.execute(gkdb.signature.delete())
                if result.rowcount == 1:
                    key = RSA.generate(2560)
                    privatekey = key.exportKey('PEM')
                    sig = {"secretcode":privatekey}
                    gkcore.secret = privatekey
                    result = self.con.execute(gkdb.signature.insert(),[sig])
            try:
                self.con.execute(select([gkdb.organisation.c.invflag]))
            except:
                inventoryMigration(self.con,eng)
            try:
                self.con.execute(select([gkdb.delchal.c.modeoftransport,gkdb.delchal.c.noofpackages]))
                self.con.execute(select([gkdb.transfernote.c.recieveddate]))
            except:
                addFields(self.con,eng)

            result = self.con.execute(gkdb.organisation.insert(),[orgdata])
            if result.rowcount==1:
                code = self.con.execute(select([gkdb.organisation.c.orgcode]).where(and_(gkdb.organisation.c.orgname==orgdata["orgname"], gkdb.organisation.c.orgtype==orgdata["orgtype"], gkdb.organisation.c.yearstart==orgdata["yearstart"], gkdb.organisation.c.yearend==orgdata["yearend"])))
                orgcode = code.fetchone()
                try:
                    currentassets= {"groupname":"Current Assets","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),currentassets)
                    result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Current Assets",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    grpcode = result.fetchone()
                    result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Bank","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Cash","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Inventory","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Loans & Advance","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Sundry Debtors","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]} ])
                    # Create account Cash in hand under subgroup Cash & Bank A/C under Bank.
                    csh = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Cash",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    cshgrpcd = csh.fetchone()
                    resultc = self.con.execute(gkdb.accounts.insert(),{"accountname":"Cash in hand","groupcode":cshgrpcd["groupcode"],"orgcode":orgcode["orgcode"], "defaultflag":3})
                    bnk = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Bank",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    bnkgrpcd = bnk.fetchone()
                    resultb = self.con.execute(gkdb.accounts.insert(),{"accountname":"Bank A/C","groupcode":bnkgrpcd["groupcode"],"orgcode":orgcode["orgcode"],"defaultflag":2})

                    currentliability= {"groupname":"Current Liabilities","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),currentliability)
                    result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Current Liabilities",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    grpcode = result.fetchone()
                    result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Provisions","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Sundry Creditors for Expense","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Sundry Creditors for Purchase","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Duties & Taxes","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]}])
                    resultDT = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Duties & Taxes",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    grpcd = resultDT.fetchone()
                    resultp = self.con.execute(gkdb.accounts.insert(),[{"accountname":"Krishi Kalyan Cess","groupcode":grpcd["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Swachh Bharat Cess","groupcode":grpcd["groupcode"],"orgcode":orgcode["orgcode"]}])
                    resultL = self.con.execute(gkdb.accounts.insert(),[{"accountname":"VAT_OUT","groupcode":grpcd["groupcode"],"orgcode":orgcode["orgcode"],"sysaccount":1},{"accountname":"VAT_IN","groupcode":grpcd["groupcode"],"orgcode":orgcode["orgcode"],"sysaccount":1}])

                    # Create Direct expense group , get it's group code and create subgroups under it.
                    directexpense= {"groupname":"Direct Expense","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),directexpense)
                    result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname == "Direct Expense", gkdb.groupsubgroups.c.orgcode == orgcode["orgcode"])))
                    DEGrpCodeData = result.fetchone()
                    DEGRPCode = DEGrpCodeData["groupcode"]
                    insData = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Purchase","subgroupof":DEGRPCode,"orgcode":orgcode["orgcode"]},{"groupname":"Consumables","subgroupof":DEGRPCode,"orgcode":orgcode["orgcode"]}])
                    purchgrp = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname == "Purchase", gkdb.groupsubgroups.c.orgcode == orgcode["orgcode"])))
                    purchgrpcd = purchgrp.fetchone()
                    resultp = self.con.execute(gkdb.accounts.insert(),{"accountname":"Purchase A/C","groupcode":purchgrpcd["groupcode"],"orgcode":orgcode["orgcode"], "defaultflag":16})

                    directincome= {"groupname":"Direct Income","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),directincome)
                    results = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname == "Direct Income", gkdb.groupsubgroups.c.orgcode == orgcode["orgcode"])))
                    DIGrpCodeData = results.fetchone()
                    insData = self.con.execute(gkdb.groupsubgroups.insert(),{"groupname":"Sales","subgroupof":DIGrpCodeData["groupcode"],"orgcode":orgcode["orgcode"]})
                    slgrp = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname == "Sales", gkdb.groupsubgroups.c.orgcode == orgcode["orgcode"])))
                    slgrpcd = slgrp.fetchone()
                    resultsl = self.con.execute(gkdb.accounts.insert(),{"accountname":"Sale A/C","groupcode":slgrpcd["groupcode"],"orgcode":orgcode["orgcode"], "defaultflag":19})

                    fixedassets= {"groupname":"Fixed Assets","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),fixedassets)
                    result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Fixed Assets",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    grpcode = result.fetchone()
                    result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Building","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Furniture","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Land","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Plant & Machinery","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]} ])
                    resultad = self.con.execute(gkdb.accounts.insert(),{"accountname":"Accumulated Depreciation","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]})

                    indirectexpense= {"groupname":"Indirect Expense","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),indirectexpense)
                    resultie = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Indirect Expense",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    iegrpcd = resultie.fetchone()
                    resultDP = self.con.execute(gkdb.accounts.insert(),[{"accountname":"Discount on Sale","groupcode":iegrpcd["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Bonus","groupcode":iegrpcd["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Depreciation Expense","groupcode":iegrpcd["groupcode"],"orgcode":orgcode["orgcode"]}])

                    indirectincome= {"groupname":"Indirect Income","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),indirectincome)
                    resultii = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Indirect Income",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    iigrpcd = resultii.fetchone()
                    resultDS = self.con.execute(gkdb.accounts.insert(),{"accountname":"Discount on Purchase","groupcode":iigrpcd["groupcode"],"orgcode":orgcode["orgcode"]})

                    investment= {"groupname":"Investments","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),investment)
                    result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Investments",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    grpcode = result.fetchone()
                    result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Investment in Bank Deposits","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Investment in Shares & Debentures","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]}, ])

                    loansasset= {"groupname":"Loans(Asset)","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),loansasset)

                    loansliab= {"groupname":"Loans(Liability)","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),loansliab)
                    result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Loans(Liability)",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    grpcode = result.fetchone()
                    result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Secured","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]},{"groupname":"Unsecured","orgcode":orgcode["orgcode"],"subgroupof":grpcode["groupcode"]} ])

                    reserves= {"groupname":"Reserves","orgcode":orgcode["orgcode"]}
                    result = self.con.execute(gkdb.groupsubgroups.insert(),reserves)

                    result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Direct Income",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    grpcode = result.fetchone()
                    if orgdata["orgtype"] == "Profit Making":
                        result = self.con.execute(gkdb.groupsubgroups.insert(),[{"groupname":"Capital","orgcode":orgcode["orgcode"]},{"groupname":"Miscellaneous Expenses(Asset)","orgcode":orgcode["orgcode"]}])

                        result = self.con.execute(gkdb.accounts.insert(),{"accountname":"Profit & Loss","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"], "sysaccount":1})

                    else:
                        result = self.con.execute(gkdb.groupsubgroups.insert(),{"groupname":"Corpus","orgcode":orgcode["orgcode"]})

                        result = self.con.execute(gkdb.accounts.insert(),{"accountname":"Income & Expenditure","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"], "sysaccount":1})

                    result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Inventory",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    grpcode = result.fetchone()
                    result = self.con.execute(gkdb.accounts.insert(),[{"accountname":"Closing Stock","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"], "sysaccount":1},{"accountname":"Stock at the Beginning","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"], "sysaccount":1}])

                    result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.groupname=="Direct Expense",gkdb.groupsubgroups.c.orgcode==orgcode["orgcode"])))
                    grpcode = result.fetchone()
                    result = self.con.execute(gkdb.accounts.insert(),{"accountname":"Opening Stock","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"], "sysaccount":1})
                    results = self.con.execute(gkdb.accounts.insert(),[{"accountname":"Salary","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Miscellaneous Expense","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Bank Charges","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Rent","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Travel Expense","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Electricity Expense","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]},{"accountname":"Professional Fees","groupcode":grpcode["groupcode"],"orgcode":orgcode["orgcode"]}])

                    userdata["orgcode"] = orgcode["orgcode"]
                    userdata["userrole"] = -1
                    result = self.con.execute(gkdb.users.insert().values(username = userdata["username"], userpassword=userdata["userpassword"], userrole = -1, userquestion = userdata["userquestion"], useranswer = userdata["useranswer"], orgcode=userdata["orgcode"]))
                    if result.rowcount==1:
                        result = self.con.execute(select([gkdb.users.c.userid]).where(and_(gkdb.users.c.username==userdata["username"], gkdb.users.c.userpassword== userdata["userpassword"], gkdb.users.c.orgcode==userdata["orgcode"])) )
                        if result.rowcount == 1:
                            record = result.fetchone()

                            token = jwt.encode({"orgcode":userdata["orgcode"],"userid":record["userid"]},gkcore.secret,algorithm='HS256')
                            self.con.close()
                            return {"gkstatus":enumdict["Success"],"token":token }
                        else:
                            self.con.close()
                            return {"gkstatus":enumdict["ConnectionFailed"]}
                    else:
                            self.con.close()
                            return {"gkstatus":enumdict["ConnectionFailed"]}
                except:
                    result = self.con.execute(gkdb.organisation.delete().where(gkdb.organisation.c.orgcode==orgcode["orgcode"]))
                    self.con.close()
                    return {"gkstatus":enumdict["ConnectionFailed"]}
            else:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}
        except:
            self.con.close()
            return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(route_name='organisation', request_method='GET',renderer='json')
    def getOrg(self):
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
                result = self.con.execute(select([gkdb.organisation]).where(gkdb.organisation.c.orgcode==authDetails["orgcode"]))
                row = result.fetchone()
                if(row["orgcity"]==None):
                    orgcity=""
                else:
                    orgcity=row["orgcity"]

                if(row["orgaddr"]==None):
                    orgaddr=""
                else:
                    orgaddr=row["orgaddr"]

                if(row["orgpincode"]==None):
                    orgpincode=""
                else:
                    orgpincode=row["orgpincode"]

                if(row["orgstate"]==None):
                    orgstate=""
                else:
                    orgstate=row["orgstate"]

                if(row["orgcountry"]==None):
                    orgcountry=""
                else:
                    orgcountry=row["orgcountry"]

                if(row["orgtelno"]==None):
                    orgtelno=""
                else:
                    orgtelno=row["orgtelno"]

                if(row["orgfax"]==None):
                    orgfax=""
                else:
                    orgfax=row["orgfax"]

                if(row["orgwebsite"]==None):
                    orgwebsite=""
                else:
                    orgwebsite=row["orgwebsite"]

                if(row["orgemail"]==None):
                    orgemail=""
                else:
                    orgemail=row["orgemail"]

                if(row["orgpan"]==None):
                    orgpan=""
                else:
                    orgpan=row["orgpan"]

                if(row["orgmvat"]==None):
                    orgmvat=""
                else:
                    orgmvat=row["orgmvat"]

                if(row["orgstax"]==None):
                    orgstax=""
                else:
                    orgstax=row["orgstax"]

                if(row["orgregno"]==None):
                    orgregno=""
                else:
                    orgregno=row["orgregno"]

                if(row["orgregdate"]==None):
                    orgregdate=""
                else:
                    orgregdate=row["orgregdate"]

                if(row["orgfcrano"]==None):
                    orgfcrano=""
                else:
                    orgfcrano=row["orgfcrano"]

                if(row["orgfcradate"]==None):
                    orgfcradate=""
                else:
                    orgfcradate=row["orgfcradate"]
                if(row["gstin"]==None):
                    gstin=""

                if(row["bankdetails"]==None):
                   bankdetails=""
                else:
                    bankdetails=row["bankdetails"]
                 
                orgDetails={"orgname":row["orgname"], "orgtype":row["orgtype"],"yearstart":str(row["yearstart"]),"yearend":str(row["yearend"]),"orgcity":orgcity,"orgaddr":orgaddr, "orgpincode":orgpincode,"orgstate":orgstate, "orgcountry":orgcountry,"orgtelno":orgtelno, "orgfax":orgfax,"orgwebsite":orgwebsite, "orgemail":orgemail,"orgpan":orgpan, "orgmvat":orgmvat,"orgstax":orgstax, "orgregno":orgregno,"orgregdate":orgregdate, "orgfcrano":orgfcrano,"orgfcradate":orgfcradate, "roflag":row["roflag"],"booksclosedflag":row["booksclosedflag"],"invflag":row["invflag"],"billflag":row["billflag"],"invsflag":row["invsflag"],"gstin":row["gstin"],"bankdetails":row["bankdetails"],"avflag":row["avflag"],"maflag":["maflag"],"modeflag":row["modeflag"]}
                
                self.con.close()
                return {"gkstatus":enumdict["Success"],"gkdata":orgDetails}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}

        """
        This function returns Organisation Details for Invoicing.
        'statecode' receiving from frontend view & depending on statecode gstin will get.
        """
    @view_config(request_method="GET", renderer="json", request_param="billingdetails")
    def getbillingdetails(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                statecode =self.request.params["statecode"]
                result = self.con.execute(select([gkdb.organisation]).where(gkdb.organisation.c.orgcode==authDetails["orgcode"]))
                row = result.fetchone()
                if(row["orgcity"]==None):
                    orgcity=""
                else:
                    orgcity=row["orgcity"]
                if(row["orgaddr"]==None):
                    orgaddr=""
                else:
                    orgaddr=row["orgaddr"]
                if(row["orgpincode"]==None):
                    orgpincode=""
                else:
                    orgpincode=row["orgpincode"]
                if(row["orgstate"]==None):
                    orgstate=""
                else:
                    orgstate = row["orgstate"]
                if(row["orgwebsite"]==None):
                    orgwebsite=""
                else:
                    orgwebsite=row["orgwebsite"]
                if(row["orgpan"]==None):
                    orgpan=""
                else:
                    orgpan=row["orgpan"]
                if(row["orgtelno"]==None):
                    orgtelno=""
                else:
                    orgtelno=row["orgtelno"]
                if(row["orgemail"]==None):
                    orgemail=""
                else:
                    orgemail=row["orgemail"]
                if(row["gstin"]==None):
                    gstin=""
                elif(row["gstin"].has_key(str(statecode))):
                    gstin = row["gstin"][str(statecode)]
                else:
                    gstin=""
                if(row["bankdetails"]==None):
                    bankdetails = ""
                else:
                    bankdetails = row["bankdetails"]

                orgDetails={"orgname":row["orgname"], "orgaddr":orgaddr, "orgpincode":orgpincode, "orgstate":orgstate, "orgwebsite":orgwebsite, "orgpan":orgpan, "orgstategstin":gstin, "orgcity":orgcity, "bankdetails":bankdetails, "orgtelno":orgtelno, "orgemail":orgemail}
                self.con.close()
                return {"gkstatus":enumdict["Success"],"gkdata":orgDetails}
            except:
                return {"gkstatus":  enumdict["ConnectionFailed"]}
        
    @view_config(request_method="GET",renderer="json",request_param="osg=true")
    def getOrgStateGstin(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con =eng.connect()
                gstinResult = self.con.execute("select gstin ->> '%d' as stgstin from organisation where gstin ? '%d' and orgcode = %d "%(int(self.request.params["statecode"]),int(self.request.params["statecode"]),int(authDetails["orgcode"])))
                gstinval = ""
                if gstinResult.rowcount > 0 :
                    gstinrow = gstinResult.fetchone()
                    gstinval = str(gstinrow["stgstin"])
                return{"gkstatus":enumdict["Success"],"gkresult":gstinval}
            except:
                return {"gkstatus":  enumdict["ConnectionFailed"]}
    #code for saving null values of bankdetails and updation in database
    #variable created for orgcode so that query will work easily
    @view_config(request_method='PUT', renderer='json')
    def putOrg(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        orgcode=authDetails['orgcode'] 
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
                userRole = user.fetchone()
                dataset = self.request.json_body
                if userRole[0]==-1:
                    result = self.con.execute(gkdb.organisation.update().where(gkdb.organisation.c.orgcode==authDetails["orgcode"]).values(dataset))
                    if 'bankdetails' not in dataset:
                        self.con.execute("update organisation set bankdetails=NULL where bankdetails IS NOT NULL and orgcode=%d"%int(orgcode))
                    self.con.close()
                    return {"gkstatus":enumdict["Success"]}
                else:
                    {"gkstatus":  enumdict["BadPrivilege"]}
            except:
                self.con.close()
                return {"gkstatus":  enumdict["ConnectionFailed"]}

    @view_config(request_method='DELETE', renderer='json')
    def deleteOrg(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
                userRole = user.fetchone()
                if userRole[0]==-1:
                    result = self.con.execute(gkdb.organisation.delete().where(gkdb.organisation.c.orgcode==authDetails["orgcode"]))
                    if result.rowcount == 1:
                        result = self.con.execute(select([func.count(gkdb.organisation.c.orgcode).label('ocount')]))
                        orgcount = result.fetchone()
                        if orgcount["ocount"]==0:
                            result = self.con.execute(gkdb.signature.delete())
                    self.con.close()
                    return {"gkstatus":enumdict["Success"]}
                else:
                    {"gkstatus":  enumdict["BadPrivilege"]}
            except:
                self.con.close()
                return {"gkstatus":  enumdict["ConnectionFailed"]}

    @view_config(request_method='GET',request_param="type=exists",renderer='json')
    def Orgexists(self):
        try:
            self.con = eng.connect()
            orgtype = self.request.params["orgtype"]
            orgname= self.request.params["orgname"]
            finstart = self.request.params["finstart"]
            finend = self.request.params["finend"]
            orgncount = self.con.execute(select([func.count(gkdb.organisation.c.orgcode).label('orgcode')]).where(and_(gkdb.organisation.c.orgname==orgname,gkdb.organisation.c.orgtype==orgtype, gkdb.organisation.c.yearstart==finstart,gkdb.organisation.c.yearend==finend)))
            org = orgncount.fetchone()
            if org["orgcode"] !=0:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            else:
                return {"gkstatus":enumdict["Success"]}
        except:
            self.con.close()
            return {"gkstatus":  enumdict["ConnectionFailed"]}


    @view_config(request_param='orgcode', request_method='GET',renderer='json')
    def getOrgcode(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            return {"gkstatus":enumdict["Success"],"gkdata":authDetails["orgcode"]}


    @view_config(request_method='PUT', request_param="type=editorganisation", renderer='json')
    def editOrg(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con =eng.connect()
                dataset = self.request.json_body
                result = self.con.execute(gkdb.organisation.update().where(gkdb.organisation.c.orgcode==dataset["orgcode"]).values(dataset))
                self.con.close()
                return {"gkstatus":enumdict["Success"]}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(request_method='PUT', request_param="type=getinventory", renderer='json')
    def getinventory(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
                userRole = user.fetchone()
                dataset = self.request.json_body
                if userRole[0]==-1:
                    result = self.con.execute(gkdb.organisation.update().where(gkdb.organisation.c.orgcode==authDetails["orgcode"]).values(dataset))
                    self.con.close()
                    return {"gkstatus":enumdict["Success"]}
                else:
                    {"gkstatus":  enumdict["BadPrivilege"]}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(route_name='organisation', request_method='GET',request_param='attach=image', renderer='json')
    def getattachment(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails['auth'] == False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(select([gkdb.organisation.c.logo]).where(gkdb.organisation.c.orgcode==authDetails["orgcode"]))
                row=result.fetchone()
                return {"logo":row["logo"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
    #Code for fetching organisations bankdetails depending on organisation code. 
    @view_config(route_name='organisation' , request_method='GET'  , request_param='orgbankdetails' , renderer='json')
    def getorgbankdetails(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(select([gkdb.organisation.c.bankdetails]).where(gkdb.organisation.c.orgcode==authDetails["orgcode"]))
                row = result.fetchone()
                if(row["bankdetails"]==None):
                    bankdetails = ""
                else:
                    bankdetails = row["bankdetails"]

                orgbankDetails={"bankdetails":bankdetails}
                self.con.close()
                return {"gkstatus":enumdict["Success"],"gkbankdata":orgbankDetails}
            except:
                return {"gkstatus":  enumdict["ConnectionFailed"]}

    '''
    Purpose: Get groupcode of group 'Current Liabilities' and subgroup 'Duties & Taxes'
    We have a default subgroup 'Duties & Taxes' under group 'Current Liabilities'.
    All accounts for GST are created under this subgroup.
    This function returns the groupcode of that group and subgroup so that front end can trigger creation of accounts.
    '''
    @view_config(route_name='organisation' , request_method='GET'  , request_param='getgstgroupcode' , renderer='json')
    def getGSTGroupCode(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.orgcode==authDetails["orgcode"], gkdb.groupsubgroups.c.groupname == 'Duties & Taxes')))
                grOup = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.orgcode==authDetails["orgcode"], gkdb.groupsubgroups.c.groupname == 'Current Liabilities')))
                grOupName = grOup.fetchone()
                row = result.fetchone()
                if result.rowcount != 0 and row["groupcode"]!=None:
                    return {"gkstatus":enumdict["Success"],"subgroupcode":int(row["groupcode"]), "groupcode":int(grOupName["groupcode"])}
                else:
                    return {"gkstatus":enumdict["Success"],"subgroupcode":"New", "groupcode":int(grOupName["groupcode"])}
                self.con.close()
            except:
                return {"gkstatus":  enumdict["ConnectionFailed"]}

    '''
    Purpose: Get all accounts of group 'Current Liabilities' and subgroup 'Duties & Taxes' created for GST.
    We have a default subgroup 'Duties & Taxes' under group 'Current Liabilities'.
    All accounts for GST are created under this subgroup.
    This function returns those accounts.
    '''
    @view_config(route_name='organisation' , request_method='GET'  , request_param='getgstaccounts' , renderer='json')
    def getGSTGaccounts(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(select([gkdb.groupsubgroups.c.groupcode]).where(and_(gkdb.groupsubgroups.c.orgcode==authDetails["orgcode"], gkdb.groupsubgroups.c.groupname == 'Duties & Taxes')))
                row = result.fetchone()
                accounts=[]
                if result.rowcount != 0 and row["groupcode"]!=None:
                    accountsdata=self.con.execute(select([gkdb.accounts.c.accountname]).where(and_(gkdb.accounts.c.orgcode==authDetails["orgcode"], gkdb.accounts.c.groupcode == row["groupcode"])))
                    accountslist = accountsdata.fetchall()
                    for account in accountslist:
                        accounts.append(account["accountname"])
                    return {"gkstatus":enumdict["Success"],"accounts":accounts}
                else:
                    return {"gkstatus":  enumdict["ConnectionFailed"]}
                self.con.close()
            except:
                return {"gkstatus":  enumdict["ConnectionFailed"]}

    # returns avfalag , to decide auto voucher creation
    @view_config(request_method='GET',request_param='autovoucher' , renderer='json')
    def getAVflag(self):
        token = self.request.headers['gktoken']
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(select([gkdb.organisation.c.avflag]).where(gkdb.organisation.c.orgcode==authDetails["orgcode"]))
                return {"gkstatus":enumdict["Success"],"autovoucher":result["avflag"]}
                self.con.close()
            except:
                return {"gkstatus":  enumdict["ConnectionFailed"]}

    
    
