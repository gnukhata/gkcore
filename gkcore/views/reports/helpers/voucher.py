from sqlalchemy.sql import select
from gkcore.models.gkdb import vouchers, accounts, voucherbin
from gkcore import enumdict

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


def get_voucher_accounts(accounts_list, entry_type, connection):
    """Fetches the account details of voucher accounts and returns a list of dicts
    with account details."""
    voucher_accounts = []
    for account_code in accounts_list.keys():
        account_details = get_account_details(account_code, connection)
        account_details.update(
            {"amount": float(accounts_list[account_code]), "entry_type": entry_type}
        )
        voucher_accounts.append(account_details)
    return voucher_accounts


def get_transaction_details(voucher_code, connection, entry_type=None, is_cancelled=False):
    """Returns details of a transaction. Dr/Cr items will be listed in a unified list
    with "name", "group", "sysaccount", "amount and entry_type" data.
    Attributes: `voucher_id`, `is_cancelled`, `entry_type`
    `is_cancelled` is the status of voucher, it should be true if the voucher is
    cancelled. `is_cancelled` is False by default.
    `entry_type` can be "Dr" or "Cr", by default its None.
    """
    voucher_table = voucherbin if is_cancelled else vouchers
    voucher = connection.execute(
        select("*").where(voucher_table.c.vouchercode == voucher_code)
    ).fetchone()
    if not voucher:
        return voucher
    voucher = dict(voucher)
    if not entry_type:
        voucher["transactions"] = [
            *get_voucher_accounts(voucher["drs"], "Dr", connection),
            *get_voucher_accounts(voucher["crs"], "Cr", connection),
        ]
    elif entry_type in ["Dr", "Cr"]:
        voucher["transactions"] = [
            *get_voucher_accounts(voucher[entry_type.lower()+"s"], entry_type, connection),
        ]
    else:
        raise AttributeError("'entry_type' accepts only 'Dr' and 'Cr' as allowed values")
    return voucher


def billwiseEntryLedger(con, orgcode, vouchercode, invid, drcrid):
    try:
        dcinfo = ""
        if invid == None:
            billdetl = con.execute(
                "select invid, adjamount from billwise where vouchercode = %d and orgcode =%d"
                % (vouchercode, orgcode)
            )
            billDetails = billdetl.fetchall()
            if len(billDetails) != 0:
                inno = "Invoice Nos.:"
                cmno = "Cash Memo Nos.:"
                for inv in billDetails:
                    invno = con.execute(
                        "select invoiceno, icflag from invoice where invid = %d and orgcode = %d"
                        % (inv["invid"], orgcode)
                    )
                    invinfo = invno.fetchone()
                    if invinfo["icflag"] == 9:
                        inno += (
                            str(invinfo["invoiceno"])
                            + ":"
                            + str(inv["adjamount"])
                            + ","
                        )
                        dcinfo = inno
                    else:
                        cmno += (
                            str(invinfo["invoiceno"])
                            + ":"
                            + str(inv["adjamount"])
                            + ","
                        )
                        dcinfo = cmno
        else:
            invno = con.execute(
                "select  invoiceno, icflag from invoice where invid = %d and orgcode = %d"
                % (invid, orgcode)
            )
            invinfo = invno.fetchone()
            if invinfo["icflag"] == 9:
                dcinfo = "Invoice No.:" + str(invinfo["invoiceno"])
            else:
                dcinfo = "Cash Memo No.:" + str(invinfo["invoiceno"])
        if drcrid != None:
            drcrno = con.execute(
                "select drcrno, dctypeflag from drcr where drcrid = %d and orgcode = %d"
                % (drcrid, orgcode)
            )
            drcrinfo = drcrno.fetchone()
            if drcrinfo["dctypeflag"] == 3:
                dcinfo = "Credit note no.:" + str(drcrinfo["drcrno"])
            else:
                dcinfo = "Dedit note no.:" + str(drcrinfo["drcrno"])
        return dcinfo
    except:
        return {"gkstatus": enumdict["ConnectionFailed"]}