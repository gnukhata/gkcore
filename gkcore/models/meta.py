
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
from sqlalchemy.engine import create_engine
from gkcore.models.gkdb import metadata
def dbconnect():
	stmt = 'postgresql+psycopg2:///gkdata?host=/var/run/postgresql'
#now we will create an engine instance to connect to the given database.
	#engine = Engine
	engine = create_engine(stmt, echo=False, pool_size = 15, max_overflow=100)
	return engine

def inventoryMigration(con,eng):
	metadata.create_all(eng)
	con.execute("alter table categorysubcategories add  foreign key (subcategoryof) references categorysubcategories(categorycode)")
	con.execute("alter table unitofmeasurement add  foreign key (subunitof) references unitofmeasurement(uomid)")
	con.execute("alter table organisation add column invflag Integer default 0 ")
	con.execute("alter table vouchers add column invid Integer")
	con.execute("alter table vouchers add foreign key (invid) references invoice(invid)")
	try:
		con.execute("select themename from users")
	except:
		con.execute("alter table users add column themename text default 'Default'")
	return 0
