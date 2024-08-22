from sqlalchemy import and_, select
from gkcore import eng
from gkcore.models.gkdb import customerandsupplier


def check_duplicate_contact_name(contact_name, orgcode, current_custid=None):
    """Check for entries with same name. Requires `contact_name` and `orgcode`.
    `current_custid` is required to exclude the current item from the filter while
    item name is being updated.
    """
    with eng.connect() as conn:
        statement = select([customerandsupplier.c.custid]).where(
            and_(
                customerandsupplier.c.custname == contact_name,
                customerandsupplier.c.orgcode == orgcode,
            )
        )
        if current_custid:
            statement = statement.where(
                customerandsupplier.c.custid != current_custid,
            )
        contact_results = conn.execute(statement)
        if contact_results.rowcount:
            raise ValueError("This name is already used.")
