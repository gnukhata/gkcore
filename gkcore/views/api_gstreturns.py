from datetime import datetime
from copy import deepcopy
from collections import defaultdict
from sqlalchemy.sql import select, and_
from pyramid.request import Request
from pyramid.view import view_defaults,  view_config
from gkcore.views.api_login import authCheck
from gkcore import eng, enumdict
from gkcore.models.gkdb import (invoice,
                                customerandsupplier,
                                state,
                                drcr)


def taxable_value(inv, productcode, drcr=False):
    """Returns taxable value of product given invoice and product"""
    rate, qty = inv["contents"][productcode].items()[0]
    if drcr:
        rate = inv["reductionval"][productcode]
    taxable_value = float(rate) * float(qty)
    taxable_value -= float(inv["discount"][productcode])
    return taxable_value


def cess_amount(inv, productcode, drcr=False):
    """Returns cess amount of product given invoice and product"""
    if inv["cess"][productcode] is not 0:
        cess_rate = float(inv["cess"][productcode])
        rate, qty = inv["contents"][productcode].items()[0]
        if drcr:
            rate = inv["reductionval"][productcode]
        cess_amount = (float(rate) * float(qty)) * cess_rate/100
        return float(cess_amount)
    else:
        return 0


def state_name_code(con, statename=None, statecode=None):
    """
    Returns statecode if statename is given
    Returns statename if statecode is given
    """
    if statename:
        query = (select([state.c.statecode])
                 .where(state.c.statename == statename))
    else:
        query = (select([state.c.statename])
                 .where(state.c.statecode == statecode))
    result = con.execute(query).fetchone()[0]
    return result


def product_level(inv):
    """
    Invoices can contain multiple products with different tax rates this
    function adds taxable value and cess amount of all products with same rate
    `data` is a dictionary with tax_rate as key and value is a dictionary
    containing taxable_value and cess_amount
    """
    data = {}
    for product in inv["contents"]:
        rate = inv["tax"][product]
        if data.get(rate, None):
            data[rate]["taxable_value"] += float(taxable_value(inv, product))
            data[rate]["cess"] += float(cess_amount(inv, product))
        else:
            data[rate] = {}
            data[rate]["taxable_value"] = float(taxable_value(inv, product))
            data[rate]["cess"] = float(cess_amount(inv, product))

    return data


def product_level_drcr(note):
    data = {}
    for product, value in note["reductionval"].items():
        rate = note["tax"][product]
        if data.get(rate, None):
            data[rate]["taxable_value"] += float(taxable_value(note, product, drcr=True))
            data[rate]["cess"] += float(cess_amount(note, product, drcr=True))
        else:
            data[rate] = {}
            data[rate]["taxable_value"] = float(taxable_value(note, product, drcr=True))
            data[rate]["cess"] = float(cess_amount(note, product, drcr=True))

    return data


def b2b_r1(invoices, con):
    """
    Collects and formats data about invoices made to other registered taxpayers
    """

    invs = filter(lambda inv: inv["gstin"] != {}, invoices)

    b2b = []
    for inv in invs:
        ts_code = state_name_code(con, statename=inv["taxstate"])

        row = defaultdict()
        row["gstin"] = inv["gstin"][str(ts_code)]
        row["receiver"] = inv["custname"]
        row["invoice_number"] = inv["invoiceno"]
        row["invoice_date"] = inv["invoicedate"].strftime("%d-%b-%y")
        row["invoice_value"] = "%.2f" % float(inv["invoicetotal"])
        row["place_of_supply"] = "%d-%s" % (ts_code, inv["taxstate"])
        row["applicable_tax_rate"] = ""
        row["invoice_type"] = "Regular"
        row["ecommerce_gstin"] = ""
        if inv["reversecharge"] == "0":
            row["reverse_charge"] = "N"
        else:
            row["reverse_charge"] == "Y"

        for rate, tax_cess in product_level(inv).items():
            prod_row = deepcopy(row)
            prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
            prod_row["rate"] = "%.2f" % rate
            prod_row["cess"] = "%.2f" % tax_cess["cess"]
            b2b.append(prod_row)

    return b2b


