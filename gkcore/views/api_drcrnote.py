from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice,tax,state,drcr,customerandsupplier,users
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
                invresult=self.con.execute(select([invoice]).where(invoice.c.invid==drcrrow["invid"]))
                invrow=invresult.fetchone()
                custresult=self.con.execute(select([customerandsupplier.c.custid,customerandsupplier.c.custname,customerandsupplier.c.custaddr,customerandsupplier.c.gstin,customerandsupplier.c.custtan,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invrow["custid"]))
                custrow=custresult.fetchone()
                n=15
                if drcrrow["dctypeflag"]==3 and n==15:
                    if drcrrow["caseflag"] == 1 or drcrrow["caseflag"] == 3:
                        
                        print "FROM 3 15 1 3"
                        
                elif drcrrow["dctypeflag"]==4 or n==9 :
                    if drcrrow["caseflag"] == 0 or drcrrow["caseflag"] == 2:
                        print "FROM 4 9 0 AND 2"
               

                     
                drcrdata = {"drcrid":drcrrow["drcrid"],"drcrno":drcrrow["drcrno"],"drcrdate":datetime.strftime(drcrrow["drcrdate"],"%d-%m-%Y"),"dctypeflag":drcrrow["dctypeflag"],"caseflag":drcrrow["caseflag"],"totreduct":"%.2f"%float(drcrrow["totreduct"]),"invid":drcrrow["invid"],"contents":drcrrow["contents"],"reference":drcrrow["reference"]}
                print "\n \n drcr data"+str(drcrdata)
                invdata={"invid":invrow["invid"],"invoiceno":invrow["invoiceno"],"custid":invrow["custid"],"invoicedate":datetime.strftime(invrow["invoicedate"],"%d-%m-%Y"),"inoutflag":invrow["inoutflag"],"taxflag":invrow["taxflag"]}  
                a=9
                if invrow["sourcestate"] != None or invrow["taxstate"] !=None:
                    if a==9:
                        invdata["sourcestate"] = invrow["sourcestate"]
                        sourceStateCode = getStateCode(invrow["sourcestate"],self.con)["statecode"]
                        invdata["sourcestatecode"] = sourceStateCode
                        invdata["taxstate"]=invrow["taxstate"]
                        taxStateCode=getStateCode(invrow["taxstate"],self.con)["statecode"]
                        invdata["taxstatecode"]=taxStateCode
                    else:
                        invdata["sourcestate"]=invrow["taxstate"]
                        sourceStateCode= getStateCode(invrow["taxstate"],self.con)["statecode"]
                        invdata["sourcestatecode"] = sourceStateCode
                        invdata["taxstate"]=invrow["sourcestate"]
                        taxStateCode=getStateCode(invrow["sourcestate"],self.con)["statecode"]
                        invdata["taxstatecode"]=taxStateCode                                                    
                print " \n \n invoice data"+str(invdata)
                if custrow["csflag"] == 3:
                    custdata={"custid":custrow["custid"],"custname":custrow["custname"],"custaddr":custrow["custaddr"],"gstin":custrow["gstin"],"custtan":custrow["custtan"]}
                    print "\n \n this is customer data "+str(custdata)
                else:
                    suppdata={"custid":custrow["custid"],"custname":custrow["custname"],"custaddr":custrow["custaddr"],"gstin":custrow["gstin"],"custtan":custrow["custtan"]}
                    print "\n \n this is supp data "+str(suppdata)
                userresult=self.con.execute(select([users.c.userid,users.c.username,users.c.userrole]).where(users.c.userid==drcrrow["userid"]))
                userrow=userresult.fetchone()
                userdata={"userid":userrow["userid"],"username":userrow["username"],"userrole":userrow["userrole"]}
                print "\n \n user data "+str(userdata)
                #to extract issuername and designation from invoice and user login
                a=15
                if a==15:
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

    @view_config(request_method='GET',request_param="drcr=all", renderer ='json')
    def getAlldrcr(self):
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
                result = self.con.execute(select([drcr.c.drcrno,drcr.c.drcrid,drcr.c.drcrdate,drcr.c.invid,drcr.c.dctypeflag,drcr.c.totreduct,drcr.c.attachmentcount]).where(drcr.c.orgcode==authDetails["orgcode"]).order_by(drcr.c.drcrdate))
                drcrdata = []
                for row in result:
                    #invoice,cust
                    inv=self.con.execute(select([invoice.c.custid]).where(invoice.c.invid==row["invid"]))
                    invdata=inv.fetchone()
                    # print "\n \n invdata from all ="+str(invdata)
                    custsupp=self.con.execute(select([customerandsupplier.c.custname,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invdata["custid"]))
                    custsuppdata= custsupp.fetchone()
                    #print "\n \n custdata from all ="+str(custsuppdata)
                    if self.request.params.has_key('drcrflagstatus'):                        
                        if int(self.request.params["drcrflagstatus"]) ==4 and custsuppdata["csflag"]==19:
                            if int(self.request.params["drcrflagstatus"])==int(row["dctypeflag"]):
                                if self.request.params.has_key('caseflagstatus'): 
                                    if int(self.request.params["caseflagstatus"])==0 or int(self.request.params["caseflagstatus"])==2:
                                        print "0 and 2 and supp data \n \n "
                                        drcrdata.append({"drcrid":row["drcrid"],"drcrno":row["drcrno"],"drcrdate":row["drcrdate"],"dctypeflag":row["dctypeflag"],"totreduct":row["totreduct"],"invid":row["invid"],"attachmentcount":row["attachmentcount"],"custid":invdata["custid"],"custname":custsuppdata["custname"],"csflag":custsuppdata["csflag"]})
                                        print "\n \n supp data"+str(drcrdata)
                                        
                        elif int(self.request.params["drcrflagstatus"]) == 3 and custsuppdata["csflag"]==3:
                            if int(self.request.params["drcrflagstatus"])==int(row["dctypeflag"]):
                                if self.request.params.has_key('caseflagstatus'):
                                    if int(self.request.params["caseflagstatus"])==1 or int(self.request.params["caseflagstatus"])==3:
                                        print "1 and 3  cust data"
                                        drcrdata.append({"drcrid":row["drcrid"],"drcrno":row["drcrno"],"drcrdate":row["drcrdate"],"dctypeflag":row["dctypeflag"],"totreduct":row["totreduct"],"invid":row["invid"],"attachmentcount":row["attachmentcount"],"custid":invdata["custid"],"custname":custsuppdata["custname"],"csflag":custsuppdata["csflag"]})
                                        print "\n \n cust data"+str(drcrdata)
                                                                                     
                    else:
                        print "all datata"
                        drcrdata.append({"drcrid":row["drcrid"],"drcrno":row["drcrno"],"drcrdate":row["drcrdate"],"dctypeflag":row["dctypeflag"],"totreduct":row["totreduct"],"invid":row["invid"],"attachmentcount":row["attachmentcount"],"custid":invdata["custid"],"custname":custsuppdata["custname"],"csflag":custsuppdata["csflag"]})
                                        

                #return {"gkstatus": gkcore.enumdict["Success"], "gkresult":drcrdata }
            #except:
                #return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
            #finally:
                self.con.close()



    
