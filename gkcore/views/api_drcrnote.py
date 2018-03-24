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
"Krishnakant Mane" <kk@gmail.com>
"Reshma Bhatwadekar" <reshma@dff.org.in>
"Vasudha Kadge" <kadge.vasudha@gmail.com>
'Abhijith Balan'<abhijith@dff.org.in>
"""
from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice,tax,state,drcr,customerandsupplier,users,product,unitofmeasurement
from gkcore.views.api_tax  import calTax
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from datetime import datetime,date
import jwt
import gkcore
from gkcore.views.api_login import authCheck
from gkcore.views.api_user import getUserRole
from gkcore.views.api_invoice import getStateCode

@view_defaults(route_name='drcrnote')
class api_drcr(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection
    @view_config(request_method='POST',renderer='json')
    def createDrCrNote(self):
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
                dataset = self.request.json_body
                dataset["orgcode"] = authDetails["orgcode"]
                result=self.con.execute(drcr.insert(),[dataset])
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
                
    @view_config(request_method='GET',request_param="drcr=single", renderer ='json')
    def getDrCrDetails(self):
        """
        purpose: gets details of single debit or credit note from it's drcrid.
        The details include related customer or supplier and sales or purchase invoice details as well as calculation of amount.
        Description:
        This function returns a single record as key:value pair for debit-credit note given it's drcrid.
        Depending upon dctypeflag(for credit note it is "3" and for debit note it is"4")it will return the details of debit note and credit note.
        It also calculates total amount, taxable amount, new taxable amount, total debited/credited value with all the taxes.
        The function returns a dictionary with the details of debit & credit note.
        If reference equal to none then send null value otherwise respected reference credit/debit note number and credit/debit note date.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        else:
           # try:
                self.con = eng.connect()
                #taken credit/debit note data on the basis on drcrid
                drcrresult=self.con.execute(select([drcr]).where(drcr.c.drcrid==self.request.params["drcrid"]))
                drcrrow=drcrresult.fetchone()
                invdata={}
                custSupDetails={}
                drcrdata={}
                drcrdata = {"drcrid":drcrrow["drcrid"],"drcrno":drcrrow["drcrno"],"drcrdate":datetime.strftime(drcrrow["drcrdate"],"%d-%m-%Y"),"dctypeflag":drcrrow["dctypeflag"],"totreduct":"%.2f"%float(drcrrow["totreduct"]),"reduct":drcrrow["reductionval"]}
                #reference is a dictionary which contains reference number as key and reference date as value.
                #if reference field is not None then send refernce dictionary.
                if drcrrow["reference"] == None:
                    drcrdata["reference"]= ""
                else:
                    drcrdata["reference"]=drcrrow["reference"]
                #taken data of invoice on the basis of invid.
                invresult=self.con.execute(select([invoice]).where(invoice.c.invid==drcrrow["invid"]))
                invrow=invresult.fetchone()
                invdata={"invid":invrow["invid"],"invoiceno":invrow["invoiceno"],"invoicedate":datetime.strftime(invrow["invoicedate"],"%d-%m-%Y"),"inoutflag":invrow["inoutflag"],"taxflag":invrow["taxflag"],"tax":invrow["tax"],"orgstategstin":invrow["orgstategstin"]}
                drcrdata["contents"] = invrow["contents"]
                contentsData = invrow["contents"]
                if invrow["sourcestate"] != None or invrow["taxstate"] !=None:
                        invdata["sourcestate"] = invrow["sourcestate"]
                        sourceStateCode = getStateCode(invrow["sourcestate"],self.con)["statecode"]
                        invdata["sourcestatecode"] = sourceStateCode
                        invdata["taxstate"]=invrow["taxstate"]
                        taxStateCode=getStateCode(invrow["taxstate"],self.con)["statecode"]
                        invdata["taxstatecode"]=taxStateCode
                #taken data of customerandsupplier on the basis of custid
                custresult=self.con.execute(select([customerandsupplier.c.custid,customerandsupplier.c.custname,customerandsupplier.c.custaddr,customerandsupplier.c.gstin,customerandsupplier.c.custtan,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invrow["custid"]))
                custrow=custresult.fetchone()
                custSupDetails={"custid":custrow["custid"],"custname":custrow["custname"],"custaddr":custrow["custaddr"],"gstin":custrow["gstin"],"custtin":custrow["custtan"]}
                #tin and gstin checked.
                if custSupDetails["custtin"] != None:
                    custSupDetails["custtin"] = custSupDetails["custtin"]
                if custSupDetails["gstin"] != None:
                    if int(custrow["csflag"]) == 3 :
                        try:
                            custSupDetails["custgstin"] = custrow["gstin"][str(taxStateCode)]
                        except:
                            custSupDetails["custgstin"] = None
                    else:
                        try:
                            custSupDetails["custgstin"] = custrow["gstin"][str(sourceStateCode)]
                        except:
                            custSupDetails["custgstin"] = None
                drcrdata["custSupDetails"] = custSupDetails              

                #all data checked using inout flag,
                if int(invrow["inoutflag"])==15:
                    #if inoutflag=15 then issuername and designation is same as invoice details
                    invdata["issuername"]=invrow["issuername"]
                    invdata["designation"]=invrow["designation"]
                elif int(invrow["inoutflag"])==9 :
                    #if inoutflag=9 then issuername and designation is taken from login details.
                    #user deatils
                    userresult=self.con.execute(select([users.c.userid,users.c.username,users.c.userrole]).where(users.c.userid==drcrrow["userid"]))
                    userrow=userresult.fetchone()
                    userdata={"userid":userrow["userid"],"username":userrow["username"],"userrole":userrow["userrole"]}
                    invdata["issuername"]=userrow["username"]
                    invdata["designation"]=userrow["userrole"]
                    
                #calculations 
                #contents is a nested dictionary from drcr table.
                #It contains productcode as the key with a value as a dictionary.
                #this dictionary has two key value pair, priceperunit and quantity.
                idrateData=drcrrow["reductionval"]
                #drcrdata is the final dictionary which will not just have the dataset from original contents,
                #but also productdesc,unitname,discount,taxname,taxrate,amount and taxamount
                #invdata containing invoice details.
                drcrContents = {}
                idrate={}
                #get the dictionary of discount and access it inside the loop for one product each.
                totalDisc = 0.00
                totalTaxableVal = 0.00
                totalTaxAmt = 0.00
                totalCessAmt = 0.00
                discounts = invrow["discount"]
                
                #pc will have the productcode which will be the key in contentsData.
                for pc in idrateData.keys():
                    if discounts != None:
                        discount=discounts[pc]                        
                    else:
                        discount= 0.00
                    prodresult = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gsflag,product.c.gscode]).where(product.c.productcode == pc))
                    prodrow = prodresult.fetchone()
                    #product or service check and taxableAmount calculate=newppu*newqty
                    taxRate = 0.00
                    totalAmount = 0.00
                    taxRate =  float(invrow["tax"][pc])
                    if int(invrow["taxflag"]) == 22:
                        umresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid == int(prodrow["uomid"])))
                        umrow = umresult.fetchone()
                        unitofMeasurement = umrow["unitname"]
                        reductprice=((float(contentsData[pc][contentsData[pc].keys()[0]]))*(float(idrateData[pc])))
                        taxRate =  float(invrow["tax"][pc])
                        taxAmount = (reductprice * float(taxRate/100))
                        taxname = 'VAT'
                        totalAmount = reductprice + taxAmount
                        totalDisc = totalDisc + float(discount)
                        totalTaxableVal = totalTaxableVal + reductprice
                        totalTaxAmt = totalTaxAmt + taxAmount
                        drcrContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][contentsData[pc].keys()[0]])),"priceperunit":"%.2f"% (float(contentsData[pc].keys()[0])),"discount":"%.2f"% (float(discount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":"VAT","taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount)),"newtaxableamnt":"%.2f"% (float(taxAmount))}
                        idrate[pc]={"reductionval":idrateData}
                    else:   
                        if int(prodrow["gsflag"]) == 7:
                            umresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid == int(prodrow["uomid"])))
                            umrow = umresult.fetchone()
                            unitofMeasurement = umrow["unitname"]
                            reductprice=float(contentsData[pc][contentsData[pc].keys()[0]])*float(idrateData[pc])
                        else:
                            unitofMeasurement = ""
                            reductprice=float(idrateData[pc])
                        cessRate = 0.00
                        cessAmount = 0.00
                        cessVal = 0.00
                        taxname = ""
                        if invrow["cess"] != None:
                            cessVal = float(invrow["cess"][pc])
                            cessAmount = (reductprice * (cessVal/100))
                            totalCessAmt = totalCessAmt + cessAmount

                        if invrow["sourcestate"] != invrow["taxstate"]:
                            taxname = "IGST"
                            taxAmount = (reductprice * (taxRate/100))
                            totalAmount = reductprice + taxAmount + cessAmount
                        else:
                            taxname = "SGST"
                            # SGST and CGST rates are equal and exactly half the IGST rate.
                            taxAmount = (reductprice * (taxRate/200))
                            totalAmount = reductprice + (2*taxAmount) + cessAmount                   
                        totalDisc = totalDisc + float(discount)
                        totalTaxableVal = totalTaxableVal + reductprice
                        totalTaxAmt = totalTaxAmt + taxAmount
                        drcrContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][contentsData[pc].keys()[0]])),"priceperunit":"%.2f"% (float(contentsData[pc].keys()[0])),"discount":"%.2f"% (float(discount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":taxname,"taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount)),"cess":"%.2f"%(float(cessAmount)),"cessrate":"%.2f"%(float(cessVal)),"newtaxableamnt":"%.2f"% (float(reductprice))}
                drcrdata["totaltaxablevalue"] = "%.2f"% (float(totalTaxableVal))
                drcrdata["totaltaxamt"] = "%.2f"% (float(totalTaxAmt))
                drcrdata["totalcessamt"] = "%.2f"% (float(totalCessAmt))
                drcrdata['taxname'] = taxname
                drcrdata["drcrcontents"] = drcrContents
                drcrdata["reductval"]=idrateData
                drcrdata["invdata"]=invdata
                return {"gkstatus":gkcore.enumdict["Success"],"gkresult":drcrdata}
            #except:
             #   return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
           # finally:
            #    self.con.close()
                
    @view_config(request_method='GET',request_param="drcr=all", renderer ='json')
    def getAlldrcr(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(select([drcr.c.drcrno,drcr.c.drcrid,drcr.c.drcrdate,drcr.c.invid,drcr.c.dctypeflag,drcr.c.totreduct,drcr.c.attachmentcount]).where(drcr.c.orgcode==authDetails["orgcode"]).order_by(drcr.c.drcrdate))
                drcrdata = []
                for row in result:
                    #invoice,cust
                    inv=self.con.execute(select([invoice.c.custid]).where(invoice.c.invid==row["invid"]))
                    invdata=inv.fetchone()
                    custsupp=self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invdata["custid"]))
                    custsuppdata= custsupp.fetchone()
                    if self.request.params.has_key('drcrflag'):                       
                        if int(self.request.params["drcrflag"])==int(row["dctypeflag"]):
                            drcrdata.append({"drcrid":row["drcrid"],"drcrno":row["drcrno"],"drcrdate":datetime.strftime(row["drcrdate"],'%d-%m-%Y'),"dctypeflag":row["dctypeflag"],"totreduct":"%.2f"%float(row["totreduct"]),"invid":row["invid"],"attachmentcount":row["attachmentcount"],"custid":invdata["custid"],"custname":custsuppdata["custname"],"csflag":custsuppdata["csflag"]})
                    else:
                        drcrdata.append({"drcrid":row["drcrid"],"drcrno":row["drcrno"],"drcrdate":datetime.strftime(row["drcrdate"],'%d-%m-%Y'),"dctypeflag":row["dctypeflag"],"totreduct":"%.2f"%float(row["totreduct"]),"invid":row["invid"],"attachmentcount":row["attachmentcount"],"custid":invdata["custid"],"custname":custsuppdata["custname"],"csflag":custsuppdata["csflag"]})
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":drcrdata }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
    '''
    Deleteing drcr on the basis of reference field and drcrid
    if credit/debit note number is not used as reference then it can be deleted.
    '''
    @view_config(request_method='DELETE', renderer ='json')
    def deletedrcr(self):
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
                dataset = self.request.json_body
                result=self.con.execute(select([drcr.c.drcrid,drcr.c.reference]).where(drcr.c.drcrid==dataset["drcrid"]))
                row=result.fetchone()                
                if not row["reference"]:
                     result = self.con.execute(drcr.delete().where(drcr.c.drcrid==dataset["drcrid"]))
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET',request_param='attach=image', renderer='json')
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
                ur = getUserRole(authDetails["userid"])
                urole = ur["gkresult"]
                drcrid = self.request.params["drcrid"]
                drcrData = self.con.execute(select([drcr.c.drcrno, drcr.c.attachment]).where(drcr.c.drcrid == drcrid))
                attachment = drcrData.fetchone()
                return {"gkstatus":enumdict["Success"],"gkresult":attachment["attachment"],"drcrno":attachment["drcrno"],"userrole":urole["userrole"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
    '''This is a function to update .
    This function is primarily used to enable editing of debit and credit note.
    It receives a dictionary with information regarding debit and credit note
        Update for debit and credit note.'''
    @view_config(request_method='PUT', renderer='json')
    def editDrCrNote(self):
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
                dataset = self.request.json_body
                result = self.con.execute(drcr.update().where(drcr.c.drcrid==dataset["drcrid"]).values(dataset))
                return {"gkstatus":enumdict["Success"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    