def b2cl_r1(invoices, con):
    """
    Collects and formats data about invoices for taxable outward supplies to
    consumers where:
        a)Place of supply is outside the state where the supplier is registered
        b)The total invoice value is more than Rs 2,50,000
    """

    def b2cl_filter(invoice):
        if invoice["gstin"] != {}:
            return False
        if invoice["taxstate"] == invoice["sourcestate"]:
            return False
        if invoice["invoicetotal"] > 250000:
            return True
        return False

    invs = filter(b2cl_filter, invoices)

    b2cl = []
    for inv in invs:

        ts_code = state_name_code(con, statename=inv["taxstate"])

        row = {}
        row["invoice_number"] = inv["invoiceno"]
        row["invoice_date"] = inv["invoicedate"].strftime("%d-%b-%y")
        row["invoice_value"] = "%.2f" % float(inv["invoicetotal"])
        row["place_of_supply"] = "%d-%s" % (ts_code, inv["taxstate"])
        row["applicable_tax_rate"] = ""
        row["ecommerce_gstin"] = ""
        row["sale_from_bonded_wh"] = "N"

        for rate, tax_cess in product_level(inv).items():
            prod_row = deepcopy(row)
            prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
            prod_row["rate"] = "%.2f" % rate
            prod_row["cess"] = "%.2f" % tax_cess["cess"]
            b2cl.append(prod_row)

    return b2cl


def b2cs_r1(invoices, con):
    """
    Collects and formats data about supplies made to consumers
    of the following nature:
        a)Intra-State: Any value
        b)Inter-State: Invoice value Rs 2.5 lakhs or less
    """

    def b2cs_filter(invoice):
        if invoice["gstin"] != {}:
            return False
        if invoice["taxstate"] == invoice["sourcestate"]:
            return True
        if invoice["invoicetotal"] <= 250000:
            return True
        return False

    invs = filter(b2cs_filter, invoices)

    b2cs = []
    for inv in invs:

        ts_code = state_name_code(con, statename=inv["taxstate"])

        row = {}
        row["type"] = "OE"
        row["place_of_supply"] = "%d-%s" % (ts_code, inv["taxstate"])
        row["applicable_tax_rate"] = ""
        row["ecommerce_gstin"] = ""

        for product in inv["contents"]:
            prod_row = deepcopy(row)
            prod_row["taxable_value"] = float(taxable_value(inv, product))
            prod_row["rate"] = "%.2f" % float(inv["tax"][product])
            cess = cess_amount(inv, product)
            prod_row["cess"] = float(cess_amount(inv, product)) if cess != "" else 0

            for existing in b2cs:
                if (existing["place_of_supply"] == prod_row["place_of_supply"]
                        and existing["rate"] == prod_row["rate"]):

                    existing["taxable_value"] += prod_row["taxable_value"]
                    existing["cess"] += prod_row["cess"]
                    break
            else:
                b2cs.append(prod_row)

    for row in b2cs:
        row["taxable_value"] = "%.2f" % row["taxable_value"]
        if row["cess"] is 0:
            row["cess"] = ""
        else:
            row["cess"] = "%.2f" % row["cess"]

    return b2cs


def cdnr_r1(drcr_all, con):
    """
    Collects and formats data about Credit/ Debit Notes/Refund vouchers issued
    to the registered taxpayers
    """

    drcrs = filter(lambda inv: inv["gstin"] != {}, drcr_all)

    cdnr = []
    for note in drcrs:

        ts_code = state_name_code(con, statename=note["taxstate"])

        row = {}
        row["gstin"] = note["gstin"][str(ts_code)]
        row["receiver"] = note["custname"]
        row["invoice_number"] = note["invoiceno"]
        row["invoice_date"] = note["invoicedate"].strftime("%d-%b-%y")
        row["voucher_number"] = note["drcrno"]
        row["voucher_date"] = note["drcrdate"].strftime("%d-%b-%y")
        if note["dctypeflag"] == 4:
            row["document_type"] = "D"
        else:
            row["document_type"] = "C"
        row["place_of_supply"] = "%d-%s" % (ts_code, note["taxstate"])
        row["refund_voucher_value"] = "%.2f" % float(note["totreduct"])
        row["applicable_tax_rate"] = ""
        row["pregst"] = "N"

        for rate, tax_cess in product_level_drcr(note).items():
            prod_row = deepcopy(row)
            prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
            prod_row["rate"] = "%.2f" % rate
            prod_row["cess"] = "%.2f" % tax_cess["cess"]
            cdnr.append(prod_row)

    return cdnr


