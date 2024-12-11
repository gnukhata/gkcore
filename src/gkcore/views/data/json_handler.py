import json, io, logging
from gkcore import eng
from sqlalchemy import MetaData, select, func, and_
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.elements import quoted_name
from sqlalchemy.sql.schema import Table
from gkcore.models import gkdb

log = logging.getLogger(__name__)
metadata = MetaData()

metadata.reflect(bind=eng)


def get_table_array(con: Connection, table_name: str, orgcode: int) -> list:
    """Return given sql table contents as an array of dicts

    :param con: SQL Alchemy engine connection
    :param table_name: Database table name
    :param orgcode: `orgcode` of the new organisation
    :return: List of rows of the table
    """
    with eng.connect() as con:

        table = getattr(gkdb, table_name)

        # handle case for gkusers table as it does not have orgcode column
        if table_name == "gkusers":
            statement = table.select().where(
                func.jsonb_extract_path_text(
                    table.c.orgs, str(orgcode)
                ) != None
            )
        else:
            statement = table.select().where(table.c.orgcode == orgcode)

        table_org = con.execute(statement).fetchall()

        table_org_dict =  [dict(row) for row in table_org]

        if table_name == "gkusers":
            for user in table_org_dict:
                user["orgs"] = {str(orgcode): user["orgs"][str(orgcode)]}

        return table_org_dict


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
        log.info(key_type)
        return str(key)


def export_org_data(con: Connection, orgcode: int) -> str:
    """Export all database tables to a json file

    :param con: SQL Alchemy engine connection
    :param orgcode: `orgcode` of the old organisation
    :return: Organisation data exported as JSON
    """

    # get tables list from the db
    db_tables = eng.table_names()

    # add gnukhata key to the exported json
    # This helps to validate the file during import operations
    data: dict = {"gnukhata": {"export_version": 1}}

    # These tables are excluded during the export
    ignored_tables: list[str] = [
        "state",
        "signature",
        "unitofmeasurement",
    ]

    # loop through the tables and assign table data to their respective keys
    for table in db_tables:
        if table not in ignored_tables:
            data[table] = get_table_array(con, table, orgcode)

    # create a file object
    file_obj = io.StringIO()
    # convert the tables object to human readable json format and
    # return a file
    json.dump(data, file_obj, default=type_cast)
    export_file = file_obj.getvalue()
    file_obj.close()
    return export_file


def import_org_data(con: Connection, data: dict) -> int:
    """ Imports organisation data.

    This function will loop through table list twice.

    In first iteration, it will insert table data. The order at which table data will
    depend on foreignkey dependance of the table. This is to make sure foreignkey
    references are already inserted before they get referred. SQL Alchemy's
    `sorted_tables` is used to sort tables wrt foreignkey dependancy.

    Old and new `pk`s of the inserted tables will be saved in a dictionary `pk_map`.
    This will be used to update the foreignkey constraints of tables that referring
    them.

    In Second iteration, `pk`s stored in JSONB fields are updated.

    If the imported organisation has users that have names that are present in the
    host gnukhata instance, the imported usernames are updated to <username>_<number>
    format.

    :param con: SQL Alchemy engine connection
    :param data: Organisation data to be imported
    :return: `orgcode` of the new organisation
    """
    table_list = metadata.sorted_tables
    excluded_tables = ["unitofmeasurement", "state", "signature"]

    pk_map = {}
    for table in table_list:
        table_data = data.get(table.name, [])
        if table.name == "gkusers":
            data_user_name_list = [user["username"] for user in table_data]
            current_user_names = con.execute(
                select([gkdb.gkusers.c.username])
            ).fetchall()
            current_user_names = [user.username for user in current_user_names]
            duplicate_user_names = list(
                set(current_user_names) & set(data_user_name_list)
            )

            for user in table_data:
                if user["username"] in duplicate_user_names:
                    counter = 1
                    username = user["username"]
                    while username in current_user_names:
                        username = f"{user['username']}_{counter}"
                        counter += 1
                    user["username"] = username

        if table.name in ["signature", "state"]:
            continue
        is_excluded = table.name in excluded_tables
        table_pk_map = insert_org_data(con, table, table_data, pk_map, is_excluded)
        pk_map.update({table.name: table_pk_map})
    for table in table_list:
        if table.name in ["signature", "state"]:
            continue
        update_json_fields(con, table, pk_map)
    new_org_code = list(pk_map["organisation"].values())[0]
    return new_org_code


