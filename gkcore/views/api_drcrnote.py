from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice,tax, state, drcr,customerandsupplier,users
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
        purpose: gets details of single debit or credit note from it's drcrid.
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
                resultdrcr=self.con.execute(select([drcr]).where(drcr.c.drcrid==self.request.params["drcrid"]))
                drcrrow=resultdrcr.fetchone()
                drcrdata = {"drcrid":drcrrow["drcrid"],"taxflag":drcrrow["taxflag"],"drcrno":drcrrow["drcrno"],"drcrdate":datetime.strftime(drcrrow["drcrdate"],"%d-%m-%Y"),"dctypeflag":drcrrow["dctypeflag"],"caseflag":drcrrow["caseflag"],"taxflag":drcrrow["taxflag"],"totreduct":"%.2f"%float(drcrrow["totreduct"]),"invid":drcrrow["invid"],"tax":drcrrow["tax"],"contents":drcrrow["contents"],"reference":drcrrow["reference"],"userid":drcrrow["userid"]}
                
                print "\n \n drcr data"+str(drcrdata)
                
                resultinv=self.con.execute(select([invoice]).where(invoice.c.invid==drcrrow["invid"]))
                invrow=resultinv.fetchone()
                invdata={"invid":invrow["invid"],"invoiceno":invrow["invoiceno"],"custid":invrow["custid"],"invoicedate":datetime.strftime(invrow["invoicedate"],"%d-%m-%Y"),"issuername":invrow["issuername"],"designation":invrow["designation"],"inoutflag":invrow["inoutflag"]}

                print " \n \n invoice data"+str(invdata)                

                resultcust=self.con.execute(select([customerandsupplier.c.custid,customerandsupplier.c.custname,customerandsupplier.c.custaddr,customerandsupplier.c.gstin,customerandsupplier.c.custtan]).where(customerandsupplier.c.custid==invrow["custid"]))
                custrow=resultcust.fetchone()
                custdata={"custid":custrow["custid"],"custname":custrow["custname"],"custaddr":custrow["custaddr"],"gstin":custrow["gstin"],"custtan":custrow["custtan"]}
                
                print "\n \n this is customer data "+str(custdata)

                resultuser=self.con.execute(select([users.c.userid,users.c.username,users.c.userrole]).where(users.c.userid==drcrrow["userid"]))
                userrow=resultuser.fetchone()
                userdata={"userid":userrow["userid"],"username":userrow["username"],"userrole":userrow["userrole"]}

                print "\n \n user data "+str(userdata)
            #except:
                #return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            #finally:
                self.con.close()
                


    
