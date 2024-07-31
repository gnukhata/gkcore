from gkcore.views.helpers.account import get_account_details
from gkcore.views.helpers.invoice import get_invoice_details
from gkcore.views.helpers.drcr_note import get_drcr_note_details
from sqlalchemy.sql import select
from gkcore.models.gkdb import vouchers, accounts, voucherbin, invoice, product
from sqlalchemy import func



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


def get_business_item_invoice_data(
        connection,
        product_code,
        from_date = None,
        to_date = None,
):
    """Calculates total purchase and sales for a product. Product code is required, from
    date and to dates are optional. Returns tuple (Purchase Total, Sales Total)
    """
    statement = (
        select(
            [
                invoice.c.contents[str(product_code)],
                invoice.c.discount[str(product_code)],
                 invoice.c.inoutflag,
            ]
        )
        .where(func.jsonb_extract_path_text(invoice.c.contents, str(product_code)) != None)
    )

    if from_date:
        statement = statement.where(invoice.c.invoicedate >= from_date)
    if to_date:
        statement = statement.where(invoice.c.invoicedate <= to_date)

    invoices = connection.execute(statement).fetchall()

    total_purchase = 0
    total_sale = 0
    for sale_obj, discount, inout_flag in invoices:
        for amount, quantity in sale_obj.items():
            if inout_flag == 9:
                total_purchase += float(amount)*float(quantity) - float(discount)
            if inout_flag == 15:
                total_sale += float(amount)*float(quantity) - float(discount)
    return total_purchase, total_sale


def get_org_invoice_data(
        connection,
        org_code,
        from_date = None,
        to_date = None,
        gsflag = None,
):
    """Calculates total purchase and sales for a org. Organization code is required,
    from date, to date and gsflag are optional. If gsflag is given it will give result
    for the given gsflag (Service:19, Product:7). Returns tuple (Purchase Total,
    Sales Total)
    """
    statement = select([product.c.productcode]).where(
            product.c.orgcode == org_code
        )
    if gsflag:
        statement = statement.where(product.c.gsflag == gsflag)
    business_items = connection.execute(statement).fetchall()
    org_total_purchase = 0
    org_total_sale = 0
    for product_code in business_items:
        total_purchase, total_sale = get_business_item_invoice_data(
            connection, product_code[0], from_date, to_date
        )
        org_total_purchase += total_purchase
        org_total_sale += total_sale
    return org_total_purchase, org_total_sale


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
