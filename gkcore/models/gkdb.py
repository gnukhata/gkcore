


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

from gkcore.models.meta import Base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Unicode,	 #<- will provide Unicode field
    UnicodeText, #<- will provide Unicode text field
DateTime	 #<- time abstraction field
    )
from sqlalchemy.sql.schema import PrimaryKeyConstraint, ForeignKey
from sqlalchemy.orm import relationship

class organisation(Base):
	__tablename__ = 'organisation'
	orgcode = Column(Integer, primary_key=True)
	orgname = Column(UnicodeText, nullable=False)
	orgtype = Column(UnicodeText, nullable=False)
	orgcity = Column(UnicodeText)
	orgaddr = Column(UnicodeText)
	orgpincode = Column(Unicode(30))
	orgstate = Column(UnicodeText)
	orgcountry = Column(UnicodeText)
	orgtelno = Column(UnicodeText)
	orgfax = Column(UnicodeText)
	orgwebsite = Column(UnicodeText)
	orgemail = Column(UnicodeText)
	orgpan = Column(UnicodeText)
	orgmvat = Column(UnicodeText)
	orgstax = Column(UnicodeText)
	orgregno = Column(UnicodeText)
	orgregdate = Column(UnicodeText)
	orgfcrano = Column(UnicodeText)
	orgfcradate = Column(UnicodeText)
	roflag = Column(Integer)
	booksclosedflag  = Column(Integer)
	def __init__(self, orgtype, orgname, orgaddr, orgcity, orgpincode, orgstate, orgcountry, orgtelno, orgfax, orgwebsite, orgemail, orgpan, orgmvat, orgstax, orgregno, orgregdate, orgfcrano, orgfcradate, roflag,booksclosedflag):	
		self.orgtype = orgtype
		self.orgname = orgname
		self.orgaddr = orgaddr
		self.orgcity = orgcity
		self.orgpincode = orgpincode
		self.orgstate = orgstate
		self.orgcountry = orgcountry
		self.orgtelno = orgtelno
		self.orgfax = orgfax
		self.orgwebsite = orgwebsite
		self.orgemail = orgemail
		self.orgpan = orgpan
		self.orgmvat = orgmvat
		self.orgstax = orgstax
		self.orgregno = orgregno
		self.orgregdate = orgregdate
		self.orgfcrano = orgfcrano
		self.orgfcradate = orgfcradate
		self.roflag = roflag
		self.booksclosedflag = booksclosedflag

class groupsubgroups(Base):
	__tablename__ = 'groupsubgroups'
	groupcode = Column(Integer,primary_key=True)
	groupname = Column(UnicodeText,  nullable=False)
	subgroupof = Column(Integer)
	def __init__(self,groupcode,groupname,subgroupof):
		self.groupcode = groupcode
		self.groupname = groupname
		self.subgroupof = subgroupof


class accounts(Base):
	__tablename__ = 'accounts'
	accountcode = Column( Integer, primary_key=True )
	accountname = Column(UnicodeText, nullable=False)
	groupcode  = Column(Integer, ForeignKey('groupsubgroups.groupcode'))
	def __init__(self,accountcode,accountname,groupcode):
		self.accountcode = accountcode
		self.accountname = accountname
		self.groupcode = groupcode
class Projects(Base):
	__tablename__ = 'projects'
	projectcode = Column(Integer, primary_key=True)
	projectname = Column(UnicodeText)
	sanctionedamount = Column(Numeric(13,2))
	def __init__(self, projectcode, projectname,sanctionedamount):
		self.projectcode = projectcode
		self.projectname = projectname
		self.sanctionedamount = sanctionedamount

class Users(Base):
	__tablename__ = 'users'
	userid = Column(Integer, primary_key=True)
	username = Column(Text)
	userpassword = Column(Text)
	userrole = Column(Integer)
	userquestion = Column(Text)
	useranswer = Column(Text)

	def __init__(self, username, userpassword, userrole,userquestion,useranswer):
		self.userid = None
		self.username = username
		self.userpassword = userpassword
		self.userrole = userrole
		self.userquestion = userquestion
		self.useranswer = useranswer


class BankRecon(Base):
	__tablename__ = "bankrecon"
	reconcode = Column(Integer,primary_key = True)
	vouchercode = Column(Integer,ForeignKey("voucher_master.vouchercode"))
	reffdate = Column(TIMESTAMP)
	accountname = Column(String(40))
	dramount = Column(Numeric(13,2))
	cramount = Column(Numeric(13,2))
	clearancedate = Column(TIMESTAMP)
	memo = Column(Text)
	def __init__(self,reconcode,vouchercode,reffdate,accountname,dramount,cramount,clearancedate,memo):
		self.reconcode = reconcode
		self.vouchercode = vouchercode
		self.reffdate = reffdate
		self.accountname = accountname
		self.dramount = dramount
		self.cramount = cramount
		self.clearancedate = clearancedate
		self.memo = memo

