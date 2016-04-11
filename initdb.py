
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
"Krishnakant Mane" <kk@dff.org.in>
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
curtime=datetime.datetime.now()
str_time=str(curtime.microsecond)
new_microsecond=str_time[0:2]		

secret = str(curtime.year) + str(curtime.month) + str(curtime.day) + str(curtime.hour) + str(curtime.minute) + str(curtime.second) + new_microsecond

eng.execute("insert into signature values(%s)"%secret)
eng.execute("alter table groupsubgroups add  foreign key (subgroupof) references groupsubgroups(groupcode)")

print "secret signature generated"