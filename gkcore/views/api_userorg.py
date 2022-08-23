from gkcore import eng, enumdict
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
import gkcore
from gkcore.views.api_login import authCheck, userAuthCheck, generateAuthToken
import traceback


"""
api_userorg is used to handle user org relation related functionalities like invitations, role updates, etc.
"""


@view_defaults(route_name="userorg")
class api_userorg(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    @view_config(request_method="POST", request_param="type=create_invite", renderer="json")
    def inviteUser(self):
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
                userOrgQuery = self.con.execute(
                    "select orgs->'%s' from gkusers where userid = %d;"
                    % (str(authDetails["orgcode"]), authDetails["userid"])
                )
                if userOrgQuery.rowcount != 1:
                    return {"gkstatus": enumdict["ActionDisallowed"]}
                userOrgData = userOrgQuery.fetchone()
                userRole = userOrgData["userrole"]

                dataset = self.request.json_body

                if userRole == -1 or (userRole == 0 and dataset["userrole"] == 1):
                    # Add entry in gkusers and organisation table, with invite status false
                    userOrgPayload = {
                        "invitestatus": False,
                        "userconf": {},
                        "userrole": dataset["userrole"],
                    }
                    if "golist" in dataset:
                        userOrgPayload["golist"] = dataset["golist"]
                    # data in the gkusers table will be used by the user to determine invite status
                    self.con.execute(
                        "update gkusers set orgs = jsonb_set(orgs, '{%s}', '%s') where userid = %d;"
                        % (
                            str(dataset["orgcode"]),
                            json.dumps(userOrgPayload),
                            dataset["userid"],
                        )
                    )
                    # data in the organisation table will be used by the organisation to determine invited users
                    self.con.execute(
                        "update organisation set users = jsonb_set(users, '{%s}', 'false') where orgcode = %d;"
                        % (
                            str(dataset["userid"]),
                            dataset["orgcode"],
                        )
                    )
                    return {"gkstatus": enumdict["Success"]}
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(
        request_method="PUT", request_param="type=accept_invite", renderer="json"
    )
    def acceptInvite(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = userAuthCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body

                # check if the user has a valid invite in the requested org
                userQuery = self.con.execute(
                    "select orgs->'%s' from gkusers where userid = %d;"
                    % (str(dataset["orgcode"]), authDetails["userid"])
                )

                orgQuery = self.con.execute(
                    "select users->'%s' from organisation where orgcode = %d;"
                    % (str(authDetails["userid"]), dataset["orgcode"])
                )

                if userQuery.rowcount == 1 and orgQuery.rowcount == 1:
                    # Update the gkusers and organisation tables
                    userData = userQuery.fetchone()
                    # update invite status to true
                    self.con.execute(
                        "update gkusers set orgs = jsonb_set(orgs, '{%s,invitestatus}', 'true') where userid = %d;"
                        % (
                            str(dataset["orgcode"]),
                            authDetails["userid"],
                        )
                    )
                    self.con.execute(
                        "update organisation set users = jsonb_set(users, '{%s}', 'true') where orgcode = %d;"
                        % (
                            str(authDetails["userid"]),
                            dataset["orgcode"],
                        )
                    )
                    # add the godown permissions if any present
                    if "golist" in userData:
                        try:
                            for goid in userData["golist"]:
                                godata = {
                                    "userid": authDetails["userid"],
                                    "goid": goid,
                                    "orgcode": dataset["orgcode"],
                                }
                                result = self.con.execute(
                                    gkdb.usergodown.insert(), [godata]
                                )
                            # remove the golist from gkusers
                            self.con.execute(
                                "update gkusers set orgs = orgs #- '{%s,golist}' WHERE userid = %d;"
                                % (str(orgcode["orgcode"]), authDetails["userid"])
                            )
                        except:
                            return {
                                "gkstatus": gkcore.enumdict["ConnectionFailed"],
                                "gkmessage": "Error while assigning godown permissions, please contact admin and get those permissions reassigned",
                            }
                    return {"gkstatus": enumdict["Success"]}
                return {
                    "gkstatus": enumdict["UnauthorisedAccess"],
                    "gkmessage": "Invalid invite, please contact admin",
                }
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(
        request_method="PUT", request_param="type=reject_invite", renderer="json"
    )
    def rejectInvite(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = userAuthCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                dataset = self.request.json_body

                # check if the user has a valid invite in the requested org
                userQuery = self.con.execute(
                    "select orgs->'%s' from gkusers where userid = %d;"
                    % (str(dataset["orgcode"]), authDetails["userid"])
                )

                orgQuery = self.con.execute(
                    "select users->'%s' from organisation where orgcode = %d;"
                    % (str(authDetails["userid"]), dataset["orgcode"])
                )

                if userQuery.rowcount == 1 and orgQuery.rowcount == 1:
                    # remove the entry from users table but leave it in organisation table
                    userData = userQuery.fetchone()
                    if not userData["invitestatus"]:
                        self.con.execute(
                            "update gkusers set orgs = orgs - '{%s}' WHERE userid = %d;"
                            % (str(orgcode["orgcode"]), authDetails["userid"])
                        )
                        return {"gkstatus": enumdict["Success"]}
                    return {
                        "gkstatus": enumdict[
                            "ActionDisallowed"
                        ],  # disallowed because invitation has been accepted
                    }
                return {
                    "gkstatus": enumdict["UnauthorisedAccess"],
                    "gkmessage": "Invalid invite, please contact admin",
                }
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    @view_config(request_method="DELETE", request_param="type=delete_invite", renderer="json")
    def deleteInvite(self):
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
                userOrgQuery = self.con.execute(
                    "select orgs->'%s' from gkusers where userid = %d;"
                    % (str(authDetails["orgcode"]), authDetails["userid"])
                )
                if userOrgQuery.rowcount != 1:
                    return {"gkstatus": enumdict["ActionDisallowed"]}
                userOrgData = userOrgQuery.fetchone()
                userRole = userOrgData["userrole"]

                dataset = self.request.json_body

                if userRole == -1:

                    dataset = self.request.json_body
                    # check if the user has a valid invite in the requested org
                    userQuery = self.con.execute(
                        "select orgs->'%s' from gkusers where userid = %d;"
                        % (str(dataset["orgcode"]), dataset["userid"])
                    )

                    orgQuery = self.con.execute(
                        "select users->'%s' from organisation where orgcode = %d;"
                        % (str(dataset["userid"]), dataset["orgcode"])
                    )

                    if userQuery.rowcount == 1 and orgQuery.rowcount == 1:
                        userData = userQuery.fetchone()
                        if not userData["invitestatus"]:
                            # delete the invites
                            # remove the entry from gkusers and organisation table
                            self.con.execute(
                                "update gkusers set orgs = orgs - '{%s}' WHERE userid = %d;"
                                % (str(dataset["orgcode"]), dataset["userid"])
                            )
                            self.con.execute(
                                "update organisation set users = users - '{%s}' WHERE orgcode = %d;"
                                % (str(dataset["userid"]), dataset["orgcode"])
                            )
                            return {"gkstatus": enumdict["Success"]}
                        return {
                            "gkstatus": enumdict[
                                "ActionDisallowed"
                            ],  # disallowed because invitation has been accepted
                        }
                    elif orgQuery.rowcount == 1:
                        self.con.execute(
                            "update organisation set users = users - '{%s}' WHERE orgcode = %d;"
                            % (str(dataset["userid"]), dataset["orgcode"])
                        )
                        return {"gkstatus": enumdict["Success"]}
                    return {
                        "gkstatus": enumdict[
                            "ActionDisallowed"
                        ],  # disallowed because invitation has been accepted
                    }

                return {
                    "gkstatus": enumdict["UnauthorisedAccess"],
                    "gkmessage": "Invalid invite, please contact admin",
                }
            except:
                return {"gkstatus": gkcore.enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    # TODO: Add user role update method
    # use the updateuser method in api_user as base