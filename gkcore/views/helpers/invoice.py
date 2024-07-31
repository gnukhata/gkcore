from gkcore.views.helpers.contact import get_party_details
from sqlalchemy.sql import select
from gkcore.models.gkdb import invoice, state


def get_invoice_details(connection, invoice_id):
    """ Fetches invoice details.

    Details will include,
    1. Invoice database fields: `invid`, `invoiceno`, `invnarration`, `contents`,
    `invoicedate`, `invoicetotal`, `icflag`, `custid`, `inoutflag`, `address`,
    `tax`, `taxflag`, `taxstate`, `sourcestate`, `cess` and `discount`.
    2. Party details - contact details of customer/seller.
    3. GSTIN.
    4. Item wise tax details.
    5. Invoice tax free total.
    6. Invoice tax included total.
    7. Cumulative tax amount for the invoice.
    8. Document No.
    """

    invoice_details = connection.execute(
        select(
            [
                invoice.c.invid,
                invoice.c.invoiceno,
                invoice.c.invnarration,
                invoice.c.contents,
                invoice.c.invoicedate,
                invoice.c.invoicetotal,
                invoice.c.icflag,
                invoice.c.custid,
                invoice.c.inoutflag,
                invoice.c.address,
                invoice.c.tax,
                invoice.c.taxflag,
                invoice.c.taxstate,
                invoice.c.sourcestate,
                invoice.c.cess,
                invoice.c.discount,
            ]
        ).where(invoice.c.invid == invoice_id)
    ).fetchone()

    party_details = get_party_details(connection, invoice_details["custid"])

    state_details = connection.execute(
        select([state.c.statecode]).where(
            state.c.statename == invoice_details["taxstate"]
        )
    ).fetchone()

    gstin = (
        party_details["gstin"].get(str(state_details["statecode"]))
        if party_details["gstin"]
        else party_details["gstin"]
    )

    tax_details = []
    if invoice_details["taxflag"] == 22:
        tax_name = "VAT"
    elif invoice_details["taxflag"] == 7:
        if invoice_details["sourcestate"] == invoice_details["sourcestate"]:
            tax_name = "SGST"
        else:
            tax_name = "IGST"


    tax_total = sum([float(value) for value in invoice_details["tax"].values()])
    invoice_total_taxfree = float(invoice_details["invoicetotal"])*100/(100+tax_total)

    for item_id, tax_percent in invoice_details["tax"].items():
        tax_percent = float(tax_percent)/2 if tax_name == "SGST" else float(tax_percent)
        item_qty = float(list(invoice_details["contents"][item_id].values())[0])
        item_price = float(list(invoice_details["contents"][item_id].keys())[0])
        item_discount = float(invoice_details["discount"][item_id])
        item_price_taxfree = item_price*item_qty - item_discount
        tax_amount = f"{item_price_taxfree*tax_percent/100:.2f}"
        if tax_amount == "0.00":
            continue
        item_tax_details = {
            "product_id": item_id,
            "tax_amount": tax_amount,
            "tax_name": tax_name,
            "tax_str": f"{tax_percent}% {tax_name}",
            "tax_percent": tax_percent,
        }
        tax_details.append(item_tax_details)
        if tax_name == "SGST":
            tax_name = "CGST"
            tax_details.append(
                {
                    "product_id": item_id,
                    "tax_amount": tax_amount,
                    "tax_name": tax_name,
                    "tax_str": f"{tax_percent}% {tax_name}",
                    "tax_percent": tax_percent,
                }
            )

    return {
        **dict(invoice_details),
        **dict(party_details),
        "docuemnt_no": invoice_details["invoiceno"],
        "tax_total": sum([float(value) for value in invoice_details["tax"].values()]),
        "tax_data": tax_details,
        "taxfree": f"{invoice_total_taxfree:.2f}",
        "taxed": float(invoice_details['invoicetotal']),
        "gstin": gstin,
    }
