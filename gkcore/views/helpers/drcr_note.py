from gkcore.views.helpers.invoice import get_invoice_details
from sqlalchemy.sql import select
from gkcore.models.gkdb import drcr


def get_drcr_note_details(connection, drcr_id):
    """ Fetches debit-credit note entry details.

    Details will include,
    1. All debit-credit note database fields.
    2. Info available from `get_invoice_details` function.
    3. Item wise tax details for debit-credit note.
    4. Debit-credit note tax free total.
    5. Debit-credit notetax included total.
    6. Cumulative tax amount for the debit-credit note.
    7. Document No.
    """

    drcr_note_details = connection.execute(
        select("*").where(drcr.c.drcrid == drcr_id)
    ).fetchone()
    invoice_details = get_invoice_details(connection, drcr_note_details["invid"])

    drcr_note_qty = drcr_note_details["reductionval"].pop("quantities")
    drcr_note_price = drcr_note_details["reductionval"]

    drcr_tax_details = []
    if invoice_details["taxflag"] == 22:
        tax_name = "VAT"
    elif invoice_details["taxflag"] == 7:
        if invoice_details["sourcestate"] == invoice_details["sourcestate"]:
            tax_name = "SGST"
        else:
            tax_name = "IGST"

    total_amount = 0
    for item_id, qty in drcr_note_qty.items():
        tax_percent = invoice_details["tax"][item_id]
        price_taxfree = float(qty)*float(drcr_note_price[item_id])
        tax_percent = float(tax_percent)/2 if tax_name == "SGST" else float(tax_percent)
        drcr_sign = -1 if drcr_note_details["dctypeflag"] == 3 else 1
        tax_amount = drcr_sign*price_taxfree*tax_percent/100
        total_amount += (
            drcr_sign*price_taxfree+tax_amount*(2 if tax_name == "SGST" else 1)
        )
        if tax_amount == 0:
            continue
        item_tax_details = {
            "product_id": item_id,
            "tax_amount": f"{tax_amount:.2f}",
            "tax_name": tax_name,
            "tax_str": f"{tax_percent}% {tax_name}",
            "tax_percent": tax_percent,
        }
        drcr_tax_details.append(item_tax_details)
        if tax_name == "SGST":
            tax_name = "CGST"
            drcr_tax_details.append(
                {
                    "product_id": item_id,
                    "tax_amount": f"{tax_amount:.2f}",
                    "tax_name": tax_name,
                    "tax_str": f"{tax_percent}% {tax_name}",
                    "tax_percent": tax_percent,
                }
            )

    return {
        **drcr_note_details,
        **invoice_details,
        "docuemnt_no": drcr_note_details["drcrno"],
        "tax_data": drcr_tax_details,
        "taxed": total_amount,
    }
