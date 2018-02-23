
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018 Digital Freedom Foundation & Accion Labs Pvt. Ltd.
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
"""
from sqlalchemy.dialects.postgresql.json import JSONB

"""
This module contains the sqlalchemy expression based table definitions.
They will be converted to real sql statements and tables will be subsequently created by create_all function in initdb.py.
"""
import datetime
from sqlalchemy.dialects.postgresql import JSONB, JSON

from sqlalchemy import (
    Table,
    Column,
    Index,
    Integer,
    Text,
    Unicode,     #<- will provide Unicode field
    UnicodeText, #<- will provide Unicode text field
DateTime,
Date
     #<- time abstraction field
    )
from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import BOOLEAN, Numeric, UnicodeText, Integer
from sqlalchemy import MetaData

#metadata is the module that converts Python code into real sql statements, specially for creating tables.
metadata = MetaData()
""" table for secret code that is used to decode json objects.
This will be generated during the database setup.
"""
signature = Table('signature', metadata,
    Column('secretcode',UnicodeText, primary_key=True))
""" organisation table for saving basic details including type, financial year start and end, flags for roll over and close books.
Also stores other details like the pan or sales tax number.
bankdetails is a dictionary will have bankname,accountno., branchname and ifsccode
Every time a new organisation is created or recreated for it's new financial year, a new record is added.
ivflag = inventory flag , billflag = billwise accounting , invsflag = invoicing
"""

"""
This table is for stroring records of debit note and credit note.
Structure of a tax field is {productcode:taxrate} and it is for calculating reduction of tax(VAT/GST).
In this we have json field that is contents.
This field is a nested dictionary.
The key of this field is the productcode while value is another dictionary.
This has a key as price per unit (ppu) and value as quantity (qty) of product.
"""
drcr =  Table('drcr', metadata,             
    Column('drcrid',Integer,primary_key=True),
    Column('drcrno',UnicodeText, nullable=False),
    Column('invid', Integer, ForeignKey('invoice.invid'),nullable=False),
    Column('rnid', Integer, ForeignKey('rejectionnote.rnid')),
    Column('orgcode', Integer,ForeignKey('organisation.orgcode',ondelete="CASCADE"),nullable=False),
    Column('drcrdate',DateTime,nullable=False),
    Column('dctypeflag', Integer, default=3),
    Column('caseflag', Integer, default=3),
    Column('taxflag',Integer,default=22),
    Column('tax', JSONB),
    Column('totreduct',Numeric(13,2),default=0.00),
    Column('contents',JSONB),
    Column('reference',JSONB),
    Column('attachment',JSON),
    Column('attachmentcount',Integer,default=0),
    Column('userid',Integer,ForeignKey('users.userid')),
    UniqueConstraint('orgcode','drcrno','dctypeflag')
   )


"""
This table is for storing state information.  
A state will have its corresponding code with name.
"""
state = Table('state',metadata,
        Column('statecode',Integer),
        Column('statename',UnicodeText) 
)

organisation = Table( 'organisation' , metadata,
    Column('orgcode',Integer, primary_key=True),
    Column('orgname',UnicodeText, nullable=False),
    Column('orgtype',UnicodeText, nullable=False),
    Column('yearstart',Date, nullable=False),
    Column('yearend',Date, nullable=False),
    Column('orgcity',UnicodeText),
    Column('orgaddr',UnicodeText),
    Column('orgpincode',Unicode(30)),
    Column('orgstate',UnicodeText),
    Column('orgcountry',UnicodeText),
    Column('orgtelno',UnicodeText),
    Column('orgfax',UnicodeText),
    Column('orgwebsite',UnicodeText),
    Column('orgemail',UnicodeText),
    Column('orgpan',UnicodeText),
    Column('orgmvat',UnicodeText),
    Column('orgstax',UnicodeText),
    Column('orgregno',UnicodeText),
    Column('orgregdate',UnicodeText),
    Column('orgfcrano',UnicodeText),
    Column('orgfcradate',UnicodeText),
    Column('roflag',Integer, default=0),
    Column('booksclosedflag',Integer,default=0),
    Column('invflag',Integer,default=0),
    Column('billflag',Integer,default=1),
    Column('invsflag',Integer,default=1),
    Column('logo',JSON),
    Column('gstin',JSONB),
    Column('bankdetails',JSON),
    UniqueConstraint('orgname','orgtype','yearstart'),
    UniqueConstraint('orgname','orgtype','yearend'),
    Index("orgindex", "orgname","yearstart","yearend")
    )

""" the table for groups and subgroups.
Note that the groupcode is used as an internal (self referencing) foreign key named subgroupof.
So every group is either a parent group or subgroup who will have the groupcode as foreign key in subgroup off to which this subgroup belongs.This essentially means a group can be a subgroup of a parent group who's groupcode is in it's subgroupof field."""

groupsubgroups = Table('groupsubgroups', metadata,
    Column('groupcode',Integer,primary_key=True),
    Column('groupname',UnicodeText,  nullable=False),
    Column('subgroupof',Integer),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
    UniqueConstraint('orgcode','groupname'),
    Index("grpindex","orgcode","groupname")
    )
"""
table for categories and subcategories.
This table is for storing names of categories and their optional one or many subcategories.
Note that subcategory might have it's own subcategories and so on.
The way we achieve this multi level tree is by having categorycode which is primary key of the table.
Now this key becomes foreign key in the same table under the name subcategoryof.
So if a category has a value in subcategoryof wich matches another categorycode, then that category becomes the subcategory.
"""

categorysubcategories = Table('categorysubcategories', metadata,
    Column('categorycode',Integer,primary_key=True),
    Column('categoryname',UnicodeText,  nullable=False),
    Column('subcategoryof',Integer),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
    UniqueConstraint('orgcode','categoryname'),
    Index("catindex","orgcode","categoryname")
    )
"""
This is the table for maintaining the ontology.
Once you have defined the name of category,this table will store the attributes of that category, as in what features are there.
this table not just stores the list of attributes of the category, but also the type, as in text, number, true false etc.
Needless to say that the categorycode becomes a foreign key here.
The type will be an enum, eg. 0= number, 1=text etc.
"""
categoryspecs = Table('categoryspecs',metadata,
    Column('spcode',Integer, primary_key=True),
    Column('attrname',UnicodeText, nullable=False),
    Column('attrtype',Integer,nullable=False),
    Column('productcount', Integer ,default=0),
    Column('categorycode',Integer,ForeignKey('categorysubcategories.categorycode',ondelete="CASCADE"),nullable=False),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
    UniqueConstraint('categorycode','attrname'),
    Index("catspecindex","orgcode","attrname")
    )
"""
This table is for unit of measurement for products.
The unit of measurement has units, conversion rates and its resulting unit.
"""
unitofmeasurement = Table('unitofmeasurement',metadata,
    Column('uomid',Integer,primary_key=True),
    Column('unitname',UnicodeText,nullable=False),
    Column('conversionrate',Numeric(13,2),default=0.00),
    Column('subunitof',Integer),
    Column('frequency',Integer),
    UniqueConstraint('unitname'),
    Index("unitofmeasurement_frequency","frequency"),
    Index("unitofmeasurement_unitname","unitname")
    )
"""
This table is for product, based on a certain category.
The products are stored on the basis of the selected category and must have data exactly matching the attributes or properties as one may call it.
The table is having a json field which has the keys matching the attributes from the spects table for a certain category.
gscode is to store gstin or accounting service code, gsflag is 7 for gstin and 19 for service code. 
1 organisation cannot have same products.
"""
product = Table('product',metadata,
    Column('productcode',Integer,primary_key=True),
    Column('gscode',UnicodeText),
    Column('gsflag',Integer),
    Column('productdesc',UnicodeText),
    Column('openingstock', Numeric(13,2),default=0.00),
    Column('specs', JSONB),
    Column('categorycode',Integer,ForeignKey('categorysubcategories.categorycode',ondelete="CASCADE")),
    Column('uomid',Integer,ForeignKey('unitofmeasurement.uomid',ondelete="CASCADE")),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
    UniqueConstraint('categorycode','productdesc'),
    UniqueConstraint('productdesc','orgcode'),
    Index("product_orgcodeindex","orgcode"),
    Index("product_categorycode","categorycode")
    )
"""
Table for customers and suppliers.
We need this data when we sell goods or service.
Also when we purchase the same.
The reason to store this data is that we may need it in both invoice and delivery chalan.
Here the csflag is 3 for customer and 19 for supplier
gstin to store unique code of cust/supp for gst for every state (json)
Bankdetails is a dictionary will have bankname,accountno., branchname and ifsccode.
"""
customerandsupplier = Table('customerandsupplier',metadata,
    Column('custid',Integer,primary_key=True),
    Column('custname',UnicodeText,nullable=False),
    Column('gstin',JSONB),
    Column('custaddr',UnicodeText),
    Column('custphone',UnicodeText),
    Column('custemail',UnicodeText),
    Column('custfax',UnicodeText),
    Column('custpan',UnicodeText),
    Column('custtan',UnicodeText),
    Column('custdoc',JSONB),
    Column('state', UnicodeText),
    Column('csflag',Integer,nullable=False),
    Column('bankdetails',JSONB),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
    UniqueConstraint('orgcode','custname'),
    UniqueConstraint('orgcode','custname','custemail','csflag'),
    UniqueConstraint('orgcode','custname','custpan','csflag'),
    UniqueConstraint('orgcode','custname','custtan','csflag'),
    UniqueConstraint('orgcode','custname','gstin'),
    Index("customer_supplier_orgcodeindex","orgcode")
    )
""" table to store accounts.
Every account belongs to either a group or subgroup.
For one organisation in a single financial year, an account name can never be duplicated.
So it has  2 foreign keys, first the orgcode of the organisation to which it belongs, secondly
the groupcode to with it belongs."""

accounts = Table('accounts', metadata,
    Column('accountcode',Integer, primary_key=True ),
    Column('accountname',UnicodeText, nullable=False),
    Column('groupcode',Integer, ForeignKey('groupsubgroups.groupcode'), nullable=False),
    Column('openingbal', Numeric(13,2),default=0.00),
    Column('vouchercount', Integer ,default=0),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    UniqueConstraint('orgcode','accountname'),
    Index("accindex","orgcode","accountname")
    )
""" table for storing projects for one organisation.
This means that it has one foreign key, namely the org code of the organisation to which it belongs. """
projects = Table('projects', metadata,
    Column('projectcode',Integer, primary_key=True),
    Column('projectname',UnicodeText, nullable=False),
    Column('sanctionedamount',Numeric(13,2),default=0.00),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    UniqueConstraint('orgcode','projectname')
    )
""" table to store vouchers.
This table has one foreign key from organisation to which it belongs and has the project code to which it belongs.
Additionally this table has 2 json fields named Drs and Crs.
These are the fields which actually store the dr or cr amounts which their respective account codes of the accounts which are used in those transactions.
Key is the account code and value is the amount.
This helps us to store multiple Drs and Crs because there can be many key-value pares in the dictionary field.
Apart from this orgcode is there as the foreign key.  We also connect the invoice table where sales or purchase happens.  So there is a nullable foreign key here. """
vouchers=Table('vouchers', metadata,
    Column('vouchercode',Integer,primary_key=True),
    Column('vouchernumber',UnicodeText, nullable=False),
    Column('voucherdate',DateTime,nullable=False),
    Column('entrydate',DateTime,nullable=False,default=datetime.datetime.now().date()),
    Column('narration',UnicodeText),
    Column('drs',JSONB,nullable=False),
    Column('crs',JSONB,nullable=False),
    Column('prjdrs',JSONB),
    Column('prjcrs',JSONB),
    Column('attachment',JSON),
    Column('attachmentcount',Integer,default=0),
    Column('vouchertype',UnicodeText, nullable=False),
    Column('lockflag',BOOLEAN,default=False),
    Column('delflag',BOOLEAN,default=False),
    Column('projectcode',Integer, ForeignKey('projects.projectcode')),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    Column('invid',Integer,ForeignKey('invoice.invid')),
    Column('instrumentno',UnicodeText),
    Column('bankname',UnicodeText),
    Column('branchname',UnicodeText),
    Column('instrumentdate',DateTime),
    Index("voucher_orgcodeindex","orgcode"),
    Index("voucher_entrydate","entrydate"),
    Index("voucher_vno","vouchernumber"),
    Index("voucher_vdate","voucherdate")
    )



"""
Table for storing invoice records.
Every row represents one invoice.
taxflag states which tax is applied to products/services. Default value is set as 22 for VAT and if it is GST 7 will be set as taxflag.
Apart from the number and date, we also have a json field called contents.
This field is a nested dictionary.
The key of this field is the productcode while value is another dictionary.
This has a key as price per unit (ppu) and value as quantity (qty).
Note that invoice is connected to a voucher.
So the accounting part is thus connected with stock movement of that cost.
A new json field called freeqty.
Consignee (shipped to) is a json field which has name , address, state, statecode,gstin as keys along with its value.
Bankdetails is a dictionary will have bankname,accountno., branchname and ifsccode.
taxstate is a destination sate.
sourcestate is source state from where invoice is initiated.
Structure of a tax field is {productcode:taxrate}
save orgstategstin of sourcestate for organisation.
paymentmode states that Mode of payment i.e 'bank' or 'cash'. Default value is set as 2 for 'bank' and 3 for 'cash'.
inoutflag states that invoice 'in' or 'out' (i.e 9 for 'in' and 15 for 'out') 
"""
invoice = Table('invoice',metadata,
    Column('invid',Integer,primary_key=True),
    Column('invoiceno',UnicodeText,nullable=False),
    Column('invoicedate',DateTime,nullable=False),
    Column('taxflag',Integer,default=22),
    Column('contents',JSONB),
    Column('issuername', UnicodeText),
    Column('designation', UnicodeText),
    Column('tax', JSONB),
    Column('cess',JSONB),
    Column('amountpaid',Numeric(13,2),default=0.00),
    Column('invoicetotal', Numeric(13,2),nullable=False),
    Column('icflag',Integer,default=9),
    Column('taxstate',UnicodeText),
    Column('sourcestate',UnicodeText),
    Column('orgstategstin',UnicodeText),
    Column('attachment',JSON),
    Column('attachmentcount',Integer,default=0),
    Column('orderid', Integer,ForeignKey('purchaseorder.orderid')),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    Column('custid',Integer, ForeignKey('customerandsupplier.custid')),
    Column('consignee',JSONB),
    Column('freeqty',JSONB),
    Column('reversecharge',UnicodeText),
    Column('bankdetails',JSONB),
    Column('transportationmode',UnicodeText),
    Column('vehicleno',UnicodeText),
    Column('dateofsupply',DateTime),
    Column('discount',JSONB),
    Column('paymentmode',Integer,default=2),
    Column('address',UnicodeText),
    Column('inoutflag',Integer),
    Column('invoicetotalword', UnicodeText),
    UniqueConstraint('orgcode','invoiceno','custid','icflag'),
    Index("invoice_orgcodeindex","orgcode"),
    Index("invoice_invoicenoindex","invoiceno")
    )
billwise = Table('billwise',metadata,
    Column('billid',Integer,primary_key=True),
    Column('vouchercode',Integer, ForeignKey('vouchers.vouchercode'),nullable=False),
    Column('invid',Integer,ForeignKey('invoice.invid'),nullable=False),
    Column('adjdate',DateTime),
    Column('adjamount',Numeric(12,2),nullable=False),
    Column('orgcode',Integer,ForeignKey('organisation.orgcode',ondelete="CASCADE"),nullable=False)
)

"""
Table for challan.
This table stores the delivary challans issues when the goods move out.
This is generally done when payment is due.
The invoice table and this table will be linked in a subsequent table.
This is done because one invoice may have several dc's attached and for one dc may have several invoices.
In a situation where x items have been shipped against a dc, the customer approves only x -2, so the invoice against this dc will have x -2 items.
Another invoice may be issued if the remaining two items are approved by the customer.
dcflag is used for type of transaction: 1 - Approval, 2 - consignment, 3 - Free Replacement, etc.
taxflag states which tax is applied to products/services. Default value is set as 22 for VAT and for GST 7 will be set as taxflag.
Also we have json field called 'contents' which is nested dictionary.
The key of this field is the 'productcode' while value is another dictionary.
This has a key as price per unit (ppu) and value as quantity (qty).
"""
delchal = Table('delchal',metadata,
    Column('dcid',Integer,primary_key=True),
    Column('dcno',UnicodeText,nullable=False),
    Column('dcdate',DateTime,nullable=False),
    Column('dcflag',Integer,nullable=False),
    Column('taxflag',Integer,default=22),
    Column('contents',JSONB),
    Column('tax', JSONB),
    Column('cess',JSONB),
    Column('issuername', UnicodeText),
    Column('designation', UnicodeText),
    Column('cancelflag',Integer,default=0),
    Column('canceldate',DateTime),
    Column('noofpackages', Integer, nullable=False),
    Column('modeoftransport', UnicodeText),
    Column('attachment',JSON),
    Column('consignee',JSONB),
    Column('taxstate',UnicodeText),
    Column('sourcestate',UnicodeText),
    Column('orgstategstin',UnicodeText),
    Column('freeqty',JSONB),
    Column('discount',JSONB),
    Column('vehicleno',UnicodeText),
    Column('dateofsupply',DateTime),
    Column('delchaltotal', Numeric(13,2), nullable=False),
    Column('attachmentcount',Integer,default=0),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    Column('custid',Integer, ForeignKey('customerandsupplier.custid')),
    Column('orderid',Integer, ForeignKey('purchaseorder.orderid',ondelete="CASCADE")),
    Column('inoutflag',Integer,nullable=False),
    UniqueConstraint('orgcode','dcno','custid'),
    Index("delchal_orgcodeindex","orgcode"),
    Index("delchal_dcnoindex","dcno")
    )
"""
The join table which has keys from both inv and dc table.
As explained before, one invoice may have many dc and one dc can be partially passed for many invoices.
"""
dcinv = Table('dcinv',metadata,
    Column('dcinvid',Integer,primary_key=True),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    Column('dcid',Integer, ForeignKey('delchal.dcid',ondelete="CASCADE")),
    Column('invid',Integer, ForeignKey('invoice.invid',ondelete="CASCADE")),
    Column('invprods',JSONB),
    UniqueConstraint('orgcode','dcid','invid'),
    Index("deinv_orgcodeindex","orgcode"),
    Index("deinv_dcidindex","dcid"),
    Index("deinv_invidindex","invid")
    )
"""
Table for stock.
This table records movement of goods and can give details either on basis of productcode,
invoice or dc (which ever is responsible for the movement ),
or by godown using the goid.
It has a field for product quantity.
it also has a field called dcinvtnflag which can tell if this movement was due to dc or inv or transfernote or rejection note(flag = 18).
This flag is necessary because,
Some times no dc is issued and a direct invoice is made (eg. cash memo at POS ).
So movements will be directly on invoice.
This is always the case when we purchase goods.
The inout field for in = 9 is stored and out = 15.
"""
stock = Table('stock',metadata,
    Column('stockid',Integer,primary_key=True),
    Column('productcode',Integer,ForeignKey('product.productcode'),nullable=False),
    Column('stockdate',DateTime),
    Column('qty',Numeric(13,2),nullable=False),
    Column('dcinvtnid', Integer,nullable=False),
    Column('dcinvtnflag',Integer,nullable=False),
    Column('inout',Integer,nullable=False),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    Column('goid',Integer, ForeignKey('godown.goid',ondelete="CASCADE")),
    Index("stock_orgcodeindex","orgcode"),
    Index("stock_productcodeindex","productcode"),
    Index("stock_dcinvtnid","dcinvtnid")
    )


""" table to store users for an organization.
Table for storing users for a particular organisation.
So orgcode is foreign key like other tables.
In addition this table has a field userrole which determines if the user is an admin:-1 manager:0 or operater:1 internal auditor:2 Godown In Charge:3"""
users=Table('users', metadata,
    Column('userid',Integer, primary_key=True),
    Column('username',Text, nullable=False),
    Column('userpassword',Text, nullable=False),
    Column('userrole',Integer, nullable=False),
    Column('userquestion',Text, nullable=False),
    Column('useranswer',Text, nullable=False),
    Column('themename',Text,default="Default"),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    UniqueConstraint('orgcode','username'),
    Index("userindex","orgcode","username")
    )

""" the table for storing bank reconciliation data.
Every row will have voucher code for which the transaction is being checked against bank record.
"""
bankrecon=Table('bankrecon',metadata,
    Column('reconcode',Integer,primary_key = True),
    Column('vouchercode',Integer,ForeignKey("vouchers.vouchercode", ondelete="CASCADE"), nullable=False),
    Column('accountcode',Integer, ForeignKey("accounts.accountcode", ondelete="CASCADE"), nullable=False),
    Column('clearancedate',DateTime),
    Column('memo',Text),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    UniqueConstraint('vouchercode','accountcode'),
    Index("bankrecoindex","clearancedate")
    )
"""
This is the table which acts as a bin for deleted vouchers.
While these vouchers can't be recovered, they are for investigation purpose if need be.
"""
voucherbin=Table('voucherbin', metadata,
    Column('vouchercode',Integer,primary_key=True),
    Column('vouchernumber',UnicodeText, nullable=False),
    Column('voucherdate',DateTime,nullable=False),
    Column('narration',UnicodeText),
    Column('drs',JSONB,nullable=False),
    Column('crs',JSONB,nullable=False),
    Column('vouchertype',UnicodeText, nullable=False),
    Column('projectname',UnicodeText, nullable=True),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    Index("binvoucher_orgcodeindex","orgcode"),
    Index("binvoucher_vno","vouchernumber"),
    Index("binvoucher_vdate","voucherdate")
    )

"""
table for purchase order.
This may or may not link to a certain invoice.
However if it is linked then we will have to compare the items with those in invoice.
psflag will be either 16 or 20 for purchase order and sales order respectively.

