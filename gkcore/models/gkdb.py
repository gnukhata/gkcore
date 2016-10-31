
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

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
	Unicode,	 #<- will provide Unicode field
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
Every time a new organisation is created or recreated for it's new financial year, a new record is added.
"""

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
	Column('tax',JSONB),
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
"""
product = Table('product',metadata,
	Column('productcode',Integer,primary_key=True),
	Column('productdesc',UnicodeText),
	Column('specs', JSONB,nullable=False ),
	Column('categorycode',Integer,ForeignKey('categorysubcategories.categorycode',ondelete="CASCADE"),nullable=False),
	Column('uomid',Integer,ForeignKey('unitofmeasurement.uomid',ondelete="CASCADE"),nullable=False),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
	UniqueConstraint('categorycode','productdesc'),
	Index("product_orgcodeindex","orgcode"),
	Index("product_categorycode","categorycode")
	)
"""
Table for customers and suppliers.
We need this data when we sell goods.
The reason to store this data is that we may need it in both invoice and delivery chalan.
Here the csflag is 3 for customer and 19 for supplier
"""
customerandsupplier = Table('customerandsupplier',metadata,
	Column('custid',Integer,primary_key=True),
	Column('custname',UnicodeText,nullable=False),
	Column('custaddr',UnicodeText),
	Column('custphone',UnicodeText),
	Column('custemail',UnicodeText),
	Column('custfax',UnicodeText),
	Column('custpan',UnicodeText),
	Column('custtan',UnicodeText),
	Column('custdoc',JSONB),
	Column('csflag',Integer,nullable=False),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
	UniqueConstraint('orgcode','custname','custemail'),
	UniqueConstraint('orgcode','custpan'),
	UniqueConstraint('orgcode','custtan'),
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
	Column('invid',ForeignKey('invoice.invid')),
	Index("voucher_orgcodeindex","orgcode"),
	Index("voucher_entrydate","entrydate"),
	Index("voucher_vno","vouchernumber"),
	Index("voucher_vdate","voucherdate")
	)



"""
Table for storing invoice records.
Every row represents one invoice.
Apart from the number and date, we also have a json field called contents.
This field is a nested dictionary.
The key of this field is the productcode while value is another dictionary.
This has a key as price per unit (ppu) and value as quantity (qty).
Note that invoice is connected to a voucher.
So the accounting part is thus connected with stock movement of that cost.
"""
invoice = Table('invoice',metadata,
	Column('invid',Integer,primary_key=True),
	Column('invoiceno',UnicodeText,nullable=False),
	Column('invoicedate',UnicodeText,nullable=False),
	Column('contents',JSONB),
	Column('orderno', UnicodeText,ForeignKey('purchaseorder.orderno')),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
	Column('custid',Integer, ForeignKey('customerandsupplier.custid',ondelete="CASCADE")),
	Column('orderno',UnicodeText, ForeignKey('purchaseorder.orderno',ondelete="CASCADE")),
	Index("invoice_orgcodeindex","orgcode"),
	Index("invoice_invoicenoindex","invoiceno")
	)
