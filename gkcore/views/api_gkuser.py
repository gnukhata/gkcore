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
from gkcore.utils import authCheck, userAuthCheck, generateAuthToken
from datetime import datetime
import traceback


def getUserRole(userid, orgcode):
    try:
        con = Connection
        con = eng.connect()
        uid = userid
        roleQuery = con.execute(
            "select u.orgs#>'{%s,userrole}' as userrole from gkusers u where userid = %d;"
            % (str(orgcode), userid)
        )

        # print(row)
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
        print(traceback.format_exc())
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
        """
        try:
            self.con = eng.connect()
            dataset = self.request.json_body

            if "orgs" not in dataset:
                dataset["orgs"] = {}
            result = self.con.execute(gkdb.gkusers.insert(), [dataset])
            userid = self.con.execute(
                select([gkdb.gkusers.c.userid]).where(
                    gkdb.gkusers.c.username == dataset["username"]
                )
            ).fetchone()
            token = generateAuthToken(
                self.con,
                {"userid": userid["userid"], "username": dataset["username"]},
                "user",
            )
            return {"gkstatus": enumdict["Success"], "token": token}
        except exc.IntegrityError:
            return {"gkstatus": enumdict["DuplicateEntry"]}
        except:
            return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
        finally:
            self.con.close()

    """
    updateDefaultUserName() method is used to update the username in gkusers table that was created during migration 
    to satisfy the uniqueness constraint, with a user given username.
    """

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
                allUserData = self.con.execute(
                    "select gkusers.userid, orgs->'%s' as userconf, username from gkusers inner join (select jsonb_object_keys(users) as userid from organisation where orgcode = %d) orgs on cast(orgs.userid as integer) = gkusers.userid;"
                    % (str(authDetails["orgcode"]), authDetails["orgcode"])
                ).fetchall()

                checkFlag = self.con.execute(
                    select([gkdb.organisation.c.invflag]).where(
                        gkdb.organisation.c.orgcode == authDetails["orgcode"]
                    )
                )
                invf = checkFlag.fetchone()

                users = []
                ROLES = {
                    -1: "Admin",
                    0: "Manager",
                    1: "Operator",
                    2: "Internal Auditor",
                    3: "Godown In Charge",
                }
                for userData in allUserData:
                    # print(userData)
                    users.append(
                        {
                            "userid": userData["userid"],
                            "username": userData["username"],
                            "userrole": userData["userconf"]["userrole"]
                            if userData["userconf"]
                            else "",
                            "userrolename": ROLES[userData["userconf"]["userrole"]]
                            if userData["userconf"]
                            else "",
                            "invitestatus": userData["userconf"]["invitestatus"]
                            if userData["userconf"]
                            else "Rejected",
                        }
                    )

                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": users}
            except:
                print(traceback.format_exc())
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
            token = self.request.headers["gkusertoken"]
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
                if userData["orgs"] and type(userData["orgs"]) == dict:
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
                                "invitestatus": userData["orgs"][orgCode][
                                    "invitestatus"
                                ],
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
            result = query.rowcount == 0

            if "check_legacy" in self.request.params:
                query2 = {"rowcount": 0}
                if tableExists("users"):
                    query2 = self.con.execute(
                        select([gkdb.users.c.userid,]).where(
                            gkdb.users.c.username == self.request.params["username"]
                        )
                    )

                result = result and query2.rowcount == 0
            return {"gkstatus": gkcore.enumdict["Success"], "gkresult": result}
        except:
            print(traceback.format_exc())
            return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
        finally:
            self.con.close()

    @view_config(
        request_method="GET", request_param="type=recovery_question", renderer="json"
    )
    def getquestion(self):
        try:
            self.con = eng.connect()
            username = self.request.params["username"]
            result = self.con.execute(
                select([gkdb.gkusers]).where(
                    and_(
                        gkdb.gkusers.c.username == username,
                    )
                )
            )
            if result.rowcount > 0:
                row = result.fetchone()
                user = {"userquestion": row["userquestion"], "userid": row["userid"]}
                return {"gkstatus": gkcore.enumdict["Success"], "gkresult": user}
            else:
                # check if orgcode exists
                # if it does, try to recreate the migrated username and check
                # else check if the old users table exists,
                # if it does, ask the user to send both username and orgcode
                if "orgname" in self.request.params:
                    orgQuery = self.con.execute(
                        select([gkdb.organisation.c.orgcode]).where(
                            and_(
                                gkdb.organisation.c.orgname
                                == self.request.params["orgname"],
                                gkdb.organisation.c.orgtype
                                == self.request.params["orgtype"],
                            )
                        )
                    )
                    if orgQuery.rowcount:
                        orgname = "_".join(self.request.params["orgname"].split(" "))
                        orgtype = (
                            "p"
                            if self.request.params["orgtype"] == "Profit Making"
                            else "np"
                        )
                        uname = (
                            orgname
                            + "_"
                            + orgtype
                            + "_"
                            + self.request.params["username"]
                        )
                        result = self.con.execute(
                            select([gkdb.gkusers]).where(
                                and_(
                                    gkdb.gkusers.c.username == uname,
                                )
                            )
                        )
                        if result.rowcount > 0:
                            row = result.fetchone()
                            user = {
                                "userquestion": row["userquestion"],
                                "userid": row["userid"],
                            }
                            return {
                                "gkstatus": gkcore.enumdict["Success"],
                                "gkresult": user,
                            }
                elif tableExists("users"):
                    query2 = self.con.execute(
                        select([gkdb.users.c.userid]).where(
                            gkdb.users.c.username == self.request.params["username"]
                        )
                    )
                    if query2.rowcount > 0:
                        return {"gkstatus": enumdict["ActionDisallowed"]}
                return {"gkstatus": enumdict["BadPrivilege"]}
        except:
            return {"gkstatus": enumdict["ConnectionFailed"]}
        finally:
            self.con.close()

    @view_config(
        request_method="GET",
        request_param="type=verify_answer",
        renderer="json",
    )
    def verifyanswer(self):
        try:
            self.con = eng.connect()
            userid = self.request.params["userid"]
            useranswer = self.request.params["useranswer"]
            result = self.con.execute(
                select([gkdb.gkusers]).where(gkdb.gkusers.c.userid == userid)
            )
            row = result.fetchone()
            print(useranswer)
            print(row["useranswer"])
            if useranswer == row["useranswer"]:
                return {"gkstatus": enumdict["Success"]}
            else:
                return {"gkstatus": enumdict["BadPrivilege"]}
        except:
            return {"gkstatus": enumdict["ConnectionFailed"]}
        finally:
            self.con.close()

    @view_config(
        request_method="PUT", request_param="type=reset_password", renderer="json"
    )
    def resetpassword(self):
        try:
            self.con = eng.connect()
            dataset = self.request.json_body
            user = self.con.execute(
                select([gkdb.gkusers]).where(
                    and_(
                        gkdb.gkusers.c.userid == dataset["userid"],
                        gkdb.gkusers.c.useranswer == dataset["useranswer"],
                    )
                )
            )
            if user.rowcount > 0:
                result = self.con.execute(
                    gkdb.gkusers.update()
                    .where(gkdb.gkusers.c.userid == dataset["userid"])
                    .values(userpassword=dataset["userpassword"])
                )
                return {"gkstatus": enumdict["Success"]}
            else:
                return {"gkstatus": enumdict["BadPrivilege"]}
        except:
            print(traceback.format_exc())
            return {"gkstatus": enumdict["ConnectionFailed"]}
        finally:
            self.con.close()
