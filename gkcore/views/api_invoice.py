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
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"Mohd. Talha Pawaty" <mtalha456@gmail.com>
"Vaibhav Kurhe" <vaibhav.kurhe@gmail.com>
"Bhavesh Bawadhane" <bbhavesh07@gmail.com>
"Prajkta Patkar" <prajakta@dff.org.in>
"Reshma Bhatwadekar" <bhatawadekar1reshma@gmail.com>
"Aditya Shukla" <adityashukla9158.as@gmail.com>
"""


from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice, dcinv, delchal, stock, product, customerandsupplier, unitofmeasurement, godown, rejectionnote,tax, state, users,organisation,accounts,state
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


def gst(ProductCode,con):
    gstData = con.execute(select([product.c.gsflag,product.c.gscode]).where(product.c.productcode == ProductCode))
    gst = gstData.fetchone()
    return {"gsflag":gst["gsflag"],"gscode":gst["gscode"]}

def getStateCode(StateName,con):
    stateData = con.execute(select([state.c.statecode]).where(state.c.statename == StateName))
    staterow = stateData.fetchone()
    return {"statecode":staterow["statecode"]}



@view_defaults(route_name='invoice')
class api_invoice(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection
    @view_config(request_method='POST',renderer='json')
    def addInvoice(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        else:
           # try:
                self.con = eng.connect()
                dtset = self.request.json_body
                dcinvdataset={}
                invdataset = dtset["invoice"]
                #print invdataset
                freeqty = invdataset["freeqty"]
                stockdataset = dtset["stock"]
                items = invdataset["contents"]
                invdataset["orgcode"] = authDetails["orgcode"]
                stockdataset["orgcode"] = authDetails["orgcode"]
                queryParams = {}
                result = self.con.execute(invoice.insert(),[invdataset])
                print "InvDataset Inserted"
                if invdataset.has_key("dcid"):
                    if result.rowcount == 1:
                        result = self.con.execute(select([invoice.c.invid]).where(and_(invoice.c.custid==invdataset["custid"], invoice.c.invoiceno==invdataset["invoiceno"],invoice.c.orgcode==invdataset["orgcode"],invoice.c.icflag==9)))
                        invoiceid = result.fetchone()
                        dcinvdataset["dcid"]=invdataset["dcid"]
                        dcinvdataset["invid"]=invoiceid["invid"]
                        dcinvdataset["orgcode"]=invdataset["orgcode"]
                        dcinvdataset["invprods"] = stockdataset["items"]
                        result = self.con.execute(dcinv.insert(),[dcinvdataset])
                        if result.rowcount ==1:
                            print "Invoice inserted 1 "
                            # check automatic voucher flag  if it is 1 get maflag
                            avfl = self.con.execute(select([organisation.c.avflag]).where(organisation.c.orgcode == invdataset["orgcode"]))
                            av = avfl.fetchone()
                            if av["avflag"] == 1:
                                print "1 avflag is 1"
                                avData = invdataset["av"]
                                mafl = self.con.execute(select([organisation.c.maflag]).where(organisation.c.orgcode == invdataset["orgcode"]))
                                csName = self.con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.orgcode == invdataset["orgcode"],customerandsupplier.c.custid==int(invdataset["custid"]))))
                                CSname = csName.fetchone()
                                
                                queryParams = {"invtype":invdataset["inoutflag"],"pmtmode":invdataset["paymentmode"],"taxType":invdataset["taxflag"],"gstname":av["avtax"]["GSTName"],"destinationstate":invdataset["taxstate"],"totaltaxablevalue":avData["totaltaxable"],"maflag":mafl["maflag"],"totalAmount":invdataset["invoicetotal"],"invoicedate":invdataset["invoicedate"],"invid":invoiceid["invid"],"invoiceno":invdataset["invno"],"csname":csName["custname"]}
                                if "taxpayment" in avData:
                                    queryParams = {"taxpayement":avData["taxpayement"]}
                                #call getDefaultAcc
                                a = getStateCode(self,queryParams,int(invdataset["orgcode"]))
                                print a
                            return {"gkstatus":enumdict["Success"],"gkresult":invoiceid["invid"]} 
                        else:
                            return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
                else:
                  #  try:
                        if invdataset.has_key('icflag'):
                            result = self.con.execute(select([invoice.c.invid,invoice.c.invoicedate]).where(and_(invoice.c.invoiceno==invdataset["invoiceno"],invoice.c.orgcode==invdataset["orgcode"],invoice.c.icflag==invdataset["icflag"])))
                            invoiceid = result.fetchone()
                            stockdataset["dcinvtnid"] = invoiceid["invid"]
                            for item in items.keys():
                                gstResult = gst(item,self.con)
                                if int(gstResult["gsflag"]) == 7:
                                    stockdataset["productcode"] = item
                                    stockdataset["qty"] = float(items[item].values()[0])+float(freeqty[item])
                                    stockdataset["dcinvtnflag"] = "3"
                                    stockdataset["stockdate"] = invoiceid["invoicedate"]
                                    result = self.con.execute(stock.insert(),[stockdataset])
                            print "2 Inserted data"
                            avfl = self.con.execute(select([organisation.c.avflag]).where(organisation.c.orgcode == invdataset["orgcode"]))
                            if avfl["avflag"] == 1:
                                #{"invtype":19 or 16 ,"csname":customer/supplier name ,"pmtmode":2 or 3 or 15,"taxType":7 or 22,"gstname":"CGST / IGST","cessname":"cess","maflag":True /False,"products":{"productname":Taxable value,"productname1":Taxabe value,.........},"destination":taxstate,"totaltaxablevalue":value,"totalAmount":invoicetotal,"invoicedate":invDate,"invid":id,"invoiceno":invno,"taxpayement":VATtax}
                                avData = invdataset["av"]
                                mafl = self.con.execute(select([organisation.c.maflag]).where(organisation.c.orgcode == invdataset["orgcode"]))
                                csName = self.con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.orgcode == invdataset["orgcode"],customerandsupplier.c.custid==int(invdataset["custid"]))))
                                
                                queryParams = {"invtype":invdataset["inoutflag"],"pmtmode":invdataset["paymentmode"],"taxType":invdataset["taxflag"],"gstname":av["avtax"]["GSTName"],"destinationstate":invdataset["taxstate"],"totaltaxablevalue":avData["totaltaxable"],"maflag":mafl["maflag"],"totalAmount":invdataset["invoicetotal"],"invoicedate":invdataset["invoicedate"],"invid":invoiceid["invid"],"invoiceno":invdataset["invno"]}
                                if "taxpayment" in avData:
                                    queryParams = {"taxpayement":avData["taxpayement"]}
                                a = getStateCode(self,queryParams,int(invdataset["orgcode"]))
                            return {"gkstatus":enumdict["Success"],"gkresult":invoiceid["invid"]}
                        else:
                            print "i am in invoice condition"
                            result = self.con.execute(select([invoice.c.invid,invoice.c.invoicedate]).where(and_(invoice.c.custid==invdataset["custid"], invoice.c.invoiceno==invdataset["invoiceno"],invoice.c.orgcode==invdataset["orgcode"],invoice.c.icflag==9)))
                            invoiceid = result.fetchone()
                            stockdataset["dcinvtnid"] = invoiceid["invid"]
                            stockdataset["stockdate"] = invoiceid["invoicedate"]
                            for item in items.keys():
                                gstResult = gst(item,self.con)
                                print"goods ki service"
                                if int(gstResult["gsflag"]) == 7:
                                    stockdataset["productcode"] = item
                                    stockdataset["qty"] = float(items[item].values()[0])+float(freeqty[item])
                                    stockdataset["dcinvtnflag"] = "9"
                                    result = self.con.execute(stock.insert(),[stockdataset])
                                print "Invoice 333333"
                                # check automatic voucher flag  if it is 1 get maflag
                                avfl = self.con.execute(select([organisation.c.avflag]).where(organisation.c.orgcode == invdataset["orgcode"]))
                                av = avfl.fetchone()
                                if av["avflag"] == 1:
                                    print "1 avflag is 1"
                                    avData = invdataset["av"]
                                    mafl = self.con.execute(select([organisation.c.maflag]).where(organisation.c.orgcode == invdataset["orgcode"]))
                                    maFlag = mafl.fetchone()
                                    csName = self.con.execute(select([customerandsupplier.c.custname]).where(and_(customerandsupplier.c.orgcode == invdataset["orgcode"],customerandsupplier.c.custid==int(invdataset["custid"]))))
                                    CSname = csName.fetchone()
                                    queryParams = {"invtype":invdataset["inoutflag"],"pmtmode":invdataset["paymentmode"],"taxType":invdataset["taxflag"],"gstname":avData["avtax"]["GSTName"],"destinationstate":invdataset["taxstate"],"totaltaxablevalue":avData["totaltaxable"],"maflag":maFlag["maflag"],"totalAmount":invdataset["invoicetotal"],"invoicedate":invdataset["invoicedate"],"invid":invoiceid["invid"],"invoiceno":invdataset["invoiceno"],"csname":CSname["custname"],"taxes":invdataset["tax"]}
                                    if "taxpayment" in avData:
                                        queryParams = {"taxpayement":avData["taxpayement"]}
                                    #call getDefaultAcc
                                    a = self.getDefaultAcc(queryParams,int(invdataset["orgcode"]))
                                    print a
                            return {"gkstatus":enumdict["Success"],"gkresult":invoiceid["invid"]}
                    #except:
                     #   result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==invoiceid["invid"],stock.c.dcinvtnflag==9)))
                     #   result = self.con.execute(invoice.delete().where(invoice.c.invid==invoiceid["invid"]))
                     #   return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            #except exc.IntegrityError:
            #    return {"gkstatus":enumdict["DuplicateEntry"]}
            #except:
            #    return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            #finally:
            #    self.con.close()

    '''
    This is a function to update an invoice.
    This function is primarily used to enable editing of invoices.
    It receives a dictionary with information regarding an invoice, changes to be made in stock if any and delivery notes linked if any.
    '''
    @view_config(request_method='PUT', renderer='json')
    def editInvoice(self):
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
                # Data is stored in a variable dtset.
                dtset = self.request.json_body
                # Empty dictionary to store details of delivery challan linked if any.
                dcinvdataset={}
                # Details of invoice and stock are stored in separate variables.
                invdataset = dtset["invoice"]
                stockdataset = dtset["stock"]
                items = invdataset["contents"]
                invdataset["orgcode"] = authDetails["orgcode"]
                stockdataset["orgcode"] = authDetails["orgcode"]
                # Entries in dcinv and stock tables are deleted to avoid duplicate entries.
                try:
                    deletestock = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==invdataset["invid"],stock.c.dcinvtnflag==9)))
                except:
                    pass
                try:
                    deletedcinv = self.con.execute(dcinv.delete().where(dcinv.c.invid==invdataset["invid"]))
                except:
                    pass
                # If delivery chalan is linked  details of invoice are updated and a new entry is made in the dcinv table.
                if invdataset.has_key("dcid"):
                    dcinvdataset["dcid"]=invdataset.pop("dcid")
                    dcinvdataset["orgcode"]=invdataset["orgcode"]
                    dcinvdataset["invid"]=invdataset["invid"]
                    dcinvdataset["invprods"] = stockdataset["items"]
                    try:
                        updateinvoice = self.con.execute(invoice.update().where(invoice.c.invid==invdataset["invid"]).values(invdataset))
                        result = self.con.execute(dcinv.insert(),[dcinvdataset])
                        return {"gkstatus":enumdict["Success"]}
                    except:
                        return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
                # If no delivery challan is linked an entry is made in stock table after invoice details are updated.
                else:
                    try:
                        updateinvoice = self.con.execute(invoice.update().where(invoice.c.invid==invdataset["invid"]).values(invdataset))
                        #Code for updating bankdetails when user switch to cash payment from bank.
                        getpaymentmode = int(invdataset["paymentmode"]) #Loading paymentmode.
                        idinv = int(invdataset["invid"])   #Loading invoiceid.
                        #checking paymentmod whether it is 2 or 3 (i.e. 2 for bank and 3 for cash).
                        if getpaymentmode == 3:
                            #Updating bankdetails to NULL if paymentmod is 3.
                            updatebankdetails = self.con.execute("update invoice set bankdetails = NULL where invid = %d"%(idinv))
                        result = self.con.execute(select([invoice.c.invid,invoice.c.invoicedate]).where(and_(invoice.c.custid==invdataset["custid"], invoice.c.invoiceno==invdataset["invoiceno"])))
                        invoiceid = result.fetchone()
                        stockdataset["dcinvtnid"] = invoiceid["invid"]
                        stockdataset["stockdate"] = invoiceid["invoicedate"]
                        stockdataset["dcinvtnflag"] = "9"
                        for item in items.keys():
                            stockdataset["productcode"] = item
                            stockdataset["qty"] = items[item].values()[0]
                            result = self.con.execute(stock.insert(),[stockdataset])
                        return {"gkstatus":enumdict["Success"]}
                    except:
                        return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
    @view_config(request_method='PUT',request_param='type=bwa',renderer='json')
    def updatePayment(self):
        """
        purpose: updates the total payed amount for a certain bill or invoice or puts it on account for custommer/supplyer.
        Description:
        The function will take invid and amount received.
        The function also takes a flag called payflag.
        This flag will have the value 1:advance,2:billwise,15:on-account.
        If payflag = 2 then function will update the invoice table,
        with the given amount by incrementing paydamount for the given invoice.
        Else the amount will be added to either advamce for value 1 and onaccamt for value 15,
        Both in customer table, which implies that csid must be needed.