"""
Table for challan.
This table stores the delivary challans issues when the goods move out.
This is generally done when payment is due.
The invoice table and this table will be linked in a subsequent table.
This is done because one invoice may have several dc's attached and for one dc may have several invoices.
In a situation where x items have been shipped against a dc, the customer approves only x -2, so the invoice against this dc will have x -2 items.
Another invoice may be issued if the remaining two items are approved by the customer.
"""
delchal = Table('delchal',metadata,
	Column('dcid',Integer,primary_key=True),
	Column('dcno',UnicodeText,nullable=False),
	Column('dcdate',UnicodeText,nullable=False),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
	Column('custid',Integer, ForeignKey('customerandsupplier.custid',ondelete="CASCADE")),
	Column('orderno',UnicodeText, ForeignKey('purchaseorder.orderno',ondelete="CASCADE")),
	UniqueConstraint('orgcode','dcno'),
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
it also has a field called dcinvflag which can tell if this movement was due to dc or inv.
This flag is necessary because,
Some times no dc is issued and a direct invoice is made (eg. cash memo at POS ).
So movements will be directly on invoice.
This is always the case when we purchase goods.
The inout field is self explainatory.
"""
stock = Table('stock',metadata,
	Column('stockid',Integer,primary_key=True),
	Column('productcode',Integer,ForeignKey('product.productcode'),nullable=False),
	Column('qty',Integer,nullable=False),
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
In addition this table has a field userrole which determines if the user is an admin:-1 manager:0 or operater:1 """
users=Table('users', metadata,
	Column('userid',Integer, primary_key=True),
	Column('username',Text, nullable=False),
	Column('userpassword',Text, nullable=False),
	Column('userrole',Integer, nullable=False),
	Column('userquestion',Text, nullable=False),
	Column('useranswer',Text, nullable=False),
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
"""
purchaseorder = Table( 'purchaseorder' , metadata,
    Column('orderno',UnicodeText, primary_key=True),
    Column('podate', DateTime, nullable=False),
    Column('maxdate', DateTime, nullable=False),
    Column('datedelivery',DateTime),
    Column('deliveryplaceaddr', UnicodeText),
    Column('payterms',UnicodeText),
    Column('schedule',UnicodeText),
    Column('modeoftransport', UnicodeText),
    Column('packaging',JSONB),
    Column('tax',JSONB),
    Column('productdetails', JSONB),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    Column('csid',Integer,ForeignKey('customerandsupplier.custid',ondelete="CASCADE"), nullable=False),
    Index("purchaseorder_orgcodeindex","orgcode"),
    Index("purchaseorder_date","podate"),
)

"""
Table for storing godown details.
Basically one organization may have many godowns and we aught to know from which one goods have moved out.
"""
godown = Table('godown',metadata,
    Column('goid',Integer,primary_key=True),
    Column('goname',UnicodeText),
    Column('goaddr',UnicodeText),
    Column('gocontact',UnicodeText),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
    UniqueConstraint('orgcode','goname'),
    Index("godown_orgcodeindex","orgcode")
    )

""" Table for transferNote details.
"""

transfernote = Table('transfernote',metadata,
	Column('transfernoteno',UnicodeText,primary_key=True),
	Column('transfernotedate', DateTime, nullable=False),
	Column('transportationmode', UnicodeText),
	Column('productdetails',JSONB, nullable = False),
	Column('nopkt',Integer),
	Column('recieved', BOOLEAN),
	Column('fromgodown',Integer,ForeignKey('godown.goid', ondelete="CASCADE"),nullable = False),
	Column('togodown',Integer,ForeignKey('godown.goid', ondelete = "CASCADE"),nullable = False),
	Column('orgcode',Integer ,ForeignKey('organisation.orgcode',ondelete = "CASCADE"),nullable = False),
	Index("transfernote_date",'transfernotedate'),
	Index("transfernote_fromgodown",'fromgodown'),
	Index("transfernote_togodown",'togodown'),
	Index("transfernote_orgcode","orgcode")
) 



discrepancynote = Table ('discrepancynote' ,metadata,
     Column('discrepancyno',UnicodeText,Primary_Key= True),
     Column('discrepancydate',DateTime,nullable=False),
     Column('discrepancydetails',JSONB , nullable = False),
     Column('dcinvpotnflag',Integer , nullable = False),
     Column('supplier',Integer,ForeignKey('customerandsupplier.custid', ondelete="CASCADE"),nullable = False),
     Column('transfernoteno',Integer,ForeignKey('transfernote.transfernoteno', ondelete="CASCADE"),nullable = False),
     Column('purchaseorderno',Integer,ForeignKey('purchaseorder.orderno', ondelete="CASCADE"),nullable = False),
     Column('delchalno',Integer,ForeignKey('delchal.dcid', ondelete="CASCADE"),nullable = False),
     Column('invoiceno',Integer,ForeignKey('invoice.invid', ondelete="CASCADE"),nullable = False),
     Column('orgcode',Integer ,ForeignKey('organisation.orgcode',ondelete = "CASCADE"),nullable = False),
     Index("discrepancy_date",'discrepancydate'),
     Index("discrepancy_details",'discrepancydetails')
       )