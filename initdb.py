
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
    print numofuom
    if int(numofuom["numofuom"]) == 0:
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BAG',0.00,'BAG')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BGS',0.00,'BAGS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BLS',0.00,'BAILS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BTL',0.00,'BOTTLES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BOU',0.00,'BOU')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BOX',0.00,'BOXES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BKL',0.00,'BUCKLES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BLK',0.00,'BULK')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BUN',0.00,'BUNCHES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BDL',0.00,'BUNDLES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CAN',0.00,'CANS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CTN',0.00,'CARTONS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CAS',0.00,'CASES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CMS',0.00,'CENTIMETER')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CHI',0.00,'CHEST')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CLS',0.00,'COILS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('COL',0.00,'COLLIES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CRI',0.00,'CRATES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CCM',0.00,'CUBIC CENTIMETER')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CIN',0.00,'CUBIC INCHES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CBM',0.00,'CUBIC METER')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CQM',0.00,'CUBIC METERS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CYL',0.00,'CYLINDER')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('SDM',0.00,'DECAMETER SQUARE')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('DAY',0.00,'DAYS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('DOZ',0.00,'DOZEN')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('DRM',0.00,'DRUMS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('FTS',0.00,'FEET')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('FLK',0.00,'FLASKS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('GMS',0.00,'GRAMS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('TON',0.00,'GREAT BRITAIN TON')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('GGR',0.00,'GREAT GROSS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('GRS',0.00,'GROSS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('GYD',0.00,'GROSS YARDS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('HBK',0.00,'HABBUCK')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('HKS',0.00,'HANKS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('HRS',0.00,'HOURS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('INC',0.00,'INCHES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('JTA',0.00,'JOTTA')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('KGS',0.00,'KILOGRAMS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('KLR',0.00,'KILOLITER')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('KME',0.00,'KILOMETERS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('LTR',0.00,'LITERS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('LOG',0.00,'LOGS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('LOT',0.00,'LOTS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('MTR',0.00,'METER')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('MTS',0.00,'METRIC TON')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('MGS',0.00,'MILLIGRAMS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('MLT',0.00,'MILLILITER')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('MMT',0.00,'MILLIMETER')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('NONE',0.00,'NOT CHOSEN')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('NOS',0.00,'NUMBERS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('ODD',0.00,'ODDS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('PAC',0.00,'PACKS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('PAI',0.00,'PAILS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('PRS',0.00,'PAIRS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('PLT',0.00,'PALLETS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('PCS',0.00,'PIECES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('LBS',0.00,'POUNDS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('QTL',0.00,'QUINTAL')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('REL',0.00,'REELS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('ROL',0.00,'ROLLS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('SET',0.00,'SETS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('SHT',0.00,'SHEETS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('SLB',0.00,'SLABS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('SQF',0.00,'SQUARE FEET')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('SQI',0.00,'SQUARE INCHES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('SQC',0.00,'SQUARE CENTIMETERS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('SQM',0.00,'SQUARE METER')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('SQY',0.00,'SQUARE YARDS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('BLO',0.00,'STEEL BLOCKS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('TBL',0.00,'TABLES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('TBS',0.00,'TABLETS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('TGM',0.00,'TEN GROSS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('THD',0.00,'THOUSANDS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('TIN',0.00,'TINS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('TOL',0.00,'TOLA')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('TRK',0.00,'TRUNK')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('TUB',0.00,'TUBES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('UNT',0.00,'UNITS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('UGS',0.00,'US GALLONS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('VLS',0.00,'VIALS')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('CSK',0.00,'WOODEN CASES')")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description)values('YDS',0.00,'YARDS')")

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
