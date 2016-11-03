"""REST API for tax """

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result


@view_defaults(route_name='tax')
class api_tax(object):
    def __init__(self,request):
        self.request = Request
        self.request = request
        self.con = Connection
        print "tax initialized"
        
    @view_config(request_method='POST',renderer='json')
    def addtax(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
#        print authCheck(token)
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
                userRole = user.fetchone()
                dataset = self.request.json_body
                if userRole[0]==-1:
                    dataset["orgcode"] = authDetails["orgcode"]
                    result = self.con.execute(gkdb.tax.insert(),[dataset])
                    return {"gkstatus":enumdict["Success"]}
                else:
                    return {"gkstatus":  enumdict["BadPrivilege"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["DuplicateEntry"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
    @view_config(request_method='GET',renderer='json')
    def gettaxdata(self):
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
                print "creating taxdata"
                result = self.con.execute(select([gkdb.tax]).where(gkdb.tax.c.taxid==self.request.matchdict["taxid"]))
                row = result.fetchone()
                acc={"taxid":row["taxid"], "taxname":row["taxname"], "taxrate":"%.2f"%float(row["taxrate"]),"state":row["state"]}
                return {"gkstatus": enumdict["Success"], "gkresult":acc}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
                
                
    @view_config(request_method='PUT', renderer='json')
    def edittaxdata(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
#        print authCheck(token)
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                print "editing data"
                user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
                userRole = user.fetchone()
                dataset = self.request.json_body
                if userRole[0]==-1:
                    result = self.con.execute(gkdb.users.update().where(gkdb.tax.c.taxid==dataset["taxid"]).values(dataset))
                    print result
                    return {"gkstatus":enumdict["Success"]}
                else:
                    return {"gkstatus":  enumdict["BadPrivilege"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()
                
    @view_config(request_method='DELETE', renderer ='json')
    def deletetaxdata(self):
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
                user=self.con.execute(select([gkdb.users.c.userrole]).where(gkdb.users.c.userid == authDetails["userid"] ))
                userRole = user.fetchone()
                dataset = self.request.json_body
                if userRole[0]==-1:
                    result = self.con.execute(gkdb.tax.delete().where(gkdb.tax.c.taxid==dataset["taxid"]))
                    return {"gkstatus":enumdict["Success"]}
                else:
                    {"gkstatus":  enumdict["BadPrivilege"]}
            except exc.IntegrityError:
                return {"gkstatus":enumdict["ActionDisallowed"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"] }
            finally:
                self.con.close()