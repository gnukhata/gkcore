
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
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BAG',0.00,'BAG',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BGS',0.00,'BAGS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BLS',0.00,'BAILS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BTL',0.00,'BOTTLES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BOU',0.00,'BOU',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BOX',0.00,'BOXES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BKL',0.00,'BUCKLES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BLK',0.00,'BULK',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BUN',0.00,'BUNCHES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BDL',0.00,'BUNDLES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CAN',0.00,'CANS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CTN',0.00,'CARTONS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CAS',0.00,'CASES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CMS',0.00,'CENTIMETER',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CHI',0.00,'CHEST',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CLS',0.00,'COILS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('COL',0.00,'COLLIES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CRI',0.00,'CRATES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CCM',0.00,'CUBIC CENTIMETER',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CIN',0.00,'CUBIC INCHES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CBM',0.00,'CUBIC METER',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CQM',0.00,'CUBIC METERS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CYL',0.00,'CYLINDER',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('SDM',0.00,'DECAMETER SQUARE',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('DAY',0.00,'DAYS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('DOZ',0.00,'DOZEN',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('DRM',0.00,'DRUMS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('FTS',0.00,'FEET',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('FLK',0.00,'FLASKS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('GMS',0.00,'GRAMS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('TON',0.00,'GREAT BRITAIN TON',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('GGR',0.00,'GREAT GROSS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('GRS',0.00,'GROSS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('GYD',0.00,'GROSS YARDS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('HBK',0.00,'HABBUCK',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('HKS',0.00,'HANKS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('HRS',0.00,'HOURS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('INC',0.00,'INCHES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('JTA',0.00,'JOTTA',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('KGS',0.00,'KILOGRAMS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('KLR',0.00,'KILOLITER',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('KME',0.00,'KILOMETERS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('LTR',0.00,'LITERS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('LOG',0.00,'LOGS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('LOT',0.00,'LOTS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('MTR',0.00,'METER',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('MTS',0.00,'METRIC TON',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('MGS',0.00,'MILLIGRAMS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('MLT',0.00,'MILLILITER',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('MMT',0.00,'MILLIMETER',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('NONE',0.00,'NOT CHOSEN',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('NOS',0.00,'NUMBERS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('ODD',0.00,'ODDS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('PAC',0.00,'PACKS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('PAI',0.00,'PAILS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('PRS',0.00,'PAIRS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('PLT',0.00,'PALLETS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('PCS',0.00,'PIECES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('LBS',0.00,'POUNDS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('QTL',0.00,'QUINTAL',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('REL',0.00,'REELS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('ROL',0.00,'ROLLS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('SET',0.00,'SETS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('SHT',0.00,'SHEETS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('SLB',0.00,'SLABS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('SQF',0.00,'SQUARE FEET',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('SQI',0.00,'SQUARE INCHES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('SQC',0.00,'SQUARE CENTIMETERS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('SQM',0.00,'SQUARE METER',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('SQY',0.00,'SQUARE YARDS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('BLO',0.00,'STEEL BLOCKS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('TBL',0.00,'TABLES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('TBS',0.00,'TABLETS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('TGM',0.00,'TEN GROSS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('THD',0.00,'THOUSANDS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('TIN',0.00,'TINS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('TOL',0.00,'TOLA',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('TRK',0.00,'TRUNK',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('TUB',0.00,'TUBES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('UNT',0.00,'UNITS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('UGS',0.00,'US GALLONS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('VLS',0.00,'VIALS',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('CSK',0.00,'WOODEN CASES',1)")
        eng.execute("insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('YDS',0.00,'YARDS',1)")

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
