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
  Free Software Foundation, Inc.,51 Franklin Street, 
  Fifth Floor, Boston, MA 02110, United States


Contributors:
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"Prajkta Patkar" <prajakta@dff.org.in>
"""

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc,alias, or_, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.ext.baked import Result
from sqlalchemy.sql.expression import null
from gkcore.models.meta import dbconnect
from gkcore.models.gkdb import accounts
"""
purpose:
This class is the resource to create, update, read and delete accounts.

connection rules:
con is used for executing sql expression language based queries,
while eng is used for raw sql execution.
routing mechanism:
@view_defaults is used for setting the default route for crud on the given resource class.
if specific route is to be attached to a certain method, or for giving get, post, put, delete methods to default route, the view_config decorator is used.
For other predicates view_config is generally used.
"""
"""
default route to be attached to this resource.
refer to the __init__.py of main gkcore package for details on routing url
"""
@view_defaults(route_name='accounts')
class api_account(object):
    #constructor will initialise request.
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection
        print "accounts initialized"

    @view_config(request_method='POST',renderer='json')
    def addAccount(self):
        """
        purpose:
        Adds an account under either a group or it's subgroup.
        Request_method is post which means adding a resource.
        returns a json object containing success result as true if account is created.
        Alchemy expression language will be used for inserting into accounts table.
        The data is fetched from request.json_body.
        Expects accountname,groupsubgroupcode and opening balance.
        Function will only proceed if auth check is successful, because orgcode needed as a common parameter can be procured only through the said method.
        """
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
                result = self.con.execute(gkdb.accounts.insert(),[dataset])
                self.con.close()
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                self.con.close()
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(route_name='account', request_method='GET',renderer='json')
    def getAccount(self):
        """
        Purpose:
        Returns an account given it's account code.
        Returns a json object containing:
        *accountcode
        *accountname
        *openingbal as float
        *groupsubgroupcode
        The request_method is  get meaning retriving data.
        The route_name has been override here to make a special call which does not come under view_default.
        parameter will be taken from request.matchdict in a get request.
        Function will only proceed if auth check is successful, because orgcode needed as a common parameter can be procured only through the said method.
        """
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
                result = self.con.execute(select([gkdb.accounts]).where(gkdb.accounts.c.accountcode==self.request.matchdict["accountcode"]))
                row = result.fetchone()
                acc={"accountcode":row["accountcode"], "accountname":row["accountname"], "openingbal":"%.2f"%float(row["openingbal"]),"groupcode":row["groupcode"]}
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult":acc}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"] }

    @view_config(request_method='GET', renderer ='json')
    def getAllAccounts(self):
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
                result = self.con.execute(select([gkdb.accounts]).where(gkdb.accounts.c.orgcode==authDetails["orgcode"]).order_by(gkdb.accounts.c.accountname))
                accs = []
                srno=1
                for accrow in result:
                    g = gkdb.groupsubgroups.alias("g")
                    sg = gkdb.groupsubgroups.alias("sg")

                    resultset = self.con.execute(select([(g.c.groupcode).label('groupcode'),(g.c.groupname).label('groupname'),(sg.c.groupcode).label('subgroupcode'),(sg.c.groupname).label('subgroupname')]).where(or_(and_(g.c.groupcode==int(accrow["groupcode"]),g.c.subgroupof==null(),sg.c.groupcode==int(accrow["groupcode"]),sg.c.subgroupof==null()),and_(g.c.groupcode==sg.c.subgroupof,sg.c.groupcode==int(accrow["groupcode"])))))
                    grprow = resultset.fetchone()
                    if grprow["groupcode"]==grprow["subgroupcode"]:
                        accs.append({"srno":srno,"accountcode":accrow["accountcode"], "accountname":accrow["accountname"], "openingbal":"%.2f"%float(accrow["openingbal"]),"groupcode":grprow["groupcode"],"groupname":grprow["groupname"],"subgroupcode":"","subgroupname":""})
                    else:
                        accs.append({"srno":srno,"accountcode":accrow["accountcode"], "accountname":accrow["accountname"], "openingbal":"%.2f"%float(accrow["openingbal"]),"groupcode":grprow["groupcode"],"groupname":grprow["groupname"],"subgroupcode":grprow["subgroupcode"],"subgroupname":grprow["subgroupname"]})
                    srno = srno+1
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult":accs}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"] }

    @view_config(request_method='GET',request_param='accbygrp', renderer ='json')
    def getAllAccountsByGroup(self):
        """
        Purpose:
        This function returns accountcode , accountname and openingbalance for a certain groupcode (group) which has been provided.
        """
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
                result = self.con.execute(select([accounts.c.accountcode,accounts.c.accountname,accounts.c.openingbal]).where(and_(accounts.c.orgcode==authDetails["orgcode"],accounts.c.groupcode==self.request.params["groupcode"])))
                accData = result.fetchall()
                allAcc = []
                for row in accData:
                    allAcc.append({"accountcode":row["accountcode"], "accountname":row["accountname"],"openingbal":"%.2f"%float(row["openingbal"])})
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult":allAcc}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"] }


    @view_config(request_method='GET',request_param='acclist', renderer ='json')
    def getAccountslist(self):
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
                accData = self.con.execute(select([accounts.c.accountcode,accounts.c.accountname]).where(accounts.c.orgcode == authDetails["orgcode"]))
                accRows = accData.fetchall()
                accList = {}
                for row in accRows:
                    accList[row["accountname"]]= row["accountcode"]
                    
                return {"gkstatus": enumdict["Success"], "gkresult":accList}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()


    @view_config(request_method='GET',request_param='find=exists', renderer ='json')
    def accountExists(self):
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
                accountname = self.request.params["accountname"]
                result = self.con.execute(select([func.count(gkdb.accounts.c.accountname).label('acc')]).where(and_(gkdb.accounts.c.accountname==accountname,gkdb.accounts.c.orgcode==authDetails["orgcode"])))
                acccount = result.fetchone()
                if acccount["acc"]>0:
                    self.con.close()
                    return {"gkstatus": enumdict["DuplicateEntry"]}
                else:
                    self.con.close()
                    return {"gkstatus": enumdict["Success"]}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"] }

    @view_config(request_method='PUT', renderer='json')
    def editAccount(self):
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
                result = self.con.execute(gkdb.accounts.update().where(gkdb.accounts.c.accountcode==dataset["accountcode"]).values(dataset))
                self.con.close()
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                self.con.close()
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"]}

    @view_config(request_method='DELETE', renderer ='json')
    def deleteAccount(self):
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
                user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
                userRole = user.fetchone()
                dataset = self.request.json_body
                if userRole[0]==-1:
                    vouchercountdata = self.con.execute(select([gkdb.accounts.c.vouchercount]).where(gkdb.accounts.c.accountcode==dataset["accountcode"]))
                    vouchercountrow = vouchercountdata.fetchone()
                    if vouchercountrow["vouchercount"]!=0:
                        self.con.close()
                        return {"gkstatus":enumdict["ActionDisallowed"]}
                    else:
                        result = self.con.execute(gkdb.accounts.delete().where(gkdb.accounts.c.accountcode==dataset["accountcode"]))
                        self.con.close()
                        return {"gkstatus":enumdict["Success"]}
                else:
                    self.con.close()
                    return {"gkstatus":  enumdict["BadPrivilege"]}
            except:
                self.con.close()
                return {"gkstatus":enumdict["ConnectionFailed"] }
