
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
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
"Bhavesh Bawadhane" <bbhavesh07@gmail.com>
"""


from gkcore import eng, enumdict
from gkcore.models.gkdb import rejectionnote, stock, customerandsupplier, goprod, users, godown, delchal, invoice, product, unitofmeasurement, dcinv
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from datetime import datetime, date
import jwt
import gkcore
from gkcore.views.api_login import authCheck
from gkcore.views.api_user import getUserRole
from gkcore.views.api_invoice import getStateCode

@view_defaults(route_name='rejectionnote')
class api_rejectionnote(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection
    """
    create method for rejectionnote resource.
    stock table is also updated after rejection entry is made.
        -rnid goes in dcinvtnid column of stock table.
        -dcinvtnflag column will be set to 18 for rejection note entry.
    If stock table insert fails then the rejectionnote entry will be deleted.
    """
    @view_config(request_method='POST',renderer='json')
    def addRejectionNote(self):
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
                rejectionnotedata = dataset["rejectionnotedata"]
                stockdata = dataset["stockdata"]
                rejectionnotedata["orgcode"] = authDetails["orgcode"]
                stockdata["orgcode"] = authDetails["orgcode"]
                rejectionnotedata["issuerid"] = authDetails["userid"]
                result = self.con.execute(rejectionnote.insert(),[rejectionnotedata])
                if result.rowcount==1:
                    rniddata = self.con.execute(select([rejectionnote.c.rnid,rejectionnote.c.rndate]).where(and_(rejectionnote.c.orgcode==authDetails["orgcode"],rejectionnote.c.rnno==rejectionnotedata["rnno"])))
                    rnidrow = rniddata.fetchone()
                    stockdata["dcinvtnid"] = rnidrow["rnid"]
                    stockdata["dcinvtnflag"] = 18
                    stockdata["stockdate"] = rnidrow["rndate"]
                    items = stockdata.pop("items")
                    try:
                        for key in items.keys():
                            stockdata["productcode"] = key
                            stockdata["qty"] = items[key]
                            result = self.con.execute(stock.insert(),[stockdata])
                            if stockdata.has_key("goid"):
                                resultgoprod = self.con.execute(select([goprod]).where(and_(goprod.c.goid == stockdata["goid"], goprod.c.productcode==key)))
                                if resultgoprod.rowcount == 0:
                                    result = self.con.execute(goprod.insert(),[{"goid":stockdata["goid"],"productcode": key,"goopeningstock":0.00, "orgcode":authDetails["orgcode"]}])

                    except:
                        result = self.con.execute(stock.delete().where(and_(stock.c.dcinvtnid==rnidrow["rnid"],stock.c.dcinvtnflag==18)))
                        result = self.con.execute(rejectionnote.delete().where(rejectionnote.c.rnid==rnidrow["rnid"]))
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

    @view_config(request_method='GET',request_param="type=all", renderer ='json')
    def getAllRejectionNotes(self):
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
                result = self.con.execute(select([rejectionnote]).where(rejectionnote.c.orgcode==authDetails["orgcode"]).order_by(rejectionnote.c.rnno))
                rnotes = []
                for row in result:
                    rnotes.append({"rnid":row["rnid"],"rnno":row["rnno"], "inout":row["inout"], "dcid":row["dcid"], "invid":row["invid"], "rndate":datetime.strftime(row["rndate"],'%d-%m-%Y')})
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":rnotes}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
                
    @view_config(request_method='GET',request_param="type=single", renderer ='json')
    def getRejectionNote(self):
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
                result = self.con.execute(select([rejectionnote]).where(rejectionnote.c.rnid==self.request.params["rnid"]))
                rndata = result.fetchone()
                issuerdata = self.con.execute(select([users.c.username]).where(users.c.userid == rndata["issuerid"]))
                issuerdata = issuerdata.fetchone()
                rejectionnotedata = {"rnid": rndata["rnid"], "rndate": datetime.strftime(rndata["rndate"],"%d-%m-%Y"), "rnno": rndata["rnno"], "inout":rndata["inout"], "dcid": rndata["dcid"], "invid": rndata["invid"]}
                rejectionnotedata.update({"issuername": issuerdata["username"]})
                typeoftrans = {1:"Approval", 3:"Consignment",5:"Free Replacement",4: "Sales",19:"Sample"}
                if rejectionnotedata["dcid"] != None:
                    dcdata = self.con.execute(select([delchal.c.dcno, delchal.c.dcdate, delchal.c.dcflag]).where(delchal.c.dcid==rejectionnotedata["dcid"]))
                    dcdata = dcdata.fetchone()
                    custdata = self.con.execute("select custname, custaddr, custtan from customerandsupplier where custid = (select custid from delchal where dcid = %d)"%int(rejectionnotedata["dcid"]))
                    custdata = custdata.fetchone()
                    rejectionnotedata.update({"dcno":dcdata["dcno"], "dcdate":datetime.strftime(dcdata["dcdate"],"%d-%m-%Y"), "transactiontype":typeoftrans[dcdata["dcflag"]], "custname": custdata["custname"], "custaddr":custdata["custaddr"], "custtin":custdata["custtan"]})
                #invoicedata
                if rejectionnotedata["invid"] != None:
                    invdata = self.con.execute(select([invoice]).where(invoice.c.invid==rejectionnotedata["invid"]))
                    invdata = invdata.fetchone()
                    rejinvdata={"invno":invdata["invoiceno"], "invdate":datetime.strftime(invdata["invoicedate"],"%d-%m-%Y"),"taxflag":invdata["taxflag"],"tax":invdata["tax"]}
                    if invdata["sourcestate"] != None or invdata["taxstate"] !=None:
                        rejinvdata["sourcestate"] = invdata["sourcestate"]
                        sourceStateCode = getStateCode(invdata["sourcestate"],self.con)["statecode"]
                        rejinvdata["sourcestatecode"] = sourceStateCode
                        rejinvdata["taxstate"]=invdata["taxstate"]
                        taxStateCode=getStateCode(invdata["taxstate"],self.con)["statecode"]
                        rejinvdata["taxstatecode"]=taxStateCode
                    rejectionnotedata["invdata"]=rejinvdata
                    dcinvdata = self.con.execute(select([dcinv.c.dcid]).distinct().where(dcinv.c.invid == invdata["invid"]))
                    dcinvdata = dcinvdata.fetchone()
                    custsupdata = self.con.execute(select([customerandsupplier.c.custid,customerandsupplier.c.custname,customerandsupplier.c.custaddr,customerandsupplier.c.gstin,customerandsupplier.c.state,customerandsupplier.c.custtan,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invdata["custid"]))
                    custdata = custsupdata.fetchone()
                    custsupstatecode = getStateCode(custdata["state"],self.con)["statecode"]
                    custSupDetails = {"custname":custdata["custname"],"custsupstate":custdata["state"],"custaddr":custdata["custaddr"],"csflag":custdata["csflag"],"custsupstatecode":custsupstatecode}
                    if custdata["custtan"] != None:
                        custSupDetails["custtin"] = custdata["custtan"]
                    if custdata["gstin"] != None:
                        if int(custdata["csflag"]) == 3 :
                           try:
                               custSupDetails["custgstin"] = custdata["gstin"][str(taxStateCode)]
                           except:
                               custSupDetails["custgstin"] = None
                        else:
                            try:
                                custSupDetails["custgstin"] = custdata["gstin"][str(sourceStateCode)]
                            except:
                                custSupDetails["custgstin"] = None
                        rejectionnotedata["invdata"]["custSupDetails"] = custSupDetails
                    #Details of Delivery Note
                    if dcinvdata != None:
                        dcdata = self.con.execute(select([delchal.c.dcno, delchal.c.dcdate, delchal.c.dcflag]).where(delchal.c.dcid==dcinvdata[0]))
                        dcdata = dcdata.fetchone()
                        rejectionnotedata.update({"dcno":dcdata["dcno"], "dcdate":datetime.strftime(dcdata["dcdate"],"%d-%m-%Y"), "transactiontype":typeoftrans[dcdata["dcflag"]]})
                    #nested Dictionary
                    rejectionData = invdata["contents"]
                    for pc in rejectionData.keys():
                        print"hello"
                        prod = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gsflag,product.c.gscode]).where(product.c.productcode == pc))
                        prodrow = prod.fetchone()
                        if int(prodrow["gsflag"]) == 7:
                            um = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid == int(prodrow["uomid"])))
                            unitrow = um.fetchone()
                            unitofMeasurement = unitrow["unitname"]
                            #taxableAmount = ((float(rejectionData[pc][rejectionData[pc].keys()[0]])) * float(rejectionData[pc].keys()[0])) - float(discount)
                        else:
                            unitofMeasurement = ""
                            #taxableAmount = float(rejectionData[pc].keys()[0]) - float(discount)
                    
                #Product Description
                items = {}
                stockdata = self.con.execute(select([stock.c.productcode,stock.c.qty,stock.c.inout,stock.c.goid]).where(and_(stock.c.dcinvtnflag==18,stock.c.dcinvtnid==self.request.params["rnid"])))
                for stockrow in stockdata:
                    productdata = self.con.execute(select([product.c.productdesc,product.c.uomid]).where(product.c.productcode==stockrow["productcode"]))
                    productdesc = productdata.fetchone()
                    uomresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid==productdesc["uomid"]))
                    unitnamrrow = uomresult.fetchone()
                    items[stockrow["productcode"]] = {"qty":"%.2f"%float(stockrow["qty"]),"productdesc":productdesc["productdesc"],"unitname":unitnamrrow["unitname"]}
                    goiddata = stockrow["goid"]
                rejectionnotedata.update({"rejected":items})
                if goiddata!=None:
                    godata = self.con.execute(select([godown.c.goname,godown.c.state]).where(godown.c.goid==goiddata))
                    goname = godata.fetchone()
                
                    rejectionnotedata.update({"goid": goiddata, "goname": goname["goname"], "gostate": goname["state"]})
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": rejectionnotedata}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
