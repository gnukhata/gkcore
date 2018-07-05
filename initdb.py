
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018 Digital Freedom Foundation & Accion Labs 
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
from gkcore.models import gkdb
from sqlalchemy.sql import select
from sqlalchemy import func
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

try:
    uomscount = eng.execute(select([func.count(gkdb.unitofmeasurement.c.uomid).label("numofuom")]))
    numofuom = uomscount.fetchone()
    if int(numofuom["numofuom"]) == 0:
        dictofuqc = {'BAG':'BAG','BGS':'BAGS','BLS':'BAILS','BTL':'BOTTLES','BOU':'BOU','BOX':'BOXES','BKL':'BUCKLES','BLK':'BULK','BUN':'BUNCHES','BDL':'BUNDLES','CAN':'CANS','CTN':'CARTONS','CAS':'CASES','CMS':'CENTIMETER','CHI':'CHEST','CLS':'COILS','COL':'COLLIES','CRI':'CRATES','CCM':'CUBIC CENTIMETER','CIN':'CUBIC INCHES','CBM':'CUBIC METER','CQM':'CUBIC METERS','CYL':'CYLINDER','SDM':'DECAMETER SQUARE','DAY':'DAYS','DOZ':'DOZEN','DRM':'DRUMS','FTS':'FEET','FLK':'FLASKS','GMS':'GRAMS','TON':'GREAT BRITAIN TON','GGR':'GREAT GROSS','GRS':'GROSS','GYD':'GROSS YARDS','HBK':'HABBUCK','HKS':'HANKS','HRS':'HOURS','INC':'INCHES','JTA':'JOTTA','KGS':'KILOGRAMS','KLR':'KILOLITER','KME':'KILOMETERS','LTR':'LITERS','LOG':'LOGS','LOT':'LOTS','MTR':'METER','MTS':'METRIC TON','MGS':'MILLIGRAMS','MLT':'MILLILITER','MMT':'MILLIMETER','NONE':'NOT CHOSEN','NOS':'NUMBERS','ODD':'ODDS','PAC':'PACKS','PAI':'PAILS','PRS':'PAIRS','PLT':'PALLETS','PCS':'PIECES','LBS':'POUNDS','QTL':'QUINTAL','REL':'REELS','ROL':'ROLLS','SET':'SETS','SHT':'SHEETS','SLB':'SLABS','SQF':'SQUARE FEET','SQI':'SQUARE INCHES','SQC':'SQUARE CENTIMETERS','SQM':'SQUARE METER','SQY':'SQUARE YARDS','BLO':'STEEL BLOCKS','TBL':'TABLES','TBS':'TABLETS','TGM':'TEN GROSS','THD':'THOUSANDS','TIN':'TINS','TOL':'TOLA','TRK':'TRUNK','TUB':'TUBES','UNT':'UNITS','UGS':'US GALLONS','VLS':'VIALS','CSK':'WOODEN CASES','YDS':'YARDS'}

        for unit, desc in dictofuqc.items():
            eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('%s',0.00,'%s',1)"%(unit,desc))
            dictofuqc.pop(unit,0)

    statescount = eng.execute(select([func.count(gkdb.state.c.statecode).label("numberofstates")]))
    numberofstates = statescount.fetchone()
    if int(numberofstates["numberofstates"]) == 0:
        eng.execute("insert into state( statecode, statename, abbreviation)values(1, 'Jammu and Kashmir', 'JK')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(2, 'Himachal Pradesh', 'HP')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(3, 'Punjab', 'PB')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(4, 'Chandigarh', 'CH')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(5, 'Uttarakhand', 'UK')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(6, 'Haryana', 'HR')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(7, 'Delhi', 'DL')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(8, 'Rajasthan', 'RJ')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(9, 'Uttar Pradesh', 'UP')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(10, 'Bihar', 'BR')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(11, 'Sikkim', 'SK')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(12, 'Arunachal Pradesh', 'AR')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(13, 'Nagaland', 'NL')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(14, 'Manipur', 'MN')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(15, 'Mizoram', 'MZ')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(16, 'Tripura', 'TR')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(17, 'Meghalaya', 'ML')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(18, 'Assam', 'AS')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(19, 'West Bengal', 'WB')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(20, 'Jharkhand', 'JH')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(21, 'Odisha', 'OR')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(22, 'Chhattisgarh', 'CG')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(23, 'Madhya Pradesh', 'MP')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(24, 'Gujarat', 'GJ')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(25, 'Daman and Diu', 'DD')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(26, 'Dadra and Nagar Haveli', 'DH')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(27, 'Maharashtra', 'MH')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(28, 'Andhra Pradesh', 'AP')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(29, 'Karnataka', 'KA')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(30, 'Goa', 'GA')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(31, 'Lakshdweep', 'LD')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(32, 'Kerala', 'KL')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(33, 'Tamil Nadu', 'TN')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(34, 'Pondicherry', 'PY')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(35, 'Andaman and Nicobar Islands', 'AN')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(36, 'Telangana', 'TS')")
        eng.execute("insert into state( statecode, statename, abbreviation)values(37, 'Andhra Pradesh (New)', 'AP')")
        eng.execute("alter table transfernote add recieveddate date")
    eng.execute("alter table delchal add noofpackages int")
    eng.execute("alter table delchal add modeoftransport text")
except:
    pass



print "secret signature generated"
