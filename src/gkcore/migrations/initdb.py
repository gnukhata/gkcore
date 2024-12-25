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

from gkcore import eng
from gkcore.models.gkdb import metadata
from gkcore.models import gkdb
from gkcore.models.meta import does_foreignkey_exist
from sqlalchemy.sql import select
from sqlalchemy import func

"""
This module is used only once per installation.
It will use the sqlalchemy's create_all function to convert all python based table spects to real sql tables.
Refer to gkdb.py in models package for structure of all tables expressed in the alchemy expression language.
After creating all tables, it will also create the signature based on timestamp and store in the database.
"""

def create_tables():
    metadata.create_all(eng)
    print("Tables created successfully")

def load_initial_data():
    with eng.connect() as con:
        if not does_foreignkey_exist(
                eng,
                "groupsubgroups",
                "groupsubgroups_subgroupof_fkey"
        ):
            con.execute(
                "alter table groupsubgroups add  foreign key (subgroupof) references groupsubgroups(groupcode)"
            )
        if not does_foreignkey_exist(
                eng,
                "categorysubcategories",
                "categorysubcategories_subcategoryof_fkey"
        ):
            con.execute(
                "alter table categorysubcategories add  foreign key (subcategoryof) references categorysubcategories(categorycode)"
            )
        if not does_foreignkey_exist(
                eng,
                "unitofmeasurement",
                "unitofmeasurement_subunitof_fkey"
        ):
            con.execute(
                "alter table unitofmeasurement add  foreign key (subunitof) references unitofmeasurement(uomid)"
            )

        uomscount = con.execute(
            select([func.count(gkdb.unitofmeasurement.c.uomid).label("numofuom")])
        )
        numofuom = uomscount.fetchone()
        if int(numofuom["numofuom"]) == 0:
            # UQC list as per Indian GST law
            dictofuqc = {
                "BAG": "BAGS",
                "BAL": "BALE",
                "BDL": "BUNDLES",
                "BKL": "BUCKLES",
                "BOU": "BILLIONS OF UNITS",
                "BOX": "BOX",
                "BTL": "BOTTLES",
                "BUN": "BUNCHES",
                "CAN": "CANS",
                "CBM": "CUBIC METER",
                "CCM": "CUBIC CENTIMETER",
                "CMS": "CENTIMETER",
                "CRT": "Carat",
                "CTN": "CARTONS",
                "DOZ": "DOZEN",
                "DRM": "DRUM",
                "GGK": "GREAT GROSS",
                "GMS": "GRAMS",
                "GRS": "GROSS",
                "GYD": "GROSS YARDS",
                "KGS": "KILOGRAMS",
                "KLR": "KILOLITER",
                "KME": "KILOMETERS",
                "MLT": "MILLILITER",
                "MTR": "METER",
                "MTS": "METRIC TON",
                "NOS": "NUMBER",
                "OTH": "OTHERS",
                "PAC": "PACKS",
                "PCS": "PIECES",
                "PRS": "PAIRS",
                "QTL": "QUINTAL",
                "ROL": "ROLLS",
                "SET": "SETS",
                "SQF": "SQUARE FEET",
                "SQM": "SQUARE METER",
                "SQY": "SQUARE YARDS",
                "TBS": "TABLETS",
                "TGM": "TEN GRAMS",
                "THD": "THOUSANDS",
                "TON": "GREAT BRITAIN TON",
                "TUB": "TUBES",
                "UGS": "US GALLONS",
                "UNT": "UNITS",
                "YDS": "YARDS",
            }

            for unit, desc in list(dictofuqc.items()):
                con.execute(
                    "insert into unitofmeasurement(unitname, conversionrate, description, sysunit)values('%s',0.00,'%s',1)"
                    % (unit, desc)
                )
                dictofuqc.pop(unit, 0)

        statescount = con.execute(
            select([func.count(gkdb.state.c.statecode).label("numberofstates")])
        )
        numberofstates = statescount.fetchone()
        if int(numberofstates["numberofstates"]) == 0:
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(1, 'Jammu and Kashmir', 'JK')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(2, 'Himachal Pradesh', 'HP')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(3, 'Punjab', 'PB')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(4, 'Chandigarh', 'CH')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(5, 'Uttarakhand', 'UK')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(6, 'Haryana', 'HR')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(7, 'Delhi', 'DL')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(8, 'Rajasthan', 'RJ')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(9, 'Uttar Pradesh', 'UP')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(10, 'Bihar', 'BR')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(11, 'Sikkim', 'SK')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(12, 'Arunachal Pradesh', 'AR')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(13, 'Nagaland', 'NL')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(14, 'Manipur', 'MN')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(15, 'Mizoram', 'MZ')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(16, 'Tripura', 'TR')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(17, 'Meghalaya', 'ML')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(18, 'Assam', 'AS')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(19, 'West Bcon.l', 'WB')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(20, 'Jharkhand', 'JH')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(21, 'Odisha', 'OR')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(22, 'Chhattisgarh', 'CG')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(23, 'Madhya Pradesh', 'MP')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(24, 'Gujarat', 'GJ')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(25, 'Daman and Diu (Old)', 'DD')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(26, 'Daman and Diu & Dadra and Nagar Haveli (New)', 'DH')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(27, 'Maharashtra', 'MH')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(28, 'Andhra Pradesh', 'AP')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(29, 'Karnataka', 'KA')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(30, 'Goa', 'GA')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(31, 'Lakshdweep', 'LD')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(32, 'Kerala', 'KL')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(33, 'Tamil Nadu', 'TN')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(34, 'Pondicherry', 'PY')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(35, 'Andaman and Nicobar Islands', 'AN')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(36, 'Telangana', 'TS')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(37, 'Andhra Pradesh (New)', 'AP')"
            )
            con.execute(
                "insert into state( statecode, statename, abbreviation)values(38, 'Ladakh', 'LA')"
            )

            con.execute("alter table transfernote add column if not exists recieveddate date")
            con.execute("alter table delchal add column if not exists noofpackages int")
            con.execute("alter table delchal add column if not exists modeoftransport text")
