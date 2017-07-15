
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
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
"Prajkta Patkar"<prajakta@dff.org.in>


Main entry point:
This package initializer module is run when the application is served.
The module contains enum dict containing all gnukahta success and failure messages.
It also contains all the routes which are connected to respective resources.
To trace the link of the routes we look at the name of a route and then see where it appeares in any of the @view_defaults or @view_config decorator of any resource.
This module also scanns for the secret from the database which is then used for jwt authentication.
"""

from pyramid.config import Configurator
from gkcore.models.meta import dbconnect
from gkcore.views import *
from webob import request
from webob.request import Request
from wsgicors import CORS
try:
    eng = dbconnect()
    resultset = eng.execute("select * from signature")
    row = resultset.fetchone()
    secret = row[0]
    #print secret
except:
    secret = ""

enumdict = {"Success":0,"DuplicateEntry":1,"UnauthorisedAccess":2,"ConnectionFailed":3,"BadPrivilege":4, "ActionDisallowed":5}

def calTax(taxflag,source,destination,productcode,con):
        """
        Purpose:
        Takes the product code and returns tax rate based on inter or intra state basis.
        Description:
        This function takes product code, custermer and supplier states and taxflag as parameters and 
        returns the tax rate (either GST or VAT).
        The function searches the tax table for the tax rate given the productcode.
        If GST is sent as taxflag then IGST is returned for inter state sales.
        For this the 2 states provided as parameters must be different.
        If it is intra state then IGST is divided by 2 and the values are sent as CGST and SGST.
        Returns the taxname and tax rate as dictionary in gkresult.
        """
        
        if taxflag == 22:
            #this is VAT.
            if source == destination:
                taxResult = con.execute(select([tax.c.taxrate]).where(and_(tax.c.taxname == 'VAT',tax.c.productcode == productcode)))
                taxData = taxResult.fetchone()
                return{"gkstatus":enumdict["Success"],"gkresult":{"taxname":"VAT","taxrate":"%.2f"%float(taxData["taxrate"])}}
            else:
                taxResult = con.execute(select([tax.c.taxrate]).where(and_(tax.c.taxname == 'CVAT',tax.c.productcode == productcode)))
                taxData = taxResult.fetchone()
                return{"gkstatus":enumdict["Success"],"gkresult":{"taxname":"CVAT","taxrate":"%.2f"%float(taxData["taxrate"])}}
        else:
            #since it is not 22 means it is 7 = "GST".
            if source == destination:
                #this is SGST and CGST.
                #IGST / 2 = SGST and CGST.
                taxResult = con.execute(select([tax.c.taxrate]).where(and_(tax.c.taxname == 'IGST',tax.c.productcode == productcode)))
                taxData = taxResult.fetchone()
                gst = float(taxData["taxrate"]) /2
                #note although we are returning only SGST, same rate applies to CGST.
                #so when u see taxname is sgst then cgst with same rate is asumed.                                                
                return{"gkstatus":enumdict["Success"],"gkresult":{"taxname":"SGST","taxrate":"%.2f"%float(gst)}}
            else:
                #this is IGST.
                taxResult = con.execute(select([tax.c.taxrate]).where(and_(tax.c.taxname == 'IGST',tax.c.productcode == productcode)))
                taxData = taxResult.fetchone()
                return{"gkstatus":enumdict["Success"],"gkresult":{"taxname":"IGST","taxrate":"%.2f"%float(taxData["taxrate"])}}
                        

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.add_route("organisation","/organisation")
    config.add_route("invoice","/invoice")
    config.add_route("organisations","/organisations")
    config.add_route("categoryspecs","/categoryspecs")
    config.add_route("orgyears","/orgyears/{orgname}/{orgtype}")
    config.add_route("transaction","/transaction")
    config.add_route("users",'/users')
    config.add_route('user','/user')
    config.add_route('bankrecon','/bankrecon')
    config.add_route("accounts",'/accounts')
    config.add_route("account",'/account/{accountcode}')
    config.add_route("projects",'/projects')
    config.add_route("project",'/project/{projectcode}')
    config.add_route("customersupplier",'/customersupplier')
    config.add_route("unitofmeasurement","/unitofmeasurement")
    config.add_route("accountsbyrule",'/accountsbyrule')
    config.add_route("login",'/login')
    config.add_route("groupallsubgroup","/groupallsubgroup/{groupcode}")
    config.add_route("groupsubgroup","/groupsubgroup/{groupcode}")
    config.add_route("groupsubgroups","/groupsubgroups")
    config.add_route("groupDetails","/groupDetails/{groupcode}")
    config.add_route("report","/report")
    config.add_route("rollclose","/rollclose")
    config.add_route("forgotpassword","/forgotpassword")
    config.add_route("categories","/categories")
    config.add_route("products","/products")
    config.add_route("godown","/godown")
    config.add_route("delchal","/delchal")
    config.add_route("purchaseorder","/purchaseorder")
    config.add_route("transfernote","/transfernote")
    config.add_route("discrepancynote","/discrepancynote")
    config.add_route("tax","/tax")
    config.add_route("log", "/log")
    config.add_route("rejectionnote", "/rejectionnote")
    config.add_route('billwise','/billwise')

    config.scan("gkcore.views")

    return CORS(config.make_wsgi_app(),headers="*",methods="*",maxage="180",origin="*")
