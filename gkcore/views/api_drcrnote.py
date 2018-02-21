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
from gkcore.views.api_invoice import getStateCode

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
                invresult=self.con.execute(select([invoice]).where(invoice.c.invid==drcrrow["invid"]))
                invrow=invresult.fetchone()
                invdata={"invid":invrow["invid"],"invoiceno":invrow["invoiceno"],"sourcestate":invrow["sourcestate"],"taxstate":invrow["taxstate"],"custid":invrow["custid"],"invoicedate":datetime.strftime(invrow["invoicedate"],"%d-%m-%Y"),"issuername":invrow["issuername"],"designation":invrow["designation"],"inoutflag":invrow["inoutflag"],"taxflag":invrow["taxflag"]}
                
                if invrow["sourcestate"] != None:
                    invdata["sourcestate"] = invrow["sourcestate"]
                    invdata["sourcestatecode"] = getStateCode(invrow["sourcestate"],self.con)["statecode"]
                    sourceStateCode = getStateCode(invrow["sourcestate"],self.con)["statecode"]
                if invrow["taxstate"] != None:
                        invdata["destinationstate"]=invrow["taxstate"]
                        taxStateCode =  getStateCode(invrow["taxstate"],self.con)["statecode"]
                        invdata["taxstatecode"] = taxStateCode
                        
                print " \n \n invoice data"+str(invdata)                
                resultcust=self.con.execute(select([customerandsupplier.c.custid,customerandsupplier.c.custname,customerandsupplier.c.custaddr,customerandsupplier.c.gstin,customerandsupplier.c.custtan,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invrow["custid"]))
                custrow=resultcust.fetchone()
                if custrow["csflag"] == 3:
                    custdata={"custid":custrow["custid"],"custname":custrow["custname"],"custaddr":custrow["custaddr"],"gstin":custrow["gstin"],"custtan":custrow["custtan"]}
                    print "\n \n this is customer data "+str(custdata)
                else:
                    suppdata={"custid":custrow["custid"],"custname":custrow["custname"],"custaddr":custrow["custaddr"],"gstin":custrow["gstin"],"custtan":custrow["custtan"]}
                    print "\n \n this is supp data "+str(suppdata)
                resultuser=self.con.execute(select([users.c.userid,users.c.username,users.c.userrole]).where(users.c.userid==drcrrow["userid"]))
                userrow=resultuser.fetchone()
                userdata={"userid":userrow["userid"],"username":userrow["username"],"userrole":userrow["userrole"]}
                print "\n \n user data "+str(userdata)
                #to extract issuername and designation from invoice and user login
                if invrow["inoutflag"]==15:
                    invdata["issuername"]=invrow["issuername"]
                    invdata["designation"]=invrow["designation"]
                    print "invdata sale "+str(invdata)
                else:
                    invdata["issuername"]=userrow["username"]
                    invdata["designation"]=userrow["userrole"]
                    print "invdata"+str(invdata)
            #except:
                #return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            #finally:
                self.con.close()

    @view_config(request_method='GET',request_param='attach=image', renderer='json')
    def getattachment(self):
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails['auth'] == False:
            return {"gkstatus":enumdict["UnauthorisedAccess"]}
        else:
            try:
                self.con = eng.connect()
                drcrid = self.request.params["drcrid"]
                drcrData = self.con.execute(select([drcr.c.drcrno, drcr.c.attachment]).where(drcr.c.drcrid == drcrid))
                attachment = drcrData.fetchone()
                return {"gkstatus":enumdict["Success"],"gkresult":attachment["attachment"],"drcrno":attachment["drcrno"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
                


    