Here schedule json field will be having all the product details in format,
product code is key and value will be dictionary having product name, quantity, price per unit, number of packages, reorder limit, tax rate,
and  dictionary for saving staggered delivery details whose key will be date and value will be quantity.
"""
purchaseorder = Table( 'purchaseorder' , metadata,
    Column('orderid',Integer, primary_key=True),
    Column('orderno',UnicodeText,nullable=False),
    Column('orderdate', DateTime, nullable=False),
    Column('creditperiod', UnicodeText),
    Column('payterms',UnicodeText),
    Column('modeoftransport', UnicodeText),
    Column('issuername', UnicodeText),
    Column('designation', UnicodeText),
    Column('schedule',JSONB),
    Column('taxstate',UnicodeText),
    Column('psflag',Integer,nullable=False),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    Column('csid',Integer,ForeignKey('customerandsupplier.custid',ondelete="CASCADE"), nullable=False),
    Column('togodown',Integer,ForeignKey('godown.goid', ondelete = "CASCADE")),
    UniqueConstraint('orderno','orderdate','csid','psflag'),
    Index("purchaseorder_orgcodeindex","orgcode"),
    Index("purchaseorder_date","orderdate"),
    Index("purchaseorder_togodown",'togodown')
)


"""
Table for storing godown details.
Basically one organization may have many godowns and we aught to know from which one goods have moved out.
"""
godown = Table('godown',metadata,
    Column('goid',Integer,primary_key=True),
    Column('goname',UnicodeText),
    Column('goaddr',UnicodeText),
    Column('state', UnicodeText),
    Column('gocontact',UnicodeText),
    Column('contactname',UnicodeText),
    Column('designation',UnicodeText),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
    UniqueConstraint('orgcode','goname'),
    Index("godown_orgcodeindex","orgcode")
    )

"""
Table for storing product godownwise.
When products are stored in the different godowns its openingstick will be entered accordingly.
"""
goprod = Table('goprod',metadata,
    Column('goprodid',Integer,primary_key=True),
    Column('goid',Integer, ForeignKey('godown.goid', ondelete="CASCADE"), nullable=False),
    Column('productcode',Integer, ForeignKey('product.productcode', ondelete="CASCADE"), nullable=False),
    Column('goopeningstock',Numeric(13,2),default=0.00,nullable=False),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
    UniqueConstraint('goid','productcode','orgcode'),
    Index("godown_product","productcode")
    )
#now table for user godown rights.
usergodown = Table('usergodown',metadata,
                   Column('ugid', Integer, primary_key=True),
                   Column('goid',Integer, ForeignKey('godown.goid',ondelete='CASCADE')),
                   Column('userid',Integer, ForeignKey('users.userid', ondelete='CASCADE')),
                   Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False)
                   )

''' Table for transferNote details.
    When the goods are to be trasnferred from one godown to another or from godown to factory floor, or vice versa.

'''

transfernote = Table('transfernote',metadata,
    Column('transfernoteid',Integer,primary_key=True),
    Column('transfernoteno',UnicodeText),
    Column('transfernotedate', DateTime, nullable=False),
    Column('transportationmode', UnicodeText),
    Column('nopkt',Integer),
    Column('issuername',UnicodeText),
    Column('designation', UnicodeText),
    Column('recieved', BOOLEAN,default=False),
    Column('recieveddate', DateTime),
    Column('duedate', DateTime),
    Column('grace',Integer),
    Column('fromgodown',Integer,ForeignKey('godown.goid', ondelete = "CASCADE"),nullable = False),
    Column('togodown',Integer,ForeignKey('godown.goid', ondelete = "CASCADE"),nullable = False),
    Column('orgcode',Integer ,ForeignKey('organisation.orgcode',ondelete = "CASCADE"),nullable = False),
    UniqueConstraint('transfernoteno','orgcode'),
    Index("transfernote_date",'transfernotedate'),
    Index("transfernote_togodown",'togodown'),
    Index("transfernote_orgcode","orgcode")

)



"""table to store tax
This taxex would be vat , gst etc. For particular product and category (mutually exelusive)"""
tax = Table('tax',metadata,
    Column('taxid',Integer,primary_key=True),
    Column('taxname',UnicodeText,nullable=False),
    Column('taxrate',Numeric(5,2)),
    Column('state',UnicodeText),
    Column('productcode',Integer, ForeignKey('product.productcode',ondelete="CASCADE")),
    Column('categorycode',Integer, ForeignKey('categorysubcategories.categorycode',ondelete="CASCADE")),
    Column('orgcode',Integer ,ForeignKey('organisation.orgcode',ondelete = "CASCADE"),nullable = False),
    UniqueConstraint('state','taxname','productcode','orgcode'),
    UniqueConstraint('state','taxname','categorycode','orgcode'),
    Index("taxindex","productcode","taxname"),
    Index("tax_taxindex","categorycode","taxname")
    )

"""Table to store Log of users
This table will store all the activities made by different users. eg. created account at this time, deleted account, created voucher, etc."""
log = Table('log',metadata,
    Column('logid',Integer,primary_key=True),
    Column('time',DateTime),
    Column('activity',UnicodeText),
    Column('userid',Integer, ForeignKey('users.userid',ondelete="CASCADE")),
    Column('orgcode',Integer ,ForeignKey('organisation.orgcode',ondelete = "CASCADE"),nullable = False),
    Index("logindex","userid","activity")
    )

"""Table to store Rejection Note
This table will store invoice or delivery note id against which rejection note prepared
inout is a flag to indicate rejection in or out. in = 9, out = 15"""
rejectionnote = Table('rejectionnote',metadata,
    Column('rnid',Integer,primary_key=True),
    Column('rnno',UnicodeText, nullable=False),
    Column('rndate', DateTime, nullable=False),
    Column('inout', Integer, nullable=False),
    Column('dcid',Integer ,ForeignKey('delchal.dcid',ondelete = "CASCADE")),
    Column('invid',Integer ,ForeignKey('invoice.invid',ondelete = "CASCADE")),
    Column('issuerid',Integer,ForeignKey('users.userid',ondelete="CASCADE")),
    Column('orgcode',Integer ,ForeignKey('organisation.orgcode',ondelete = "CASCADE"),nullable = False),
    UniqueConstraint('rnno','inout', 'orgcode'),
    Index("rejection_note","orgcode")
    )
