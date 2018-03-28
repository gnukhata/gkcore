
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
This file is part of GNUKhata:A modular,robust anhd Free Accounting System.

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
"Pornima Kolte <pornima@openmailbox.org>"
"Prajkta Patkar<prajkta.patkar007@gmail.com>"
"""


from pyramid.view import view_defaults,  view_config
from gkcore.views.api_login import authCheck
from gkcore import eng, enumdict
from pyramid.request import Request
from gkcore.models.gkdb import purchaseorder,invoice, dcinv, delchal, stock, product, customerandsupplier, unitofmeasurement, godown, rejectionnote, tax, state, users
from sqlalchemy.sql import select, distinct
from sqlalchemy import func, desc
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_ ,exc
from datetime import datetime,date
import jwt
import gkcore
from gkcore.models.meta import dbconnect

from datetime import datetime,date

def getStateCode(StateName,con):
    stateData = con.execute(select([state.c.statecode]).where(state.c.statename == StateName))
    staterow = stateData.fetchone()
    return {"statecode":staterow["statecode"]}



@view_defaults(route_name='purchaseorder')
class api_purchaseorder(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection
        print "Purchase order initialized"

    @view_config(request_method='POST',renderer='json')
    def addPoSo(self):
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
                dataset["orgcode"] = authDetails["orgcode"]
                result = self.con.execute(purchaseorder.insert(),[dataset])
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()


    @view_config(request_method='GET',renderer='json')
    def getAllPoSoData(self):
        """ This function returns all existing PO and SO """
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(select([purchaseorder]).where(purchaseorder.c.orgcode==authDetails["orgcode"]).order_by(purchaseorder.c.orderdate))
                allposo = []
                for row in result:
                    custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["csid"]))
                    custrow = custdata.fetchone()
                    allposo.append({"orderid":row["orderid"],"orderno": row["orderno"], "orderdate": datetime.strftime(row["orderdate"],'%d-%m-%Y'),"creditperiod": custrow["creditperiod"],"payterms": row["payterms"],"modeoftransport":row["modeoftransport"],"designation":["designation"],
                                        "schedule":row["schedule"],"taxstate":row["taxstate"],"psflag":row["psflag"]})
                self.con.close()
                return {"gkstatus":enumdict["Success"], "gkresult":allposo}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method='GET',request_param='psflag',renderer='json')
    def getposo(self):

        """
        This function gives all purchaseorder or salesorder by matching parameter psflag
        """
        try:

            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                psflagdata =int(self.request.params["psflag"])
                result=self.con.execute(select([purchaseorder.c.orderid,purchaseorder.c.orderno,purchaseorder.c.orderdate,purchaseorder.c.csid]).where(and_(purchaseorder.c.psflag == psflagdata,purchaseorder.c.orgcode==authDetails["orgcode"])))
                po =[]
                for row in result:
                    custdata = self.con.execute(select([customerandsupplier.c.custname]).where(customerandsupplier.c.custid==row["csid"]))
                    custrow = custdata.fetchone()
                    po.append({"orderid":row["orderid"],"orderno": row["orderno"], "orderdate":datetime.strftime(row["orderdate"],'%d-%m-%Y') ,"custname": custrow["custname"]})
                return {"gkstatus":enumdict["Success"],"gkresult":po}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

                

    @view_config(request_method='GET',request_param="poso=single", renderer ='json')
    def getSingleposo(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        else:
            self.con = eng.connect()
            result = self.con.execute(select([purchaseorder]).where(purchaseorder.c.orderid==self.request.params["orderid"]))
            podata = result.fetchone()
            schedule = podata["schedule"]
            details={}          #Stores schedule
            productinf={}       #Stores productdesc and unitofmeasurement.
            for key in schedule:
                details[key] = {"productname":schedule[key],"packages":schedule[key]["packages"],"rateperunit":schedule[key]["rateperunit"],"quantity":schedule[key]["quantity"],"staggered":schedule[key]["staggered"],"rateperunit":schedule[key]["rateperunit"]}
                #Productname and unitofMeasurement depending on productcode. 
                prod = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gsflag]).where(product.c.productcode == key))
                prodrow = prod.fetchone()
                if int(prodrow["gsflag"]) == 7:
                    um = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid == int(prodrow["uomid"])))
                    unitrow = um.fetchone()
                    unitofMeasurement = unitrow["unitname"]
                else:
                    unitofMeasurement = ""
                productinf[key]={"productdesc":prodrow["productdesc"],"productuomid":prodrow["uomid"],"unitofmeasurement":unitofMeasurement} 

            po = {
                "orderno":podata["orderno"],
                "orderdate": datetime.strftime(podata["orderdate"],"%d-%m-%Y"),
                "creditperiod":podata["creditperiod"],
                "payterms":podata["payterms"],
                "modeoftransport":podata["modeoftransport"],
                #"issuername":podata["issuername"],
                #"designation":podata["designation"],
                "schedule":details,
                #"taxstate":podata["taxstate"],
                "psflag":podata["psflag"],
                "csid":podata["csid"],
                "togodown":podata["togodown"],
                "taxflag" :podata["taxflag"],
                "tax" :podata["tax"],
                "purchaseordertotal" :"%.2f"%float(podata["purchaseordertotal"]),
                #"sourcestate" :podata["sourcestate"],
                "prgstategstin" :podata["orgstategstin"],
                "consignee" :podata["consignee"],
                "freeqty" :podata["freeqty"],
                "reversecharge" :podata["reversecharge"],
                "bankdetails" :podata["bankdetails"],
                "vehicleno" :podata["vehicleno"],
                "dateofsupply" :datetime.strftime(podata["dateofsupply"],"%d-%m-%Y"),
                "discount" :podata["discount"],
                "paymentmode" :podata["paymentmode"],
                #"address" :podata["address"],
                "orgcode" :podata["orgcode"],
                "productinf":productinf
                }
            if podata["psflag"] == 16:
                po["issuername"]=podata["issuername"]
                po["designation"]=podata["designation"]
                po["address"]=podata["address"]
                
            #If sourcestate and taxstate are present.
            if podata["sourcestate"] != None:
                    po["sourcestate"] = podata["sourcestate"]
                    po["sourcestatecode"] = getStateCode(podata["sourcestate"],self.con)["statecode"]
                    sourceStateCode = getStateCode(podata["sourcestate"],self.con)["statecode"]
            if podata["taxstate"] != None:
                        po["destinationstate"]=podata["taxstate"]
                        taxStateCode =  getStateCode(podata["taxstate"],self.con)["statecode"]
                        po["taxstatecode"] = taxStateCode
                        
            #Customer And Supplier details    
            custandsup = self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.state, customerandsupplier.c.custaddr, customerandsupplier.c.custtan,customerandsupplier.c.gstin, customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==podata["csid"]))
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

                    po["custSupDetails"] = custSupDetails
            return {"gkstatus":enumdict["Success"],"gkresult":po}
            self.con.close()


    @view_config(request_method='PUT',renderer='json')
    def editPurchaseOrder(self):
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
                result = self.con.execute(purchaseorder.update().where(purchaseorder.c.orderid == dataset["orderid"]).values(dataset))
                return {"gkstatus":enumdict["Success"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()


    @view_config(request_method='DELETE',renderer='json')
    def deletePurchaseOrder(self):
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
                result = self.con.execute(purchaseorder.delete().where(purchaseorder.c.orderid == dataset["orderid"]))
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