There will be an icFlag which will determine if it's  an incrementing or decrement.
        """
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
                payflag = int(self.request.params["payflag"])
                pdamt = float(self.request.params["pdamt"])
                if payflag == 1:
                    icFlag =int( self.request.params["icflag"])
                    custid = int(self.request.params["custid"])
                    if icFlag == 9:
                        result = self.con.execute("update customerandsupplier set advamt = advamt + %f where custid = %d"%(pdamt,custid))
                    else:
                        result = self.con.execute("update customerandsupplier set advamt = advamt - %f where custid = %d"%(pdamt,custid))
                if payflag == 15:
                    icFlag = int(self.request.params["icflag"])
                    custid = int(self.request.params["custid"])
                    if icFlag == 9:
                        result = self.con.execute("update customerandsupplier set onaccamt = onaccamt + %f where custid = %d"%(pdamt,custid))
                    else:
                        result = self.con.execute("update customerandsupplier set onaccamt = onaccamt - %f where custid = %d"%(pdamt,custid))
                if payflag == 2:
                    invid = int(self.request.params["invid"])
                    result = self.con.execute("update invoice set amountpaid = amountpaid + %f where invid = %d"%(pdamt,invid))
                return {"gkstatus":enumdict["Success"]}

            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET',request_param="inv=single", renderer ='json')
    def getInvoiceDetails(self):
        """
        purpose: gets details on an invoice given it's invid.
        The details include related customer or supplier details as well as calculation of amount.
        Description:
        This function returns a single record as key:value pare for an invoice given it's invid.
        Depending on the invoice type it will return the details on customer or supplier.
        It also calculates total amount, taxable amount with all the taxes.
        The function returns a nested dictionary with dicts for products with their costing details, free quantyty etc.
        If address equal to none then send null value otherwise respected address.
        "inoutflag" gives invoice is in or out (i.e Purchase or Sale) for sales invoice "inoutflag"=15 and for Purchase invoice "inoutflag"=9.
        Note: the details such as state code, place of supplyer etc depends on the tax type.
        The above mentioned and some more fields are only returned if the tax is GST.
    """
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
                result = self.con.execute(select([invoice]).where(invoice.c.invid==self.request.params["invid"]))
                invrow = result.fetchone()
                inv = {"invid":invrow["invid"],"taxflag":invrow["taxflag"],"invoiceno":invrow["invoiceno"],"invoicedate":datetime.strftime(invrow["invoicedate"],"%d-%m-%Y"),"icflag":invrow["icflag"],"invoicetotal":"%.2f"%float(invrow["invoicetotal"]),"invoicetotalword":invrow["invoicetotalword"],"bankdetails":invrow["bankdetails"], "orgstategstin":invrow["orgstategstin"], "paymentmode":invrow["paymentmode"], "inoutflag" : invrow["inoutflag"]}
                if invrow["sourcestate"] != None:
                    inv["sourcestate"] = invrow["sourcestate"]
                    inv["sourcestatecode"] = getStateCode(invrow["sourcestate"],self.con)["statecode"]
                    sourceStateCode = getStateCode(invrow["sourcestate"],self.con)["statecode"]
                if invrow["address"] == None:
                    inv["address"]= ""
                else:
                    inv["address"]=invrow["address"]
                if invrow["icflag"]==9:
                    inv["issuername"]=invrow["issuername"]
                    inv["designation"]=invrow["designation"]
                    inv["consignee"] = invrow["consignee"]
                    inv["attachmentcount"] = invrow["attachmentcount"]
                    if invrow["dateofsupply"] != None:
                        inv["dateofsupply"]=datetime.strftime(invrow["dateofsupply"],"%d-%m-%Y")
                    else:
                        inv["dateofsupply"] = ""
                    inv["transportationmode"] = invrow["transportationmode"]
                    inv["vehicleno"] = invrow["vehicleno"]
                    inv["reversecharge"] = invrow["reversecharge"]
                    if invrow["taxstate"] != None:
                        inv["destinationstate"]=invrow["taxstate"]
                        taxStateCode =  getStateCode(invrow["taxstate"],self.con)["statecode"]
                        inv["taxstatecode"] = taxStateCode
                        
                    result =self.con.execute(select([dcinv.c.dcid]).where(dcinv.c.invid==invrow["invid"]))
                    dcid = result.fetchone()
                    if result.rowcount>0:
                        dc = self.con.execute(select([delchal.c.dcno, delchal.c.dcdate]).where(delchal.c.dcid==dcid["dcid"]))
                        delchalData = dc.fetchone()                      
                        inv["dcid"]=dcid["dcid"]
                        inv["dcno"]=delchalData["dcno"]
                        inv["dcdate"] = datetime.strftime(delchalData["dcdate"],"%d-%m-%Y")
                    custandsup = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.state, customerandsupplier.c.custaddr, customerandsupplier.c.custtan,customerandsupplier.c.gstin, customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invrow["custid"]))
                    custData = custandsup.fetchone()
                    custsupstatecode = getStateCode(custData["state"],self.con)["statecode"]
                    custSupDetails = {"custname":custData["custname"],"custsupstate":custData["state"],"custaddr":custData["custaddr"],"csflag":custData["csflag"],"custsupstatecode":custsupstatecode}
                    if custData["custtan"] != None:
                        custSupDetails["custtin"] = custData["custtan"]
                    if custData["gstin"] != None:
                        if int(custData["csflag"]) == 3 :
                           try:
                               custSupDetails["custgstin"] = custData["gstin"][str(taxStateCode)]
                           except:
                               custSupDetails["custgstin"] = None
                        else:
                            try:
                                custSupDetails["custgstin"] = custData["gstin"][str(sourceStateCode)]
                            except:
                                custSupDetails["custgstin"] = None

                    inv["custSupDetails"] = custSupDetails
                #contents is a nested dictionary from invoice table.
                #It contains productcode as the key with a value as a dictionary.
                #this dictionary has two key value pare, priceperunit and quantity.
                contentsData = invrow["contents"]
                #invContents is the finally dictionary which will not just have the dataset from original contents,
                #but also productdesc,unitname,freeqty,discount,taxname,taxrate,amount and taxam
                invContents = {}
                #get the dictionary of discount and access it inside the loop for one product each.
                #do the same with freeqty.
                totalDisc = 0.00
                totalTaxableVal = 0.00
                totalTaxAmt = 0.00
                totalCessAmt = 0.00
                discounts = invrow["discount"]
                freeqtys = invrow["freeqty"]
                #now looping through the contents.
                #pc will have the productcode which will be the ke in invContents.
                for pc in contentsData.keys():
                    #freeqty and discount can be 0 as these field were not present in previous version of 4.25 hence we have to check if it is None or not and have to pass values accordingly for code optimization. 
                    if discounts != None:
                        discount = discounts[pc]
                    else:
                        discount = 0.00

                    if freeqtys != None:
                        freeqty = freeqtys[pc]
                    else:
                        freeqty = 0.00
                    prod = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gsflag,product.c.gscode]).where(product.c.productcode == pc))
                    prodrow = prod.fetchone()
                    if int(prodrow["gsflag"]) == 7:
                        um = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid == int(prodrow["uomid"])))
                        unitrow = um.fetchone()
                        unitofMeasurement = unitrow["unitname"]
                        taxableAmount = ((float(contentsData[pc][contentsData[pc].keys()[0]])) * float(contentsData[pc].keys()[0])) - float(discount)
                    else:
                        unitofMeasurement = ""
                        taxableAmount = float(contentsData[pc].keys()[0]) - float(discount)
                    
                       
                    taxRate = 0.00
                    totalAmount = 0.00
                    taxRate =  float(invrow["tax"][pc])
                    if int(invrow["taxflag"]) == 22:
                        taxRate =  float(invrow["tax"][pc])
                        taxAmount = (taxableAmount * float(taxRate/100))
                        taxname = 'VAT'
                        totalAmount = float(taxableAmount) + (float(taxableAmount) * float(taxRate/100))
                        totalDisc = totalDisc + float(discount)
                        totalTaxableVal = totalTaxableVal + taxableAmount
                        totalTaxAmt = totalTaxAmt + taxAmount
                        invContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][contentsData[pc].keys()[0]])),"freeqty":"%.2f"% (float(freeqty)),"priceperunit":"%.2f"% (float(contentsData[pc].keys()[0])),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":"VAT","taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount))}

                    else:
                        cessRate = 0.00
                        cessAmount = 0.00
                        cessVal = 0.00
                        taxname = ""
                        if invrow["cess"] != None:
                            cessVal = float(invrow["cess"][pc])
                            cessAmount = (taxableAmount * (cessVal/100))
                            totalCessAmt = totalCessAmt + cessAmount

                        if invrow["sourcestate"] != invrow["taxstate"]:
                            taxname = "IGST"
                            taxAmount = (taxableAmount * (taxRate/100))
                            totalAmount = taxableAmount + taxAmount + cessAmount
                        else:
                            taxname = "SGST"
                            taxRate = (taxRate/2)
                            taxAmount = (taxableAmount * (taxRate/100))
                            totalAmount = taxableAmount + (taxableAmount * ((taxRate * 2)/100)) + cessAmount
  
                        totalDisc = totalDisc + float(discount)
                        totalTaxableVal = totalTaxableVal + taxableAmount
                        totalTaxAmt = totalTaxAmt + taxAmount

                        invContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"gsflag":prodrow["gsflag"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][contentsData[pc].keys()[0]])),"freeqty":"%.2f"% (float(freeqty)),"priceperunit":"%.2f"% (float(contentsData[pc].keys()[0])),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":taxname,"taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount)),"cess":"%.2f"%(float(cessAmount)),"cessrate":"%.2f"%(float(cessVal))}
                inv["totaldiscount"] = "%.2f"% (float(totalDisc))
                inv["totaltaxablevalue"] = "%.2f"% (float(totalTaxableVal))
                inv["totaltaxamt"] = "%.2f"% (float(totalTaxAmt))
                inv["totalcessamt"] = "%.2f"% (float(totalCessAmt))
                inv['taxname'] = taxname
                inv["invcontents"] = invContents

                return {"gkstatus":gkcore.enumdict["Success"],"gkresult":inv}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method='GET',request_param="type=bwa", renderer ='json')
    def getCSUPBills(self):
        """
        Purpose: gets list of unpaid bills for a given customerandsupplier or supplier.
        Takes the person's id and returns a grid containing bills.
