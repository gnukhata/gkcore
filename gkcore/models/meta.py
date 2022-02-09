"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020 Digital Freedom Foundation & Accion Labs 
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.

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
"Prajkta Patkar"<prajkta.patkar007@gmail.com>
"""

# this module contains the functions and objects needed for database objects configuration.
# Metadata is one such object which helps to get all database related info.
# inspect is another functions from alchemy which helps to find details info on tables or columns.

from sqlalchemy.engine import create_engine
from sqlalchemy.dialects.postgresql.base import PGInspector
import sys, os, json, pathlib
from pyramid.request import Request

# from sqlalchemy.sql.expression import null
from gkcore.models.gkdb import metadata


def dbconnect():
    """
    purpose:
    returns an engine object for the postgresql database.
    In our case the database is called gkdata.
    Description:
    This function can be called to get a working interface to the database.
    It is as good as a database connection which can directly execute sql queries.
    """
    if sys.platform.startswith("win"):
        stmt = "postgresql://postgres:gkadmin@localhost/gkdata"
    else:
        # if env variable GKCORE_DB_URL is set, Use it
        if os.getenv("GKCORE_DB_URL") != None:
            stmt = os.getenv("GKCORE_DB_URL")
        else:
            stmt = "postgresql+psycopg2:///gkdata?host=/var/run/postgresql"
    # now we will create an engine instance to connect to the given database.
    # Note that the echo parameter set to False means sql queries will not be printed to the termina.
    # Pool size is important to balance between database holding capacity in ram and speed.

    engine = create_engine(stmt, echo=False, pool_size=15, max_overflow=100)
    return engine


def inventoryMigration(con, eng):
    metadata.create_all(eng)
    con.execute(
        "alter table categorysubcategories add  foreign key (subcategoryof) references categorysubcategories(categorycode)"
    )
    con.execute(
        "alter table unitofmeasurement add  foreign key (subunitof) references unitofmeasurement(uomid)"
    )
    con.execute("alter table organisation add column invflag Integer default 0 ")
    con.execute("alter table vouchers add column invid Integer")
    con.execute(
        "alter table vouchers add foreign key (invid) references invoice(invid)"
    )
    try:
        con.execute("select themename from users")
    except:
        con.execute("alter table users add column themename text default 'Default'")
    return 0


def addFields(con, eng):
    metadata.create_all(eng)
    try:
        con.execute("select noofpackages,modeoftransport from delchal")
        con.execute("select recieveddate from transfernote")
    except:
        con.execute("alter table transfernote add recieveddate date")
        con.execute("alter table delchal add noofpackages int")
        con.execute("alter table delchal add modeoftransport text")
    return 0


def columnExists(tableName, columnName):
    """
    purpose:
    Checkes weather the column mentiond is alredy present in the given table.
    description:
    Given the table and the name of the column, this functions checks if that column exists.
    It uses the inspect function to do so.
    The function traverces through the list of columns and checks if the name exists.
    Returns True if the column exists or False otherwise.
    """
    gkInspect = PGInspector(dbconnect())
    cols = gkInspect.get_columns(tableName)
    for col in cols:
        if col["name"] in columnName:
            return True
    return False


def tableExists(tblName):
    """
    purpose:
    Finds out weather the given table exists in the database.
    Function uses inspect object for postgresql.
    """
    gkInspect = PGInspector(dbconnect())
    tblList = gkInspect.get_table_names()
    return tblName in tblList


def getOnDelete(tblName, keyName):
    """
    purpose:
    Returns the value of ondelete option for a foreign key in a table.
    Accepts names of table and the foreign key as params.
    It fetches all foreign keys and then loops through them.
    On finding the matching foreign key, its value for ondelete option is returned.
    """
    onDelete = False
    gkInspect = PGInspector(dbconnect())
    fkeys = gkInspect.get_foreign_keys(tblName)
    for fkey in fkeys:
        if fkey["name"] == keyName:
            onDelete = fkey["options"]["ondelete"]
    return onDelete


def gk_api(url: str, header: object, request: object):
    """Call's gkcore api internally

    If success, returns result object, else raises Exception.

    params
    ======
    url = api url (eg: '/state')
    header = url headers
    request = request object
    """
    try:
        subreq = Request.blank(url, headers=header)
        Request.POST
        result = json.loads(request.invoke_subrequest(subreq).text)
        return result
    except Exception as e:
        print(e)
        raise


def gk_hsn():
    """Read HSN Code file and return an array of hsn codes"""
    try:
        gkcore_root = pathlib.Path("././").resolve()
        with open(f"{gkcore_root}/static/gst-hsn.json", "r") as f:
            hsn_array = json.load(f)
        return hsn_array
        # wb = openpyxl.load_workbook(f"{gkcore_root}/static/HSN_SAC.xlsx")
        # ws = wb["HSN"]
        # for row in ws.values:
        #     # hsn_array.append({"hsn_code": row[0], "hsn_desc": row[1]})

        #     # first object is useless. So, remove it.
        #     # hsn_array.pop(0)

        #     print(hsn_array)
        #     return hsn_array
    except Exception as e:
        print(e)
        raise e


# def gk_auth(**params):
#     """Verify user's identity\n
#     __Params:__\n
#     token: jwt token

#     """
#     print("params: ", params)
#     # token = params["token"] or None
#     # if token == None:
#     #     return {"gkstatus": gkcore.enumdict["UnauthorisedAccess"]}
#     authDetails = ac(params["token"])
#     if authDetails["auth"] == False:
#         return {"gkstatus": 2}
