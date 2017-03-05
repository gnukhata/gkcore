
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
"Abhijith Balan" <abhijithb21@openmailbox.org>
"""


from gkcore import eng, enumdict
from gkcore.models.gkdb import godown
from gkcore.models.gkdb import stock
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
import jwt
import gkcore
from gkcore.views.api_login import authCheck

@view_defaults(route_name='godown')
class api_godown(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection

    @view_config(request_method='POST',renderer='json')
    def addGodown(self):
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
                result = self.con.execute(godown.insert(),[dataset])
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='PUT', renderer='json')
    def editGodown(self):
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
                result = self.con.execute(godown.update().where(godown.c.goid==dataset["goid"]).values(dataset))
                return {"gkstatus":enumdict["Success"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET', renderer ='json')
    def getAllGodowns(self):
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
                result = self.con.execute(select([godown]).where(godown.c.orgcode==authDetails["orgcode"]).order_by(godown.c.goname))
                godowns = []
                srno=1
                for row in result:
                    godownstock = self.con.execute(select([func.count(stock.c.goid).label("godownstockstatus") ]).where(stock.c.goid==row["goid"]))
                    godownstockcount = godownstock.fetchone()
                    godownstatus = godownstockcount["godownstockstatus"]
                    if godownstatus > 0:
                        status = "Active"
                    else:
                        status = "Inactive"
                    godowns.append({"godownstatus":status, "srno":srno, "goid": row["goid"], "goname": row["goname"], "goaddr": row["goaddr"], "gocontact": row["gocontact"],"state":row["state"],"contactname":row["contactname"],"designation":row["designation"]})
                    srno = srno+1
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":godowns }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_param='qty=single', request_method='GET',renderer='json')
    def getGodown(self):
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
                result = self.con.execute(select([godown]).where(godown.c.goid == self.request.params["goid"]))
                row = result.fetchone()
                godownDetails={"goid": row["goid"], "goname": row["goname"], "goaddr": row["goaddr"], "gocontact": row["gocontact"],"state":row["state"],"contactname":row["contactname"],"designation":row["designation"]}
                self.con.close()
                return {"gkstatus":enumdict["Success"],"gkresult":godownDetails}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method='DELETE', renderer ='json')
    def deleteGodown(self):
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
                result = self.con.execute(godown.delete().where(godown.c.goid==dataset["goid"]))
                return {"gkstatus":enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    @view_config(request_method='GET', request_param='type=lastfivegodown', renderer ='json')
    def lastfivegodata(self):
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
                result = self.con.execute(select([godown]).where(godown.c.orgcode==authDetails["orgcode"]).order_by(godown.c.goid.desc()).limit(5))
                godowns = []
                srno=1
                for row in result:
                    godowns.append({"goname": row["goname"], "goaddr": row["goaddr"], "state":row["state"]})
                    srno = srno+1
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":godowns }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
