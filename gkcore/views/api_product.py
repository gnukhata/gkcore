"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020,2019 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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


from pyramid.view import view_defaults, view_config
from gkcore.utils import authCheck, gk_log
from gkcore.views.api_tax import calTax
from gkcore import eng, enumdict
from gkcore.models import gkdb
from sqlalchemy.sql import select
from sqlalchemy import func
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, func
from gkcore.models.gkdb import goprod, product, accounts
from gkcore.views.api_gkuser import getUserRole
from gkcore.views.api_godown import getusergodowns
from datetime import datetime
import traceback


@view_defaults(route_name="product")
class api_product(object):
    def __init__(self, request):
        self.request = request
        self.con = Connection

    @view_config(request_method="GET", renderer="json")
    def getAllProducts(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        with eng.connect() as con:
            userrole = getUserRole(authDetails["userid"], authDetails["orgcode"])
            gorole = userrole["gkresult"]
            if gorole["userrole"] == 3:
                uId = getusergodowns(authDetails["userid"])
                gid = []
                for record1 in uId["gkresult"]:
                    gid.append(record1["goid"])
                productCodes = []
                for record2 in gid:
                    proCode = con.execute(
                        select([gkdb.goprod.c.productcode]).where(
                            gkdb.goprod.c.goid == record2
                        )
                    )
                    proCodes = proCode.fetchall()
                    for record3 in proCodes:
                        if record3["productcode"] not in productCodes:
                            productCodes.append(record3["productcode"])
                results = []
                for record4 in productCodes:
                    result = con.execute(
                        select(
                            [
                                gkdb.product.c.productcode,
                                gkdb.product.c.productdesc,
                                gkdb.product.c.categorycode,
                                gkdb.product.c.uomid,
                                gkdb.product.c.gsflag,
                                gkdb.product.c.prodsp,
                                gkdb.product.c.prodmrp,
                            ]
                        )
                        .where(
                            and_(
                                gkdb.product.c.orgcode == authDetails["orgcode"],
                                gkdb.product.c.productcode == record4,
                            )
                        )
                        .order_by(gkdb.product.c.productdesc)
                    )
                    products = result.fetchone()
                    results.append(products)
            else:
                invdc = 9
                try:
                    invdc = int(self.request.params["invdc"])
                except:
                    invdc = 9
                if invdc == 4:
                    results = con.execute(
                        select(
                            [
                                gkdb.product.c.productcode,
                                gkdb.product.c.gsflag,
                                gkdb.product.c.productdesc,
                                gkdb.product.c.categorycode,
                                gkdb.product.c.uomid,
                                gkdb.product.c.prodsp,
                                gkdb.product.c.prodmrp,
                            ]
                        )
                        .where(
                            and_(
                                gkdb.product.c.orgcode == authDetails["orgcode"],
                                gkdb.product.c.gsflag == 7,
                            )
                        )
                        .order_by(gkdb.product.c.productdesc)
                    )
                if invdc == 9:
                    results = con.execute(
                        select(
                            [
                                gkdb.product.c.productcode,
                                gkdb.product.c.productdesc,
                                gkdb.product.c.gsflag,
                                gkdb.product.c.categorycode,
                                gkdb.product.c.uomid,
                                gkdb.product.c.prodsp,
                                gkdb.product.c.prodmrp,
                            ]
                        )
                        .where(gkdb.product.c.orgcode == authDetails["orgcode"])
                        .order_by(gkdb.product.c.productdesc)
                    )

            products = []
            srno = 1
            for row in results:
                unitsofmeasurement = con.execute(
                    select([gkdb.unitofmeasurement.c.unitname]).where(
                        gkdb.unitofmeasurement.c.uomid == row["uomid"]
                    )
                )
                unitofmeasurement = unitsofmeasurement.fetchone()
                if unitofmeasurement != None:
                    unitname = unitofmeasurement["unitname"]
                else:
                    unitname = ""
                if row["categorycode"] != None:
                    categories = con.execute(
                        select([gkdb.categorysubcategories.c.categoryname]).where(
                            gkdb.categorysubcategories.c.categorycode
                            == row["categorycode"]
                        )
                    )
                    category = categories.fetchone()
                    categoryname = category["categoryname"]
                else:
                    categoryname = ""
                if row["productcode"] != None:
                    openingStockResult = con.execute(
                        select([gkdb.product.c.openingstock]).where(
                            gkdb.product.c.productcode == row["productcode"]
                        )
                    )
                    osRow = openingStockResult.fetchone()
                    openingStock = osRow["openingstock"]
                    productstockin = con.execute(
                        select(
                            [func.sum(gkdb.stock.c.qty).label("sumofins")]
                        ).where(
                            and_(
                                gkdb.stock.c.productcode == row["productcode"],
                                gkdb.stock.c.inout == 9,
                            )
                        )
                    )
                    stockinsum = productstockin.fetchone()
                    if stockinsum["sumofins"] != None:
                        openingStock = openingStock + stockinsum["sumofins"]
                    productstockout = con.execute(
                        select(
                            [func.sum(gkdb.stock.c.qty).label("sumofouts")]
                        ).where(
                            and_(
                                gkdb.stock.c.productcode == row["productcode"],
                                gkdb.stock.c.inout == 15,
                            )
                        )
                    )
                    stockoutsum = productstockout.fetchone()
                    if stockoutsum["sumofouts"] != None:
                        openingStock = openingStock - stockoutsum["sumofouts"]
                products.append(
                    {
                        "srno": srno,
                        "unitname": unitname,
                        "categoryname": categoryname,
                        "productcode": row["productcode"],
                        "productdesc": row["productdesc"],
                        "categorycode": row["categorycode"],
                        "productquantity": "%.2f" % float(openingStock),
                        "gsflag": row["gsflag"],
                    }
                )
                srno = srno + 1
            return {"gkstatus": enumdict["Success"], "gkresult": products}


    @view_config(request_method="POST", renderer="json")
    def addProduct(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            self.con = eng.connect()
            try:
                gk_log(__name__).warn("prod")
                dataset = self.request.json_body
                productDetails = dataset["productdetails"]
                godownFlag = dataset["godownflag"]
                productDetails["orgcode"] = authDetails["orgcode"]
                duplicateproduct = self.con.execute(
                    select(
                        [
                            func.count(gkdb.product.c.productcode).label(
                                "productcount"
                            )
                        ]
                    ).where(
                        and_(
                            gkdb.product.c.productdesc
                            == productDetails["productdesc"],
                            gkdb.product.c.categorycode == None,
                            gkdb.product.c.orgcode == productDetails["orgcode"],
                        )
                    )
                )
                duplicateproductrow = duplicateproduct.fetchone()
                if duplicateproductrow["productcount"] > 0:
                    return {"gkstatus": enumdict["DuplicateEntry"]}

                # handle exception if db insertion fails for product
                try:
                    result = self.con.execute(gkdb.product.insert(), [productDetails])
                except Exception as e:
                    gk_log(__name__).error(e)
                    return {"gkstatus": enumdict["ConnectionFailed"], "error": f"{e}"}

                spec = productDetails["specs"]
                for sp in list(spec.keys()):
                    self.con.execute(
                        "update categoryspecs set productcount = productcount +1 where spcode = %d"
                        % (int(sp))
                    )

                if ("categorycode" in productDetails) == False:
                    productDetails["categorycode"] = None
                result = self.con.execute(
                    select([gkdb.product.c.productcode]).where(
                        and_(
                            gkdb.product.c.productdesc == productDetails["productdesc"],
                            gkdb.product.c.categorycode
                            == productDetails["categorycode"],
                            gkdb.product.c.orgcode == productDetails["orgcode"],
                        )
                    )
                )
                row = result.fetchone()
                productCode = row["productcode"]
                # create godown only if godown flag is true and is product
                if godownFlag and productDetails["gsflag"] == 7:
                    goDetails = dataset["godetails"]
                    # insert godown stock into goprod table & calculate opening stock
                    ttlOpening = 0.00
                    # loop over all godowns stock entries
                    for goId in list(goDetails.keys()):
                        goDetail = goDetails[goId]
                        if type(goDetail) != dict:
                            goDetail = {"qty": goDetail, "rate": 0}
                        # calculate the opening stock
                        # ttlOpening = ttlOpening + float(goDetail["qty"])
                        ttlOpening += float(goDetail["qty"])
                        goro = {
                            "productcode": productCode,
                            "goid": goId,
                            "goopeningstock": goDetail["qty"],
                            "openingstockvalue": goDetail["rate"],
                            "orgcode": authDetails["orgcode"],
                        }
                        try:
                            self.con.execute(goprod.insert(), [goro])
                        except Exception as e:
                            return {
                                "gkstatus": enumdict["ConnectionFailed"],
                                "error": str(e),
                            }
                    # update opening stock value
                    self.con.execute(
                        product.update()
                        .where(
                            and_(
                                product.c.productcode == productCode,
                                product.c.orgcode == authDetails["orgcode"],
                            )
                        )
                        .values(openingstock=ttlOpening)
                    )

                # We need to create sale and purchase accounts for product under sales and purchase groups respectively.
                sp = self.con.execute(
                    "select groupcode from groupsubgroups where groupname in ('%s','%s') and orgcode = %d"
                    % ("Sales", "Purchase", productDetails["orgcode"])
                )
                s = sp.fetchall()
                prodName = productDetails["productdesc"]
                proSale = prodName + " Sale"
                proPurch = prodName + " Purchase"
                self.con.execute(
                    gkdb.accounts.insert(),
                    [
                        {
                            "accountname": proPurch,
                            "groupcode": s[0][0],
                            "orgcode": authDetails["orgcode"],
                            "sysaccount": 1,
                        },
                        {
                            "accountname": proSale,
                            "groupcode": s[1][0],
                            "orgcode": authDetails["orgcode"],
                            "sysaccount": 1,
                        },
                    ],
                )

                return {"gkstatus": enumdict["Success"], "gkresult": row["productcode"]}

            except exc.IntegrityError:
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except Exception as e:
                gk_log(__name__).error("prod err", e)
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """
    Here product data is updated with new data input by the user while editing product.
    If godowns have been created and godownwise opening stock has been entered for a product the record in "goprod" table is first deleted and fresh record is created.
    If godownwise opening stock was not recorded while creating product it can be created here.
    In this case a new record is created in "goprod" table.
    """

    @view_config(
        request_method="PUT", route_name="product_productcode", renderer="json"
    )
    def editProduct(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body
                productCode = self.request.matchdict["productcode"]
                productDetails = dataset["productdetails"]

                godownFlag = dataset["godownflag"]
                pn = self.con.execute(
                    select([gkdb.product.c.productdesc]).where(
                        gkdb.product.c.productcode == productCode
                    )
                )
                prodName = pn.fetchone()
                self.con.execute(
                    gkdb.product.update()
                    .where(gkdb.product.c.productcode == productCode)
                    .values(productDetails)
                )
                if godownFlag:
                    goDetails = dataset["godetails"]
                    result = self.con.execute(
                        gkdb.goprod.delete().where(
                            and_(
                                gkdb.goprod.c.productcode == productCode,
                                gkdb.goprod.c.orgcode == authDetails["orgcode"],
                            )
                        )
                    )
                    ttlOpening = 0.0
                    for goId in list(goDetails.keys()):
                        goDetail = goDetails[goId]
                        if type(goDetail) != dict:
                            goDetail = {"qty": goDetail, "rate": 0}
                        ttlOpening = ttlOpening + float(goDetail["qty"])
                        goro = {
                            "productcode": productCode,
                            "goid": goId,
                            "goopeningstock": goDetail["qty"],
                            "openingstockvalue": goDetail["rate"],
                            "orgcode": authDetails["orgcode"],
                        }
                        self.con.execute(gkdb.goprod.insert(), [goro])
                    self.con.execute(
                        product.update()
                        .where(
                            and_(
                                product.c.productcode == productCode,
                                product.c.orgcode == authDetails["orgcode"],
                            )
                        )
                        .values(openingstock=ttlOpening)
                    )
                # We need to update accountname also.
                pnSL = str(prodName["productdesc"]) + " Sale"
                newpnSL = str(productDetails["productdesc"]) + " Sale"
                pnPurch = str(prodName["productdesc"]) + " Purchase"
                newpnPH = str(productDetails["productdesc"]) + " Purchase"
                self.con.execute(
                    accounts.update()
                    .where(
                        and_(
                            accounts.c.accountname == pnSL,
                            accounts.c.orgcode == authDetails["orgcode"],
                        )
                    )
                    .values(accountname=newpnSL)
                )
                self.con.execute(
                    accounts.update()
                    .where(
                        and_(
                            accounts.c.accountname == pnPurch,
                            accounts.c.orgcode == authDetails["orgcode"],
                        )
                    )
                    .values(accountname=newpnPH)
                )
                return {"gkstatus": enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except Exception as e:
                gk_log(__name__).warn(e)
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(
        request_method="DELETE", route_name="product_productcode", renderer="json"
    )
    def deleteProduct(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body
                result = self.con.execute(
                    select([gkdb.product.c.specs, gkdb.product.c.productdesc]).where(
                        gkdb.product.c.productcode == dataset["productcode"]
                    )
                )
                row = result.fetchone()
                spec = row["specs"]
                pn = row["productdesc"]
                for sp in list(spec.keys()):
                    self.con.execute(
                        "update categoryspecs set productcount = productcount -1 where spcode = %d"
                        % (int(sp))
                    )

                result = self.con.execute(
                    gkdb.product.delete().where(
                        gkdb.product.c.productcode == dataset["productcode"]
                    )
                )
                try:
                    self.con.execute(
                        accounts.delete().where(
                            and_(
                                accounts.c.accountname.like(pn + "%"),
                                accounts.c.orgcode == authDetails["orgcode"],
                            )
                        )
                    )
                except:
                    pass
                return {"gkstatus": enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    # request_param="qty=single",
    @view_config(
        route_name="product_productcode", request_method="GET", renderer="json"
    )
    def getProduct(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                productCode = self.request.matchdict["productcode"]
                result = self.con.execute(
                    select([gkdb.product]).where(
                        gkdb.product.c.productcode == productCode
                    )
                )
                row = result.fetchone()
                productDetails = {
                    "discountpercent": "%.2f" % float(row["percentdiscount"]),
                    "discountamount": "%.2f" % float(row["amountdiscount"]),
                    "productcode": row["productcode"],
                    "productdesc": row["productdesc"],
                    "gsflag": row["gsflag"],
                    "gscode": row["gscode"],
                }

                # the field deletable is for check whether product/service are in use or not
                # first it check that product/service are use in stock table and purchaseorder table and then give count of product/service are in use
                # if count is grater than 0 it send 1 else it send 0 as value of deletable key
                if int(row["gsflag"]) == 19:
                    prod_countinv = self.con.execute(
                        "SELECT (contents ::json)->'%s' is NULL FROM invoice where orgcode ='%d'"
                        % (
                            (str(productCode)),
                            (int(authDetails["orgcode"])),
                        )
                    ).fetchall()
                    if (False,) in prod_countinv:
                        productDetails["deletable"] = 1
                    else:
                        prod_purch = self.con.execute(
                            "SELECT (schedule ::json)->'%s' is NULL FROM purchaseorder where orgcode ='%d'"
                            % (
                                (str(productCode)),
                                (int(authDetails["orgcode"])),
                            )
                        ).fetchall()
                        if (False,) in prod_purch:
                            productDetails["deletable"] = 1

                if row["prodsp"] != None:
                    productDetails["prodsp"] = "%.2f" % float(row["prodsp"])
                else:
                    productDetails["prodsp"] = "%.2f" % 0.00
                if row["prodmrp"] != None:
                    productDetails["prodmrp"] = "%.2f" % float(row["prodmrp"])
                else:
                    productDetails["prodmrp"] = "%.2f" % 0.00
                if int(row["gsflag"]) == 7:
                    prod_countinstock = self.con.execute(
                        "select count(productcode) as pccount from stock where productcode='%s' and orgcode='%d'"
                        % (
                            (str(productCode)),
                            (int(authDetails["orgcode"])),
                        )
                    )
                    pc_countinstock = prod_countinstock.fetchone()

                    if pc_countinstock["pccount"] > 0:
                        productDetails["deletable"] = 1

                    else:
                        prod_countinpuchaseorder = self.con.execute(
                            "select count(purchaseorder.schedule) as pccount from purchaseorder where purchaseorder.schedule?'%s'and orgcode='%d'"
                            % (
                                (str(productCode)),
                                (int(authDetails["orgcode"])),
                            )
                        )
                        pc_countinpuchaseorder = prod_countinpuchaseorder.fetchone()
                        if pc_countinpuchaseorder["pccount"] > 0:
                            productDetails["deletable"] = 1
                        else:
                            productDetails["deletable"] = 0
                    result1 = self.con.execute(
                        select([gkdb.unitofmeasurement.c.unitname]).where(
                            gkdb.unitofmeasurement.c.uomid == row["uomid"]
                        )
                    )
                    unitrow = result1.fetchone()
                    productDetails["specs"] = row["specs"]
                    productDetails["categorycode"] = row["categorycode"]
                    productDetails["uomid"] = row["uomid"]
                    productDetails["gsflag"] = row["gsflag"]
                    productDetails["unitname"] = unitrow["unitname"]
                    productDetails["openingstock"] = "%.2f" % float(row["openingstock"])
                    userrole = getUserRole(
                        authDetails["userid"], authDetails["orgcode"]
                    )
                    if int(userrole["gkresult"]["userrole"]) != 3:
                        godownswithstock = self.con.execute(
                            select(
                                [
                                    func.count(gkdb.goprod.c.productcode).label(
                                        "numberofgodowns"
                                    )
                                ]
                            ).where(gkdb.goprod.c.productcode == productCode)
                        )
                        godowns = godownswithstock.fetchone()
                        numberofgodowns = godowns["numberofgodowns"]
                    else:
                        usergodowmns = getusergodowns(authDetails["userid"])
                        numberofgodowns = 0
                        for usergodown in usergodowmns["gkresult"]:
                            godownswithstock = self.con.execute(
                                select([gkdb.goprod.c.goid]).where(
                                    and_(
                                        gkdb.goprod.c.productcode == productCode,
                                        gkdb.goprod.c.goid == usergodown["goid"],
                                    )
                                )
                            )
                            usergodownwithstock = godownswithstock.fetchone()
                            try:
                                if usergodownwithstock["goid"]:
                                    numberofgodowns = numberofgodowns + 1
                            except:
                                continue
                    return {
                        "gkstatus": enumdict["Success"],
                        "gkresult": productDetails,
                        "numberofgodowns": "%d" % int(numberofgodowns),
                    }
                else:
                    return {"gkstatus": enumdict["Success"], "gkresult": productDetails}

            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    # request_param="type=pt",
    @view_config(request_method="GET", route_name="product_tax", renderer="json")
    def getTaxForProduct(self):
        """
        Purpose: returns either VAT or GST for a selected product based on product code and state.
        description:
        This function takes productcode,source and destination states,
        (called source and destination as params).
        Also takes taxflag.
        The function makes calld to the global function calTax found in api_tax.
        Will return a dictionary containing the tax name and rate.
        Please refer calTax in api_tax for details.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                return calTax(
                    int(self.request.params["taxflag"]),
                    self.request.params["source"],
                    self.request.params["destination"],
                    int(self.request.params["productcode"]),
                    self.con,
                )

            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    # request_param="by=category",
    @view_config(request_method="GET", route_name="product_category", renderer="json")
    def getProductbyCategory(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                categoryCode = self.request.matchdict["categorycode"]
                if categoryCode == "":
                    result = self.con.execute(
                        select(
                            [gkdb.product.c.productcode, gkdb.product.c.productdesc]
                        ).where(gkdb.product.c.categorycode == None)
                    )
                else:
                    result = self.con.execute(
                        select(
                            [gkdb.product.c.productcode, gkdb.product.c.productdesc]
                        ).where(gkdb.product.c.categorycode == categoryCode)
                    )
                prodlist = []
                for row in result:
                    productDetails = {
                        "productcode": row["productcode"],
                        "productdesc": row["productdesc"],
                    }
                    prodlist.append(productDetails)
                return {"gkstatus": enumdict["Success"], "gkresult": prodlist}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    # , request_param="by=godown"
    @view_config(request_method="GET", route_name="godown_product", renderer="json")
    def getProductbyGodown(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                productcode = self.request.matchdict["productcode"]
                userrole = getUserRole(authDetails["userid"], authDetails["orgcode"])
                if int(userrole["gkresult"]["userrole"]) != 3:
                    result = self.con.execute(
                        select([goprod]).where(goprod.c.productcode == productcode)
                    )
                    godowns = []
                    for row in result:
                        goDownDetails = {
                            "goid": row["goid"],
                            "goopeningstock": "%.2f" % float(row["goopeningstock"]),
                            "openingstockvalue": "%.2f"
                            % float(row["openingstockvalue"]),
                            "productcode": row["productcode"],
                        }
                        godowns.append(goDownDetails)
                else:
                    usergodowns = getusergodowns(authDetails["userid"])
                    godowns = []
                    for usergodown in usergodowns["gkresult"]:
                        thisgodown = self.con.execute(
                            select([goprod]).where(
                                and_(
                                    goprod.c.productcode == productcode,
                                    goprod.c.goid == usergodown["goid"],
                                )
                            )
                        )
                        thisgodown = thisgodown.fetchone()
                        try:
                            goDownDetails = {
                                "goid": thisgodown["goid"],
                                "goopeningstock": "%.2f"
                                % float(thisgodown["goopeningstock"]),
                                "productcode": thisgodown["productcode"],
                            }
                            godowns.append(goDownDetails)
                        except:
                            continue
                return {"gkstatus": enumdict["Success"], "gkresult": godowns}
            except:
                print(traceback.format_exc())
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="GET", route_name="product_godown", renderer="json")
    def getProductfromGodown(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                goid = self.request.matchdict["godownid"]
                result = self.con.execute(
                    select(
                        [
                            gkdb.goprod.c.goprodid,
                            gkdb.goprod.c.goopeningstock,
                            gkdb.goprod.c.productcode,
                        ]
                    ).where(
                        and_(
                            gkdb.goprod.c.goid == goid,
                            gkdb.goprod.c.orgcode == authDetails["orgcode"],
                        )
                    )
                )
                products = []
                for row in result:
                    productDetails = {
                        "goprodid": row["goprodid"],
                        "goopeningstock": "%.2f" % float(row["goopeningstock"]),
                        "productcode": row["productcode"],
                    }
                    products.append(productDetails)
                return {"gkstatus": enumdict["Success"], "gkresult": products}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    # request_param="tax=vatorgst",
    @view_config(request_method="GET", route_name="product_check_gst", renderer="json")
    def getvatorgst(self):
        """
        Purpose:
        To determine what kind of tax will be applible to the goods of corresponding organisation.
        Description:
        This function uses orgcode of organisation and will fetch it's financialStart and financialEnddate.
        gstdate as "01/07/2017" is used which is compared with financialStart and financialEnd based on this gstorvatflag changes as following:
        gstorvatflag=7 (means GST is applible)
        gstorvatflag=22 (means VAT is applible)
        gstorvatflag=29 (GST and VAT are applible)
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(
                    select(
                        [gkdb.organisation.c.yearstart, gkdb.organisation.c.yearend]
                    ).where(gkdb.organisation.c.orgcode == authDetails["orgcode"])
                )
                yearstartandend = result.fetchone()
                gstorvatflag = 29
                date1 = "2017-07-01"
                gstdate = datetime.strptime(date1, "%Y-%m-%d")
                financialStart = datetime.strptime(
                    str(yearstartandend["yearstart"]), "%Y-%m-%d"
                )
                financialEnd = datetime.strptime(
                    str(yearstartandend["yearend"]), "%Y-%m-%d"
                )

                if gstdate > financialStart and gstdate > financialEnd:
                    gstorvatflag = 22
                elif gstdate > financialStart and gstdate <= financialEnd:
                    gstorvatflag = 29
                elif gstdate <= financialStart and gstdate <= financialEnd:
                    gstorvatflag = 7
                return {"gkstatus": enumdict["Success"], "gkresult": str(gstorvatflag)}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """
    A godown keeper can only access the list of products that are present in the godowns assigned to him.
    This function lets a godown keeper access the list of all products in an organisation.
    Also, godown incharge cannot access products which are already having openingStock for particular godown which is selected.
    """

    @view_config(request_method="GET", request_param="list=allprod", renderer="json")
    def getAllProdList(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                currentgoid = int(self.request.params["goid"])
                userrole = getUserRole(authDetails["userid"], authDetails["orgcode"])
                gorole = userrole["gkresult"]
                if gorole["userrole"] == 3:
                    uId = getusergodowns(authDetails["userid"])
                    gid = []
                    for record1 in uId["gkresult"]:
                        gid.append(record1["goid"])
                    if currentgoid in gid:
                        proCode = self.con.execute(
                            select([gkdb.goprod.c.productcode]).where(
                                gkdb.goprod.c.goid == currentgoid
                            )
                        )
                        proCodes = proCode.fetchall()
                    productCodes = []
                    for record3 in proCodes:
                        if record3["productcode"] not in productCodes:
                            productCodes.append(record3["productcode"])
                    results = self.con.execute(
                        select([gkdb.product.c.productcode, gkdb.product.c.productdesc])
                        .where(
                            and_(
                                gkdb.product.c.orgcode == authDetails["orgcode"],
                                gkdb.product.c.gsflag == 7,
                            )
                        )
                        .order_by(gkdb.product.c.productdesc)
                    )
                    products = []
                    for row in results:
                        if row["productcode"] not in productCodes:
                            products.append(
                                {
                                    "productcode": row["productcode"],
                                    "productdesc": row["productdesc"],
                                }
                            )

                    return {"gkstatus": enumdict["Success"], "gkresult": products}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="GET", route_name="product_hsn", renderer="json")
    def gethsnuom(self):
        """
        This function is written for fetching the HSN code, UOM automatically when product is selected.
        Services do not have an UOM
        """
        try:
            token = self.request.headers["gktoken"]
        except Exception as e:
            return {"gkstatus": enumdict["UnauthorisedAccess"], "gkresult": str(e)}
        try:
            url_params = self.request.params
        except Exception as e:
            return {
                "gkstatus": enumdict["ConnectionFailed"],
                "gkresult": f"productcode is required: {e}",
            }
        authDetails = authCheck(token)
        if authDetails["auth"] is False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            self.con = eng.connect()
            try:
                # fetch a product matching the given productcode
                product = self.con.execute(
                    select(
                        [
                            gkdb.product.c.uomid,
                            gkdb.product.c.gscode,
                        ]
                    ).where(
                        and_(
                            gkdb.product.c.productcode == url_params["productcode"],
                            gkdb.product.c.orgcode == authDetails["orgcode"],
                            gkdb.product.c.gsflag == 7,
                        )
                    )
                ).fetchone()
                # only products have an uomid
                if product is not None:
                    uom = self.con.execute(
                        select([gkdb.unitofmeasurement.c.unitname]).where(
                            gkdb.unitofmeasurement.c.uomid == product["uomid"]
                        )
                    )
                    unitname = uom.fetchone()
                    productDetails = {
                        "unitname": unitname["unitname"],
                        "gscode": product["gscode"],
                    }
                    return {"gkstatus": enumdict["Success"], "gkresult": productDetails}
                else:
                    # return error when the item is a service
                    return {
                        "gkstatus": enumdict["ActionDisallowed"],
                        "gkresult": "Not a Product",
                    }
            except Exception as e:
                gk_log(__name__).error(e)
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    # request_param="type=addstock",
    @view_config(request_method="POST", route_name="product_stock", renderer="json")
    def addstock(self):
        """
        This is a function for saving opening stock for the selected product
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body
                orgcode = authDetails["orgcode"]
                goid = dataset["goid"]
                productDetails = dataset["productdetails"]
                for product in productDetails:
                    details = {
                        "goid": goid,
                        "goopeningstock": productDetails[product],
                        "productcode": product,
                        "orgcode": orgcode,
                    }
                    result = self.con.execute(gkdb.goprod.insert(), [details])
                return {"gkstatus": enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """
    This funtion returns the last price for which a product was sold/purchased to/from a party.
    To find out the price the function needs productcode of the product, custid of the party and inoutflag(to determine whether selling/purchase price is needed)
    A select query first fetches the invid of the last sale/purchase invoice created for the party involving the product.
    Another query retrives the contents of the invoice whose invid is same as the result of the above query.
    Price is found out from the contents using productcode as key and sent as response.
    """

    # request_param="type=lastprice",
    @view_config(route_name="product_lastprice", request_method="GET", renderer="json")
    def lastPrice(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                lastPriceData = self.con.execute(
                    select([gkdb.cslastprice.c.lastprice]).where(
                        and_(
                            gkdb.cslastprice.c.custid
                            == int(self.request.params["custid"]),
                            gkdb.cslastprice.c.productcode
                            == int(self.request.params["productcode"]),
                            gkdb.cslastprice.c.inoutflag
                            == int(self.request.params["inoutflag"]),
                            gkdb.cslastprice.c.orgcode == int(authDetails["orgcode"]),
                        )
                    )
                )
                lastPriceValue = lastPriceData.fetchone()["lastprice"]
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": "%.2f" % float(lastPriceValue),
                }
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