Apart from the bills it also returns customerandsupplier or supplyer name.
        Description:
        The function will take customerandsupplier or supplier id while orgcode is  taken from token.
        The invoice table will be scanned for all the bills concerning the party.
        If the total amount is greater than amountpaid(which is 0 by default ) then the bill qualifies to be returned.
        The function will return json object with gkstatus,csName:name of the party and gkresult:grid of bills.
The bills grid calld gkresult will return a list as it's value.
        The columns will be as follows:
        Bill no., Bill date, Customer/ supplier name,total amount and outstanding.
        the outstanding is calculated as total - amountpaid.
        """
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
                unpaidBillsRecords = self.con.execute(select([invoice.c.invid,invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.custid,invoice.c.invoicetotal,invoice.c.amountpaid]).where(and_(invoice.c.custid == self.request.params["custid"],invoice.c.invoicetotal > invoice.c.amountpaid)))

                unpaidBills = unpaidBillsRecords.fetchall()
                bills = []
                for bill in unpaidBills:
                    upb = {}
                    upb["invid"] = bill["invid"]
                    upb["invoiceno"] = bill["invoiceno"]
                    upb["invoicedate"]=datetime.strftime(bill["invoicedate"],'%d-%m-%Y')
                    upb["invoicetotal"] ="%.2f"%float(bill["invoicetotal"])
                    upb["pendingamount"] = "%.2f"% (float(bill["invoicetotal"]) -  float(bill["amountpaid"]))
                    bills.append(upb)
                custNameData = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid == self.request.params["custid"]))
                custnameRecord = custNameData.fetchone()
                csName = custnameRecord["custname"]
                gkresult = {"csname":csName,"unpaidbills":bills}
                return{"gkstatus":enumdict["Success"],"gkresult":gkresult}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()


    @view_config(request_method='GET',request_param="inv=all", renderer ='json')
    def getAllinvoices(self):
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
                result = self.con.execute(select([invoice.c.invoiceno,invoice.c.invid,invoice.c.invoicedate,invoice.c.custid,invoice.c.invoicetotal,invoice.c.attachmentcount]).where(and_(invoice.c.orgcode==authDetails["orgcode"],invoice.c.icflag==9)).order_by(invoice.c.invoicedate))
                invoices = []
                for row in result:
                    customer = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==row["custid"]))
                    custname = customer.fetchone()
                    if self.request.params.has_key('type'):
                        if str(self.request.params["type"]) == 'sale' and int(custname['csflag']) == 3:
                            invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"],"custname":custname["custname"],"csflag":custname["csflag"],"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y'),"invoicetotal":"%.2f"%float(row["invoicetotal"]), "attachmentcount":row["attachmentcount"]})
                        elif str(self.request.params["type"]) == 'purchase' and int(custname['csflag']) == 19:
                            invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"],"custname":custname["custname"],"csflag":custname["csflag"],"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y'),"invoicetotal":"%.2f"%float(row["invoicetotal"]), "attachmentcount":row["attachmentcount"]})
                    else:
                        invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"],"custname":custname["custname"],"csflag":custname["csflag"],"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y'),"invoicetotal":"%.2f"%float(row["invoicetotal"]), "attachmentcount":row["attachmentcount"]})
                
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":invoices }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()


    @view_config(request_method='GET',request_param="forvoucher", renderer ='json')
    def getforvoucher(self):
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
                invsData = self.con.execute("select invid from invoice where icflag = 9 and orgcode = %d except select invid from vouchers where orgcode = %d"%(authDetails["orgcode"],authDetails["orgcode"]))
                invoices = []
                for inv in invsData:
                    filteredInvoices = self.con.execute(select([invoice.c.invoiceno,invoice.c.invoicedate,invoice.c.custid,invoice.c.invoicetotal]).where(invoice.c.invid == inv["invid"]))
                    invdataset = filteredInvoices.fetchone()
                    csdata = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invdataset["custid"]))
                    custname = csdata.fetchone()
                    invoices.append({"invoiceno":invdataset["invoiceno"], "invid":inv["invid"],"custname":custname["custname"],"csflag":custname["csflag"],"invoicedate":datetime.strftime(invdataset["invoicedate"],'%d-%m-%Y'),"invoicetotal":"%.2f"%float(invdataset["invoicetotal"])})

                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":invoices }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method='GET',request_param="cash=all", renderer ='json')
    def getAllcashmemos(self):
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
                result = self.con.execute(select([invoice.c.invoiceno,invoice.c.invid,invoice.c.invoicedate]).where(and_(invoice.c.orgcode==authDetails["orgcode"],invoice.c.icflag==3,invoice.c.inoutflag==self.request.params["inoutflag"])).order_by(invoice.c.invoicedate))
                invoices = []
                for row in result:
                    invoices.append({"invoiceno":row["invoiceno"], "invid":row["invid"],"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y')})
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":invoices }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
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
                invid = self.request.params["invid"]
                invoiceData = self.con.execute(select([invoice.c.invoiceno, invoice.c.attachment]).where(and_(invoice.c.invid == invid)))
                attachment = invoiceData.fetchone()
                return {"gkstatus":enumdict["Success"],"gkresult":attachment["attachment"],"invoiceno":attachment["invoiceno"],"userrole":urole["userrole"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method='DELETE', renderer ='json')
    def deleteinvoice(self):
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
                dataset["canceldate"]=datetime.now().date()
                result = self.con.execute(invoice.update().where(invoice.c.invid==dataset["invid"]).values(dataset))
                if dataset["icflag"]==9:
                    stockcancel = {"dcinvtnflag":90}
                else:
                    stockcancel = {"dcinvtnflag":30}
                result = self.con.execute(stock.update().where(and_(stock.c.dcinvtnid==dataset["invid"],stock.c.dcinvtnflag==dataset["icflag"])).values(stockcancel))
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET', request_param="unbilled_delnotes", renderer ='json')
    def unbilled_delnotes(self):
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
                orgcode = authDetails["orgcode"]
                dataset = self.request.json_body
                inputdate = dataset["inputdate"]
                new_inputdate = dataset["inputdate"]
                new_inputdate = datetime.strptime(new_inputdate, "%Y-%m-%d")
                dc_unbilled = []
                alldcids = self.con.execute(select([delchal.c.dcid, delchal.c.dcdate]).distinct().where(and_(delchal.c.orgcode == orgcode, delchal.c.dcdate <= new_inputdate, stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 4, delchal.c.dcid == stock.c.dcinvtnid)).order_by(delchal.c.dcdate))
                alldcids = alldcids.fetchall()
                dcResult = []
                i = 0
                while(i < len(alldcids)):
                    dcid = alldcids[i]
                    invidresult = self.con.execute(select([dcinv.c.invid]).where(and_(dcid[0] == dcinv.c.dcid, dcinv.c.orgcode == orgcode, invoice.c.orgcode == orgcode, invoice.c.invid == dcinv.c.invid, invoice.c.invoicedate <= new_inputdate)))
                    invidresult = invidresult.fetchall()
                    if len(invidresult) == 0:
                        dcprodresult = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 4, dcid[0] == stock.c.dcinvtnid)))
                        dcprodresult = dcprodresult.fetchall()
                        #This code is for rejection note
                        #even if an invoice is not prepared and rejection note prepared for whole delivery note then it should not come into unbilled delivery note.
                        allrnidres = self.con.execute(select([rejectionnote.c.rnid]).distinct().where(and_(rejectionnote.c.orgcode == orgcode, rejectionnote.c.rndate <= new_inputdate, rejectionnote.c.dcid == dcid[0])))
                        allrnidres = allrnidres.fetchall()
                        rnprodresult = []
                        #get stock respected to all rejection notes
                        for rnid in allrnidres:
                            temp = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 18, stock.c.dcinvtnid == rnid[0])))
                            temp = temp.fetchall()
                            rnprodresult.append(temp)
                        matchedproducts = []
                        remainingproducts = {}
                        totalqtyofdcprod = {}
                        for eachitem in dcprodresult:
                            totalqtyofdcprod.update({eachitem[0]:eachitem[1]})
                        for row in rnprodresult:
                            for prodc, qty in row:
                                if prodc in remainingproducts:
                                    remainingproducts[prodc] = float(remainingproducts[prodc]) + float(qty)
                                    if float(remainingproducts[prodc]) >= float(totalqtyofdcprod[prodc]):
                                        matchedproducts.append(prodc)
                                        del remainingproducts[prodc]
                                elif float(qty) >= float(totalqtyofdcprod[prodc]):
                                    matchedproducts.append(prodc)
                                else:
                                    remainingproducts.update({prodc:float(qty)})
                        if len(matchedproducts) == len(dcprodresult):
                            #Now we have got the delchals, for which invoices are also sent completely.
                            alldcids.remove(dcid)
                            i-=1
                    else:
                        #invid's will be distinct only. So no problem to explicitly applying distinct clause.
                        dcprodresult = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 4, dcid[0] == stock.c.dcinvtnid)))
                        dcprodresult = dcprodresult.fetchall()
                        #I am assuming :productcode must be distinct. So, I haven't applied distinct construct.
                        #what if dcprodresult or invprodresult is empty?
                        invprodresult = []
                        for invid in invidresult:
                            temp = self.con.execute(select([invoice.c.contents]).where(and_(invoice.c.orgcode == orgcode, invid == invoice.c.invid)))
                            temp = temp.fetchall()
                            #Below two lines are intentionally repeated. It's not a mistake.
                            temp = temp[0]
                            temp = temp[0]
                            invprodresult.append(temp)
                        #Now we have to compare the two results: dcprodresult and invprodresult
                        #I assume that the delchal must have at most only one entry for a particular product. If not, then it's a bug and needs to be rectified.
                        #But, in case of invprodresult, there can be more than one productcodes mentioned. This is because, with one delchal, there can be many invoices linked.
                        matchedproducts = []
                        remainingproducts = {}
                        totalqtyofdcprod = {}
                        for eachitem in dcprodresult:
                        #dcprodresult is a list of tuples. eachitem is one such tuple.
                            totalqtyofdcprod.update({eachitem[0]:eachitem[1]})
                            for eachinvoice in invprodresult:
                            #invprodresult is a list of dictionaries. eachinvoice is one such dictionary.
                                for eachproductcode in eachinvoice.keys():
                                    #eachitem[0] is unique. It's not repeated.
                                    dcprodcode = eachitem[0]
                                    if int(dcprodcode) == int(eachproductcode):
                                        #this means that the product in delchal matches with the product in invoice
                                        #now we will check its quantity
                                        invqty = eachinvoice[eachproductcode].values()[0]
                                        dcqty = eachitem[1]
                                        if float(dcqty) == float(invqty):#conversion of datatypes to compatible ones is very important when comparing them.
                                            #this means the quantity of current individual product is matched exactly
                                            matchedproducts.append(int(eachproductcode))
                                        elif float(dcqty) > float(invqty):
                                            #this means current invoice has not billed the whole product quantity.
                                            if dcprodcode in remainingproducts.keys():
                                                if float(dcqty) == (float(remainingproducts[dcprodcode]) + float(invqty)):
                                                    matchedproducts.append(int(eachproductcode))
                                                    #whether we use eachproductcode or dcprodcode, doesn't matter. Because, both values are the same here.
                                                    del remainingproducts[int(eachproductcode)]
                                                else:
                                                    #It must not be the case that below addition is greater than dcqty.
                                                    remainingproducts[dcprodcode] = (float(remainingproducts[dcprodcode]) + float(invqty))
                                            else:
                                                remainingproducts.update({dcprodcode:float(invqty)})
                                        else:
                                            #"dcqty < invqty" should never happen.
                                            # It could happen when multiple delivery chalans have only one invoice.
                                            pass

                        #This code is for rejection note
                        allrnidres = self.con.execute(select([rejectionnote.c.rnid]).distinct().where(and_(rejectionnote.c.orgcode == orgcode, rejectionnote.c.rndate <= new_inputdate, rejectionnote.c.dcid == dcid[0])))
                        allrnidres = allrnidres.fetchall()
                        rnprodresult = []
                        #get stock respected to all rejection notes
                        for rnid in allrnidres:
                            temp = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 18, stock.c.dcinvtnid == rnid[0])))
                            temp = temp.fetchall()
                            rnprodresult.append(temp)
                        for row in rnprodresult:
                            for prodc, qty in row:
                                if prodc in remainingproducts:
                                    remainingproducts[prodc] = float(remainingproducts[prodc]) + float(qty)
                                    if float(remainingproducts[prodc]) >= float(totalqtyofdcprod[prodc]):
                                        matchedproducts.append(prodc)
                                        del remainingproducts[prodc]

                        if len(matchedproducts) == len(dcprodresult):
                            #Now we have got the delchals, for which invoices are also sent completely.
                            alldcids.remove(dcid)
                            i-=1
                    i+=1
                    pass

                for eachdcid in alldcids:
                    singledcResult = self.con.execute(select([delchal.c.dcid, delchal.c.dcno, delchal.c.dcdate, delchal.c.dcflag, customerandsupplier.c.custname, customerandsupplier.c.csflag, delchal.c.attachmentcount]).distinct().where(and_(delchal.c.orgcode == orgcode, customerandsupplier.c.orgcode == orgcode, eachdcid[0] == delchal.c.dcid, delchal.c.custid == customerandsupplier.c.custid, stock.c.dcinvtnflag == 4, eachdcid[0] == stock.c.dcinvtnid)))
                    singledcResult = singledcResult.fetchone()
                    dcResult.append(singledcResult)

                temp_dict = {}
                srno = 1
                if dataset["type"] == "invoice":
                    for row in dcResult:
                        temp_dict = {"dcid": row["dcid"], "srno": srno, "dcno":row["dcno"], "dcdate": datetime.strftime(row["dcdate"],"%d-%m-%Y"), "dcflag": row["dcflag"], "csflag": row["csflag"], "custname": row["custname"], "attachmentcount": row["attachmentcount"]}
                        if temp_dict["dcflag"] == 19:
                            #We don't have to consider sample.
                            temp_dict["dcflag"] = "Sample"
                        elif temp_dict["dcflag"]== 6:
                            #we ignore this as well
                            temp_dict["dcflag"] = "Free Replacement"
                        if temp_dict["dcflag"] != "Sample" and temp_dict["dcflag"] !="Free Replacement":
                            dc_unbilled.append(temp_dict)
                            srno += 1
                else:
                    #type=rejection note
                    #Here even delivery type sample and free Replacement can also be rejected.
                    for row in dcResult:
                        temp_dict = {"dcid": row["dcid"], "srno": srno, "dcno":row["dcno"], "dcdate": datetime.strftime(row["dcdate"],"%d-%m-%Y"), "dcflag": row["dcflag"], "csflag": row["csflag"], "custname": row["custname"], "attachmentcount": row["attachmentcount"]}
                        dc_unbilled.append(temp_dict)
                        srno += 1
                self.con.close()
                return {"gkstatus":enumdict["Success"], "gkresult": dc_unbilled}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    '''This mehtod gives all invoices which are not fully rejected yet. It is used in rejection note, to prepare rejection note against these invoices'''
    @view_config(request_method='GET', request_param="type=nonrejected", renderer ='json')
    def nonRejected(self):
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
                invResult = self.con.execute(select([invoice.c.invid,invoice.c.invoicedate,invoice.c.contents,invoice.c.invoiceno,invoice.c.custid,invoice.c.taxflag,invoice.c.sourcestate,invoice.c.taxstate]).where(and_(invoice.c.orgcode == authDetails["orgcode"], invoice.c.icflag == 9)))
                allinv = invResult.fetchall()
                allinvids = []
                for invrow in allinv:
                    #keep an empty dictionary for rejectable products.
                    rejContents = {}
                    rejectedResult =self.con.execute(select ([rejectionnote.c.rnid,rejectionnote.c.rejprods]).where(and_(rejectionnote.c.orgcode == authDetails["orgcode"],rejectionnote.c.invid == invrow["invid"])))
                    rejectedNotes = rejectedResult.fetchall()
                    gscounter = 0
                    for content in invrow["contents"].keys():
                        qty = float(invrow["contents"][content].values()[0])
                        # for goods quantity will not be 0 anytime
                        if qty > 0:
                            gscounter = gscounter + 1
                            # check whether this product is rejected before.
                            #if there are no rejections then just add the quantity directly to the rejContents.
                            if rejectedResult.rowcount == 0:
                                rejContents[content] = qty
                            else:
                                
                                #Now query each note to see if this product is partially or fully rejected.

                                for rejrow in rejectedNotes:
                                    rejdict = rejrow["rejprods"]
                                    if rejdict.has_key(content):
                                        qty = qty - float(rejrow["rejprods"][content].values()[0])
                                        if qty > 0:
                                            rejContents[content] =  qty
                                        else:
                                            if content in rejContents:
                                                rejContents.pop(content)
                    if gscounter > 0 and len(rejContents) > 0:
                        custandsup = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.state, customerandsupplier.c.custaddr, customerandsupplier.c.custtan,customerandsupplier.c.gstin, customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invrow["custid"]))
                        custData = custandsup.fetchone()
                        custSupDetails = {"custname":custData["custname"],"custaddr":custData["custaddr"],"csflag":custData["csflag"]}

                        if int(invrow["taxflag"]) == 22:
                            if custData["custtan"] != None:
                                custSupDetails["custtin"] = custData["custtan"]
                                custSupDetails["custstate"] = custData["state"]
                        else:
                            if invrow["sourcestate"] != None:
                                sourceStateCode = getStateCode(invrow["sourcestate"],self.con)["statecode"]
                                custSupDetails["custstate"] = invrow["sourcestate"]
                            if invrow["taxstate"] != None:
                                taxStateCode =  getStateCode(invrow["taxstate"],self.con)["statecode"]
                                custSupDetails["custstate"] = invrow["taxstate"]
                            if custData["gstin"] != None:
                                if int(custData["csflag"]) == 3 :
                                    try:
                                        custSupDetails["custgstin"] = custData["gstin"][str(taxStateCode)]
                                        
                                    except:
                                        custSupDetails["custgstin"] = None
                                        custSupDetails["custstate"] = None
                                else:
                                    try:
                                        custSupDetails["custgstin"] = custData["gstin"][str(sourceStateCode)]
                                        
                                    except:
                                        custSupDetails["custgstin"] = None
                                        custSupDetails["custstate"] = None
                        allinvids.append({"invid":invrow["invid"],"invoiceno":invrow["invoiceno"],"invoicedate":datetime.strftime(invrow["invoicedate"],'%d-%m-%Y'),"rejcontent":rejContents,"custsupdetail": custSupDetails})
                                
                self.con.close()
                return {"gkstatus":enumdict["Success"], "gkresult":allinvids}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    """
        This function gives details of single rejection note from it's invid.
        The details include related customer or supplier and sales or purchase invoice details as well as calculation of amount.
        It also calculates total amount, taxable amount, new taxable amount with all the taxes.
        The function returns a dictionary with the details.
        'item' dictionary contains details product and tax calculation values.
        'delchal' dictionary contains 'customerandsupplier details.
        'invDetails' dictionary contains request invoice details.
    """
    @view_config(request_method='GET',request_param='type=nonrejectedinvprods', renderer='json')
    def nonRejectedInvProds(self):
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
                dataset = self.request.json_body
                invid = dataset["invid"]
                invprodresult = []
                orgcode = authDetails["orgcode"]
                userId = authDetails["userid"]
                userdetails = self.con.execute(select([users.c.userid, users.c.username,users.c.userrole]).where(users.c.userid == userId))
                userDetails = userdetails.fetchone()
                temp = self.con.execute(select([invoice]).where(and_(invoice.c.orgcode == orgcode, invoice.c.invid == invid)))
                invData = temp.fetchone()
                invprodresult.append(invData["contents"])
                qtyc =invData["contents"]
                discounts = invData["discount"]
                invDetails={"invno":invData["invoiceno"], "invdate":datetime.strftime(invData["invoicedate"],"%d-%m-%Y"),"taxflag":invData["taxflag"],"tax":invData["tax"],"invoicetotal":float(invData["invoicetotal"]),"orgstategstin":invData["orgstategstin"],"inoutflag":invData["inoutflag"]}
                if invData["inoutflag"] == 15:
                    invDetails["issuername"] = invData["issuername"]
                    invDetails["designation"] = invData["designation"]
                else:
                    invDetails["issuername"] = userDetails["username"]
                    invDetails["designation"] = userDetails["userrole"]
                if invData["sourcestate"] != None or invData["taxstate"] !=None:
                    invDetails["sourcestate"] = invData["sourcestate"]
                    invDetails["taxstate"]=invData["taxstate"]
                    taxStateCode=getStateCode(invData["taxstate"],self.con)["statecode"]
                    invDetails["taxstatecode"]=taxStateCode
                if invData["address"]!="":
                    invDetails["address"]=invData["address"]

                totalDisc = 0.00
                totalTaxableVal = 0.00
                totalTaxAmt = 0.00
                totalCessAmt = 0.00
 
                items = {}
                for eachitem in qtyc.keys():
                    productdata = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gsflag,product.c.gscode]).where(and_(product.c.productcode==int(eachitem), product.c.gsflag==7)))
                    productdesc = productdata.fetchone()
                    if productdesc == None :
                        continue
                    uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productdesc["uomid"]))
                    unitnamrrow = uomresult.fetchone()
                    uom = unitnamrrow["unitname"]
                    freeqtys = invData["freeqty"]
                    if discounts != None:
                        discount = discounts[eachitem]
                    else:
                        discount = 0.00
                    if freeqtys != None:
                        freeqty = freeqtys[eachitem]
                    else:
                        freeqty = 0.00
                    items[int(eachitem)]={}
                    result = "%.2f"%float(qtyc[eachitem].values()[0])
                    ppu = qtyc[eachitem].keys()[0]                   
                    items[int(eachitem)] = {"qty":"%.2f"%float(result)}
                    #Checking Rejection Note Qty.
                    allrnidres = self.con.execute(select([rejectionnote.c.rnid]).distinct().where(and_(rejectionnote.c.orgcode == orgcode, rejectionnote.c.invid == invid)))
                    allrnidres = allrnidres.fetchall()
                    rnprodresult = []
                    #get stock respected to all rejection notes
                    for rnid in allrnidres:
                        #checking in rnid into stock table 
                        temp = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == orgcode, stock.c.dcinvtnflag == 18, stock.c.dcinvtnid == rnid[0])))
                        tempall = temp.fetchall()
                        rnprodresult.append(tempall)
                    for rnproddata in rnprodresult:
                        for row in rnproddata:
                            if int(row["productcode"]) == int(eachitem):
                                changedqty = float(items[int(row["productcode"])]["qty"]) - float(row["qty"])
                        items[int(eachitem)]={"qty":"%.2f"%float(changedqty)}
                    taxableAmount = (float(ppu) * float(items[int(eachitem)]["qty"])) - float(discount)
                    taxRate = 0.00
                    totalAmount = 0.00
                    taxRate =  float(invData["tax"][eachitem])
                    if int(invData["taxflag"]) == 22:
                        taxRate =  float(invData["tax"][eachitem])
                        taxAmount = (taxableAmount * float(taxRate/100))
                        taxname = 'VAT'
                        totalAmount = float(taxableAmount) + (float(taxableAmount) * float(taxRate/100))
                        totalDisc = totalDisc + float(discount)
                        totalTaxableVal = totalTaxableVal + taxableAmount
                        totalTaxAmt = totalTaxAmt + taxAmount
                        items[int(eachitem)] = {"productdesc":productdesc["productdesc"],"gscode":productdesc["gscode"],"qty":float(items[int(eachitem)]["qty"]),"feeqty":"%.2f"% (float(freeqty)),"priceperunit":"%.2f"% (float(qtyc[eachitem].keys()[0])),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":"VAT","taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount)),"uom":uom}
                    else:
                        cessRate = 0.00
                        cessAmount = 0.00
                        cessVal = 0.00
                        taxname = ""
                        if invData["cess"] != None:
                            cessVal = float(invData["cess"][eachitem])
                            cessAmount = (taxableAmount * (cessVal/100))
                            totalCessAmt = totalCessAmt + cessAmount

                        if invData["sourcestate"] != invData["taxstate"]:
                            taxname = "IGST"
                            taxAmount = (taxableAmount * (taxRate/100))
                            totalAmount = taxableAmount + taxAmount + cessAmount
                        else:
                            taxname = "SGST"
                            taxRate = (taxRate/2)
                            taxAmount = (taxableAmount * (taxRate/100))
                            totalAmount = taxableAmount + (taxableAmount * ((taxRate * 2)/100)) + cessAmount
  
                        totalDisc = totalDisc + float(discount)
                        totalTaxableVal = totalTaxableVal + taxableAmount
                        totalTaxAmt = totalTaxAmt + taxAmount

                        items[int(eachitem)]= {"productdesc":productdesc["productdesc"],"gscode":productdesc["gscode"],"qty":float(items[int(eachitem)]["qty"]),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":taxname,"taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount)),"priceperunit":"%.2f"% (float(qtyc[eachitem].keys()[0])),"cess":"%.2f"%(float(cessAmount)),"cessrate":"%.2f"%(float(cessVal)),"uom":uom}

                invDetails["totaldiscount"]="%.2f"% (float(totalDisc))
                invDetails["totaltaxablevalue"]="%.2f"% (float(totalTaxableVal))
                invDetails["totaltaxamt"]="%.2f"% (float(totalTaxAmt))
                invDetails["totalcessamt"]="%.2f"% (float(totalCessAmt))
                for productcode in items.keys():
                    if items[productcode]["qty"] == 0:
                        del items[productcode]
                temp = self.con.execute(select([dcinv.c.dcid]).where(and_(dcinv.c.orgcode == orgcode, dcinv.c.invid == invid)))
                temp = temp.fetchone()
                dcdetails = {}
                custdata = self.con.execute(select([customerandsupplier]).where(customerandsupplier.c.custid.in_(select([invoice.c.custid]).where(invoice.c.invid==invid)))) 
                custname = custdata.fetchone()
                custsupstatecodedata = getStateCode(custname["state"],self.con)["statecode"]
                dcdetails = {"custname":custname["custname"], "custaddr": custname["custaddr"], "custtin":custname["custtan"],"custsupstatecodedata":custsupstatecodedata,"taxflag":invData["taxflag"]}
                if int(invData["taxflag"]) == 22:
                    if custname["custtan"] != None:
                        dcdetails["custtin"] = custname["custtan"]
                        dcdetails["custstate"] = custname["state"]
                else:
                    if invData["sourcestate"] != None:
                        sourceStateCode = getStateCode(invData["sourcestate"],self.con)["statecode"]
                        dcdetails["custstate"] = invData["sourcestate"]
                    if invData["taxstate"] != None:
                        taxStateCode =  getStateCode(invData["taxstate"],self.con)["statecode"]
                        dcdetails["custstate"] = invData["taxstate"]
                    if custname["gstin"] != None:
                        if int(custname["csflag"]) == 3 :
                            try:
                                dcdetails["custgstin"] = custname["gstin"][str(taxStateCode)]

                            except:
                                dcdetails["custgstin"] = None
                                dcdetails["custstate"] = None
                        else:
                            try:
                                dcdetails["custgstin"] = custname["gstin"][str(sourceStateCode)]

                            except:
                                dcdetails["custgstin"] = None
                                dcdetails["custstate"] = None
                if temp:
                    result = self.con.execute(select([delchal]).where(delchal.c.dcid==temp[0]))
                    delchaldata = result.fetchone()
                    stockdata = self.con.execute(select([stock.c.goid]).where(and_(stock.c.dcinvtnflag==4,stock.c.dcinvtnid==temp[0])))
                    stockdata = stockdata.fetchone()
                    dcdetails = {"dcid":temp[0], "custname":custname["custname"], "custaddr": custname["custaddr"], "custtin":custname["custtan"], "goid":"", "goname":"", "gostate":"", "dcflag":delchaldata["dcflag"]}
                    godata = self.con.execute(select([godown.c.goname,godown.c.state, godown.c.goaddr]).where(godown.c.goid==stockdata[0]))
                    goname = godata.fetchone()
                    dcdetails["goid"] = stockdata[0]
                    dcdetails["goname"] = goname["goname"]
                    dcdetails["gostate"] = goname["state"]
                    dcdetails["goaddr"] = goname["goaddr"]
                return {"gkstatus":enumdict["Success"], "gkresult": items, "delchal": dcdetails,"invDetails":invDetails}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
                
    '''This method gives list of invoices. with all details of invoice.
    This method will be used to see report of list of invoices.
    Input parameters are: flag- 0=all invoices, 1=sales invoices, 2=purchase invoices
                          fromdate and todate this is time period to see all invoices.'''
    @view_config(request_method='GET',request_param="type=list", renderer ='json')
    def getListofInvoices(self):
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
                #fetch all invoices
                result = self.con.execute(select([invoice]).where(and_(invoice.c.orgcode==authDetails["orgcode"], invoice.c.icflag == 9, invoice.c.invoicedate <= self.request.params["todate"], invoice.c.invoicedate >= self.request.params["fromdate"])).order_by(invoice.c.invoicedate))
                invoices = []
                srno = 1
                #for each invoice
                for row in result:
                    if row["sourcestate"] != None:
                        sourceStateCode = getStateCode(row["sourcestate"],self.con)["statecode"]
                    if row["taxstate"] != None:
                        destinationStateCode = getStateCode(row["taxstate"],self.con)["statecode"]
                    dcno = ""
                    dcdate = ""
                    godowns = ""
                    dcresult = self.con.execute(select([dcinv.c.dcid]).where(and_(dcinv.c.orgcode==authDetails["orgcode"], dcinv.c.invid == row["invid"])))
                    dcresult = dcresult.fetchall()
                    #Assuming there are multiple delivery challans for a single invoice.
                    i = 1
                    #fetch all delivery challans for an invoice.
                    for dc in dcresult:
                        godownres = self.con.execute("select goname, goaddr from godown where goid = (select distinct goid from stock where dcinvtnflag=4 and dcinvtnid=%d)"%int(dc["dcid"]))
                        godownresult = godownres.fetchone()
                        if godownresult != None:
                            godownname = godownresult["goname"]
                            godownaddrs = godownresult["goaddr"]
                            godowns = godowns + godownname + "("+ godownaddrs + ")"
                        else:
                            godownname = ""
                            godownaddrs = ""
                            godowns = ""
                        delchalres = self.con.execute(select([delchal.c.dcno, delchal.c.dcdate]).where(and_(delchal.c.orgcode==authDetails["orgcode"], delchal.c.dcid == dc["dcid"])))
                        delchalres = delchalres.fetchone()
                        if i == len(dcresult):
                            dcno =  dcno + delchalres["dcno"]
                            dcdate =  dcdate + str(datetime.strftime(delchalres["dcdate"],'%d-%m-%Y'))
                            
                        else:
                            dcno =  dcno + delchalres["dcno"] + ", "
                            dcdate =  dcdate + str(datetime.strftime(delchalres["dcdate"],'%d-%m-%Y')) + ", "
                            
                        i += 1
                    taxamt = 0.00
                    #calculate tax amount of an invoice.
                    for productservice in row["contents"].iterkeys():
                        try:
                            taxrate = "%.2f"%float(row["tax"][productservice])
                            cessrate = 0.00
                            if row["cess"].has_key(productservice):
                                cessrate = "%.2f"%float(row["cess"][productservice])
                            discount =0.00
                            #Fetching GSFlag of product.
                            psdetails = self.con.execute(select([product.c.gsflag]).where(product.c.productcode == productservice))
                            gsflag = psdetails.fetchone()["gsflag"]
                            #Fetching discount and price for each product.
                            #Taxabe amount is also found out considering whether the item is a product/service
                            for productprice in row["contents"][productservice].iterkeys():
                                ppu = productprice
                                if row["discount"].has_key(productservice):
                                    discount = float(row["discount"][productservice])
                                qty = float(row["contents"][productservice][productprice])
                                #Calculating taxable amount(variable taxablevalue)
                                if int(gsflag) == 7:
                                    taxablevalue = (float("%.2f"%float(ppu)) * float("%.2f"%float(qty))) - float("%.2f"%float(discount))
                                else:
                                    taxablevalue = float("%.2f"%float(ppu)) - float("%.2f"%float(discount))
                                #Calculating tax amount.
                                taxamt = taxamt + float("%.2f"%((taxablevalue * float(taxrate))/float(100))) + float("%.2f"%((taxablevalue * float(cessrate))/float(100)))
                        except:
                            pass
                    netamt = float(row["invoicetotal"]) - taxamt
                    cresult = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag, customerandsupplier.c.custtan, customerandsupplier.c.gstin]).where(customerandsupplier.c.custid==row["custid"]))
                    customerdetails = cresult.fetchone()
                    #TIN/GSTIN of customer/supplier is found out.
                    if int(row["taxflag"]) == 7:
                        if int(customerdetails["csflag"]) == 3 :
                           try:
                               custtin = customerdetails["gstin"][str(destinationStateCode)]
                           except:
                               custtin = None
                        else:
                            try:
                                custtin = customerdetails["gstin"][str(sourceStateCode)]
                            except:
                                custtin = None
                    else:
                        try:
                            custtin  = customerdetails["custtan"]
                        except:
                            custtin = None
                                

                    #flag=0, all invoices.
                    if self.request.params["flag"] == "0":
                        invoices.append({"srno": srno, "invoiceno":row["invoiceno"], "invid":row["invid"],"dcno":dcno, "dcdate":dcdate, "netamt": "%.2f"%netamt, "taxamt":"%.2f"%taxamt, "godown":godowns, "custname":customerdetails["custname"],"csflag":customerdetails["csflag"],"custtin":custtin,"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y'),"grossamt":"%.2f"%float(row["invoicetotal"])})
                        srno += 1
                    #flag=1, sales invoices
                    elif self.request.params["flag"] == "1" and customerdetails["csflag"] == 3:
                        invoices.append({"srno": srno, "invoiceno":row["invoiceno"], "invid":row["invid"],"dcno":dcno, "dcdate":dcdate, "netamt": "%.2f"%netamt, "taxamt":"%.2f"%taxamt, "godown":godowns, "custname":customerdetails["custname"],"csflag":customerdetails["csflag"],"custtin":custtin,"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y'),"grossamt":"%.2f"%float(row["invoicetotal"])})
                        srno += 1
                    #flag=2, purchase invoices.
                    elif self.request.params["flag"] == "2" and customerdetails["csflag"] == 19:
                        invoices.append({"srno": srno, "invoiceno":row["invoiceno"], "invid":row["invid"],"dcno":dcno, "dcdate":dcdate, "netamt": "%.2f"%netamt, "taxamt":"%.2f"%taxamt, "godown":godowns, "custname":customerdetails["custname"],"csflag":customerdetails["csflag"],"custtin":custtin,"invoicedate":datetime.strftime(row["invoicedate"],'%d-%m-%Y'),"grossamt":"%.2f"%float(row["invoicetotal"])})
                        srno += 1
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":invoices }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()


    def getDefaultAcc(self,queryParams,orgcode):
        #try:
            """
            Purpose: Returns default accounts.
            Invoice type = 19:sales , 16:purchase 
            Payment Mode  15 = on credit , 3 = Cash , 2 = Bank
            Tax Type = GST :7(As default) or 22:VAT
            taxtype as a keys for dictionary where percentage is key and_ amount is value.
            csname will have customer or supplier name.
            maflag = multiple account flag in organisations table
            
            So the structure of queryParams = {"invtype":19 or 16 ,"csname":customer/supplier name ,"pmtmode":2 or 3 or 15,"taxType":7 or 22,"gstname":"CGST / IGST","cessname":"cess","maflag":True /False,"products":{"productname":Taxable value,"productname1":Taxabe value,.........},"destination":taxstate,"totaltaxablevalue":value,"totalAmount":invoicetotal,"invoicedate":invDate,"invid":id,"invoiceno":invno,"taxpayement":VATtax}
            """
            self.con = eng.connect()
            print "Aya mein idhar"
            print queryParams
            voucherDict = {}
            crs ={}
            drs = {}
            Narration = ""
            totalTaxableVal = float(queryParams["totaltaxablevalue"])
            amountPaid = float(queryParams["totalAmount"])
            #first check the invoice type sale or purchase.
            if int(queryParams["invtype"]) == 15:
                # if multiple account is 1 , then search for all the sale accounts of products in invoices 
                if int(queryParams["maflag"]) == 1:
                    prodData = queryParams["products"]
                    for prod in prodData:
                        proN = str(prod)+ " Sale" 
                        prodAccount = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname == proN, accounts.c.orgcode == orgcode)))
                        crs[prodAccount["accountcode"]] = prodData[prod]
                else:
                    # if multiple acc is 0 , then select default sale account
                    salesAccount = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.defaultflag == 19, accounts.c.orgcode == orgcode)))
                    salesAcc = salesAccount.fetchone() 
                    crs[salesAcc["accountcode"]] = totalTaxableVal
                if int(queryParams["pmtmode"]) == 2:
                    bankAccount = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.defaultflag == 2, accounts.c.orgcode == orgcode)))
                    bankRow = bankAccount.fetchone()
                    drs[bankRow["accountcode"]] = "%.2f"%float(amountPaid)
                    Narration = "Sold goods worth rupees "+ "%.2f"%float(totalAmount) +" to "+ str(queryParams["csname"])+" by cheque"+" ref invoice no. "+str(queryParams["invoiceno"])
                if int(queryParams["pmtmode"]) == 3:
                    cashAccount = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.defaultflag == 3, accounts.c.orgcode == orgcode)))
                    cashRow = cashAccount.fetchone()
                    drs[cashRow["accountcode"]] = "%.2f"%float(amountPaid)
                    Narration = "Sold goods worth rupees "+ "%.2f"%float(totalAmount) +" to "+ str(queryParams["csname"])+" by cash"+" ref invoice no. "+str(queryParams["invoiceno"])
                if int(queryParams["pmtmode"]) == 15:
                    custAccount = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname ==queryParams["csname"] , accounts.c.orgcode == orgcode)))
                    cust = custAccount.fetchone()
                    drs[cust["accountcode"]] = "%.2f"%float(amountPaid)
                    Narration = "Sold goods worth rupees "+ "%.2f"%float(totalAmount) +" to "+ str(queryParams["csname"])+" on credit \n"+" ref invoice no. "+str(queryParams["invoiceno"])
                # WHEN TAX is gst , have to check whether cgst and igst  
                if int(queryParams["taxType"]) == 7:
                    abb = self.con.execute(select([state.c.abbreviation]).where(state.c.statename == queryParams["destinationstate"]))
                    if 'sgst' in queryParams:
                        for tr in tax.values():
                            taxrate = float(tr/2)
                            taxPayment =  totalTaxableVal  * (taxrate/100)
                            taxNameSGST = "SGSTOUT"+"_"+str(abb["abbreviation"])+"@"+str(taxrate)+"%"
                            taxNameCGST = "CGSTOUT"+"_"+str(abb["abbreviation"])+"@"+str(taxrate)+"%"
                            taxACC = self.con.execute("select accountcode from accounts where orgcode = %d accountname in (%s,%s);"%(orgcode,taxNameSGST,taxNameSGST))
                            taxAcc = taxACC.fetchall()
                            crs[taxAcc["accountcode"]] = "%.2f"%float(taxPayment)
                            
                    if 'igst' in queryParams:
                        for tr in tax.values():
                            taxrate = float(tr)
                            taxPayment =  totalTaxableVal  * (taxrate/100)
                            taxNameIGST = "IGSTOUT"+"_"+str(abb["abbreviation"])+"@"+str(taxrate)+"%"
                            taxAcc = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname == taxNameIGST, accounts.c.orgcode == orgcode)))
                            taxAccount = taxAcc.fetchone()
                            crs[taxAccount["accountcode"]] = "%.2f"%float(taxPayment)
                            
                if int(queryParams["taxType"]) == 22:
                    taxAcc = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname== "VAT_OUT",accounts.c.orgcode == orgcode)))
                    taxRow = taxAcc.fetchone()
                    crs[taxRow["accountcode"]] = "%.2f"%float(taxPayment)

                voucherDict = {"drs":drs,"crs":crs,"voucherdate":queryParams["invoicedate"],"narration":Narration,"vouchertype":"sales","invid":queryParams["invid"]}

                return{"vch":voucherDict}
            """ Purchase"""
            if int(queryParams["invtype"]) == 9:
                # if multiple account is 1 , then search for all the sale accounts of products in invoices 
                if int(queryParams["maflag"]) == 1:
                    prodData = queryParams["products"]
                    for prod in prodData:
                        proN = str(prod)+ " Purchase" 
                        prodAcc = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname == proN, accounts.c.orgcode == orgcode)))
                        prodAccount = prodAcc.fetchone()
                        drs[prodAccount["accountcode"]] = prodData[prod]
                else:
                    # if multiple acc is 0 , then select default sale account
                    salesAccount = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.defaultflag == 16, accounts.c.orgcode == orgcode)))
                    saleAcc = salesAccount.fetchone()
                    drs[saleAcc["accountcode"]] = totalTaxableVal
                if int(queryParams["pmtmode"]) == 2:
                    bankAccount = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.defaultflag == 2, accounts.c.orgcode == orgcode)))
                    bankRow = bankAccount.fetchone()
                    crs[bankRow["accountcode"]] = "%.2f"%float(amountPaid)
                    Narration = "Purchased goods worth rupees "+ "%.2f"%float(queryParams["totalAmount"]) +" from "+ str(queryParams["csname"])+" by cheque \n"+ "ref invoice no. "+str(queryParams["invoiceno"])
                if int(queryParams["pmtmode"]) == 3:
                    cashAccount = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.defaultflag == 3, accounts.c.orgcode == orgcode)))
                    cashRow = cashAccount.fetchone()
                    crs[cashRow["accountcode"]] = "%.2f"%float(amountPaid)
                    Narration = "Purchased goods worth rupees "+ "%.2f"%float(queryParams["totalAmount"]) +" from "+ str(queryParams["csname"])+" by cash "+ "ref invoice no. "+str(queryParams["invoiceno"])
                if int(queryParams["pmtmode"]) == 15:
                    custAcc = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname ==queryParams["csname"] , accounts.c.orgcode == orgcode)))
                    custAccount = custAcc.fetchone() 
                    crs[custAccount["accountcode"]] = "%.2f"%float(amountPaid)
                    Narration = "Purchased goods worth rupees "+ "%.2f"%float(queryParams["totalAmount"]) +" from "+ str(queryParams["csname"])+" on credit "+ "ref invoice no. "+str(queryParams["invoiceno"])
                # WHEN TAX is gst , have to check whether cgst and igst  
                if int(queryParams["taxType"]) == 7:
                    abv = self.con.execute(select([state.c.abbreviation]).where(state.c.statename == queryParams["destinationstate"]))
                    abb = abv.fetchone()
                    if 'gstname' in queryParams:
                        taxName = queryParams["gstname"]
                        Taxes = queryParams["taxes"]
                        if taxName == "CGST":
                            for tr in Taxes.values():
                                taxrate = float(tr/2)
                                taxPayment =  totalTaxableVal  * (taxrate/100)
                                taxNameSGST = "SGSTIN_"+str(abb["abbreviation"])+"@"+str(int(taxrate))+"%"
                                taxNameCGST = "CGSTIN_"+str(abb["abbreviation"])+"@"+str(int(taxrate))+"%"
                                taxACC = self.con.execute("select accountcode from accounts where orgcode = %d accountname in (%s,%s);"%(orgcode,taxNameSGST,taxNameSGST))
                                taxAcc = taxACC.fetchall()
                                for t in taxAcc:
                                    drs[t["accountcode"]] = "%.2f"%float(taxPayment)
                            
                        if taxName == "IGST":
                            for tr in Taxes.values():
                                taxrate = float(tr)
                                taxPayment =  totalTaxableVal  * (taxrate/100)
                                taxNameIGST = "IGSTIN_"+str(abb["abbreviation"])+"@"+str(int(taxrate))+"%"
                                print taxNameIGST
                                taxAc = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname == taxNameIGST, accounts.c.orgcode == orgcode)))
                                taxAcc =taxAc.fetchone()
                                drs[taxAcc["accountcode"]] = "%.2f"%float(taxPayment)
                    
                            
                if int(queryParams["taxType"]) == 22:
                    taxAcc = self.con.execute(select([accounts.c.accountcode]).where(and_(accounts.c.accountname== "VAT_IN",accounts.c.orgcode == orgcode)))
                    taxRow = taxAcc.fetchone()
                    drs[taxRow["accountcode"]] = "%.2f"%float(taxPayment)
                
                voucherDict = {"drs":drs,"crs":crs,"voucherdate":queryParams["invoicedate"],"narration":Narration,"vouchertype":"purchase","invid":queryParams["invid"]}

                print voucherDict

                return{"vch":voucherDict}

        #except:
        #    return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
        #finally:
        #    self.con.close()
