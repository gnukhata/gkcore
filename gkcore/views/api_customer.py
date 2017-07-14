
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
"""


from gkcore import eng, enumdict
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
import jwt
import gkcore
from gkcore.views.api_login import authCheck



@view_defaults(route_name='customersupplier')
class api_customer(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection
    @view_config(request_method='POST',renderer='json')
    def addCustomer(self):
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
                result = self.con.execute(gkdb.customerandsupplier.insert(),[dataset])
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
    @view_config(request_param="qty=single", request_method='GET',renderer='json')
    def getCustomerSupplier(self):
        """
        this function returns details on one customer or supplier.
        the request parameter determines that there is only single entity to be returned.
 """
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dataset = self.request.params
                result = self.con.execute(select([gkdb.customerandsupplier]).where(gkdb.customerandsupplier.c.custid == dataset["custid"] ))
                row = result.fetchone()
                Customer = {"custid":row["custid"], "custname":row["custname"], "custaddr":row["custaddr"], "custphone":row["custphone"], "custemail":row["custemail"], "custfax":row["custfax"], "custpan":row["custpan"], "custtan":row["custtan"],"state":row["state"], "custdoc":row["custdoc"], "csflag":row["csflag"],"gstin":row["gstin"] }
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":Customer}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()



    @view_config(request_method='PUT', renderer='json')
    def editCustomerSupplier(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        else:
       #     try:
                self.con = eng.connect()
                dataset = self.request.json_body
                dataset["orgcode"] = authDetails["orgcode"]
                result = self.con.execute(gkdb.customerandsupplier.update().where(gkdb.customerandsupplier.c.custid==dataset["custid"]).values(dataset))
                return {"gkstatus":enumdict["Success"]}
        #    except:
         #       return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
         #   finally:
          #      self.con.close()
    @view_config(request_param="qty=custall", request_method='GET', renderer ='json')
    def getAllCustomers(self):
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
                #there is only one possibility for a catch which is failed connection to db.
                result = self.con.execute(select([gkdb.customerandsupplier.c.custname,gkdb.customerandsupplier.c.custid]).where(and_(gkdb.customerandsupplier.c.orgcode==authDetails["orgcode"],gkdb.customerandsupplier.c.csflag==3)).order_by(gkdb.customerandsupplier.c.custname))
                customers = []
                for row in result:
                    customers.append({"custid":row["custid"], "custname":row["custname"]})
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":customers }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_param="qty=supall", request_method='GET', renderer ='json')
    def getAllSuppliers(self):
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
                #there is only one possibility for a catch which is failed connection to db.
                result = self.con.execute(select([gkdb.customerandsupplier.c.custname,gkdb.customerandsupplier.c.custid]).where(and_(gkdb.customerandsupplier.c.orgcode==authDetails["orgcode"],gkdb.customerandsupplier.c.csflag==19)).order_by(gkdb.customerandsupplier.c.custname))
                suppliers = []
                for row in result:
                    suppliers.append({"custid":row["custid"], "custname":row["custname"]})
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":suppliers }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='DELETE', renderer ='json')
    def deleteCustomer(self):
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
                result = self.con.execute(gkdb.customerandsupplier.delete().where(gkdb.customerandsupplier.c.custid==dataset["custid"]))
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_param="by=account", request_method='GET', renderer ='json')
    def getCustomerSupplieraccount(self):
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
                #there is only one possibility for a catch which is failed connection to db.
                result = self.con.execute(select([gkdb.accounts.c.accountname]).where(and_(gkdb.accounts.c.orgcode==authDetails["orgcode"],gkdb.accounts.c.accountcode==self.request.params["accountcode"])))
                account = result.fetchone()
                accountname = account["accountname"]
                result = self.con.execute(select([gkdb.customerandsupplier.c.custid]).where(and_(gkdb.customerandsupplier.c.orgcode==authDetails["orgcode"],gkdb.customerandsupplier.c.custname==accountname)))
                customer = result.fetchone()
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":customer["custid"] }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
