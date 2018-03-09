
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
"Reshma Bhatawade" <reshma_b@riseup.net>
"Sanket Kolnoorkar" <sanketf123@gmail.com>
"""

from gkcore import eng, enumdict
from gkcore.models.gkdb import delchal, stock, customerandsupplier, godown, product, unitofmeasurement, dcinv,goprod, rejectionnote
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
            #try:
                self.con = eng.connect()
                dataset = self.request.json_body
                delchaldata = dataset["delchaldata"]                
                stockdata = dataset["stockdata"]
                inoutflag=stockdata["inout"]
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
                    #items = stockdata.pop("contents")
                    try:
                        for key in items.keys():
                            print "yes"
                            stockdata["productcode"] = key
                            stockdata["qty"] = items[key].values()[0]
                            print stockdata["qty"]
                            result = self.con.execute(stock.insert(),[stockdata])
                            if stockdata.has_key("goid"):
                                resultgoprod = self.con.execute(select([goprod]).where(and_(goprod.c.goid == stockdata["goid"], goprod.c.productcode==key)))
                                if resultgoprod.rowcount == 0:
                                    result = self.con.execute(goprod.insert(),[{"goid":stockdata["goid"],"productcode": key,"goopeningstock":0.00, "orgcode":authDetails["orgcode"]}])

                    except:
                        result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==dcidrow["dcid"],stock.c.dcinvtnflag==4)))
                        result = self.con.execute(delchal.delete().where(delchal.c.dcid==dcidrow["dcid"]))
                        return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
                    return {"gkstatus":enumdict["Success"]}
                else:
                    return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            #except exc.IntegrityError:
            #    return {"gkstatus":enumdict["DuplicateEntry"]}
            #except:
            #    return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            #finally:
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
                    for key in items.keys():
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
                if self.request.params.has_key("inoutflag"):
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
                custdata = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.state]).where(customerandsupplier.c.custid==delchaldata["custid"]))
                custname = custdata.fetchone()
                items = {}
                if delchaldata["cancelflag"]==1:
                    flag = 40
                else:
                    flag = 4
                stockdata = self.con.execute(select([stock.c.productcode,stock.c.qty,stock.c.inout,stock.c.goid]).where(and_(stock.c.dcinvtnflag==flag,stock.c.dcinvtnid==self.request.params["dcid"])))
                for stockrow in stockdata:
                    productdata = self.con.execute(select([product.c.productdesc,product.c.uomid]).where(and_(product.c.productcode==stockrow["productcode"],product.c.gsflag==7)))
                    productdesc = productdata.fetchone()
                    uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productdesc["uomid"]))
                    unitnamrrow = uomresult.fetchone()
                    items[stockrow["productcode"]] = {"qty":"%.2f"%float(stockrow["qty"]),"productdesc":productdesc["productdesc"],"unitname":unitnamrrow["unitname"]}
                    stockinout = stockrow["inout"]
                    goiddata = stockrow["goid"]
                singledelchal = {"delchaldata":{
                                    "dcid":delchaldata["dcid"],
                                    "dcno":delchaldata["dcno"],
                                    "dcflag":delchaldata["dcflag"],
                                    "issuername":delchaldata["issuername"],
                                    "designation":delchaldata["designation"],
                                    "consignee":delchaldata["consignee"],
                                    "dcdate":datetime.strftime(delchaldata["dcdate"],'%d-%m-%Y'),
                                    "custid":delchaldata["custid"],"custname":custname["custname"],
                                    "custstate":custname["state"],
                                    "cancelflag":delchaldata["cancelflag"],
                                    "noofpackages":delchaldata["noofpackages"],
                                    "modeoftransport": delchaldata["modeoftransport"],
                                    "attachmentcount": delchaldata["attachmentcount"],
                                    "inoutflag": delchaldata["inoutflag"] #added inoutflag in get method
                                },
                            "stockdata":{
                                    "inout":stockinout,"items":items
                                    }}
                if delchaldata["cancelflag"] ==1:
                    singledelchal["delchaldata"]["canceldate"] = datetime.strftime(delchaldata["canceldate"],'%d-%m-%Y')

                if goiddata!=None:
                    godata = self.con.execute(select([godown.c.goname,godown.c.state]).where(godown.c.goid==goiddata))
                    goname = godata.fetchone()
                    singledelchal["delchaldata"]["goid"]=goiddata
                    singledelchal["delchaldata"]["goname"]=goname["goname"]
                    singledelchal["delchaldata"]["gostate"]=goname["state"]

                #contents is a nested dictionary from invoice table.
                #It contains productcode as the key with a value as a dictionary.
                #this dictionary has two key value pare, priceperunit and quantity.
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
                    #uomid=unit of measurment
                    prod = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gsflag,product.c.gscode]).where(product.c.productcode == pc))
                    prodrow = prod.fetchone()
                    # For 'Goods'
                    if int(prodrow["gsflag"]) == 7:
                        um = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid == int(prodrow["uomid"])))
                        unitrow = um.fetchone()
                        unitofMeasurement = unitrow["unitname"]
                        taxableAmount = ((float(contentsData[pc][contentsData[pc].keys()[0]])) * float(contentsData[pc].keys()[0])) - float(discount)
                    # For 'Service'
                    else:
                        unitofMeasurement = ""
                        taxableAmount = float(contentsData[pc].keys()[0]) - float(discount)
                        
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
                        delchalContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][contentsData[pc].keys()[0]])),"freeqty":"%.2f"% (float(freeqty)),"priceperunit":"%.2f"% (float(contentsData[pc].keys()[0])),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":"VAT","taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount))}

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

                        delchalContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][contentsData[pc].keys()[0]])),"freeqty":"%.2f"% (float(freeqty)),"priceperunit":"%.2f"% (float(contentsData[pc].keys()[0])),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":taxname,"taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount)),"cess":"%.2f"%(float(cessAmount)),"cessrate":"%.2f"%(float(cessVal))}
                singledelchal["totaldiscount"] = "%.2f"% (float(totalDisc))
                singledelchal["totaltaxablevalue"] = "%.2f"% (float(totalTaxableVal))
                singledelchal["totaltaxamt"] = "%.2f"% (float(totalTaxAmt))
                singledelchal["totalcessamt"] = "%.2f"% (float(totalCessAmt))
                singledelchal['taxname'] = taxname
                singledelchal["delchalContents"] = delchalContents

                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":singledelchal }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
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
                stockdata = self.con.execute(select([stock.c.productcode, stock.c.qty]).where(and_(stock.c.dcinvtnflag == 4, stock.c.dcinvtnid == dcid)))
                for stockrow in stockdata:
                    productdata = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gscode]).where(and_(product.c.productcode==stockrow["productcode"],product.c.gsflag==7)))
                    productdesc = productdata.fetchone()
                    uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productdesc["uomid"]))
                    unitnamrrow = uomresult.fetchone()
                    items[stockrow["productcode"]] = {"qty":float("%.2f"%float(stockrow["qty"])),"productdesc":productdesc["productdesc"],"unitname":unitnamrrow["unitname"],"gscode":productdesc["gscode"]}
                result = self.con.execute(select([dcinv.c.invid, dcinv.c.invprods]).where(dcinv.c.dcid == dcid))
                linkedinvoices = result.fetchall()
                #linkedinvoices refers to the invoices which are associated with the delivery challan whose id = dcid.
                for invoice in linkedinvoices:
                    invprods = invoice[1]
                    try:
                        for productcode in invprods.keys():
                            items[int(productcode)]["qty"] -= float(invprods[productcode])
                    except:
                        pass
                #This code is for rejection note
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
                    for productcode in items.keys():
                        if items[productcode]["qty"] == 0:
                            del items[productcode]
                return {"gkstatus":enumdict["Success"], "gkresult": items}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
