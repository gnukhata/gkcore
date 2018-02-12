from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice,tax, state, drcr
from gkcore.views.api_tax  import calTax
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from datetime import datetime,date
import jwt
import gkcore
from gkcore.views.api_login import authCheck
from gkcore.views.api_user import getUserRole

@view_defaults(route_name='drcrnote')
class api_drcr(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection
    @view_config(request_method='POST',renderer='json')
    def createdrcrnote(self):
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
                result=self.con.execute(drcr.insert(),[dataset])
            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
                
