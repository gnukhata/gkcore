
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
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"Bhavesh Bawadhane" <bbhavesh07@gmail.com>
"Prajkta Patkar" <prajkta.patkar007@gmail.com>
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
from sqlalchemy import and_, exc, func
import jwt
import gkcore
from gkcore.models.meta import dbconnect
from gkcore.models.gkdb import goprod, product
from gkcore.views.api_user import getUserRole
from gkcore.views.api_godown import getusergodowns


@view_defaults(route_name='products')
class api_product(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection


    @view_config(request_method='GET', renderer ='json')
    def getAllProducts(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"]==False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con=eng.connect()
                userrole = getUserRole(authDetails["userid"])
                gorole = userrole["gkresult"]
                if (gorole["userrole"]==3):
                    uId = getusergodowns(authDetails["userid"])
                    gid=[]
                    for record1 in uId["gkresult"]:
                        gid.append(record1["goid"])
                    productCodes=[]
                    for record2 in gid:
                        proCode = self.con.execute(select([gkdb.goprod.c.productcode]).where(gkdb.goprod.c.goid==record2))
                        proCodes = proCode.fetchall()
                        for record3 in proCodes:
                            productCodes.append(record3["productcode"])
                    results = []
                    for record4 in productCodes:
                        result = self.con.execute(select([gkdb.product.c.productcode, gkdb.product.c.productdesc, gkdb.product.c.categorycode, gkdb.product.c.uomid]).where(and_(gkdb.product.c.orgcode==authDetails["orgcode"], gkdb.product.c.productcode==record4)).order_by(gkdb.product.c.productdesc))
                        products = result.fetchone()
                        results.append(products)
                else:
                    results = self.con.execute(select([gkdb.product.c.productcode, gkdb.product.c.productdesc, gkdb.product.c.categorycode, gkdb.product.c.uomid]).where(gkdb.product.c.orgcode==authDetails["orgcode"]).order_by(gkdb.product.c.productdesc))
                products = []
                srno=1
                for row in results:
                    unitsofmeasurement = self.con.execute(select([gkdb.unitofmeasurement.c.unitname]).where(gkdb.unitofmeasurement.c.uomid==row["uomid"]))
                    unitofmeasurement = unitsofmeasurement.fetchone()
                    if unitofmeasurement != None:
                        unitname = unitofmeasurement["unitname"]
                    if row["categorycode"]!=None:
                        categories = self.con.execute(select([gkdb.categorysubcategories.c.categoryname]).where(gkdb.categorysubcategories.c.categorycode==row["categorycode"]))
                        category = categories.fetchone()
                        categoryname = category["categoryname"]
                    else:
                        categoryname=""
                    if row["productcode"]!=None:
                        openingStockResult = self.con.execute(select([gkdb.product.c.openingstock]).where(gkdb.product.c.productcode == row["productcode"]))
                        osRow =openingStockResult.fetchone()
                        openingStock = osRow["openingstock"]
                        productstockin = self.con.execute(select([func.sum(gkdb.stock.c.qty).label("sumofins")]).where(and_(gkdb.stock.c.productcode==row["productcode"],gkdb.stock.c.inout==9)))
                        stockinsum = productstockin.fetchone()
                        if stockinsum["sumofins"]!=None:
                            openingStock = openingStock + stockinsum["sumofins"]
                        productstockout = self.con.execute(select([func.sum(gkdb.stock.c.qty).label("sumofouts")]).where(and_(gkdb.stock.c.productcode==row["productcode"],gkdb.stock.c.inout==15)))
                        stockoutsum = productstockout.fetchone()
                        if stockoutsum["sumofouts"]!=None:
                            openingStock = openingStock - stockoutsum["sumofouts"]
                    products.append({"srno":srno, "unitname":unitname, "categoryname":categoryname, "productcode": row["productcode"], "productdesc":row["productdesc"] , "categorycode": row["categorycode"], "productquantity": "%.2f"%float(openingStock)})
                    srno = srno+1
                return {"gkstatus":enumdict["Success"], "gkresult":products}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()


    @view_config(request_param='qty=single', request_method='GET',renderer='json')
    def getProduct(self):
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
                result = self.con.execute(select([gkdb.product]).where(gkdb.product.c.productcode==self.request.params["productcode"]))
                row = result.fetchone()
                result = self.con.execute(select([gkdb.unitofmeasurement.c.unitname]).where(gkdb.unitofmeasurement.c.uomid==row["uomid"]))
                unitrow= result.fetchone()
                productDetails={ "productcode":row["productcode"],"productdesc": row["productdesc"], "specs": row["specs"], "categorycode": row["categorycode"],"uomid":row["uomid"],"unitname":unitrow["unitname"],"openingstock":"%.2f"%float(row["openingstock"]),"gsflag":row["gsflag"],"gscode":row["gscode"]}
                if int(row["gsflag"]) != 19: 
                    godownswithstock = self.con.execute(select([func.count(gkdb.goprod.c.productcode).label("numberofgodowns")]).where(gkdb.goprod.c.productcode==self.request.params["productcode"]))
                    godowns = godownswithstock.fetchone()
                    numberofgodowns = godowns["numberofgodowns"]
                    return {"gkstatus":enumdict["Success"],"gkresult":productDetails,"numberofgodowns":"%d"%int(numberofgodowns)}
                else:
                    return {"gkstatus":enumdict["Success"],"gkresult":productDetails}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()


    @view_config(request_method='GET', request_param='by=category',renderer='json')
    def getProductbyCategory(self):
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
                if self.request.params["categorycode"] =="":
                    result = self.con.execute(select([gkdb.product.c.productcode,gkdb.product.c.productdesc]).where(gkdb.product.c.categorycode==None))
                else:
                    result = self.con.execute(select([gkdb.product.c.productcode,gkdb.product.c.productdesc]).where(gkdb.product.c.categorycode==self.request.params["categorycode"]))
                prodlist = []
                for row in result:
                    productDetails={ "productcode":row["productcode"],"productdesc": row["productdesc"]}
                    prodlist.append(productDetails);
                return {"gkstatus":enumdict["Success"],"gkresult":prodlist}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()


    @view_config(request_method='GET', request_param='by=godown',renderer='json')
    def getProductbyGodown(self):
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
                productcode = self.request.params["productcode"]
                result = self.con.execute(select([goprod]).where(goprod.c.productcode == productcode))
                godowns = []
                for row in result:
                    goDownDetails = {"goid":row["goid"], "goopeningstock":"%.2f"%float(row["goopeningstock"]), "productcode":row["productcode"]}
                    godowns.append(goDownDetails)
                return {"gkstatus":enumdict["Success"],"gkresult":godowns}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method='GET', request_param='from=godown',renderer='json')
    def getProductfromGodown(self):
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
                goid = self.request.params["godownid"]
                result = self.con.execute(select([gkdb.goprod.c.goprodid, gkdb.goprod.c.goopeningstock, gkdb.goprod.c.productcode]).where(and_(gkdb.goprod.c.goid== goid, gkdb.goprod.c.orgcode==authDetails["orgcode"])))
                products = []
                for row in result:
                    productDetails = {"goprodid":row["goprodid"], "goopeningstock":"%.2f"%float(row["goopeningstock"]), "productcode":row["productcode"]}
                    products.append(productDetails)
                return {"gkstatus":enumdict["Success"],"gkresult":products}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()


    @view_config(request_method='POST',renderer='json')
    def addProduct(self):
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
                productDetails = dataset["productdetails"]
                godownFlag = dataset["godownflag"]
                productDetails["orgcode"] = authDetails["orgcode"]
                if productDetails.has_key("categorycode")==False:
                    duplicateproduct = self.con.execute(select([func.count(gkdb.product.c.productcode).label("productcount")]).where(and_(gkdb.product.c.productdesc== productDetails["productdesc"],gkdb.product.c.categorycode==None,gkdb.product.c.orgcode==productDetails["orgcode"])))
                    duplicateproductrow = duplicateproduct.fetchone()
                    if duplicateproductrow["productcount"]>0:
                        return {"gkstatus":enumdict["DuplicateEntry"]}
                result = self.con.execute(gkdb.product.insert(),[productDetails])
                spec = productDetails["specs"]
                for sp in spec.keys():
                    self.con.execute("update categoryspecs set productcount = productcount +1 where spcode = %d"%(int(sp)))
                if productDetails.has_key("categorycode")==False:
                    productDetails["categorycode"]=None
                result = self.con.execute(select([gkdb.product.c.productcode]).where(and_(gkdb.product.c.productdesc==productDetails["productdesc"], gkdb.product.c.categorycode==productDetails["categorycode"],gkdb.product.c.orgcode==productDetails["orgcode"])))
                row = result.fetchone()
                productCode = row["productcode"]
                if godownFlag:
                    goDetails = dataset["godetails"]
                    ttlOpening = 0.00
                    for g in goDetails.keys():
                        ttlOpening = ttlOpening + float(goDetails[g])
                        goro = {"productcode":productCode,"goid":g,"goopeningstock":goDetails[g],"orgcode":authDetails["orgcode"]}
                        self.con.execute(goprod.insert(),[goro])
                    self.con.execute(product.update().where(and_(product.c.productcode == productCode,product.c.orgcode==authDetails["orgcode"])).values(openingstock = ttlOpening))

                return {"gkstatus":enumdict["Success"],"gkresult":row["productcode"]}

            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    '''
    Here product data is updated with new data input by the user while editing product.
    If godowns have been created and godownwise opening stock has been entered for a product the record in "goprod" table is first deleted and fresh record is created.
    If godownwise opening stock was not recorded while creating product it can be created here.
    In this case a new record is created in "goprod" table.
    '''
    @view_config(request_method='PUT', renderer='json')
    def editProduct(self):
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
                productDetails = dataset["productdetails"]
                godownFlag = dataset["godownflag"]
                productCode = productDetails["productcode"]
                result = self.con.execute(gkdb.product.update().where(gkdb.product.c.productcode==productDetails["productcode"]).values(productDetails))
                if godownFlag:
                    goDetails = dataset["godetails"]
                    result = self.con.execute(gkdb.goprod.delete().where(and_(gkdb.goprod.c.productcode==productCode,gkdb.goprod.c.orgcode==authDetails["orgcode"])))
                    ttlOpening = 0.0
                    for g in goDetails.keys():
                        ttlOpening = ttlOpening + float(goDetails[g])
                        goro = {"productcode":productCode,"goid":g,"goopeningstock":goDetails[g],"orgcode":authDetails["orgcode"]}
                        self.con.execute(gkdb.goprod.insert(),[goro])
                    self.con.execute(product.update().where(and_(product.c.productcode == productCode,product.c.orgcode==authDetails["orgcode"])).values(openingstock = ttlOpening))

                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method='DELETE', renderer ='json')
    def deleteProduct(self):
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
                result = self.con.execute(select([gkdb.product.c.specs]).where(gkdb.product.c.productcode==dataset["productcode"]))
                row = result.fetchone()
                spec = row["specs"]
                for sp in spec.keys():
                    self.con.execute("update categoryspecs set productcount = productcount -1 where spcode = %d"%(int(sp)))
                result = self.con.execute(gkdb.product.delete().where(gkdb.product.c.productcode==dataset["productcode"]))
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
