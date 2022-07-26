"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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
from gkcore.models.gkdb import log, users
from sqlalchemy.sql import select
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.view import view_defaults, view_config
from datetime import datetime
import gkcore
from gkcore.views.api_login import authCheck

"""
This class basically does Log maintenance about an organisations
whenever any activity is performed by user it is recorded in log table
Only admin role can access logs
"""


@view_defaults(route_name="log")
class api_log(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    @view_config(request_method="POST", renderer="json")
    def addLog(self):
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
                dataset["userid"] = authDetails["userid"]
                dataset["time"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                result = self.con.execute(log.insert(), [dataset])
                return {"gkstatus": enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}

    @view_config(request_method="PUT", renderer="json")
    def editLog(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        # only admin can edit logs
        if authDetails["userrole"] != -1:
            return {"gkstatus": enumdict["BadPrivilege"]}

        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body
                result = self.con.execute(
                    godown.update()
                    .where(log.c.logid == dataset["logid"])
                    .values(dataset)
                )
                return {"gkstatus": enumdict["Success"]}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", renderer="json")
    def getFullLog(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        # only admin can full logs
        if authDetails["userrole"] != -1:
            return {"gkstatus": enumdict["BadPrivilege"]}

        else:
            try:
                self.con = eng.connect()
                result = self.con.execute(
                    select([log])
                    .where(log.c.orgcode == authDetails["orgcode"])
                    .order_by(log.c.time)
                )
                logdata = []
                for row in result:
                    username = self.con.execute(
                        select([users.c.username]).where(
                            users.c.userid == row["userid"]
                        )
                    )
                    username = username.fetchone()
                    logdata.append(
                        {
                            "logid": row["logid"],
                            "time": datetime.strftime(row["time"], "%d-%m-%Y %H:%M:%S"),
                            "activity": row["activity"],
                            "userid": row["userid"],
                            "username": username["username"],
                        }
                    )
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": logdata}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}

    @view_config(request_param="qty=single", request_method="GET", renderer="json")
    def getLog(self):
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
                    select([log]).where(log.c.logid == self.request.params["logid"])
                )
                row = result.fetchone()
                username = self.con.execute(
                    select([users.c.username]).where(users.c.userid == row["userid"])
                )
                username = username.fetchone()
                logdata = {
                    "logid": row["logid"],
                    "time": datetime.strftime(row["time"], "%d-%m-%Y %H:%M:%S"),
                    "activity": row["activity"],
                    "userid": row["userid"],
                    "username": username["username"],
                }
                self.con.close()
                return {"gkstatus": enumdict["Success"], "gkresult": logdata}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_param="type=byuser", request_method="GET", renderer="json")
    def getLogbyUser(self):
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
                    select([log]).where(
                        and_(
                            log.c.userid == self.request.params["userid"],
                            log.c.orgcode == authDetails["orgcode"],
                        )
                    )
                )
                logdata = []
                for row in result:
                    logdata.append(
                        {
                            "logid": row["logid"],
                            "time": datetime.strftime(row["time"], "%d-%m-%Y %H:%M:%S"),
                            "activity": row["activity"],
                        }
                    )
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": logdata}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="DELETE", renderer="json")
    def deleteLog(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        # only admin can delete logs
        if authDetails["userrole"] != -1:
            return {"gkstatus": enumdict["BadPrivilege"]}

        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body
                result = self.con.execute(
                    log.delete().where(log.c.logid == dataset["logid"])
                )
                return {"gkstatus": enumdict["Success"]}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="range", renderer="json")
    def logs_in_date_range(self):
        """Get logs in given date range, Only admin can access logs

        *params:*\
        `from`= "yyyy-mm-dd"\
        `to` = "yyyy-mm-dd"
        """
        # check auth part
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        authDetails = authCheck(token)

        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        # only admin can access logs
        if authDetails["userrole"] != -1:
            return {"gkstatus": enumdict["BadPrivilege"]}
        else:
            # get columns in the given date range
            self.con = eng.connect()
            try:
                dataset = self.request.params
                result = self.con.execute(
                    log.select()
                    .where(log.c.time >= dataset["from"])
                    .where(log.c.time <= dataset["to"])
                    .where(log.c.orgcode == authDetails["orgcode"])
                )
                log_data = []
                # loop through the columns
                for row in result:
                    # derive username from userid
                    user = self.con.execute(
                        select([users.c.username]).where(
                            users.c.userid == row["userid"]
                        )
                    ).fetchone()
                    # append them to log_data array
                    log_data.append(
                        {
                            "logid": row["logid"],
                            "time": datetime.strftime(row["time"], "%d-%m-%Y %H:%M:%S"),
                            "activity": row["activity"],
                            "userid": row["userid"],
                            "username": user["username"],
                        }
                    )
                return {"gkstatus": enumdict["Success"], "gkresult": log_data}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
