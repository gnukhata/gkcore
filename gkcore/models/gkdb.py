


"""
Copyright (C) 2014 2015 2016 Digital Freedom Foundation


  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

  GNUKhata is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public
  License along with GNUKhata (COPYING); if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,


Contributor: 
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
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


metadata = MetaData()
signature = Table('signature', metadata,
	Column('secretcode',UnicodeText, primary_key=True))

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


groupsubgroups = Table('groupsubgroups', metadata,
	Column('groupcode',Integer,primary_key=True),
	Column('groupname',UnicodeText,  nullable=False),
	Column('subgroupof',Integer),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode', ondelete="CASCADE"), nullable=False),
	UniqueConstraint('orgcode','groupname'),
	Index("grpindex","orgcode","groupname")
	)
	

accounts = Table('accounts', metadata,
	Column('accountcode',Integer, primary_key=True ),
	Column('accountname',UnicodeText, nullable=False),
	Column('groupcode',Integer, ForeignKey('groupsubgroups.groupcode'), nullable=False),
	Column('openingbal', Numeric(13,2),default=0.00),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
	UniqueConstraint('orgcode','accountname'),
	Index("accindex","orgcode","accountname")
	)
	
projects = Table('projects', metadata,
	Column('projectcode',Integer, primary_key=True),
	Column('projectname',UnicodeText, nullable=False),
	Column('sanctionedamount',Numeric(13,2),default=0.00),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
	UniqueConstraint('orgcode','projectname')
	)
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
	Column('projectcode',Integer, ForeignKey('projects.projectcode',ondelete="CASCADE"), nullable=False),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
	Index("voucher_orgcodeindex","orgcode"),
	Index("voucher_entrydate","entrydate"),
	Index("voucher_vno","vouchernumber"),
	Index("voucher_attachment","attachment"),
	Index("voucher_vdate","voucherdate")
	)
	
	
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
	

bankRecon=Table('bankrecon',metadata,
	Column('reconcode',Integer,primary_key = True),
	Column('vouchercode',Integer,ForeignKey("vouchers.vouchercode", ondelete="CASCADE"), nullable=False),
	Column('reffdate',DateTime),
	Column('accountname',UnicodeText),
	Column('dramount',Numeric(13,2)),
	Column('cramount',Numeric(13,2)),
	Column('clearancedate',DateTime),
	Column('memo',Text),
	Column('orgcode',Integer, ForeignKey('organisation.orgcode',ondelete="CASCADE"), nullable=False),
	)
	