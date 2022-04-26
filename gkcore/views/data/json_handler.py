import json, io
from pyramid.response import Response
from gkcore.models.meta import dbconnect, gk_api
from gkcore.views.api_login import authCheck
from gkcore import eng, enumdict
from gkcore.views.api_user import getUserRole


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
        print(user)
        org_code = user["orgcode"]
        user_role = getUserRole(user["userid"])["gkresult"]["userrole"]

        # only admin can export data
        print(user_role)
        if user_role != -1:
            return {"gkstatus": enumdict["BadPrivilege"]}
    except:
        return {"gkstatus": enumdict["UnauthorisedAccess"]}

    db_tables = dbconnect().table_names()

    data = {}

    ignored_tables = [
        "log",
        "state",
        "users",
        "organisation",
        "signature",
        "unitofmeasurement",
    ]

    for n in db_tables:
        if n not in ignored_tables:
            data[n] = get_table_array(name=n, orgcode=org_code)

    file_obj = io.StringIO()
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
    """Import org data from GNUKhata's json format"""

    # Check & validate user access
    try:
        token = self.request.headers["gktoken"]
        user = authCheck(token)
        user_role = getUserRole(user["userid"])["gkresult"]["userrole"]

        # only admin can export data
        print(user_role)
        if user_role != -1:
            return {"gkstatus": enumdict["BadPrivilege"]}
    except:
        return {"gkstatus": enumdict["UnauthorisedAccess"]}

    try:
        header = {"gktoken": self.request.headers["gktoken"]}
        f = self.request.POST["gkfile"].file
        org = json.load(f)

        # customers / suppliers
        print("\n 🤝 importing customers/suppliers ...")
        for i in org["customerandsupplier"]:
            # remove foreign key
            i.pop("custid")

            response = gk_api(
                method="POST",
                url="/customersupplier",
                body=i,
                header=header,
                request=self.request,
            )
            print(i["custname"], response)
        # Godowns
        print("\n 📦 Importing Godowns ...")
        for i in org["godown"]:

            i.pop("goid")
            response = gk_api(
                method="POST",
                url="/godown",
                body=i,
                header=header,
                request=self.request,
            )
            print(i["goname"], response)
    except Exception as e:
        print(e)
        return {"gkstatus": 3}
    return {"gkstatus": 0}
