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
"Survesh" <123survesh@gmail.com>
"Sai Karthik"<kskarthik@disroot.org>

"""

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults, view_config
from sqlalchemy.ext.baked import Result
import gkcore
from jsonschema import RefResolver, Draft202012Validator, validate
from gkcore.config_schema import (
    payloadSchema1,
    payloadSchema2,
    transactionBaseSchema,
    transactionConfigSchema,
    transactionPageSchema,
    workflowConfigSchema,
    globalConfigSchema,
)

schema_store = {
    transactionBaseSchema["$id"]: transactionBaseSchema,
    transactionConfigSchema["$id"]: transactionConfigSchema,
    transactionPageSchema["party"]["$id"]: transactionPageSchema["party"],
    transactionPageSchema["ship"]["$id"]: transactionPageSchema["ship"],
    transactionPageSchema["bill"]["$id"]: transactionPageSchema["bill"],
    transactionPageSchema["payment"]["$id"]: transactionPageSchema["payment"],
    transactionPageSchema["transport"]["$id"]: transactionPageSchema["transport"],
    transactionPageSchema["total"]["$id"]: transactionPageSchema["total"],
    transactionPageSchema["comments"]["$id"]: transactionPageSchema["comments"],
}

resolver = RefResolver.from_schema(transactionBaseSchema, store=schema_store)
validator = Draft202012Validator(transactionConfigSchema, resolver=resolver)


@view_defaults(route_name="config")
class api_config(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection
        print("User config initialized")

    """
        Returns the config of a user/organisation, given proper gktoken
    """

    @view_config(request_method="GET", renderer="json")
    def getConfg(self):
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
                pageid = None
                confid = None
                if "pageid" in self.request.params:
                    pageid = self.request.params["pageid"]
                if "confid" in self.request.params:
                    confid = self.request.params["confid"]
                config = self.getConf(
                    self.request.params["conftype"],
                    authDetails["orgcode"],
                    authDetails["userid"],
                    pageid,
                    confid,
                )
                return {
                    "gkstatus": enumdict["Success"],
                    "gkresult": config,
                }
            except Exception as e:
                # print(e)
                return {"gkstatus": enumdict["ConnectionFailed"]}

    """
        Updates the entire config
    """

    @view_config(request_method="PUT", renderer="json")
    def updateConfig(self):
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
                config = dataset["config"]
                confType = self.request.params["conftype"]
                if confType == "user":
                    # self.con.execute(
                    #     gkdb.users.update()
                    #     .where(
                    #         and_(
                    #             gkdb.users.c.orgcode == authDetails["orgcode"],
                    #             gkdb.users.c.userid == authDetails["userid"],
                    #         )
                    #     )
                    #     .values(userconf=config)
                    # )
                    targetPath = [authDetails["orgcode"], "userconf"]
                    payload = "'" + json.dumps(config) + "'"
                    path = "'{" + ",".join(targetPath) + "}'"
                    self.con.execute(
                        "update gkusers set orgs = jsonb_set(orgs, %s, %s) where userid = %d;"
                        % (
                            str(path),
                            str(payload),
                            authDetails["userid"],
                        )
                    )
                else:
                    self.con.execute(
                        gkdb.organisation.update()
                        .where(gkdb.organisation.c.orgcode == authDetails["orgcode"])
                        .values(orgconf=config)
                    )
                return {"gkstatus": enumdict["Success"]}
            except Exception as e:
                # print(e)
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    """
        Updates the config based on the given path
    """

    @view_config(request_method="PUT", request_param="update=path", renderer="json")
    def updateConfigByPath(self):
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

                # Validate the payload structure
                try:
                    validate(instance=dataset, schema=payloadSchema2)
                    print("Config Structure Validated")
                except Exception as e:
                    # print(e)
                    return {
                        "gkstatus": enumdict["ActionDisallowed"],
                        "gkmessage": "Invalid Payload. Please check the payload structure",
                    }

                # Array of keys in descending order of hierarchy [parent, child, grand child, etc.]
                pathArr = dataset["path"]

                confToValidate = {}
                target = confToValidate
                pathLen = len(pathArr)
                for pathIndex, path in enumerate(pathArr):
                    target[path] = {}
                    if pathIndex + 1 < pathLen:
                        target = target[path]
                    else:
                        target[path] = dataset["config"]

                # Validate the config structure
                try:
                    # print(confToValidate)
                    if self.request.params["confcategory"] == "transaction":
                        if "inv" in confToValidate:
                            validator.validate(confToValidate)
                    elif self.request.params["confcategory"] == "global":
                        validate(instance=confToValidate, schema=globalConfigSchema)
                    else:
                        validate(instance=confToValidate, schema=workflowConfigSchema)
                    print("Config Validated")
                except Exception as e:
                    # print(e)
                    # print(confToValidate)
                    return {
                        "gkstatus": enumdict["ActionDisallowed"],
                        "gkmessage": "Invalid Config. Please check the config structure",
                    }

                newConfig = dataset["config"]
                oldConfig = self.getConf(
                    self.request.params["conftype"],
                    authDetails["orgcode"],
                    authDetails["userid"],
                    None,
                    None,
                )

                target = oldConfig
                targetPath = []
                targetParent = oldConfig
                payload = {}
                for path in pathArr:
                    if type(target) != dict:
                        target = {}
                    if path in target:
                        targetPath.append(path)
                        target = target[path]
                    else:
                        if not payload:
                            payload = target
                            payload[path] = {}
                            targetParent = payload
                            target = payload[path]
                        else:
                            target[path] = {}
                            targetParent = target
                            target = target[path]
                if not payload:
                    payload = newConfig
                else:
                    targetParent[path] = newConfig
                if not len(targetPath):
                    if self.request.params["conftype"] == "user":
                        # self.con.execute(
                        #     gkdb.users.update()
                        #     .where(
                        #         and_(
                        #             gkdb.users.c.orgcode == authDetails["orgcode"],
                        #             gkdb.users.c.userid == authDetails["userid"],
                        #         )
                        #     )
                        #     .values(userconf=payload)
                        # )
                        targetPath = [authDetails["orgcode"], "userconf"]
                        payload = "'" + json.dumps(payload) + "'"
                        path = "'{" + ",".join(targetPath) + "}'"
                        self.con.execute(
                            "update gkusers set orgs = jsonb_set(orgs, %s, %s) where userid = %d;"
                            % (
                                str(path),
                                str(payload),
                                authDetails["userid"],
                            )
                        )
                    elif self.request.params["conftype"] == "org":
                        self.con.execute(
                            gkdb.organisation.update()
                            .where(
                                gkdb.organisation.c.orgcode == authDetails["orgcode"]
                            )
                            .values(orgconf=payload)
                        )
                else:
                    targetPath = [authDetails["orgcode"], "userconf", *targetPath]
                    payload = "'" + json.dumps(payload) + "'"
                    path = "'{" + ",".join(targetPath) + "}'"
                    if self.request.params["conftype"] == "user":
                        self.con.execute(
                            "update gkusers set orgs = jsonb_set(orgs, %s, %s) where userid = %d;"
                            % (
                                str(path),
                                str(payload),
                                authDetails["userid"],
                            )
                        )
                    elif self.request.params["conftype"] == "org":
                        self.con.execute(
                            "update organisation set orgconf = jsonb_set(orgconf, %s, %s) where orgcode = %d;"
                            % (path, payload, authDetails["orgcode"])
                        )
                return {"gkstatus": enumdict["Success"]}
            except Exception as e:
                # print(e)
                return {"gkstatus": enumdict["ConnectionFailed"]}
            finally:
                self.con.close()

    def getConf(self, confType, orgcode, userid, pageid, confid):
        try:
            self.con = eng.connect()
            config = {}
            if confType == "user":
                if pageid:
                    if confid:
                        # configRow = self.con.execute(
                        #     "select u.userconf#>'{%s,%s}' as userconf from users u where orgcode = %d and userid = %d;"
                        #     % (str(pageid), str(confid), orgcode, userid)
                        # ).fetchone()
                        configRow = self.con.execute(
                            "select u.orgs#>'{%s,userconf,%s,%s}' as userconf from gkusers u where userid = %d;"
                            % (str(orgcode), str(pageid), str(confid), userid)
                        ).fetchone()
                    else:
                        # configRow = self.con.execute(
                        #     "select u.userconf#>'{%s}' as userconf from users u where orgcode = %d and userid = %d;"
                        #     % (str(pageid), orgcode, userid)
                        # ).fetchone()
                        configRow = self.con.execute(
                            "select u.orgs#>'{%s,userconf,%s}' as userconf from gkusers u where userid = %d;"
                            % (str(orgcode), str(pageid), userid)
                        ).fetchone()
                else:
                    # configRow = self.con.execute(
                    #     select([gkdb.gkusers.c.userconf]).where(
                    #         and_(
                    #             gkdb.gkusers.c.orgcode == orgcode,
                    #             gkdb.gkusers.c.userid == userid,
                    #         )
                    #     )
                    # ).fetchone()
                    configRow = self.con.execute(
                        "select u.orgs#>'{%s,userconf}' as userconf from gkusers u where userid = %d;"
                        % (str(orgcode), userid)
                    ).fetchone()
                config = configRow["userconf"]
            elif confType == "org":
                if pageid:
                    if confid:
                        configRow = self.con.execute(
                            "select org.orgconf#>'{%s,%s}' as orgconf from organisation org where orgcode = %d;"
                            % (str(pageid), str(confid), orgcode)
                        ).fetchone()
                    else:
                        configRow = self.con.execute(
                            "select org.orgconf#>'{%s}' as orgconf from organisation org where orgcode = %d;"
                            % (str(pageid), orgcode)
                        ).fetchone()
                else:
                    configRow = self.con.execute(
                        select([gkdb.organisation.c.orgconf]).where(
                            gkdb.organisation.c.orgcode == orgcode,
                        )
                    ).fetchone()
                config = configRow["orgconf"]
            return config
        except Exception as e:
            # print(e)
            return e
