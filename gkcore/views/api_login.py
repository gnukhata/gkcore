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
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"""


# login function
from gkcore import eng, enumdict
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, func
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.ext.baked import Result
from gkcore.models.meta import inventoryMigration, addFields, tableExists
import gkcore
import traceback
from datetime import datetime
from gkcore.views.api_gkuser import getUserRole
from gkcore.utils import generateAuthToken, userAuthCheck, authCheck

con = Connection


@view_config(route_name="login", request_method="POST", renderer="json")
def gkLogin(request):

    """
    purpose: take org code, username and password and authenticate the user.
    Return true if username and password matches or false otherwise.
    description:
    The function takes the orgcode and matches the username and password.
    if it is correct then the user is authorised and a  object is created.
    The object will have the userid and orgcode and this will be sent back as a response.
    Else the function will not issue any token.
    """
    try:
        con = eng.connect()
        try:
            con.execute(select([gkdb.organisation.c.invflag]))
        except:
            inventoryMigration(con, eng)
        try:
            con.execute(
                select([gkdb.delchal.c.modeoftransport, gkdb.delchal.c.noofpackages])
            )
            con.execute(select([gkdb.transfernote.c.recieveddate]))
        except:
            addFields(con, eng)
        dataset = request.json_body
        result = con.execute(
            select([gkdb.users.c.userid, gkdb.users.c.userrole]).where(
                and_(
                    gkdb.users.c.username == dataset["username"],
                    gkdb.users.c.userpassword == dataset["userpassword"],
                    gkdb.users.c.orgcode == dataset["orgcode"],
                )
            )
        )
        if result.rowcount == 1:
            record = result.fetchone()
            token = generateAuthToken(
                con, {"userid": record["userid"], "orgcode": dataset["orgcode"]}
            )
            if token == -1:
                raise Exception("Issue with generating Auth Token")
            return {
                "gkstatus": enumdict["Success"],
                "token": token,
                "userid": record["userid"],
            }
        else:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
    except:
        print(traceback.format_exc())
        return {"gkstatus": enumdict["ConnectionFailed"]}
    finally:
        con.close()


@view_config(
    route_name="login",
    request_method="POST",
    request_param="type=user",
    renderer="json",
)
def userLogin(request):

    """
    purpose: Checks if username and password match a row in gkusers table.
             If they match a row, org data related to that user are fetched from the orgs column in gkusers table.
             If not the username and password are checked in the old users table. If the username is mapped only to one
             org, then that org's details are returned. If the username is mapped to more than one org,
             then ActionDisallowed status is sent with a message asking to contact the admin for login details.
    """
    try:
        con = eng.connect()
        dataset = request.json_body
        result = con.execute(
            select([gkdb.gkusers.c.userid]).where(
                and_(
                    gkdb.gkusers.c.username == dataset["username"],
                    gkdb.gkusers.c.userpassword == dataset["userpassword"],
                )
            )
        )
        # if username and password exist in users2 table
        if result.rowcount == 1:
            record = result.fetchone()
            # check if any orgs are mapped to the userid

            userData = con.execute(
                select([gkdb.gkusers.c.orgs]).where(
                    gkdb.gkusers.c.userid == record["userid"]
                )
            ).fetchone()

            payload = {}
            if userData["orgs"]:
                for orgCode in userData["orgs"]:
                    orgData = con.execute(
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
                            "yearstart": datetime.strftime(
                                (orgData["yearstart"]), "%d-%m-%Y"
                            ),
                            "orgtype": orgData["orgtype"],
                            "yearend": datetime.strftime((orgData["yearend"]), "%d-%m-%Y"),
                            "orgcode": orgCode,
                            "invitestatus": userData["orgs"][orgCode]["invitestatus"],
                            "userrole": userData["orgs"][orgCode]["userrole"],
                        }
                    )
            token = generateAuthToken(
                con,
                {"userid": record["userid"], "username": dataset["username"]},
                "user",
            )
            return {
                "gkstatus": enumdict["Success"],
                "gkresult": payload,
                "token": token,
            }
        # else check if its available in users table
        elif tableExists("users"):
            result2 = con.execute(
                select(
                    [gkdb.users.c.userid, gkdb.users.c.orgcode, gkdb.users.c.userrole]
                ).where(
                    and_(
                        gkdb.users.c.username == dataset["username"],
                        gkdb.users.c.userpassword == dataset["userpassword"],
                    )
                )
            )

            if result2.rowcount > 0:
                #  return if only one org is available else return message contact admin for login details
                records2 = result2.fetchall()
                payload = {}

                for udata in result2:
                    orgData = con.execute(
                        select(
                            gkdb.organisation.c.orgname,
                            gkdb.organisation.c.orgtype,
                            gkdb.organisation.c.yearstart,
                            gkdb.organisation.c.yearend,
                        ).where(gkdb.organisation.c.orgcode == udata["orgcode"])
                    ).fetchone()
                    if orgData["orgname"] not in payload:
                        payload[orgData["orgname"]] = []
                    payload[orgData["orgname"]].append(
                        {
                            "orgname": orgData["orgname"],
                            "orgtype": orgData["orgtype"],
                            "orgcode": orgData["orgcode"],
                            "yearstart": datetime.strftime(
                                (orgData["yearstart"]), "%d-%m-%Y"
                            ),
                            "yearend": datetime.strftime(
                                (orgData["yearend"]), "%d-%m-%Y"
                            ),
                            "invitestatus": True,
                            "userrole": udata["userrole"],
                        }
                    )

                if len(payload) == 1:
                    token = generateAuthToken(
                        con,
                        {"userid": record["userid"], "username": dataset["username"]},
                        "user",
                    )
                    return {
                        "gkstatus": enumdict["Success"],
                        "gkresult": payload,
                        "token": token,
                    }
                else:
                    return {
                        "gkstatus": enumdict["ActionDisallowed"],
                        "gkresult": "Contact Admin for login credentials.",
                    }
            else:
                return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
    except:
        print(traceback.format_exc())
        return {"gkstatus": enumdict["ConnectionFailed"]}
    finally:
        con.close()


@view_config(
    route_name="login", request_method="POST", request_param="type=org", renderer="json"
)
def orgLogin(request):

    """
    purpose:
    """
    try:
        con = eng.connect()
        dataset = request.json_body

        userId = ""
        oldUserId = ""
        proceed = True
        renameUser = False

        if "username" in dataset and "userpassword" in dataset:
            # legacy login support
            # check if user creds are matched in gkusers table
            userIdQuery = con.execute(
                select([gkdb.gkusers.c.userid]).where(
                    and_(
                        gkdb.gkusers.c.username == dataset["username"],
                        gkdb.gkusers.c.userpassword == dataset["userpassword"],
                    )
                )
            )

            if userIdQuery.rowcount != 1:
                # recreate the migrate username and check if it exists in gkusers table
                orgData = con.execute(
                    select(
                        [gkdb.organisation.c.orgname, gkdb.organisation.c.orgtype]
                    ).where(gkdb.organisation.c.orgcode == dataset["orgcode"])
                ).fetchone()
                orgname = "_".join(orgData["orgname"].split(" "))
                orgtype = "p" if orgData["orgtype"] == "Profit Making" else "np"
                uname = orgname + "_" + orgtype + "_" + dataset["username"]

                userIdQuery = con.execute(
                    select([gkdb.gkusers.c.userid]).where(
                        and_(
                            gkdb.gkusers.c.username == uname,
                            gkdb.gkusers.c.userpassword == dataset["userpassword"],
                        )
                    )
                )
                if userIdQuery.rowcount == 1:
                    # userId = userIdQuery.fetchone()
                    renameUser = True
                    oldUserId = con.execute(
                        select([gkdb.users.c.userid]).where(
                            and_(
                                gkdb.users.c.username == dataset["username"],
                                gkdb.users.c.orgcode == dataset["orgcode"],
                            )
                        )
                    ).fetchone()
                else:
                    proceed = False

            if userIdQuery.rowcount == 1:
                # if user creds are in gkusers fetch userid and check if there is a mapping with the specified orgcode
                userId = userIdQuery.fetchone()
                userId = userId["userid"]
                userOrgQuery = con.execute(
                    "select u.orgs#>'{%s}' as orgs from gkusers u where userid = %d;"
                    % (str(dataset["orgcode"]), userId)
                )
                # print("UserOrgQuery check")
                # print(userOrgQuery["orgs"])
                # if no user org mapping found dont proceed
                if userOrgQuery.rowcount != 1:
                    proceed = False
            else:
                proceed = False
        else:
            # New login support
            try:
                token = request.headers["gkusertoken"]
            except:
                print(traceback.format_exc())
                return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
            authDetails = userAuthCheck(token)
            if authDetails["auth"] == False:
                print(traceback.format_exc())
                return {"gkstatus": enumdict["UnauthorisedAccess"]}
            else:
                userId = authDetails["userid"]
                userOrgQuery = con.execute(
                    "select u.orgs#>'{%s}' as orgs from gkusers u where userid = %d;"
                    % (str(dataset["orgcode"]), userId)
                )
                # print("UserOrgQuery check")
                # print(userOrgQuery["orgs"])
                # if no user org mapping found dont proceed
                if userOrgQuery.rowcount != 1:
                    proceed = False

        if proceed:
            token = generateAuthToken(
                con, {"userid": userId, "orgcode": dataset["orgcode"]}
            )
            if token == -1:
                raise Exception("Issue with generating Auth Token")
            payload = {"gkstatus": enumdict["Success"], "token": token}
            if renameUser:
                payload["userid"] = userId
                payload["olduserid"] = oldUserId["userid"]
            return payload
        else:
            print(traceback.format_exc())
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
    except:
        print(traceback.format_exc())
        return {"gkstatus": enumdict["ConnectionFailed"]}
    finally:
        con.close()


@view_config(route_name="login", request_method="GET", renderer="json")
def getuserorgdetails(request):
    try:
        token = request.headers["gktoken"]
    except:
        return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
    authDetails = authCheck(token)
    if authDetails["auth"] == False:
        return {"gkstatus": enumdict["UnauthorisedAccess"]}
    else:
        try:
            con = eng.connect()
            userRoleData = getUserRole(authDetails["userid"], authDetails["orgcode"])
            userRole = userRoleData["gkresult"]["userrole"]
            flagsdata = con.execute(
                select(
                    [gkdb.organisation.c.booksclosedflag, gkdb.organisation.c.roflag]
                ).where(gkdb.organisation.c.orgcode == authDetails["orgcode"])
            )
            flags = flagsdata.fetchone()
            return {
                "gkstatus": gkcore.enumdict["Success"],
                "gkresult": {
                    "userrole": int(userRole),
                    "booksclosedflag": int(flags["booksclosedflag"]),
                    "roflag": int(flags["roflag"]),
                },
            }
        except:
            return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
        finally:
            con.close()
