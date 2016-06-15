
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
from sqlalchemy.sql.sqltypes import BOOLEAN, Numeric
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
Apart from this orgcode is there as the foreign key """
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
	Column('attachment',UnicodeText),
	Column('vouchertype',UnicodeText, nullable=False),
	Column('lockflag',BOOLEAN,default=False),
	Column('delflag',BOOLEAN,default=False),
	Column('projectcode',Integer, ForeignKey('projects.projectcode')),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
	Index("voucher_orgcodeindex","orgcode"),
	Index("voucher_entrydate","entrydate"),
	Index("voucher_vno","vouchernumber"),
	Index("voucher_attachment","attachment"),
	Index("voucher_vdate","voucherdate")
	)

""" table to store users for an organization.
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

voucherbin=Table('voucherbin', metadata,
    Column('vouchercode',Integer,primary_key=True),
    Column('vouchernumber',UnicodeText, nullable=False),
    Column('voucherdate',DateTime,nullable=False),
    Column('narration',UnicodeText),
    Column('drs',JSONB,nullable=False),
    Column('crs',JSONB,nullable=False),
    Column('attachment',UnicodeText),
    Column('vouchertype',UnicodeText, nullable=False),
    Column('projectname',UnicodeText, nullable=True),
    Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
    Index("binvoucher_orgcodeindex","orgcode"),
    Index("binvoucher_vno","vouchernumber"),
    Index("binvoucher_attachment","attachment"),
    Index("binvoucher_vdate","voucherdate")
    )
