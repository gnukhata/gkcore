"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020, 2019 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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
"Mohd. Talha Pawaty" <mtalha456@gmail.com>
"""


from gkcore import eng, enumdict
from gkcore.models.gkdb import godown, usergodown, stock, goprod
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
import jwt
import gkcore
from gkcore.utils import authCheck
from gkcore.views.api_gkuser import getUserRole


def getusergodowns(userid):
    try:
        con = Connection
        con = eng.connect()
        uid = userid
        godowns = con.execute(
            select([godown]).where(
                and_(
                    godown.c.goid.in_(
                        select([usergodown.c.goid]).where(usergodown.c.userid == uid)
                    )
                )
            )
        )
        usergo = []
        srno = 1
        for row in godowns:
            godownstock = con.execute(
                select([func.count(stock.c.goid).label("godownstockstatus")]).where(
                    stock.c.goid == row["goid"]
                )
            )

            godownstockcount = godownstock.fetchone()
            godownstatus = godownstockcount["godownstockstatus"]

            if godownstatus > 0:
                status = "Active"
            else:
                status = "Inactive"

            usergo.append(
                {
                    "godownstatus": status,
                    "srno": srno,
                    "goid": row["goid"],
                    "goname": row["goname"],
                    "goaddr": row["goaddr"],
                    "gocontact": row["gocontact"],
                    "state": row["state"],
                    "contactname": row["contactname"],
                    "designation": row["designation"],
                }
            )

            srno = srno + 1
        return {"gkstatus": gkcore.enumdict["Success"], "gkresult": usergo}
    except:
        return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
    finally:
        con.close()


@view_defaults(route_name="godown")
class api_godown(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    """
    The below function is use to add godown.
    """

    @view_config(request_method="POST", renderer="json")
    def addGodown(self):

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body
                dataset["orgcode"] = authDetails["orgcode"]
                result = self.con.execute(godown.insert(), [dataset])
                godownCreated = self.con.execute(
                    select([godown.c.goid]).where(
                        and_(
                            godown.c.orgcode == authDetails["orgcode"],
                            godown.c.goname == dataset["goname"],
                        )
                    )
                ).fetchone()
                return {"gkstatus": enumdict["Success"], 'gkresult': godownCreated['goid']}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """
    below function is use to update existing godown .
    """

    @view_config(request_method="PUT", renderer="json")
    def editGodown(self):

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body
                result = self.con.execute(
                    godown.update()
                    .where(godown.c.goid == dataset["goid"])
                    .values(dataset)
                )
                return {"gkstatus": enumdict["Success"]}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """
    below function is use to get all godowns.
    """

    @view_config(request_method="GET", renderer="json")
    def getAllGodowns(self):

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                userrole = getUserRole(authDetails["userid"], authDetails["orgcode"])
                gorole = userrole["gkresult"]
                if gorole["userrole"] == 3:
                    try:
                        result = getusergodowns(authDetails["userid"])
                        return {
                            "gkstatus": gkcore.enumdict["Success"],
                            "gkresult": result["gkresult"],
                        }
                    except:
                        return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
                if gorole["userrole"] != 3:
                    result = self.con.execute(
                        select([godown])
                        .where(godown.c.orgcode == authDetails["orgcode"])
                        .order_by(godown.c.goname)
                    )
                    godowns = []
                    srno = 1
                    for row in result:
                        godownstock = self.con.execute(
                            select(
                                [func.count(stock.c.goid).label("godownstockstatus")]
                            ).where(stock.c.goid == row["goid"])
                        )
                        godownstockcount = godownstock.fetchone()
                        godownstatus = godownstockcount["godownstockstatus"]
                        if godownstatus > 0:
                            status = "Active"
                        else:
                            status = "Inactive"

                        godowns.append(
                            {
                                "godownstatus": status,
                                "srno": srno,
                                "goid": row["goid"],
                                "goname": row["goname"],
                                "goaddr": row["goaddr"],
                                "gocontact": row["gocontact"],
                                "state": row["state"],
                                "contactname": row["contactname"],
                                "designation": row["designation"],
                            }
                        )

                        srno = srno + 1
                    return {"gkstatus": gkcore.enumdict["Success"], "gkresult": godowns}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="GET", request_param="type=togodown", renderer="json")
    def togodowns(self):

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(
                    select([godown]).where(godown.c.orgcode == authDetails["orgcode"])
                )
                godowns = []
                for row in result:
                    godowns.append(
                        {
                            "goid": row["goid"],
                            "goname": row["goname"],
                            "goaddr": row["goaddr"],
                        }
                    )
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": godowns}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_param="qty=single", request_method="GET", renderer="json")
    def getGodown(self):

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
                    select([godown]).where(godown.c.goid == self.request.params["goid"])
                )
                row = result.fetchone()
                godownDetails = {
                    "goid": row["goid"],
                    "goname": row["goname"],
                    "goaddr": row["goaddr"],
                    "gocontact": row["gocontact"],
                    "state": row["state"],
                    "contactname": row["contactname"],
                    "designation": row["designation"],
                }
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": godownDetails}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """This function returns all godowns and branch associated with godown in charge.
       It takes user id as a input"""

    @view_config(request_method="GET", request_param="type=byuser", renderer="json")
    def getGodownsByUser(self):

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = getusergodowns(self.request.params["userid"])
                return {
                    "gkstatus": gkcore.enumdict["Success"],
                    "gkresult": result["gkresult"],
                }
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """
    The below function "getNumberOfProductInGodown" will be called when user select a
    godown for deletetion, it will return number of products a selected godown content.
    """

    @view_config(request_method="GET", request_param="type=goproduct", renderer="json")
    def getNumberOfProductInGodown(self):

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
                goid = self.request.params["goid"]
                result = self.con.execute(
                    select([func.count(goprod.c.productcode)]).where(
                        goprod.c.goid == goid
                    )
                )
                row = result.fetchone()
                return {"gkstatus": enumdict["Success"], "gkresult": row[0]}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """
    The below function "getGodownProd" will be called when user select Dispatched From for Transfer Note, it will return Godown Name with Address containing products.
    """

    @view_config(request_method="GET", request_param="value=1", renderer="json")
    def getGodownProd(self):

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
                    select([goprod.c.goid])
                    .distinct()
                    .where(goprod.c.orgcode == authDetails["orgcode"])
                )
                grow = result.fetchall()
                godownList = []
                for g in grow:
                    godownData = self.con.execute(
                        select([godown.c.goid, godown.c.goname, godown.c.goaddr]).where(
                            godown.c.goid == g["goid"]
                        )
                    )
                    row = godownData.fetchone()
                    godownList.append(
                        {
                            "goid": row["goid"],
                            "goname": row["goname"],
                            "goaddr": row["goaddr"],
                        }
                    )
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": godownList}
            except:
                self.con.close()
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="DELETE", renderer="json")
    def deleteGodown(self):

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
                    godown.delete().where(godown.c.goid == dataset["goid"])
                )
                return {"gkstatus": enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(
        request_method="GET", request_param="type=lastfivegodown", renderer="json"
    )
    def lastfivegodata(self):

        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(
                    select([godown])
                    .where(godown.c.orgcode == authDetails["orgcode"])
                    .order_by(godown.c.goid.desc())
                    .limit(5)
                )
                godowns = []
                srno = 1
                for row in result:
                    godowns.append(
                        {
                            "goname": row["goname"],
                            "goaddr": row["goaddr"],
                            "state": row["state"],
                        }
                    )
                    srno = srno + 1
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": godowns}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
