
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

from gkcore.models.meta import dbconnect
from gkcore.models.gkdb import metadata
import datetime
from time import strftime

"""
This module is used only once per installation.
It will use the sqlalchemy's create_all function to convert all python based table spects to real sql tables.
Refer to gkdb.py in models package for structure of all tables expressed in the alchemy expression language.
After creating all tables, it will also create the signature based on timestamp and store in the database.
"""
eng = dbconnect()
metadata.create_all(eng)
print "database created successfully"
eng.execute("alter table groupsubgroups add  foreign key (subgroupof) references groupsubgroups(groupcode)")
eng.execute("alter table categorysubcategories add  foreign key (subcategoryof) references categorysubcategories(categorycode)")
eng.execute("alter table unitofmeasurement add  foreign key (subunitof) references unitofmeasurement(uomid)")
eng.execute("insert into state( statecode, statename)values(1, 'Jammu and Kashmir')")
eng.execute("insert into state( statecode, statename)values(2, 'Himachal Pradesh')")
eng.execute("insert into state( statecode, statename)values(3, 'Punjab')")
eng.execute("insert into state( statecode, statename)values(4, 'Chandigarh')")
eng.execute("insert into state( statecode, statename)values(5, 'Uttranchal')")
eng.execute("insert into state( statecode, statename)values(6, 'Haryana')")
eng.execute("insert into state( statecode, statename)values(7, 'Delhi')")
eng.execute("insert into state( statecode, statename)values(8, 'Rajasthan')")
eng.execute("insert into state( statecode, statename)values(9, 'Uttar Pradesh')")
eng.execute("insert into state( statecode, statename)values(10, 'Bihar')")
eng.execute("insert into state( statecode, statename)values(11, 'Sikkim')")
eng.execute("insert into state( statecode, statename)values(12, 'Arunachal Pradesh')")
eng.execute("insert into state( statecode, statename)values(13, 'Nagaland')")
eng.execute("insert into state( statecode, statename)values(14, 'Manipur')")
eng.execute("insert into state( statecode, statename)values(15, 'Mizoram')")
eng.execute("insert into state( statecode, statename)values(16, 'Tripura')")
eng.execute("insert into state( statecode, statename)values(17, 'Meghalaya')")
eng.execute("insert into state( statecode, statename)values(18, 'Assam')")
eng.execute("insert into state( statecode, statename)values(19, 'West Bengal')")
eng.execute("insert into state( statecode, statename)values(20, 'Jharkhand')")
eng.execute("insert into state( statecode, statename)values(21, 'Odisha')")
eng.execute("insert into state( statecode, statename)values(22, 'Chhattisgarh')")
eng.execute("insert into state( statecode, statename)values(23, 'Madhya Pradesh')")
eng.execute("insert into state( statecode, statename)values(24, 'Gujarat')")
eng.execute("insert into state( statecode, statename)values(25, 'Daman and Diu')")
eng.execute("insert into state( statecode, statename)values(26, 'Dadra and Nagar Haveli')")
eng.execute("insert into state( statecode, statename)values(27, 'Maharashtra')")
eng.execute("insert into state( statecode, statename)values(28, 'Andhra Pradesh')")
eng.execute("insert into state( statecode, statename)values(29, 'Karnataka')")
eng.execute("insert into state( statecode, statename)values(30, 'Goa')")
eng.execute("insert into state( statecode, statename)values(31, 'Lakshdweep')")
eng.execute("insert into state( statecode, statename)values(32, 'Kerala')")
eng.execute("insert into state( statecode, statename)values(33, 'Tamil Nadu')")
eng.execute("insert into state( statecode, statename)values(34, 'Pondicherry')")
eng.execute("insert into state( statecode, statename)values(35, 'Andaman and Nicobar Islands')")
eng.execute("insert into state( statecode, statename)values(36, 'Telangana')")
eng.execute("insert into state( statecode, statename)values(37, 'Andhra Pradesh (New)')")
try:
	eng.execute("alter table transfernote add recieveddate date")
	eng.execute("alter table delchal add noofpackages int")
	eng.execute("alter table delchal add modeoftransport text")
except:
	pass



print "secret signature generated"