def cdnur_r1(drcr_all, con):
    """
    Collects and formats data about Credit/Debit Notes issued to
    unregistered person for interstate supplies
    """

    cdnur = []

    def cdnur_filter(drcr):
        return (drcr["gstin"] == {}
                and drcr["taxstate"] != drcr["sourcestate"])

    drcrs = filter(cdnur_filter, drcr_all)

    for note in drcrs:

        ts_code = state_name_code(con, statename=note["taxstate"])

        row = {}
        if note["invoicetotal"] > 250000:
            row["ur_type"] = "B2CL"
        else:
            row["ur_type"] = "B2CS"
        row["invoice_number"] = note["invoiceno"]
        row["invoice_date"] = note["invoicedate"].strftime("%d-%b-%y")
        row["voucher_number"] = note["drcrno"]
        row["voucher_date"] = note["drcrdate"].strftime("%d-%b-%y")
        if note["dctypeflag"] == 4:
            row["document_type"] = "D"
        else:
            row["document_type"] = "C"
        row["place_of_supply"] = "%d-%s" % (ts_code, note["taxstate"])
        row["supply_type"] = "Inter State"
        row["refund_voucher_value"] = "%.2f" % float(note["totreduct"])
        row["applicable_tax_rate"] = ""
        row["pregst"] = "N"

        for rate, tax_cess in product_level_drcr(note).items():
            prod_row = deepcopy(row)
            prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
            prod_row["rate"] = "%.2f" % rate
            prod_row["cess"] = "%.2f" % tax_cess["cess"]
            cdnur.append(prod_row)

    return cdnur


@view_defaults(route_name='gstreturns')
class GstReturn(object):

    def __init__(self, request):
        self.request = Request
        self.request = request

    @view_config(request_method='GET',
                 request_param="type=r1",
                 renderer='json')
    def r1(self):
        """
        Returns JSON with b2b, b2cl, b2cs, cdnr, cdnur data required
        to file GSTR1
        """
        token = self.request.headers.get("gktoken", None)

        if token is None:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        authDetails = authCheck(token)
        if authDetails["auth"] is False:
            return {"gkstatus":  enumdict["UnauthorisedAccess"]}

        self.con = eng.connect()
        dataset = self.request.params

        start_period = datetime.strptime(dataset["start"], "%Y-%m-%d")
        end_period = datetime.strptime(dataset["end"], "%Y-%m-%d")
        orgcode = authDetails["orgcode"]

        # invoices
        query = (select([invoice,
                        customerandsupplier.c.gstin,
                        customerandsupplier.c.custname])
                 .where(
                     and_(
                         invoice.c.invoicedate.between(
                             start_period.strftime("%Y-%m-%d"),
                             end_period.strftime("%Y-%m-%d")
                         ),
                         invoice.c.inoutflag == 15,
                         invoice.c.taxflag == 7,
                         invoice.c.orgcode == orgcode,
                         invoice.c.custid == customerandsupplier.c.custid,
                     )
                 ))
        invoices = self.con.execute(query).fetchall()

        # debit/credit notes
        query = (select([drcr, invoice, customerandsupplier])
                 .select_from(
                    drcr.join(invoice).join(customerandsupplier)
                 )
                 .where(
                     and_(
                         invoice.c.invoicedate.between(
                             start_period.strftime("%Y-%m-%d"),
                             end_period.strftime("%Y-%m-%d")
                         ),
                         invoice.c.inoutflag == 15,
                         invoice.c.taxflag == 7,
                         drcr.c.orgcode == orgcode,
                     )
                 ))

        drcrs_all = self.con.execute(query).fetchall()

        gkdata = {}
        gkdata["b2b"] = b2b_r1(invoices, self.con)
        gkdata["b2cl"] = b2cl_r1(invoices, self.con)
        gkdata["b2cs"] = b2cs_r1(invoices, self.con)
        gkdata["cdnr"] = cdnr_r1(drcrs_all, self.con)
        gkdata["cdnur"] = cdnur_r1(drcrs_all, self.con)

        self.con.close()
        return {"gkresult": 0, "gkdata": gkdata}