def get_pk_field_name(table: Table) -> str:
    """Imports organisation data.

    :param table: SQL Alchemy table object
    :return: Field name of `pk`
    :raises ValueError: If table does not have primary key
    """
    for column in table.columns.values():
        if column.primary_key:
            return column.name
    raise ValueError(f"Table {table} does not have primary key.")


def insert_org_data(
        con: Connection,
        table: Table,
        table_data: list,
        pk_map: dict,
        is_excluded: bool
) -> dict:
    """ Imports organisation data.

    :param con: SQL Alchemy engine connection
    :param table: SQL Alchemy table object
    :param table_data: Table data to be imported
    :param pk_map: Mapping between old `pk`s and newly created `pk`s
    :param is_excluded: Is table to be excluded from inserting
    :return: Map between old `pk`s and newly created `pk`s of the table
    """

    pk_field = get_pk_field_name(table)

    table_pk_map = {}

    # If in excluded list, append pk_map with existing primary keys
    if is_excluded:
        table_column = con.execute(select([getattr(table.c, pk_field)]))
        for item in table_column.fetchall():
            table_pk_map.update({item[pk_field]: item[pk_field]})
        return table_pk_map

    # Make a dictionary of foreignkeys with with name as key
    foreign_keys = {
        foreign_key.parent.name: foreign_key for foreign_key in list(
            table.foreign_keys
        )
    }

    while len(table_data) > 0:
        row = table_data.pop(0)
        row_pk_map = insert_row(
            con, row, pk_field, foreign_keys, table, pk_map, table_pk_map
        )
        if not row_pk_map:
            table_data.append(row)
            continue
        # Update pk_map with newly created primary key and the old one
        table_pk_map.update(row_pk_map)
    return table_pk_map


def insert_row(
        con: Connection,
        row: dict,
        pk_field: quoted_name,
        foreign_keys: dict,
        table: Table,
        pk_map: dict,
        table_pk_map: dict,
) -> dict | None:
    """Inserts single row after updating foreign key relations with newly mapped
    primary keys.

    :param con: SQL Alchemy engine connection
    :param row: Row to be inserted to the database
    :param pk_field: Primary key field name
    :param foreign_keys: A map between foreignkey field name and foreignkey object
    :param table: SQL Alchemy table object
    :param pk_map: Mapping between old `pk`s and newly created `pk`s for all tables
    :param table_pk_map: Mapping between old `pk`s and newly created `pk`s of
    current table rows
    :return: Map between old `pk` and newly created `pk` of the row
    """

    pk_value = row.pop(pk_field)

    for field, value in dict(row).items():
        if value == None:
            row.pop(field)

    for field_name in row.keys():
        if (field_name in foreign_keys) and row.get(field_name):
            fk_table_name = foreign_keys[field_name].constraint.referred_table.name

            # Self referencing tables may have connected foreign key row listed
            # below the row where the foreign key is referred. So if thw rows are
            # inserted in order, it will raise foreign key is not fount error.
            if fk_table_name == table.name:
                field_value = table_pk_map.get(row[field_name])
                if not field_value:
                    return None
            else:
                field_value = pk_map[fk_table_name].get(row[field_name])
            row[field_name] = field_value

    statement = table.insert().values(row).returning(
        getattr(table.c, pk_field)
    )
    # Insert row to database
    row_insert = con.execute(statement).scalar()

    return {pk_value: row_insert}


