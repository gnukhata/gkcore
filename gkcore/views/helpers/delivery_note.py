from datetime import datetime
from sqlalchemy.sql import select, and_
from gkcore.models.gkdb import (
    dcinv,
    delchal,
    delchalbin,
    stock,
)


def create_delivery_note(con, payload, org_code):
    delchaldata = payload['delchalPayload']["delchaldata"]
    stockdata = payload['delchalPayload']["stockdata"]
    discount = payload["payload"]["invoice"]["discount"]
    freeqty = delchaldata["freeqty"]
    inoutflag = stockdata["inout"]
    items = delchaldata["contents"]
    delchaldata["orgcode"] = org_code
    stockdata["orgcode"] = org_code
    if delchaldata["dcflag"] == 19:
        delchaldata["issuerid"] = org_code
    result = con.execute(delchal.insert(), [delchaldata])
    if result.rowcount == 1:
        dciddata = con.execute(
            select([delchal.c.dcid, delchal.c.dcdate]).where(
                and_(
                    delchal.c.orgcode == org_code,
                    delchal.c.dcno == delchaldata["dcno"],
                    delchal.c.custid == delchaldata["custid"],
                )
            )
        )
        dcidrow = dciddata.fetchone()
        stockdata["dcinvtnid"] = dcidrow["dcid"]
        stockdata["dcinvtnflag"] = 4
        stockdata["stockdate"] = dcidrow["dcdate"]

        for key in list(items.keys()):
            itemQty = float(list(items[key].values())[0])
            itemRate = float(list(items[key].keys())[0])
            itemTotalDiscount = float(discount.get(key, 0))
            itemDiscount = 0
            if itemQty:
                itemDiscount = itemTotalDiscount / itemQty
            stockdata["rate"] = itemRate - itemDiscount
            stockdata["productcode"] = key
            stockdata["qty"] = itemQty + float(freeqty[key])
            result = con.execute(stock.insert(), [stockdata])
            if "goid" in stockdata:
                resultgoprod = con.execute(
                    select([goprod]).where(
                        and_(
                            goprod.c.goid == stockdata["goid"],
                            goprod.c.productcode == key,
                        )
                    )
                )
                if resultgoprod.rowcount == 0:
                    result = con.execute(
                        goprod.insert(),
                        [
                            {
                                "goid": stockdata["goid"],
                                "productcode": key,
                                "goopeningstock": 0.00,
                                "orgcode": org_code,
                            }
                        ],
                    )
        return {
            "gkstatus": enumdict["Success"],
            "gkresult": dcidrow["dcid"],
        }


def move_delivery_note_to_bin(con, delivery_note_id, org_code):
    """Soft delete delivery note record with the given id by removing it
    from delchal table and adding to delchalbin table.
    """

    # Fetch details of the given delivery note from the delchal table
    delivery_note = con.execute(
        select([delchal]).where(delchal.c.dcid == delivery_note_id)
    ).fetchone()
    delivery_note_archive = dict(delivery_note.items())

    # Fetch adjusted stock id and related godown id from stock table.
    # dcinvtnflag 4 is used to filter stock adjustment by delivery note.
    adjusted_stock = con.execute(
        select([stock.c.stockid, stock.c.goid]).where(and_(
            stock.c.dcinvtnid == int(delivery_note_id),
            stock.c.dcinvtnflag == 4,
            stock.c.orgcode == org_code,
        ))
    ).fetchone()

    # If stock record exists, update delivery_note_archive with godown id
    # and delete the stock record.
    godown_id = None
    if hasattr(adjusted_stock, "stockid"):
        stock_id = adjusted_stock["stockid"]
        godown_id = adjusted_stock["goid"]
        delivery_note_archive.update({
            "goid": godown_id,
        })
        con.execute(stock.delete().where(stock.c.stockid == stock_id))

    # Move delivery note data from delchal table to delchalbin table
    con.execute(delchalbin.insert(), [delivery_note_archive])
    con.execute(
        delchal.delete().where(and_(
            delchal.c.dcid == int(delivery_note_id),
            delchal.c.orgcode == org_code,
        ))
    )

    # Return related data
    return {
        **delivery_note_archive,
        "dcno": delivery_note["dcno"],
        "dcdate": datetime.strftime(delivery_note["dcdate"], "%d-%m-%Y"),
    }


def cancel_delivery_note(con, invoice_id, org_code):
    """Cancel delivery note related to the given invoice id.
    This updates all tables affected by the given delivery note. It also calls
    move_delivery_note_to_bin function for soft deleting the delivery note
    record by moving it from delchal table to the delchalbin table."""

    # Fetch details of delivery note related to the given invoice from dcinv table
    delivery_note = con.execute(
        select([dcinv.c.dcinvid, dcinv.c.dcid]).where(and_(
            dcinv.c.invid == int(invoice_id),
            dcinv.c.orgcode == org_code,
        ))
    ).fetchone()

    # Exit if no related delivery note found
    if not hasattr(delivery_note, "dcinvid"):
        return {}

    # Delete dcinv record which connects invoice and delivery note
    con.execute(
        dcinv.delete()
        .where(dcinv.c.dcinvid == delivery_note["dcinvid"])
    )

    # Soft delete delivery note
    delivery_note_details = move_delivery_note_to_bin(
        con, delivery_note["dcid"], org_code,
    )

    return delivery_note_details
