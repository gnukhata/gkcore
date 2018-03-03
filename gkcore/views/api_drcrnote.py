from gkcore import eng, enumdict
from gkcore.models.gkdb import invoice,tax,state,drcr,customerandsupplier,users,product,unitofmeasurement
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
                drcrresult=self.con.execute(select([drcr]).where(drcr.c.drcrid==self.request.params["drcrid"]))
                drcrrow=drcrresult.fetchone()
                invresult=self.con.execute(select([invoice]).where(invoice.c.invid==drcrrow["invid"]))
                invrow=invresult.fetchone()
                custresult=self.con.execute(select([customerandsupplier.c.custid,customerandsupplier.c.custname,customerandsupplier.c.custaddr,customerandsupplier.c.gstin,customerandsupplier.c.custtan,customerandsupplier.c.csflag]).where(customerandsupplier.c.custid==invrow["custid"]))
                custrow=custresult.fetchone()
                invdata={}
                custSupDetails={}
                drcrdata={}
                #common data
                 #cust and supp data
                if custrow["csflag"]==3:
                    #customer data
                    custsuppdata={"custid":custrow["custid"],"custname":custrow["custname"],"custaddr":custrow["custaddr"],"gstin":custrow["gstin"],"custtan":custrow["custtan"]}
                    print "\n \n this is customer data "+str(custsuppdata)
                      
                else:
                    #supplier data
                    custsuppdata={"custid":custrow["custid"],"custname":custrow["custname"],"custaddr":custrow["custaddr"],"gstin":custrow["gstin"],"custtan":custrow["custtan"]}
                    print "\n \n this is supp data "+str(custsuppdata)

                    
                #tin and gstin
                if custsuppdata["custtan"] != None:
                    custSupDetails["custtin"] = custsuppdata["custtan"]
                    if custsuppdata["gstin"] != None:
                        if int(custrow["csflag"]) == 3 :
                            try:
                                custSupDetails["custgstin"] = custsuppdata["gstin"][str(taxStateCode)]
                            except:
                                custSupDetails["custgstin"] = None
                        else:
                            try:
                                custSupDetails["custgstin"] = custsuppdata["gstin"][str(sourceStateCode)]
                            except:
                                custSupDetails["custgstin"] = None

                drcrdata["custSupDetails"] = custSupDetails
                print drcrdata
              
                #user deatils
                
                userresult=self.con.execute(select([users.c.userid,users.c.username,users.c.userrole]).where(users.c.userid==drcrrow["userid"]))
                userrow=userresult.fetchone()
                userdata={"userid":userrow["userid"],"username":userrow["username"],"userrole":userrow["userrole"]}
                print "\n \n user data "+str(userdata)
               

                #a is inoutflag and srcstate and taxstate
                a=9
                if invrow["sourcestate"] != None or invrow["taxstate"] !=None:
                    if a==9 :
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

               

                #all data checked using flag
                #n is inout flag
                n=15
                if drcrrow["dctypeflag"]==3 and n==15:
                    #to extract issuername and designation from invoice and user login
                    invdata["issuername"]=invrow["issuername"]
                    invdata["designation"]=invrow["designation"]
                    print "inv data sale "+str(invdata)
                    if drcrrow["caseflag"] == 1 :
                        print "FROM 3 15 1 "
                        drcrdata = {"drcrid":drcrrow["drcrid"],"drcrno":drcrrow["drcrno"],"drcrdate":datetime.strftime(drcrrow["drcrdate"],"%d-%m-%Y"),"dctypeflag":drcrrow["dctypeflag"],"caseflag":drcrrow["caseflag"],"totreduct":"%.2f"%float(drcrrow["totreduct"]),"contents":drcrrow["contents"],"reference":drcrrow["reference"]}
                        #print "\n \n drcr data"+str(drcrdata)
                        invdata={"invid":invrow["invid"],"invoiceno":invrow["invoiceno"],"invoicedate":datetime.strftime(invrow["invoicedate"],"%d-%m-%Y"),"inoutflag":invrow["inoutflag"],"taxflag":invrow["taxflag"],"tax":invrow["tax"]}  
                        print " \n \n invoice data"+str(invdata)
                    elif drcrrow["caseflag"] == 3 :
                        print "from 3 15 3 rejection"
                        
                elif drcrrow["dctypeflag"]==4 and n==9 :
                    #to extract issuername and designation from invoice and user login
                    invdata["issuername"]=userrow["username"]
                    invdata["designation"]=userrow["userrole"]
                    print "invdata"+str(invdata) 
                    if drcrrow["caseflag"] == 0 :
                        print "FROM 4 9  0"
                        drcrdata = {"drcrid":drcrrow["drcrid"],"drcrno":drcrrow["drcrno"],"drcrdate":datetime.strftime(drcrrow["drcrdate"],"%d-%m-%Y"),"dctypeflag":drcrrow["dctypeflag"],"caseflag":drcrrow["caseflag"],"totreduct":"%.2f"%float(drcrrow["totreduct"]),"contents":drcrrow["contents"],"reference":drcrrow["reference"]}
                        #print "\n \n drcr data"+str(drcrdata)
                        invdata={"invid":invrow["invid"],"invoiceno":invrow["invoiceno"],"invoicedate":datetime.strftime(invrow["invoicedate"],"%d-%m-%Y"),"inoutflag":invrow["inoutflag"],"taxflag":invrow["taxflag"],"tax":invrow["tax"]}  
                        print " \n \n invoice data"+str(invdata)
                    elif drcrrow["caseflag"]==2:
                        print "from 4 9 2  rejection"  

                
                #calculations and prodcut data

                #contents is a nested dictionary from drcr table.
                #It contains productcode as the key with a value as a dictionary.
                #this dictionary has two key value paire, priceperunit and quantity.
                contentsData = drcrrow["contents"]
                #invContents is the finally dictionary which will not just have the dataset from original contents,
                #but also productdesc,unitname,freeqty,discount,taxname,taxrate,amount and taxam
                drcrContents = {}
                #get the dictionary of discount and access it inside the loop for one product each.
                #do the same with freeqty.
                totalDisc = 0.00
                totalTaxableVal = 0.00
                totalTaxAmt = 0.00
                totalCessAmt = 0.00
                discounts = invrow["discount"]
                
                #pc will have the productcode which will be the key in drcrContents.
                for pc in contentsData.keys():
                    if discounts != None:
                        discount=discounts[pc]
                        print "hiiii"
                    else:
                        discount= 0.00
                        print "hello"
                
                    prodresult = self.con.execute(select([product.c.productdesc,product.c.uomid,product.c.gsflag,product.c.gscode]).where(product.c.productcode == pc))
                    prodrow = prodresult.fetchone()

                    #product or service check and taxableAmount calculate=newppu*newqty
                    if int(prodrow["gsflag"]) == 7:
                        umresult = self.con.execute(select([unitofmeasurement.c.unitname]).where(unitofmeasurement.c.uomid == int(prodrow["uomid"])))
                        umrow = umresult.fetchone()
                        unitofMeasurement = umrow["unitname"]
                        taxableAmount = ((float(contentsData[pc][contentsData[pc].keys()[0]])) * float(contentsData[pc].keys()[0])) - float(discount)
                    else:
                        unitofMeasurement = ""
                        taxableAmount = float(contentsData[pc].keys()[0]) - float(discount)
                    
                    #taxflag checked to check vat and gst
                    taxRate = 0.00
                    totalAmount = 0.00
                    taxRate =  float(invrow["tax"][pc])
                    if int(invrow["taxflag"]) == 22:
                        taxRate =  float(invrow["tax"][pc])
                        taxAmount = (taxableAmount * float(taxRate/100))
                        taxname = 'VAT'
                        totalAmount = float(taxableAmount) + (float(taxableAmount) * float(taxRate/100))
                        totalDisc = totalDisc + float(discount)
                        totalTaxableVal = totalTaxableVal + taxableAmount
                        totalTaxAmt = totalTaxAmt + taxAmount
                        drcrContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][contentsData[pc].keys()[0]])),"priceperunit":"%.2f"% (float(contentsData[pc].keys()[0])),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":"VAT","taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount))}

                    else:
                        cessRate = 0.00
                        cessAmount = 0.00
                        cessVal = 0.00
                        taxname = ""
                        if invrow["cess"] != None:
                            cessVal = float(invrow["cess"][pc])
                            cessAmount = (taxableAmount * (cessVal/100))
                            totalCessAmt = totalCessAmt + cessAmount

                        if invrow["sourcestate"] != invrow["taxstate"]:
                            taxname = "IGST"
                            taxAmount = (taxableAmount * (taxRate/100))
                            totalAmount = taxableAmount + taxAmount + cessAmount
                        else:
                            taxname = "SGST"
                            taxRate = (taxRate/2)
                            taxAmount = (taxableAmount * (taxRate/100))
                            totalAmount = taxableAmount + (taxableAmount * ((taxRate * 2)/100)) + cessAmount
  
                        totalDisc = totalDisc + float(discount)
                        totalTaxableVal = totalTaxableVal + taxableAmount
                        totalTaxAmt = totalTaxAmt + taxAmount

                        drcrContents[pc] = {"proddesc":prodrow["productdesc"],"gscode":prodrow["gscode"],"uom":unitofMeasurement,"qty":"%.2f"% (float(contentsData[pc][contentsData[pc].keys()[0]])),"priceperunit":"%.2f"% (float(contentsData[pc].keys()[0])),"discount":"%.2f"% (float(discount)),"taxableamount":"%.2f"%(float(taxableAmount)),"totalAmount":"%.2f"% (float(totalAmount)),"taxname":taxname,"taxrate":"%.2f"% (float(taxRate)),"taxamount":"%.2f"% (float(taxAmount)),"cess":"%.2f"%(float(cessAmount)),"cessrate":"%.2f"%(float(cessVal))}
                drcrdata["totaldiscount"] = "%.2f"% (float(totalDisc))
                drcrdata["totaltaxablevalue"] = "%.2f"% (float(totalTaxableVal))
                drcrdata["totaltaxamt"] = "%.2f"% (float(totalTaxAmt))
                drcrdata["totalcessamt"] = "%.2f"% (float(totalCessAmt))
                drcrdata['taxname'] = taxname
                drcrdata["drcrcontents"] = drcrContents
                print drcrdata
                #return {"gkstatus":gkcore.enumdict["Success"],"gkresult":drcrdata}
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
                                print "debit supp data \n \n "
                                drcrdata.append({"drcrid":row["drcrid"],"drcrno":row["drcrno"],"drcrdate":row["drcrdate"],"dctypeflag":row["dctypeflag"],"totreduct":row["totreduct"],"invid":row["invid"],"attachmentcount":row["attachmentcount"],"custid":invdata["custid"],"custname":custsuppdata["custname"],"csflag":custsuppdata["csflag"]})
                                print "\n \n supp data"+str(drcrdata)
                                        
                        elif int(self.request.params["drcrflagstatus"]) == 3 and custsuppdata["csflag"]==3:
                            if int(self.request.params["drcrflagstatus"])==int(row["dctypeflag"]):
                                print "credit cust data"
                                drcrdata.append({"drcrid":row["drcrid"],"drcrno":row["drcrno"],"drcrdate":row["drcrdate"],"dctypeflag":row["dctypeflag"],"totreduct":row["totreduct"],"invid":row["invid"],"attachmentcount":row["attachmentcount"],"custid":invdata["custid"],"custname":custsuppdata["custname"],"csflag":custsuppdata["csflag"]})
                                print "\n \n cust data"+str(drcrdata)
                                                                                     
                    else:
                        print "all datata if dctypeflag doed not have key"
                        drcrdata.append({"drcrid":row["drcrid"],"drcrno":row["drcrno"],"drcrdate":row["drcrdate"],"dctypeflag":row["dctypeflag"],"totreduct":row["totreduct"],"invid":row["invid"],"attachmentcount":row["attachmentcount"],"custid":invdata["custid"],"custname":custsuppdata["custname"],"csflag":custsuppdata["csflag"]})
                                        

                #return {"gkstatus": gkcore.enumdict["Success"], "gkresult":drcrdata }
            #except:
                #return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
            #finally:
                self.con.close()
    '''
    Deleteing drcr on the basis of reference and drcrid
    '''
    @view_config(request_method='DELETE', renderer ='json')
    def deletedrcr(self):
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		authDetails = authCheck(token)
		if authDetails["auth"]==False:
			return {"gkstatus":enumdict["UnauthorisedAccess"]}
		else:
			#try:
			    self.con = eng.connect()
                dataset = self.request.json_body
                result=self.con.execute(select([drcr.c.drcrid,drcr.c.reference]).where(drcr.c.drcrid==dataset["drcrid"]))
                row=result.fetchone()                
                if not row["reference"]:
                     result = self.con.execute(drcr.delete().where(drcr.c.drcrid==dataset["drcrid"]))
                else:
                    print "not"
                #return {"gkstatus":enumdict["Success"]}
			#except exc.IntegrityError:
			#return {"gkstatus":enumdict["ActionDisallowed"]}
			#except:
			#return {"gkstatus":enumdict["ConnectionFailed"] }
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
                ur = getUserRole(authDetails["userid"])
                urole = ur["gkresult"]
                drcrid = self.request.params["drcrid"]
                drcrData = self.con.execute(select([drcr.c.drcrno, drcr.c.attachment]).where(drcr.c.drcrid == drcrid))
                attachment = drcrData.fetchone()
                return {"gkstatus":enumdict["Success"],"gkresult":attachment["attachment"],"drcrno":attachment["drcrno"],"userrole":urole["userrole"]}
            except:
                return {"gkstatus":enumdict["ConnectionFailed"]}
            finally:
                self.con.close()
                
    '''Update for debit and credit note.'''
    @view_config(request_method='PUT', renderer='json')
    def editDrCrNote(self):
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
                result = self.con.execute(drcr.update().where(drcr.c.drcrid==dataset["drcrid"]).values(dataset))
                return {"gkstatus":enumdict["Success"]}
            except:
                return {"gkstatus":gkcore.enumdict["ConnectionFailed"] }
            finally:
                self.con.close()

    
