import json, io, logging
from gkcore.models.meta import dbconnect
from pyramid.response import Response
from gkcore.views.api_login import authCheck
from gkcore import eng, enumdict
from gkcore.views.api_gkuser import getUserRole
from gkcore.models.gkdb import customerandsupplier, godown, accounts


def get_table_array(name: str, orgcode: int):
    """Return given sql table contents as an array of dicts

    *params*

    `name`: db table name

    `orgcode`: integer

    """
    c = eng.connect()
    table = c.execute(f"select * from {name} where orgcode = {orgcode}")
    a = []
    for row in table:
        d = {}
        for i in row.keys():
            d[i] = row[i]
        # delete orgcode key as it's not required during import
        d.pop("orgcode", None)
        a.append(d)
    return a


def type_cast(key):
    """Convert sql data types to json compatable one's"""

    key_type = str(type(key))

    if key_type == "<class 'decimal.Decimal'>":
        return float(key)

    if key_type == "<class 'datetime.datetime'>":
        return str(key)

    if key_type == "<class 'datetime.date'>":
        return str(key)

    else:
        print(key_type)
        return str(key)


def export_json(self):
    """Export all database tables to a json file"""

    org_code = None

    # Check & validate user access
    try:
        token = self.request.headers["gktoken"]
        user = authCheck(token)
        org_code = user["orgcode"]
        user_role = getUserRole(user["userid"], org_code)["gkresult"]["userrole"]

        # only admin can export data
        if user_role != -1:
            return {"gkstatus": enumdict["BadPrivilege"]}
    except:
        return {"gkstatus": enumdict["UnauthorisedAccess"]}

    # get tables list from the db
    db_tables = dbconnect().table_names()

    # add gnukhata key to the exported json
    # This helps to validate the file during import operations
    data = {"gnukhata": {"export_version": 1}}

    # These tables are excluded during the export
    ignored_tables = [
        "state",
        "organisation",
        "signature",
        "unitofmeasurement",
    ]
    # loop through the tables and assign table data to their respective keys
    for n in db_tables:
        if n not in ignored_tables:
            data[n] = get_table_array(name=n, orgcode=org_code)

    # create a file object
    file_obj = io.StringIO()
    # convert the tables object to human readable json format and
    # return a file
    json.dump(data, file_obj, default=type_cast, indent=1)
    export_file = file_obj.getvalue()
    file_obj.close()
    headerList = {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": len(data),
        "Content-Disposition": "attachment; filename=report.json",
        "X-Content-Type-Options": "nosniff",
        "Set-Cookie": "fileDownload=true; path=/ ;HttpOnly",
    }

    return Response(
        export_file,
        headerlist=list(headerList.items()),
    )


def import_json(self):
    """Import org data from GNUKhata's json export file"""

    # Check & validate user access
    try:
        token = self.request.headers["gktoken"]
        user = authCheck(token)
        user_role = getUserRole(user["userid"], user["orgcode"])["gkresult"]["userrole"]

        # only admin can import data
        if user_role != -1:
            return {"gkstatus": enumdict["BadPrivilege"]}
    except:
        return {"gkstatus": enumdict["UnauthorisedAccess"]}

    # Proceed to importing
    try:
        f = self.request.POST["gkfile"].file
        org = json.load(f)
        # check if it's a valid gnukhata json file
        # else return err response
        if "gnukhata" not in org:
            logging.info("Not a valid gnukhata export format")
            return {"gkstatus": 3}

        # customers / suppliers
        print("\n 🤝 importing customers/suppliers ...")
        for i in org["customerandsupplier"]:
            # remove foreign key
            i.pop("custid")
            # add current orgcode as key
            i["orgcode"] = authCheck(self.request.headers["gktoken"])["orgcode"]
            # insert user entries to respective table
            try:
                eng.connect().execute(customerandsupplier.insert(), i)
            except Exception as e:
                logging.warning(e)
        # Godowns
        print("\n 📦 Importing Godowns ...")
        for i in org["godown"]:
            # remove foreign key
            i.pop("goid")
            # add current orgcode as key
            i["orgcode"] = authCheck(self.request.headers["gktoken"])["orgcode"]
            # insert user entries to respective table
            try:
                eng.connect().execute(godown.insert(), i)
            except Exception as e:
                logging.warning(e)

        # Accounts
        print("\n Importing Accounts ...")
        for i in org["accounts"]:
            # remove foreign key
            i.pop("accountcode")
            # add current orgcode as key
            i["orgcode"] = authCheck(self.request.headers["gktoken"])["orgcode"]
            # insert user entries to respective table
            try:
                eng.connect().execute(accounts.insert(), i)
            except Exception as e:
                logging.warning(e)
    except Exception as e:
        logging.warning(e)
        return {"gkstatus": 3}
    return {"gkstatus": 0}
