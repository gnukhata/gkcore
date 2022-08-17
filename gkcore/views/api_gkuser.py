from gkcore import eng, enumdict
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
import jwt
import gkcore
from gkcore.models.meta import (
    tableExists,
)
from gkcore.views.api_login import authCheck, userAuthCheck, generateAuthToken
from datetime import datetime
import traceback


def getUserRole(userid, orgcode):
    try:
        con = Connection
        con = eng.connect()
        uid = userid
        roleQuery = self.con.execute(
            "select u.orgs#>'{%s,userrole}' as userrole from gkusers u where userid = %d;"
            % (str(orgcode), userid)
        )
        if roleQuery.rowcount == 1:
            row = roleQuery.fetchone()
            User = {"userrole": row["userrole"]}
            return {"gkstatus": gkcore.enumdict["Success"], "gkresult": User}
        else:
            return {
                "gkstatus": gkcore.enumdict["ConnectionFailed"],
                "gkmessage": "User may not be part of the Org. Contact admin",
            }
    except:
        return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
    finally:
        con.close()


@view_defaults(route_name="gkusers")
class api_gkuser(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    """
    - Check if the user is logged in using their old username and password
    - If yes,
      - rename their user in the new table
      - generate an new auth token
    - Else
      - send bad privilege
    """

    @view_config(request_method="POST", renderer="json")
    def addUser(self):
        """
        purpose
        adds a user in the users table.
        description:
        this function  takes username and role as basic parameters.
        It may also have a list of goids for the godowns associated with this user.
        This is only true if goflag is True.
        The frontend must send the role as godownkeeper for this."""
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
                user = self.con.execute(
                    select([gkdb.users.c.userrole]).where(
                        gkdb.users.c.userid == authDetails["userid"]
                    )
                )
                userRole = user.fetchone()
                dataset = self.request.json_body
                if userRole[0] == -1 or (userRole[0] == 0 and dataset["userrole"] == 1):
                    dataset["orgcode"] = authDetails["orgcode"]
                    # golist is present when godown / branch are assign
                    if "golist" in dataset:
                        golist = tuple(dataset.pop("golist"))
                        result = self.con.execute(gkdb.users.insert(), [dataset])
                        userdata = self.con.execute(
                            select([gkdb.users.c.userid]).where(
                                and_(
                                    gkdb.users.c.username == dataset["username"],
                                    gkdb.users.c.orgcode == dataset["orgcode"],
                                )
                            )
                        )
                        userRow = userdata.fetchone()
                        lastid = userRow["userid"]
                        for goid in golist:
                            godata = {
                                "userid": lastid,
                                "goid": goid,
                                "orgcode": dataset["orgcode"],
                            }
                            result = self.con.execute(
                                gkdb.usergodown.insert(), [godata]
                            )
                    else:
                        result = self.con.execute(gkdb.users.insert(), [dataset])
                    return {"gkstatus": enumdict["Success"]}
                else:
                    return {"gkstatus": enumdict["BadPrivilege"]}
            except exc.IntegrityError:
                return {"gkstatus": enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(
        request_method="PUT", request_param="type=default_user_name", renderer="json"
    )
    def updateDefaultUserName(self):
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

                roleQuery = self.con.execute(
                    "select u.orgs#>'{%s,userrole}' as userrole from gkusers u where userid = %d;"
                    % (str(authDetails["orgcode"]), dataset["userid"])
                )

                if roleQuery.rowcount == 1:
                    result = self.con.execute(
                        gkdb.gkusers.update()
                        .where(gkdb.gkusers.c.userid == dataset["userid"])
                        .values(username=dataset["username"])
                    )

                    """ Deletes old DB data, so commenting it out till dev is completed
                    # delete row from the old table
                    self.con.execute(gkdb.users.delete().where(gkdb.users.c.userid == dataset["olduserid"]))
                    """
                    token = generateAuthToken(
                        self.con,
                        {"userid": dataset["userid"], "username": dataset["username"]},
                        "user",
                    )

                    return {"gkstatus": enumdict["Success"], "token": token}
                return {
                    "gkstatus": enumdict["ActionDisallowed"],
                    "gkmessage": "Invalid User",
                }
            except:
                print(traceback.format_exc())
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    # TODO: Update with new schema
    @view_config(
        request_method="GET", request_param="type=all_user_data", renderer="json"
    )
    def getAllUserData(self):
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
                # there is only one possibility for a catch which is failed connection to db.
                result = self.con.execute(
                    select(
                        [
                            gkdb.userorg.c.userid,
                            gkdb.userorg.c.userrole,
                            gkdb.gkusers.c.username,
                        ]
                    )
                    .where(gkdb.userorg.c.orgcode == authDetails["orgcode"])
                    .order_by(gkdb.gkusers.c.username)
                )
                checkFlag = self.con.execute(
                    select([gkdb.organisation.c.invflag]).where(
                        gkdb.organisation.c.orgcode == authDetails["orgcode"]
                    )
                )
                invf = checkFlag.fetchone()

                users = []
                for row in result:
                    if not (invf["invflag"] == 0 and row["userrole"] == 3):
                        # Specify user role
                        if row["userrole"] == -1:
                            userroleName = "Admin"
                        elif row["userrole"] == 0:
                            userroleName = "Manager"
                        elif row["userrole"] == 1:
                            userroleName = "Operator"
                        elif row["userrole"] == 2:
                            userroleName = "Internal Auditor"
                        elif row["userrole"] == 3:
                            userroleName = "Godown In Charge"
                        users.append(
                            {
                                "userid": row["userid"],
                                "username": row["username"],
                                "userrole": row["userrole"],
                                "userrolename": userroleName,
                            }
                        )

                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": users}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(
        request_method="GET",
        request_param="type=get_user_orgs",
        renderer="json",
    )
    def getAllUserOrgs(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = userAuthCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                userData = self.con.execute(
                    select([gkdb.gkusers.c.orgs]).where(
                        gkdb.gkusers.c.userid == authDetails["userid"]
                    )
                ).fetchone()

                payload = {}
                if userData["orgs"]:
                    for orgCode in userData["orgs"]:
                        orgData = self.con.execute(
                            select(
                                [
                                    gkdb.organisation.c.orgname,
                                    gkdb.organisation.c.orgtype,
                                    gkdb.organisation.c.yearstart,
                                    gkdb.organisation.c.yearend,
                                ]
                            ).where(gkdb.organisation.c.orgcode == orgCode)
                        ).fetchone()
                        if orgData["orgname"] not in payload:
                            payload[orgData["orgname"]] = []
                        payload[orgData["orgname"]].append(
                            {
                                "orgname": orgData["orgname"],
                                "orgtype": orgData["orgtype"],
                                "yearstart": datetime.strftime(
                                    (orgData["yearstart"]), "%d-%m-%Y"
                                ),
                                "yearend": datetime.strftime(
                                    (orgData["yearend"]), "%d-%m-%Y"
                                ),
                                "orgcode": orgCode,
                                "invitestatus": userData["orgs"][orgCode]["invitestatus"],
                                "userrole": userData["orgs"][orgCode]["userrole"],
                            }
                        )
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": payload,
                }
            except:
                print(traceback.format_exc())
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """This function checks if the username sent is unique"""

    @view_config(
        request_method="GET",
        request_param="type=unique_check",
        renderer="json",
    )
    def checkUserNameUnique(self):
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
                # there is only one possibility for a catch which is failed connection to db.
                # Retrieve data of that user whose userid is sent
                query = self.con.execute(
                    select(
                        [
                            gkdb.gkusers.c.userid,
                        ]
                    ).where(gkdb.gkusers.c.username == self.request.params["username"])
                )

                query2 = {"rowcount": 0}
                if tableExists("users"):
                    query2 = self.con.execute(
                        select([gkdb.users.c.userid,]).where(
                            gkdb.users.c.username == self.request.params["username"]
                        )
                    )
                result = query.rowcount == 0 and query2.rowcount == 0
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": result}
            except:
                print(traceback.format_exc())
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
