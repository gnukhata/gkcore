from sqlalchemy.sql import select
from gkcore.models.gkdb import accounts

def get_account_details(account_code, connection):
    """Fetches the account details and returns a dict with keys, "name", "group" and
    "sysaccount"."""
    account = connection.execute(
        select("*").where(accounts.c.accountcode == account_code)
    ).fetchone()
    return {
        "account_name": account["accountname"],
        "account_group": account["groupcode"],
        "is_sysaccount": account["sysaccount"]
    }
