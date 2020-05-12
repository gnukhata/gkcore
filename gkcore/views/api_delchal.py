
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
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"Reshma Bhatawade" <reshma_b@riseup.net>
"Sanket Kolnoorkar" <sanketf123@gmail.com>
"Rupali Badgujar" <rupalibadgujar1234@gmail.com>

"""

from gkcore import eng, enumdict
from gkcore.models.gkdb import delchal, stock, customerandsupplier, godown, product, unitofmeasurement, dcinv,goprod, rejectionnote, delchalbin,invoice,log
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from datetime import datetime,date
import jwt
import gkcore
from gkcore.views.api_login import authCheck
from gkcore.views.api_user import getUserRole
from gkcore.views.api_godown import getusergodowns
from gkcore.views.api_invoice import getStateCode

@view_defaults(route_name='delchal')
class api_delchal(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection

    """
create method for delchal resource.
    stock table is also updated after delchal entry is made.
        -delchal id goes in dcinvtnid column of stock table.
        -dcinvtnflag column will be set to 4 for delivery challan entry.
    If stock table insert fails then the delchal entry will be deleted.
    It's return also 'dcid' to front end.
    """
    #added delchal dataset and stockdata dataset in post method.
    @view_config(request_method='POST',renderer='json')
    def adddelchal(self):
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
                delchaldata = dataset["delchaldata"]
                stockdata = dataset["stockdata"]
                freeqty= delchaldata["freeqty"]
                inoutflag= stockdata["inout"]
                items = delchaldata["contents"]
                delchaldata["orgcode"] = authDetails["orgcode"]
                stockdata["orgcode"] = authDetails["orgcode"]
                if delchaldata["dcflag"]==19:
                    delchaldata["issuerid"] = authDetails["userid"]
                result = self.con.execute(delchal.insert(),[delchaldata])
                if result.rowcount==1:
                    dciddata = self.con.execute(select([delchal.c.dcid,delchal.c.dcdate]).where(and_(delchal.c.orgcode==authDetails["orgcode"],delchal.c.dcno==delchaldata["dcno"],delchal.c.custid==delchaldata["custid"])))
                    dcidrow = dciddata.fetchone()
                    stockdata["dcinvtnid"] = dcidrow["dcid"]
                    stockdata["dcinvtnflag"] = 4
                    stockdata["stockdate"] = dcidrow["dcdate"]
                    try:
                        for key in list(items.keys()):
                            stockdata["productcode"] = key
                            stockdata["qty"] = float(list(items[key].values())[0])+float(freeqty[key])
                            result = self.con.execute(stock.insert(),[stockdata])
                            if "goid" in stockdata:
                                resultgoprod = self.con.execute(select([goprod]).where(and_(goprod.c.goid == stockdata["goid"], goprod.c.productcode==key)))
                                if resultgoprod.rowcount == 0:
                                    result = self.con.execute(goprod.insert(),[{"goid":stockdata["goid"],"productcode": key,"goopeningstock":0.00, "orgcode":authDetails["orgcode"]}])
                        return {"gkstatus":enumdict["Success"],"gkresult":dcidrow["dcid"]}
                    except:
                        result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==dcidrow["dcid"],stock.c.dcinvtnflag==4)))
                        result = self.con.execute(delchal.delete().where(delchal.c.dcid==dcidrow["dcid"]))
                        return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
                    return {"gkstatus":enumdict["Success"]}
                else:
                    return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='PUT', renderer='json')
    def editdelchal(self):
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
                delchaldata = dataset["delchaldata"]
                stockdata = dataset["stockdata"]
                delchaldata["orgcode"] = authDetails["orgcode"]
                stockdata["orgcode"] = authDetails["orgcode"]
                stockdata["dcinvtnid"] = delchaldata["dcid"]
                stockdata["stockdate"] = dcidrow["dcdate"]
                stockdata["dcinvtnflag"] = 4
                result = self.con.execute(delchal.update().where(delchal.c.dcid==delchaldata["dcid"]).values(delchaldata))
                if result.rowcount==1:
                    result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==delchaldata["dcid"],stock.c.dcinvtnflag==4)))
                    items = stockdata.pop("items")
                    for key in list(items.keys()):
                        stockdata["productcode"] = key
                        stockdata["qty"] = items[key]
                        result = self.con.execute(stock.insert(),[stockdata])
                    return {"gkstatus":enumdict["Success"]}
                else:
                    return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET',request_param="delchal=all", renderer ='json')
    def getAlldelchal(self):
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
                '''
                given below is the condition to check the values is delivery in,out or all.
                if inoutflag is there then it will perform the following if condition for delivery in or out. otherwise it will perform else condition
                '''
                if "inoutflag" in self.request.params:
                    result = self.con.execute(select([delchal.c.dcid,delchal.c.dcno,delchal.c.custid,delchal.c.dcdate, delchal.c.noofpackages, delchal.c.modeoftransport, delchal.c.attachmentcount]).where(and_(delchal.c.inoutflag==int(self.request.params["inoutflag"]),delchal.c.orgcode==authDetails["orgcode"])))
                else:
                    result = self.con.execute(select([delchal.c.dcid,delchal.c.dcno,delchal.c.custid,delchal.c.dcdate, delchal.c.noofpackages, delchal.c.modeoftransport, delchal.c.attachmentcount]).where(delchal.c.orgcode==authDetails["orgcode"]).order_by(delchal.c.dcno))
                 
                '''
                An empty list is created. Details of each delivery note and customer/supplier associated with it is stored in it.
                Loop is used to go through the result, fetch customer/supplier data and append them to the list.
                Each entry in the list is in the form of a dictionary. 
                '''
                delchals = []
                '''
                A list of all godowns assigned to a user is retreived from API for godowns using the method usergodowmns.
                If user is not a godown keeper this list will be empty.
                If user has godowns assigned, only those delivery notes for moving goods into those godowns are appended into the above list.
                '''
                usergodowmns = getusergodowns(authDetails["userid"])["gkresult"]
                if usergodowmns:
                    godowns = []
                    for godown in usergodowmns:
                        godowns.append(godown["goid"])
                    for row in result:
                        delchalgodown = self.con.execute(select([stock.c.goid]).where(and_(stock.c.dcinvtnid == row["dcid"], stock.c.dcinvtnflag == 4)))
                        delchalgodata = delchalgodown.fetchone()
                        delchalgoid = delchalgodata["goid"]
                        if delchalgoid in godowns:
                            custdata = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==row["custid"]))
                            custrow = custdata.fetchone()
                            delchals.append({"dcid":row["dcid"],"dcno":row["dcno"],"custname":custrow["custname"],"csflag":custrow["csflag"],"dcdate":datetime.strftime(row["dcdate"],'%d-%m-%Y'), "attachmentcount":row["attachmentcount"]})
                else:
                    for row in result:
                        custdata = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==row["custid"]))
                        custrow = custdata.fetchone()
                        delchals.append({"dcid":row["dcid"],"dcno":row["dcno"],"custname":custrow["custname"],"csflag":custrow["csflag"],"dcdate":datetime.strftime(row["dcdate"],'%d-%m-%Y'), "attachmentcount":row["attachmentcount"]})
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":delchals }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
                    
    
    @view_config(request_method='GET',request_param="delchal=single", renderer ='json')
    def getdelchal(self):
        """
    This function returns the single delivery challan data to frontend depends on 'dcid;.
    if for given dcid 'contents' field not available then 'stockdata' will return, else 'delchalContents' will return.
    we also return the 'delchalflag' for 'Old' and 'new' deliverychallan. for 'Old deliverychallan' delchalflag is '15',
    and for 'New deliverychallan' delchalflag is '14' set.
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
                result = self.con.execute(select([delchal]).where(delchal.c.dcid==self.request.params["dcid"]))
                delchaldata = result.fetchone()
                items = {}
                if delchaldata["cancelflag"]==1:
                    flag = 40
                else:
                    flag = 4
                stockdata = self.con.execute(select([stock.c.productcode,stock.c.qty,stock.c.inout,stock.c.goid]).where(and_(stock.c.dcinvtnflag==flag,stock.c.dcinvtnid==self.request.params["dcid"])))
                for stockrow in stockdata:
                    stockinout = stockrow["inout"]
                    goiddata = stockrow["goid"]
                singledelchal = {"delchaldata":{
                                    "dcid":delchaldata["dcid"],
                                    "dcno":delchaldata["dcno"],
                                    "dcflag":delchaldata["dcflag"],
                                    "issuername":delchaldata["issuername"],
                                    "designation":delchaldata["designation"],
                                    "orggstin":delchaldata["orgstategstin"],
                                    "dcdate":datetime.strftime(delchaldata["dcdate"],'%d-%m-%Y'),
                                    "taxflag":delchaldata["taxflag"],
                                    "cancelflag":delchaldata["cancelflag"],
                                    "noofpackages":delchaldata["noofpackages"],
                                    "modeoftransport": delchaldata["modeoftransport"],
                                    "vehicleno":delchaldata["vehicleno"],
                                    "attachmentcount": delchaldata["attachmentcount"],
                                    "inoutflag": delchaldata["inoutflag"], #added inoutflag in get method
                                    "inout":stockinout,
                                    "dcnarration":delchaldata["dcnarration"],
                                    "roundoffflag": delchaldata["roundoffflag"],
                                    "totalinword": delchaldata["totalinword"],
                                    "dcnarration":delchaldata["dcnarration"]
                                }}

                if delchaldata["consignee"]!=None:
                    singledelchal["delchaldata"]["consignee"]=delchaldata["consignee"]
                if delchaldata["delchaltotal"] != None:
                    singledelchal["delchaldata"]["delchaltotal"] ="%.2f" %(float(delchaldata["delchaltotal"]))
                    singledelchal["delchaldata"]["roundedoffvalue"] = "%.2f" %(float(round(delchaldata["delchaltotal"])))
                
                if delchaldata["cancelflag"] ==1:
                    singledelchal["delchaldata"]["canceldate"] = datetime.strftime(delchaldata["canceldate"],'%d-%m-%Y')

                if goiddata!=None:
                    godata = self.con.execute(select([godown.c.goname,godown.c.state,godown.c.goaddr]).where(godown.c.goid==goiddata))
                    goname = godata.fetchone()
                    singledelchal["delchaldata"]["goid"]=goiddata
                    singledelchal["delchaldata"]["goname"]=goname["goname"]
                    singledelchal["delchaldata"]["gostate"]=goname["state"]
                    singledelchal["delchaldata"]["goaddr"]=goname["goaddr"]
                else:
                    singledelchal["delchaldata"]["goid"]=""
                    
                if delchaldata["taxstate"] != None:
                    singledelchal["destinationstate"]=delchaldata["taxstate"]
                    taxStateCode =  getStateCode(delchaldata["taxstate"],self.con)["statecode"]
                    singledelchal["taxstatecode"] = taxStateCode

                if delchaldata["sourcestate"] != None:
                    singledelchal["sourcestate"] = delchaldata["sourcestate"]
                    singledelchal["sourcestatecode"] = getStateCode(delchaldata["sourcestate"],self.con)["statecode"]
                    sourceStateCode = getStateCode(delchaldata["sourcestate"],self.con)["statecode"]

                if delchaldata["dateofsupply"] != None:
                        singledelchal["dateofsupply"]=datetime.strftime(delchaldata["dateofsupply"],"%d-%m-%Y")
                else:
                        singledelchal["dateofsupply"] = ""

                custandsup = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.state, customerandsupplier.c.custaddr, customerandsupplier.c.custtan,customerandsupplier.c.pincode,customerandsupplier.c.gstin, customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==delchaldata["custid"]))
                custData = custandsup.fetchone()
                custsupstatecode = getStateCode(custData["state"],self.con)["statecode"]
                singledelchal["custSupDetails"] = {"custname":custData["custname"],"custsupstate":custData["state"],"custaddr":custData["custaddr"],"csflag":custData["csflag"],"pincode":custData["pincode"],"custsupstatecode":custsupstatecode}
                singledelchal["custSupDetails"]["custid"] = delchaldata["custid"]
                if custData["custtan"] != None:
                    singledelchal["custSupDetails"]["custtin"] = custData["custtan"]
                    if custData["gstin"] != None:
                        if int(delchaldata["inoutflag"]) == 15 :
                            try:
                                singledelchal["custSupDetails"]["custgstin"] = custData["gstin"][str(taxStateCode)]
                            except:
                                singledelchal["custSupDetails"]["custgstin"] = None
                        else:
                            try:
                                singledelchal["custSupDetails"]["custgstin"] = custData["gstin"][str(sourceStateCode)]
                            except:
                                singledelchal["custSupDetails"]["custgstin"] = None

                #..........................................Delchal ProductCode Info....................
                #contents is a nested dictionary from invoice table.
                #It contains productcode as the key with a value as a dictionary.
                #this dictionary has two key value pare, priceperunit and quantity.
                if delchaldata["contents"] == None:
                    singledelchal["delchalflag"]=15
                    stockdata = self.con.execute(select([stock.c.productcode,stock.c.qty,stock.c.inout,stock.c.goid]).where(and_(stock.c.dcinvtnflag==flag,stock.c.dcinvtnid==self.request.params["dcid"])))
                for stockrow in stockdata:
                    productdata = self.con.execute(select([product.c.productdesc,product.c.uomid]).where(and_(product.c.productcode==stockrow["productcode"],product.c.gsflag==7)))
                    productdesc = productdata.fetchone()
                    uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productdesc["uomid"]))
                    unitnamrrow = uomresult.fetchone()
                    items[stockrow["productcode"]] = {"qty":"%.2f"%float(stockrow["qty"]),"productdesc":productdesc["productdesc"],"unitname":unitnamrrow["unitname"]}
                singledelchal["stockdata"]=items
                if delchaldata["contents"]!=None:
                    singledelchal["delchalflag"]=14
                    contentsData = delchaldata["contents"]
                    #delchalContents is the finally dictionary which will not just have the dataset from original contents,
                    #but also productdesc,unitname,freeqty,discount,taxname,taxrate,amount and taxamount
                    delchalContents = {}
                    #get the dictionary of discount and access it inside the loop for one product each.
                    #do the same with freeqty.
                    totalDisc = 0.00
                    totalTaxableVal = 0.00
                    totalTaxAmt = 0.00
                    totalCessAmt = 0.00
                    discounts = delchaldata["discount"]
                    freeqtys = delchaldata["freeqty"]
                    #now looping through the contents.
                    #pc will have the productcode which will be the key in delchalContents.
                    for pc in list(contentsData.keys()):
                        #freeqty and discount can be 0 as these field were not present in previous version of 4.25 hence we have to check if it is None or not and have to pass values accordingly for code optimization. 
                        if discounts != None:
                            # discflag is for discount type. Percent=16/Amount=1
                            # here we convert percent discount in to amount.
                            if delchaldata["discflag"] == 16:
                                qty = float(list(contentsData[str(pc)].keys())[0])
                                price = float(list(contentsData[str(pc)].values())[0])
                                totalWithoutDiscount = qty * price
                                discount = totalWithoutDiscount * float(float(discounts[pc]) / 100)
                            else:
                                discount = discounts[pc]
                        else:
                            discount = 0.00

                        if freeqtys != None:
                            freeqty = freeqtys[pc]
                        else:
                            freeqty = 0.00
                        #uomid=unit of measurment
                        prod = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gsflag,product.c.gscode]).where(product.c.productcode == pc))
                        prodrow = prod.fetchone()
                        # For 'Goods'
                        if int(prodrow["gsflag"]) == 7:
                            um = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid == int(prodrow["uomid"])))
                            unitrow = um.fetchone()
                            unitofMeasurement = unitrow["unitname"]
                            taxableAmount = ((float(contentsData[pc][list(contentsData[pc].keys())[0]])) * float(list(contentsData[pc].keys())[0])) - float(discount)
                        # For 'Service'
                        else:
                            unitofMeasurement = ""
                            taxableAmount = float(list(contentsData[pc].keys())[0]) - float(discount)
                        
                        taxRate = 0.00
                        totalAmount = 0.00
                        taxRate =  float(delchaldata["tax"][pc])
                        if int(delchaldata["taxflag"]) == 22:
                            taxRate =  float(delchaldata["tax"][pc])
                            taxAmount = (taxableAmount * float(taxRate/100))
                            taxname = 'VAT'
                            totalAmount = float(taxableAmount) + (float(taxableAmount) * float(taxRate/100))
                            totalDisc = totalDisc + float(discount)
                            totalTaxableVal = totalTaxableVal + taxableAmount
                            totalTaxAmt = totalTaxAmt + taxAmount
                            delchalContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][list(contentsData[pc].keys())[0]])),"freeqty":"%.2f"% (float(freeqty)),"priceperunit":"%.2f"% (float(list(contentsData[pc].keys())[0])),"discount":"%.2f"% (float(discounts[pc])),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":"VAT","taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount))}

                        else:
                            cessRate = 0.00
                            cessAmount = 0.00
                            cessVal = 0.00
                            taxname = ""
                            if delchaldata["cess"] != None:
                                cessVal = float(delchaldata["cess"][pc])
                                cessAmount = (taxableAmount * (cessVal/100))
                                totalCessAmt = totalCessAmt + cessAmount

                            if delchaldata["sourcestate"] != delchaldata["taxstate"]:
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

                            delchalContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][list(contentsData[pc].keys())[0]])),"freeqty":"%.2f"% (float(freeqty)),"priceperunit":"%.2f"% (float(list(contentsData[pc].keys())[0])),"discount":"%.2f"% (float(discounts[pc])),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":taxname,"taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount)),"cess":"%.2f"%(float(cessAmount)),"cessrate":"%.2f"%(float(cessVal))}
                    singledelchal["totaldiscount"] = "%.2f"% (float(totalDisc))
                    singledelchal["totaltaxablevalue"] = "%.2f"% (float(totalTaxableVal))
                    singledelchal["totaltaxamt"] = "%.2f"% (float(totalTaxAmt))
                    singledelchal["totalcessamt"] = "%.2f"% (float(totalCessAmt))
                    singledelchal['taxname'] = taxname
                    singledelchal["delchalContents"] = delchalContents
                    singledelchal["discflag"] = delchaldata["discflag"]
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":singledelchal}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()


    
    @view_config(request_method='GET',request_param="delchal=singlecancel", renderer ='json')
    def getcanceldelchal(self):
        """
    This function returns the single delivery challan data to frontend depends on 'dcid;.
    if for given dcid 'contents' field not available then 'stockdata' will return, else 'delchalContents' will return.
    we also return the 'delchalflag' for 'Old' and 'new' deliverychallan. for 'Old deliverychallan' delchalflag is '15',
    and for 'New deliverychallan' delchalflag is '14' set.
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
                result = self.con.execute(select([delchalbin]).where(delchalbin.c.dcid==self.request.params["dcid"]))
                delchaldata = result.fetchone()
                items = {}
                goiddata = delchaldata["goid"]
                singledelchal = {"delchaldata":{
                                    "dcid":delchaldata["dcid"],
                                    "dcno":delchaldata["dcno"],
                                    "dcflag":delchaldata["dcflag"],
                                    "issuername":delchaldata["issuername"],
                                    "designation":delchaldata["designation"],
                                    "orggstin":delchaldata["orgstategstin"],
                                    "dcdate":datetime.strftime(delchaldata["dcdate"],'%d-%m-%Y'),
                                    "taxflag":delchaldata["taxflag"],
                                    # "cancelflag":delchaldata["cancelflag"],
                                    "noofpackages":delchaldata["noofpackages"],
                                    "modeoftransport": delchaldata["modeoftransport"],
                                    "vehicleno":delchaldata["vehicleno"],
                                    "attachmentcount": delchaldata["attachmentcount"],
                                    "dcnarration":delchaldata["dcnarration"],
                                    "inoutflag": delchaldata["inoutflag"], #added inoutflag in get method
                                    # "inout":stockinout,
                                    "roundoffflag": delchaldata["roundoffflag"],
                                    "totalinword":delchaldata["totalinword"]
                                }}

                if delchaldata["consignee"]!=None:
                    singledelchal["delchaldata"]["consignee"]=delchaldata["consignee"]
                if delchaldata["delchaltotal"] != None:
                    singledelchal["delchaldata"]["delchaltotal"] ="%.2f" %float(delchaldata["delchaltotal"]) 
                    singledelchal["delchaldata"]["roundedoffvalue"] = "%.2f" %float(round(delchaldata["delchaltotal"]))
             
                if goiddata!=None:
                    godata = self.con.execute(select([godown.c.goname,godown.c.state,godown.c.goaddr]).where(godown.c.goid==goiddata))
                    goname = godata.fetchone()
                    singledelchal["delchaldata"]["goid"]=goiddata
                    singledelchal["delchaldata"]["goname"]=goname["goname"]
                    singledelchal["delchaldata"]["gostate"]=goname["state"]
                    singledelchal["delchaldata"]["goaddr"]=goname["goaddr"]
                else:
                    singledelchal["delchaldata"]["goid"]=""
                    
                if delchaldata["taxstate"] != None:
                    singledelchal["destinationstate"]=delchaldata["taxstate"]
                    taxStateCode =  getStateCode(delchaldata["taxstate"],self.con)["statecode"]
                    singledelchal["taxstatecode"] = taxStateCode

                if delchaldata["sourcestate"] != None:
                    singledelchal["sourcestate"] = delchaldata["sourcestate"]
                    singledelchal["sourcestatecode"] = getStateCode(delchaldata["sourcestate"],self.con)["statecode"]
                    sourceStateCode = getStateCode(delchaldata["sourcestate"],self.con)["statecode"]

                if delchaldata["dateofsupply"] != None:
                        singledelchal["dateofsupply"]=datetime.strftime(delchaldata["dateofsupply"],"%d-%m-%Y")
                else:
                        singledelchal["dateofsupply"] = ""

                custandsup = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.state, customerandsupplier.c.custaddr, customerandsupplier.c.custtan,customerandsupplier.c.pincode,customerandsupplier.c.gstin, customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==delchaldata["custid"]))
                custData = custandsup.fetchone()
                custsupstatecode = getStateCode(custData["state"],self.con)["statecode"]
                singledelchal["custSupDetails"] = {"custname":custData["custname"],"custsupstate":custData["state"],"custaddr":custData["custaddr"],"csflag":custData["csflag"],"pincode":custData["pincode"],"custsupstatecode":custsupstatecode}
                singledelchal["custSupDetails"]["custid"] = delchaldata["custid"]
                if custData["custtan"] != None:
                    singledelchal["custSupDetails"]["custtin"] = custData["custtan"]
                    if custData["gstin"] != None:
                        if int(delchaldata["inoutflag"]) == 15 :
                            try:
                                singledelchal["custSupDetails"]["custgstin"] = custData["gstin"][str(taxStateCode)]
                            except:
                                singledelchal["custSupDetails"]["custgstin"] = None
                        else:
                            try:
                                singledelchal["custSupDetails"]["custgstin"] = custData["gstin"][str(sourceStateCode)]
                            except:
                                singledelchal["custSupDetails"]["custgstin"] = None

                #..........................................Delchal ProductCode Info....................
                if delchaldata["contents"]!=None:
                    singledelchal["delchalflag"]=14
                    contentsData = delchaldata["contents"]
                
                    delchalContents = {}
                    
                    totalDisc = 0.00
                    totalTaxableVal = 0.00
                    totalTaxAmt = 0.00
                    totalCessAmt = 0.00
                    discounts = delchaldata["discount"]
                    freeqtys = delchaldata["freeqty"]
                    #now looping through the contents.
                    #pc will have the productcode which will be the key in delchalContents.
                    for pc in list(contentsData.keys()):
                       
                        if discounts != None:
                            discount = discounts[pc]
                        else:
                            discount = 0.00

                        if freeqtys != None:
                            freeqty = freeqtys[pc]
                        else:
                            freeqty = 0.00
                        #uomid=unit of measurment
                        prod = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gsflag,product.c.gscode]).where(product.c.productcode == pc))
                        prodrow = prod.fetchone()
                        # For 'Goods'
                        if int(prodrow["gsflag"]) == 7:
                            um = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid == int(prodrow["uomid"])))
                            unitrow = um.fetchone()
                            unitofMeasurement = unitrow["unitname"]
                            taxableAmount = ((float(contentsData[pc][list(contentsData[pc].keys())[0]])) * float(list(contentsData[pc].keys())[0])) - float(discount)
                        # For 'Service'
                        else:
                            unitofMeasurement = ""
                            taxableAmount = float(list(contentsData[pc].keys())[0]) - float(discount)
                        
                        taxRate = 0.00
                        totalAmount = 0.00
                        taxRate =  float(delchaldata["tax"][pc])
                        if int(delchaldata["taxflag"]) == 22:
                            taxRate =  float(delchaldata["tax"][pc])
                            taxAmount = (taxableAmount * float(taxRate/100))
                            taxname = 'VAT'
                            totalAmount = float(taxableAmount) + (float(taxableAmount) * float(taxRate/100))
                            totalDisc = totalDisc + float(discount)
                            totalTaxableVal = totalTaxableVal + taxableAmount
                            totalTaxAmt = totalTaxAmt + taxAmount
                            delchalContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][list(contentsData[pc].keys())[0]])),"freeqty":"%.2f"% (float(freeqty)),"priceperunit":"%.2f"% (float(list(contentsData[pc].keys())[0])),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":"VAT","taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount))}

                        else:
                            cessRate = 0.00
                            cessAmount = 0.00
                            cessVal = 0.00
                            taxname = ""
                            if delchaldata["cess"] != None:
                                cessVal = float(delchaldata["cess"][pc])
                                cessAmount = (taxableAmount * (cessVal/100))
                                totalCessAmt = totalCessAmt + cessAmount

                            if delchaldata["sourcestate"] != delchaldata["taxstate"]:
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

                            delchalContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][list(contentsData[pc].keys())[0]])),"freeqty":"%.2f"% (float(freeqty)),"priceperunit":"%.2f"% (float(list(contentsData[pc].keys())[0])),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":taxname,"taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount)),"cess":"%.2f"%(float(cessAmount)),"cessrate":"%.2f"%(float(cessVal))}
                    singledelchal["totaldiscount"] = "%.2f"% (float(totalDisc))
                    singledelchal["totaltaxablevalue"] = "%.2f"% (float(totalTaxableVal))
                    singledelchal["totaltaxamt"] = "%.2f"% (float(totalTaxAmt))
                    singledelchal["totalcessamt"] = "%.2f"% (float(totalCessAmt))
                    singledelchal['taxname'] = taxname
                    singledelchal["delchalContents"] = delchalContents
                    singledelchal["discflag"] = delchaldata["discflag"]

                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":singledelchal}
            except:
                 return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                 self.con.close()

    #Below fuction is use to cancel the deliverynote entry from delchal table using dcid and store in delchalbin table. Also delete stock entry for same dcid.
    @view_config(request_method='DELETE',request_param='type=canceldel',renderer='json')
    def cancelDelchal(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dcid=self.request.json_body["dcid"]
                #To fetch data of all data of cancel delivery note.
                delchalData=self.con.execute(select([delchal]).where(delchal.c.dcid == dcid))
                delchaldata = delchalData.fetchone()
                #Add all data of cancel delivry note into delchalbin"
                delchalbinData = {"dcid":delchaldata["dcid"],"dcno":delchaldata["dcno"],"dcdate":delchaldata["dcdate"],"dcflag":delchaldata["dcflag"],"taxflag":delchaldata["taxflag"],"contents":delchaldata["contents"],"tax":delchaldata["tax"],"cess":delchaldata["cess"],"issuername":delchaldata["issuername"],"designation":delchaldata["designation"],"noofpackages":delchaldata["noofpackages"],"modeoftransport":delchaldata["modeoftransport"],"consignee":delchaldata["consignee"],"taxstate":delchaldata["taxstate"],"sourcestate":delchaldata["sourcestate"],"orgstategstin":delchaldata["orgstategstin"],"freeqty":delchaldata["freeqty"],"discount":delchaldata["discount"],"vehicleno":delchaldata["vehicleno"],"dateofsupply":delchaldata["dateofsupply"],"delchaltotal":delchaldata["delchaltotal"],"attachmentcount":delchaldata["attachmentcount"],"orgcode":delchaldata["orgcode"],"custid":delchaldata["custid"],"orderid":delchaldata["orderid"],"inoutflag":delchaldata["inoutflag"],"roundoffflag":delchaldata["roundoffflag"],"discflag":delchaldata["discflag"],"dcnarration":delchaldata["dcnarration"], "totalinword":delchaldata["totalinword"]}
                if(delchaldata["attachment"] != None): 
                    delchalbinData["attachment"] = delchaldata["attachment"]
                try:
                    #To add goid for cancelled delivery note in delchalbin table before delete stock entry.
                    delgodown = self.con.execute("select goid from stock where dcinvtnid = %d and orgcode=%d and dcinvtnflag=4"%(int(dcid),authDetails["orgcode"]))
                    degodowninfo = delgodown.fetchone()
                    if (degodowninfo != None):
                        delchalbinData["goid"] = degodowninfo["goid"]
                except:
                    pass
                try:
                    # To delete stock entry of cancel delivery note.
                    self.con.execute("delete from stock  where dcinvtnid = %d and orgcode=%d and dcinvtnflag=4"%(int(dcid),authDetails["orgcode"]))
                except:
                    pass
                try:
                    logdata = {}
                    logdata["orgcode"] = authDetails["orgcode"]
                    logdata["userid"] = authDetails["userid"]
                    logdata["time"] = datetime.today().strftime('%Y-%m-%d')
                    logdata["activity"] = str(delchaldata["dcno"])  + ' Delivery Note Cancelled'
                    result = self.con.execute(log.insert(),[logdata])
                except:
                    pass

                dcbin = self.con.execute(delchalbin.insert(),[delchalbinData])
                
                #To delete delivery note enrty from delchal table
                self.con.execute("delete from delchal  where dcid = %d and orgcode=%d"%(int(dcid),authDetails["orgcode"]))
                return {"gkstatus":enumdict["Success"]}

            except:
                try:
                    dcid=self.request.json_body["dcid"]
                    # if delivery note entry is not deleted then delete that delivery note from bin table
                    self.con.execute("delete from delchalbin  where dcid = %d and orgcode=%d"%(int(dcid),authDetails["orgcode"]))
                    return {"gkstatus":enumdict["ConnectionFailed"]}
                except:
                    self.con.close()
                    return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    #This function return list of cancelled delivery notes.      
    @view_config(request_method='GET',request_param='type=listofcancelleddel',renderer='json')
    def listofCancelDelchal(self):
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
                inout = self.request.params["inout"]
                inputdate = dataset["inputdate"]
                del_cancelled_type = dataset["del_cancelled_type"]
                new_inputdate = dataset["inputdate"]
                new_inputdate = datetime.strptime(new_inputdate, "%Y-%m-%d")
                dc_unbilled = []
                # Adding the query here only, which will select the dcids either with "delivery-out" type or "delivery-in".
                if inout == "i":#in
                    if del_cancelled_type == "0":
                        alldcids = self.con.execute(select([delchalbin]).where(and_(delchalbin.c.orgcode == orgcode, delchalbin.c.inoutflag == 9, delchalbin.c.dcdate <= new_inputdate)).order_by(delchalbin.c.dcdate))
                    else:
                        alldcids = self.con.execute(select([delchalbin]).where(and_(delchalbin.c.orgcode == orgcode, delchalbin.c.inoutflag == 9, delchalbin.c.dcflag == int(del_cancelled_type), delchalbin.c.dcdate <= new_inputdate)).order_by(delchalbin.c.dcdate))
                if inout == "o":#out
                    if del_cancelled_type == "0":
                        alldcids = self.con.execute(select([delchalbin]).where(and_(delchalbin.c.orgcode == orgcode, delchalbin.c.inoutflag == 15, delchalbin.c.dcdate <= new_inputdate)).order_by(delchalbin.c.dcdate))
                    else:
                        alldcids = self.con.execute(select([delchalbin]).where(and_(delchalbin.c.orgcode == orgcode, delchalbin.c.inoutflag == 15, delchalbin.c.dcflag == int(del_cancelled_type), delchalbin.c.dcdate <= new_inputdate)).order_by(delchalbin.c.dcdate))
                alldcids = alldcids.fetchall()
                dcdata = []
                srno = 1
                for row in alldcids:
                    godown = ""
                    cresult = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==row["custid"]))
                    customerdetails = cresult.fetchone()
                    if row["goid"] != None:
                        godownres = self.con.execute("select goname, goaddr from godown where goid = %d" %int(row["goid"]))
                        godownresult = godownres.fetchone()
                        if godownresult != None:
                            godownname = godownresult["goname"]
                            godownaddrs = godownresult["goaddr"]
                            godown =  godownname + "("+ godownaddrs + ")"
                        else:
                            godownname = ""
                            godownaddrs = ""
                            godown = ""

                    if row["dcflag"] == 1:
                        dcflag = "Approval"
                    elif row["dcflag"] == 3:
                        dcflag = "Consignment"
                    elif row["dcflag"] == 4:
                        dcflag = "Sale"
                    elif row["dcflag"] == 16:
                        dcflag = "Purchase"
                    elif row["dcflag"] == 19:
                        #We don't have to consider sample.
                        dcflag = "Sample"
                    elif row["dcflag"]== 6:
                        #we ignore this as well
                        dcflag = "Free Replacement"
                    singledcdata={"dcid":row["dcid"],"dcno":row["dcno"],"dcdate":datetime.strftime(row["dcdate"],'%d-%m-%Y'),"dcflag":dcflag,"inoutflag":row["inoutflag"],"custname":customerdetails["custname"],"goname":godown,"srno":srno}
                    dcdata.append(singledcdata)
                    srno += 1
                return {"gkstatus":enumdict["Success"],"gkresult":dcdata}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()


    @view_config(request_param="delchal=last",request_method='GET',renderer='json')
    def getLastDelChalDetails(self):
        try:
            """
            Purpose:
            returns a last created note no. of Deliverychallan.
            Returns a json dictionary containing that Deliverychallan.
            """
            token = self.request.headers['gktoken']
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                deliverychallandata = {"dcdate": "","dcno":""}
                dcstatus = int(self.request.params["status"])
                result = self.con.execute(select([delchal.c.dcno,delchal.c.dcdate]).where(delchal.c.dcid==(select([func.max(stock.c.dcinvtnid)]).where(and_(stock.c.inout==dcstatus,stock.c.dcinvtnflag==4,stock.c.orgcode==authDetails["orgcode"] )))) )
                row = result.fetchone()
                if row != None:
                    deliverychallandata["dcdate"] = datetime.strftime((row["dcdate"]),"%d-%m-%Y")
                    deliverychallandata["dcno"] = row["dcno"]
                self.con.close()
                return {"gkstatus":enumdict["Success"], "gkresult":deliverychallandata}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}

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
                dcid = self.request.params["dcid"]
                delchalData = self.con.execute(select([delchal.c.dcno, delchal.c.attachment,delchal.c.cancelflag]).where(and_(delchal.c.dcid == dcid)))
                attachment = delchalData.fetchone()
                return {"gkstatus":enumdict["Success"],"gkresult":attachment["attachment"], "dcno": attachment["dcno"], "cancelflag":attachment["cancelflag"],"userrole":urole["userrole"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method='GET',request_param='action=getdcinvprods', renderer='json')
    def getdcinvproducts(self):
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
                dcid = self.request.params["dcid"]
                items = {}
                
                delchalresult = self.con.execute(select([delchal.c.contents,delchal.c.freeqty]).where(delchal.c.dcid == dcid))
                deliveryinfo = delchalresult.fetchone()
                freeprod = deliveryinfo["freeqty"]
                proddata = deliveryinfo["contents"]
                for pc in list(proddata.keys()):
                    productdata = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gscode]).where(and_(product.c.productcode==pc,product.c.gsflag==7)))
                    productdesc = productdata.fetchone()
                    uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productdesc["uomid"]))
                    unitnamrrow = uomresult.fetchone()
                    items[int(pc)] = {"qty":float("%.2f"%float(proddata[pc][list(proddata[pc].keys())[0]])),"productdesc":productdesc["productdesc"],"unitname":unitnamrrow["unitname"],"gscode":productdesc["gscode"]}
                for frep in list(freeprod.keys()):
                    items[int(frep)]["freeqty"] = float("%.2f"%float(freeprod[frep]))

                result = self.con.execute(select([dcinv.c.invid, dcinv.c.invprods]).where(dcinv.c.dcid == dcid))
                linkedinvoices = result.fetchall()
                #linkedinvoices refers to the invoices which are associated with the delivery challan whose id = dcid.
                for invoiceid in linkedinvoices:
                    invresult = self.con.execute(select([invoice.c.contents,invoice.c.freeqty]).where(invoice.c.invid == invoiceid["invid"]))
                    invoiceinfo = invresult.fetchone()
                    freeprodinv = invoiceinfo["freeqty"]
                    proddatainv = invoiceinfo["contents"]
                    for pc in list(proddatainv.keys()):
                        try:
                            items[int(pc)]["qty"] -= float("%.2f"%float(proddatainv[pc][list(proddatainv[pc].keys())[0]]))
                        except:
                            pass
                    for pc in list(freeprodinv.keys()):
                        try:
                            items[int(pc)]["freeqty"] -= float("%.2f"%float(freeprodinv[pc]))
                        except:
                            pass
                            
                allrnidres = self.con.execute(select([rejectionnote.c.rnid]).distinct().where(and_(rejectionnote.c.orgcode == authDetails["orgcode"], rejectionnote.c.dcid == dcid)))
                allrnidres = allrnidres.fetchall()
                rnprodresult = []
                #get stock respected to all rejection notes
                for rnid in allrnidres:
                    temp = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.orgcode == authDetails["orgcode"], stock.c.dcinvtnflag == 18, stock.c.dcinvtnid == rnid[0])))
                    temp = temp.fetchall()
                    rnprodresult.append(temp)
                for row in rnprodresult:
                    try:
                        for prodc, qty in row:
                            items[int(prodc)]["qty"] -= float(qty)
                    except:
                        pass
                if len(linkedinvoices) != 0 or len(rnprodresult) != 0:
                    for productcode in list(items.keys()):
                        if items[productcode]["qty"] == 0:
                            del items[productcode]
                return {"gkstatus":enumdict["Success"], "gkresult": items}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
