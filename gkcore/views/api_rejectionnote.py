
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
from gkcore.models.gkdb import rejectionnote, stock, customerandsupplier, goprod
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
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult":result }
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