def update_json_fields(con: Connection, table: Table, pk_map: dict) -> None:
    """ Updates JSONB fields with updated primary key.

    JSONB fields are handled by using info attribute of SQL Alchemy tables. Following
    entries shall be added to database table for recognising JSONB fields with related
    tables here.

    `key_related_json_fields`: If the table has a jsonb field and if the stored data
    has key fields related to another table, their relation can be stored as a
    dictionary of structure ``{"field_name: related_table_name"}`` here.

    eg, `info={"key_related_json_fields": {"drs": "accounts", "crs": "accounts"}}`

    `key_related_json_fields`: If the table has a jsonb field and if the stored data
    has value fields related to another table, their relation can be stored as a
    dictionary of structure `{"field_name: related_table_name"}` here.
    eg, `info={"value_related_json_fields": {"drs": "accounts", "crs": "accounts"}}`

    :param con: SQL Alchemy engine connection
    :param table: SQL Alchemy table object
    :param pk_map: Mapping between old `pk`s and newly created `pk`s
    :return: None
    """
    # Table is being required to imported again, otherwise old data is being shown
    table = getattr(gkdb, table.name)
    pk_field = get_pk_field_name(table)
    key_related_json_fields = table.info.get("key_related_json_fields")
    value_related_json_fields = table.info.get("value_related_json_fields")
    if not (key_related_json_fields or value_related_json_fields):
        return

    orgcode = list(pk_map["organisation"].values()).pop()
    table_rows = con.execute(table.select().where(table.c.orgcode == orgcode)).fetchall()
    for row in table_rows:
        for field_name in row.keys():
            field = getattr(table.c, field_name)
            value = row[field_name]
            # Update if the key is a related field
            if key_related_json_fields and (field_name in key_related_json_fields):
                related_table_name = key_related_json_fields[field_name]
                for item in value.keys():
                    try:
                        item = int(item)
                    except ValueError:
                        continue
                    related_value = pk_map[related_table_name][int(item)]
                    con.execute(
                        table
                        .update()
                        .where(getattr(table.c, pk_field) == row[pk_field])
                        .values(
                            {
                                field_name: func.jsonb_set(
                                    field, '{'+str(related_value)+'}', field[str(item)]
                                ).op('-')(str(item))
                            }
                        )
                    )
            # Update if the value is a related field
            if value_related_json_fields and field_name in value_related_json_fields:
                related_table_name = value_related_json_fields[field_name]
                for item in value.keys():
                    related_value = pk_map[related_table_name][int(item)]
                    con.execute(
                        table
                        .update()
                        .where(getattr(table.c, pk_field) == row[pk_field])
                        .values(
                            {
                                field_name: func.jsonb_set(
                                    field, '{'+str(item)+'}', str(related_value)
                                )
                            }
                        )
                    )

def update_user_conf(con: Connection, userid: int, orgcode: int) -> None:
    """Updates user conf with new orgcode.

    :param con: SQL Alchemy engine connection
    :param userid: User ID of the updating user
    :param orgcode: `orgcode` of the new organisation
    :return: None
    """

    # User config for an organisation for admin role
    org_conf = {
        "userconf": {},
        "userrole": -1,
        "invitestatus": True
    }
    con.execute(
        gkdb.gkusers
        .update()
        .where(gkdb.gkusers.c.userid == userid)
        .values(
            orgs = func.jsonb_set(
                gkdb.gkusers.c.orgs, '{'+str(orgcode)+'}', json.dumps(org_conf)
            )
        )
    )


def delete_organisation(con: Connection, orgcode: int) -> None:
    """Deletes the organisation and org config from user table.

    :param con: SQL Alchemy engine connection
    :param orgcode: `orgcode` of the old organisation
    :return: None
    """

    # Delete the org
    con.execute(
        gkdb.organisation.delete().where(
            gkdb.organisation.c.orgcode == orgcode
        )
    )

    # Update the user config
    con.execute(
        gkdb.gkusers
        .update()
        .where(
            func.jsonb_extract_path_text(
                gkdb.gkusers.c.orgs, str(orgcode)
            ) != None,
        )
        .values(
            {
                "orgs": gkdb.gkusers.c.orgs.op('-')(str(orgcode))
            }
        )
    )


def update_organisation_rocode(con: Connection, orgcode: int) -> None:
    """Updates rocode of an organisation. If an organisation doesn't have rocode 0, this
    function checks for an organisation with ro code 0 and financial period above the
    current one, if its not found it update the rocode of current org to 1. This would
    enable it to rollover to create a new org after it.

    :param con: SQL Alchemy engine connection
    :param orgcode: `orgcode` of the old organisation
    :return: None
    """

    # Fetch org details
    organisation = con.execute(
        gkdb.organisation.select().where(
            gkdb.organisation.c.orgcode == orgcode
        )
    ).fetchone()

    if organisation["roflag"] != 0:
        related_organisations = con.execute(
            gkdb.organisation.select().where(
                and_(
                    gkdb.organisation.c.orgname == organisation["orgname"],
                    gkdb.organisation.c.orgtype == organisation["orgtype"],
                    gkdb.organisation.c.roflag == 0,
                    gkdb.organisation.c.yearstart >= organisation["yearend"],
                )
            )
        )
        if related_organisations.rowcount == 0:
            # Update the user config
            con.execute(
                gkdb.organisation.update()
                .where(gkdb.organisation.c.orgcode == orgcode)
                .values(roflag = 0)
            )
