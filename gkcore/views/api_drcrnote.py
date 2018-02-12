from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice,tax, state, drcr,customerandsupplier
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
    def createDrCrNote(self):
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
                
    @view_config(request_method='GET',request_param="drcr=single", renderer ='json')
    def getDrCrDetails(self):
        """
        purpose: gets details of debit and credit note from it's drcrid.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}
        else:
            #try:
                self.con = eng.connect()
                result=self.con.execute(select([drcr]).where(drcr.c.drcrid==self.request.params["drcrid"]))
                drcrrow=result.fetchone()
                result1=self.con.execute(select([invoice]).where(invoice.c.invid==drcrrow["invid"]))
                inv=result1.fetchone()
                print "\n invid=="+str(inv["invid"])
                print "result1 invoice"+str(inv)


                result2=self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.state,customerandsupplier.c.custaddr]).where(customerandsupplier.c.custid==inv["custid"]))
                custdata=result2.fetchone()
                print "\n \n ---- this is customer data "+str(custdata)
   
                drcrdata = {"drcrid":drcrrow["drcrid"],"taxflag":drcrrow["taxflag"],"drcrno":drcrrow["drcrno"],"drcrdate":datetime.strftime(drcrrow["drcrdate"],"%d-%m-%Y"),"dctypeflag":drcrrow["dctypeflag"],"totreduct":"%.2f"%float(drcrrow["totreduct"]),"invid":drcrrow["invid"]}
                print "\n drcr data"+str(drcrdata)
                
            #except:
                #return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            #finally:
                self.con.close()
