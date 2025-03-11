from ast import literal_eval
from copy import deepcopy
from collections import defaultdict
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import text
from gkcore.views.api_invoice import getInvoiceList, getInvoiceData
from gkcore.models.gkdb import (
    state,
    product,
    unitofmeasurement,
)
from ast import literal_eval
from json import loads
from gkcore.data.enum import GST_REG_TYPE

import traceback  # for printing detailed exception logs



def taxable_value(con, inv, productcode, drcr=False):
    """
    Returns taxable value of product given invoice/drcr note and productcode
    If dr/cr is due to change in quantity(drcrmode=18) then taxable value is
    present in reductionval dict with productcode as key else dr/cr must be a
    change in ppu and new rate has to be retrieved
    """
    try:
        rate, qty = list(inv["contents"][productcode].items())[0]
        query = select([product.c.gsflag]).where(product.c.productcode == productcode)
        gsflag = con.execute(query).fetchone()[0]
        if gsflag == 19:
            qty = 1

        if drcr:
            if inv["drcrmode"] == 18:
                return float(inv["reductionval"][productcode])
            else:
                rate = inv["reductionval"][productcode]

        taxable_value = float(rate) * float(qty)
        if not drcr:
            taxable_value -= float(inv["discount"][productcode])
        return taxable_value
    except:
        print(traceback.format_exc())
        return 0


def cess_amount(con, inv, productcode, drcr=False):
    """
    Returns cess amount of product given invoice/drcr note and productcode
    """
    try:
        if inv["cess"].get(productcode) == 0 or inv["cess"] == {}:
            return 0
        else:
            cess_rate = float(inv["cess"][productcode])

            t_value = taxable_value(con, inv, productcode, drcr=drcr)
            cess_amount = t_value * cess_rate / 100

            return float(cess_amount)
    except:
        print(traceback.format_exc())
        return 0


def state_name_code(con, statename=None, statecode=None):
    """
    Returns statecode if statename is given
    Returns statename if statecode is given
    """
    if statename:
        query = select([state.c.statecode]).where(state.c.statename == statename)
    else:
        query = select([state.c.statename]).where(state.c.statecode == statecode)
    result = con.execute(query).fetchone()[0]
    return result


def normalise_state_code(statecode, gstin):
    """
    Sometimes statecode < 10 will be prefixed with zero and sometimes not
    This causes issues while using the wrong the statecode in gstin objects
    Returns a normalised statecode that is available in the gstin object
    """
    if int(statecode) < 10:
        if gstin and statecode not in gstin:
            if ("0" + str(statecode)) in gstin:
                statecode = "0" + str(statecode)
    return statecode


def product_level(con, inv, drcr=False):
    """
    Invoices/drcr notes can contain multiple products with different tax rates
    this function adds taxable value and cess amount of all products with same
    rate `data` is a dictionary with tax_rate as key and value is a dictionary
    containing taxable_value and cess_amount

    If drcr flag is True then products will be in reductionval dict
    If drcr is change in quantity then reductionval dict will contain a key
    quantities. Quantities dict contains the new quantity but that will be
    handled by taxable_value function so we can remove it
    """

    data = {}
    if drcr:
        products = list(inv["reductionval"].keys())
        if "quantities" in products:
            products.remove("quantities")
    else:
        products = inv["contents"]

    for prod in products:
        rate = float(inv["tax"][prod])
        if data.get(rate, None):
            data[rate]["taxable_value"] += taxable_value(con, inv, prod, drcr)
            data[rate]["cess"] += cess_amount(con, inv, prod, drcr)
        else:
            data[rate] = {}
            data[rate]["taxable_value"] = taxable_value(con, inv, prod, drcr)
            data[rate]["cess"] = cess_amount(con, inv, prod, drcr)

    return data


def b2b_r1(con, invoices):
    """
    Collects and formats data about invoices made to other registered taxpayers
    """

    try:

        def b2b_filter(inv):
            try:
                ts_code = normalise_state_code(
                    state_name_code(con, statename=inv["taxstate"]), inv["gstin"]
                )

                if inv["gstin"] and inv["gstin"].get(str(ts_code)):
                    return True
                else:
                    return False
            except:
                print(traceback.format_exc())
                return False

        invs = list(filter(b2b_filter, invoices))
        b2b = []
        b2b_json = {}
        for inv in invs:
            ts_code = normalise_state_code(
                state_name_code(con, statename=inv["taxstate"]), inv["gstin"]
            )

            row = defaultdict(dict)
            row["gstin"] = inv["gstin"][str(ts_code)]
            row["receiver"] = inv["custname"]
            row["invid"] = inv["invid"]
            row["invoice_number"] = inv["invoiceno"]
            row["invoice_date"] = inv["invoicedate"].strftime("%d-%b-%y")
            row["invoice_value"] = "%.2f" % float(inv["invoicetotal"])
            row["place_of_supply"] = "%s-%s" % (str(ts_code), inv["taxstate"])
            row["applicable_tax_rate"] = ""
            row["invoice_type"] = "Regular"
            row["ecommerce_gstin"] = ""
            if inv["reversecharge"] == "0":
                row["reverse_charge"] = "N"
            else:
                row["reverse_charge"] = "Y"

            b2b_json_inv = {
                "inum": inv["invoiceno"],
                "idt": inv["invoicedate"].strftime("%d-%m-%Y"),
                "val": "%.2f" % float(inv["invoicetotal"]),
                "pos": "%02d" % int(ts_code),
                "rchrg": row["reverse_charge"],
                "inv_typ": "R",  # Need to handle other gst types
                "itms": [],
            }
            for rate, tax_cess in list(product_level(con, inv).items()):
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
                prod_row["rate"] = "%.2f" % rate
                prod_row["cess"] = "%.2f" % tax_cess["cess"]
                b2b.append(prod_row)

                b2b_json_item = {
                    "num": 1
                    if not prod_row["rate"]
                    else "%d%02d"
                    % (
                        int(float(prod_row["rate"])),
                        1,
                    ),  # need to check how floating vales are handled
                    "itm_det": {
                        "txval": prod_row["taxable_value"],
                        "rt": prod_row["rate"],
                        "csamt": prod_row["cess"],
                    },
                }
                tax_amt = "%.2f" % (
                    (float(prod_row["taxable_value"]) * float(rate)) / 100.0
                )
                if inv["taxstate"] == inv["sourcestate"]:
                    b2b_json_item["itm_det"].update(
                        {
                            "camt": "%.2f" % (float(tax_amt) / 2.0),
                            "samt": "%.2f" % (float(tax_amt) / 2.0),
                        }
                    )
                else:
                    b2b_json_item["itm_det"].update(
                        {
                            "iamt": tax_amt,
                        }
                    )

                b2b_json_inv["itms"].append(b2b_json_item)

            if row["gstin"] not in b2b_json:
                b2b_json[row["gstin"]] = []

            b2b_json[row["gstin"]].append(b2b_json_inv)

        b2b_json_arr = []
        for gstin in b2b_json:
            b2b_json_arr.append({"ctin": gstin, "inv": b2b_json[gstin]})

        return {"status": 0, "data": b2b, "json": b2b_json_arr}
    except:
        print(traceback.format_exc())
        return {"status": 3}


def b2cl_r1(con, invoices):
    """
    Collects and formats data about invoices for taxable outward supplies to
    consumers where:
        a)Place of supply is outside the state where the supplier is registered
        b)The total invoice value is more than Rs 2,50,000
    """

    try:

        def b2cl_filter(inv):
            try:
                ts_code = normalise_state_code(
                    state_name_code(con, statename=inv["taxstate"]), inv["gstin"]
                )
                if inv["gstin"] and inv["gstin"].get(str(ts_code)):
                    return False
                if inv["taxstate"] == inv["sourcestate"]:
                    return False
                if inv["invoicetotal"] > 250000:
                    return True
                return False
            except:
                print(traceback.format_exc())
                return False

        # print("Invoice count = %d" % (len(invoices)))
        invs = list(filter(b2cl_filter, invoices))

        b2cl = []
        b2cl_json = {}
        for inv in invs:
            ts_code = state_name_code(con, statename=inv["taxstate"])

            row = {}
            row["invid"] = inv["invid"]
            row["invoice_number"] = inv["invoiceno"]
            row["invoice_date"] = inv["invoicedate"].strftime("%d-%b-%y")
            row["invoice_value"] = "%.2f" % float(inv["invoicetotal"])
            row["place_of_supply"] = "%02d-%s" % (ts_code, inv["taxstate"])
            row["applicable_tax_rate"] = ""
            row["ecommerce_gstin"] = ""
            row["sale_from_bonded_wh"] = "N"

            b2cl_json_inv = {
                "inum": inv["invoiceno"],
                "idt": inv["invoicedate"].strftime("%d-%m-%Y"),
                "val": "%.2f" % float(inv["invoicetotal"]),
                "itms": [],
            }

            for rate, tax_cess in list(product_level(con, inv).items()):
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
                prod_row["rate"] = "%.2f" % rate
                prod_row["cess"] = "%.2f" % tax_cess["cess"]
                b2cl.append(prod_row)

                b2cl_json_item = {
                    "num": 1
                    if not prod_row["rate"]
                    else "%d%02d" % (prod_row["rate"], 1),
                    "itm_det": {
                        "txval": prod_row["taxable_value"],
                        "rt": prod_row["rate"],
                        "csamt": prod_row["cess"],
                    },
                }
                tax_amt = "%.2f" % (
                    float(prod_row["taxable_value"] * float(rate)) / 100.0
                )
                if inv["taxstate"] == inv["sourcestate"]:
                    b2cl_json_item["itm_det"].update(
                        {
                            "camt": "%.2f" % (float(tax_amt) / 2.0),
                            "samt": "%.2f" % (float(tax_amt) / 2.0),
                        }
                    )
                else:
                    b2cl_json_item["itm_det"].update(
                        {
                            "iamt": tax_amt,
                        }
                    )

                b2cl_json_inv["itms"].append(b2cl_json_item)

            if ts_code not in b2cl_json:
                b2cl_json[ts_code] = []

            b2cl_json[ts_code].append(b2cl_json_inv)

        b2cl_json_arr = []
        for b2cl_pos in b2cl_json:
            b2cl_json_arr.append(
                {"pos": "%02d" % (b2cl_pos), "inv": b2cl_json[b2cl_pos]}
            )

        return {"status": 0, "data": b2cl, "json": b2cl_json_arr}
    except:
        print(traceback.format_exc())
        return {"status": 3}


def b2cs_r1(con, invoices, drcr):
    """
    Collects and formats data about supplies made to consumers
    of the following nature:
        a)Intra-State: Any value
        b)Inter-State: Invoice value Rs 2.5 lakhs or less

    Note1: Here entries are not made invoice wise instead entries with same
    place_of_supply and taxrate are consolidated.
    Debit Credit Notes that match the above conditions are also listed under B2CS, with negative value
    """

    try:

        def b2cs_filter(inv):
            try:
                ts_code = normalise_state_code(
                    state_name_code(con, statename=inv["taxstate"]), inv["gstin"]
                )
                if inv["gstin"] and inv["gstin"].get(str(ts_code)):
                    return False
                if inv["taxstate"] == inv["sourcestate"]:
                    return True
                if inv["invoicetotal"] <= 250000:
                    return True
                return False
            except:
                print(traceback.format_exc())
                return False

        invs = list(filter(b2cs_filter, invoices))
        print("inv count = %d" % (len(invoices)))
        b2cs = []
        b2cs_json_arr = []
        for inv in invs:
            ts_code = state_name_code(con, statename=inv["taxstate"])
            if int(ts_code) < 10:
                ts_code = "0" + str(ts_code)
            row = {}
            row["invid"] = inv["invid"]
            row["invoice_number"] = inv["invoiceno"]
            if drcr:
                row["drcrid"] = inv["drcrid"]
                row["voucher_number"] = inv["drcrno"]
                row["voucher_date"] = inv["drcrdate"].strftime("%d-%b-%y")
            else:
                row["drcrid"] = ""
                row["voucher_number"] = ""
                row["voucher_date"] = ""
            # icflag = 9 -> invoice, 3 -> cash memo
            row["icflag"] = inv["icflag"] if "icflag" in inv else 9
            row["type"] = "OE"
            row["place_of_supply"] = "%s-%s" % (str(ts_code), inv["taxstate"])
            row["applicable_tax_rate"] = ""
            row["ecommerce_gstin"] = ""
            for prod in inv["contents"]:
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = taxable_value(con, inv, prod, drcr)
                prod_row["rate"] = "%.2f" % float(inv["tax"][prod])
                cess = cess_amount(con, inv, prod, drcr)
                prod_row["cess"] = (
                    cess_amount(con, inv, prod, drcr) if cess != "" else 0
                )

                # for existing in b2cs:
                #     if (
                #         existing["place_of_supply"] == prod_row["place_of_supply"]
                #         and existing["rate"] == prod_row["rate"]
                #     ):

                #         existing["taxable_value"] += prod_row["taxable_value"]
                #         existing["cess"] += prod_row["cess"]
                #         break

                b2cs.append(prod_row)

                b2cs_json_inv = {
                    "sply_ty": "INTRA"
                    if inv["taxstate"] == inv["sourcestate"]
                    else "INTER",
                    "pos": "%02d" % (int(ts_code)),
                    "typ": "OE",
                    "txval": prod_row["taxable_value"],
                    "rt": prod_row["rate"],
                    "csamt": prod_row["cess"],
                }

                tax_amt = "%.2f" % (
                    (float(prod_row["taxable_value"]) * float(inv["tax"][prod])) / 100.0
                )

                if inv["taxstate"] == inv["sourcestate"]:
                    b2cs_json_inv.update(
                        {
                            "camt": "%.2f" % (float(tax_amt) / 2.0),
                            "samt": "%.2f" % (float(tax_amt) / 2.0),
                        }
                    )
                else:
                    b2cs_json_inv.update(
                        {
                            "iamt": tax_amt,
                        }
                    )
                b2cs_json_arr.append(b2cs_json_inv)

        for row in b2cs:
            # row["drcr_flag"] = 1 if drcr else 0
            if drcr:
                row["taxable_value"] *= -1
            row["taxable_value"] = "%.2f" % row["taxable_value"]
            if row["cess"] == 0:
                row["cess"] = "0.00"
            else:
                row["cess"] = "%.2f" % row["cess"]
        return {"status": 0, "data": b2cs, "json": b2cs_json_arr}
    except:
        print(traceback.format_exc())
        return {"status": 3, "data": []}


def cdnr_r1(con, drcr_all):
    """
    Collects and formats data about Credit/Debit Notes issued
    to the registered taxpayers
    """

    try:

        def cdnr_filter(inv):
            ts_code = normalise_state_code(
                state_name_code(con, statename=inv["taxstate"]), inv["gstin"]
            )
            # print("tscode = %s, gstin = %s" % (str(ts_code), inv["gstin"]))
            if inv["gstin"] and inv["gstin"].get(str(ts_code)):
                return True
            else:
                return False

        # print("drcr notes = %d" % (len(drcr_all)))
        drcrs = list(filter(cdnr_filter, drcr_all))

        cdnr = []
        cdnr_json = {}
        for note in drcrs:
            ts_code = normalise_state_code(
                state_name_code(con, statename=note["taxstate"]), note["gstin"]
            )
            # print(note.keys())
            row = {}
            # print("Invoice id: %s"%(str(note["invid"])))
            row["gstin"] = note["gstin"][str(ts_code)]
            row["receiver"] = note["custname"]
            row["invid"] = note["invid"]
            row["invoice_number"] = note["invoiceno"]
            row["invoice_date"] = note["invoicedate"].strftime("%d-%b-%y")
            row["drcrid"] = note["drcrid"]
            row["voucher_number"] = note["drcrno"]
            row["voucher_date"] = note["drcrdate"].strftime("%d-%b-%y")
            if note["dctypeflag"] == 4:
                row["document_type"] = "D"
            else:
                row["document_type"] = "C"
            row["place_of_supply"] = "%s-%s" % (str(ts_code), note["taxstate"])
            row["refund_voucher_value"] = "%.2f" % float(note["totreduct"])
            row["applicable_tax_rate"] = ""
            if note["taxflag"] == 7:
                row["pregst"] = "N"
            else:
                row["pregst"] = "Y"

            cdnr_json_inv = {
                "nt_num": note["invoiceno"],
                "nt_dt": note["invoicedate"].strftime("%d-%m-%Y"),
                "val": "%.2f" % float(note["totreduct"]),
                "ntty": "D" if note["dctypeflag"] == 4 else "C",
                "pos": "%02d" % (ts_code),
                "rchrg": "N",
                "inv_typ": "R",  # Need to handle other gst types
                "itms": [],
            }
            for rate, tax_cess in list(product_level(con, note, drcr=True).items()):
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
                prod_row["rate"] = "%.2f" % rate
                prod_row["cess"] = "%.2f" % tax_cess["cess"]
                cdnr.append(prod_row)

                cdnr_json_item = {
                    "num": 1
                    if not prod_row["rate"]
                    else "%d%02d"
                    % (
                        int(float(prod_row["rate"])),
                        1,
                    ),  # need to check how floating values are handled
                    "itm_det": {
                        "txval": prod_row["taxable_value"],
                        "rt": prod_row["rate"],
                        "csamt": prod_row["cess"],
                    },
                }
                tax_amt = "%.2f" % (
                    (float(prod_row["taxable_value"]) * float(rate)) / 100.0
                )
                if note["taxstate"] == note["sourcestate"]:
                    cdnr_json_item["itm_det"].update(
                        {
                            "camt": "%.2f" % (float(tax_amt) / 2.0),
                            "samt": "%.2f" % (float(tax_amt) / 2.0),
                        }
                    )
                else:
                    cdnr_json_item["itm_det"].update(
                        {
                            "iamt": tax_amt,
                        }
                    )

                cdnr_json_inv["itms"].append(cdnr_json_item)

            if row["gstin"] not in cdnr_json:
                cdnr_json[row["gstin"]] = []

            cdnr_json[row["gstin"]].append(cdnr_json_inv)

        cdnr_json_arr = []
        for cdnr_gstin in cdnr_json:
            cdnr_json_arr.append({"ctin": cdnr_gstin, "nt": cdnr_json[cdnr_gstin]})

        return {"status": 0, "data": cdnr, "json": cdnr_json_arr}
    except:
        print(traceback.format_exc())
        return {"status": 3}


def cdnur_r1(con, drcr_all):
    """
    Collects and formats data about Credit/Debit Notes issued to
    unregistered person for interstate supplies
    """

    try:
        cdnur = []

        def cdnur_filter(drcr):
            ts_code = state_name_code(con, statename=drcr["taxstate"])
            # print("Gstin = %s, tsCode = %s, taxstate = %s, sourcestate = %s, invoicetotal = %d"%(drcr["gstin"], ts_code, drcr["taxstate"], drcr["sourcestate"], drcr["invoicetotal"]))
            if drcr["gstin"] and drcr["gstin"].get(str(ts_code)):
                return False
            if drcr["taxstate"] == drcr["sourcestate"]:
                return False
            if drcr["invoicetotal"] <= 250000:
                return False
            return True

        drcrs = list(filter(cdnur_filter, drcr_all))
        cdnur_json_arr = []
        # print("drcr notes = %d" % (len(drcrs)))
        for note in drcrs:
            ts_code = state_name_code(con, statename=note["taxstate"])

            row = {}
            # ur_type can be ExportWithPay(EXPWP) / ExportWithoutPay(EXPWOP) / B2CL
            row["ur_type"] = "B2CL"
            row["invoice_number"] = note["invoiceno"]
            row["invid"] = note["invid"]
            row["invoice_date"] = note["invoicedate"].strftime("%d-%b-%y")
            row["drcrid"] = note["drcrid"]
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
            if note["taxflag"] == 7:
                row["pregst"] = "N"
            else:
                row["pregst"] = "Y"

            cdnur_json_inv = {
                "nt_num": note["invoiceno"],
                "nt_dt": note["invoicedate"].strftime("%d-%m-%Y"),
                "val": "%.2f" % float(note["totreduct"]),
                "ntty": "D" if note["dctypeflag"] == 4 else "C",
                "pos": "%02d" % (ts_code),
                "typ": "R",
                "itms": [],
            }
            for rate, tax_cess in list(product_level(con, note, drcr=True).items()):
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
                prod_row["rate"] = "%.2f" % rate
                prod_row["cess"] = "%.2f" % tax_cess["cess"]
                cdnur.append(prod_row)

                cdnur_json_item = {
                    "num": 1
                    if not prod_row["rate"]
                    else "%d%02d" % (prod_row["rate"], 1),
                    "itm_det": {
                        "txval": prod_row["taxable_value"],
                        "rt": prod_row["rate"],
                        "csamt": prod_row["cess"],
                    },
                }
                tax_amt = "%.2f" % (float(prod_row["taxable_value"] * rate) / 100.0)
                if note["taxstate"] == note["sourcestate"]:
                    cdnur_json_item["itm_det"].update(
                        {
                            "camt": "%.2f" % (float(tax_amt) / 2.0),
                            "samt": "%.2f" % (float(tax_amt) / 2.0),
                        }
                    )
                else:
                    cdnur_json_item["itm_det"].update(
                        {
                            "iamt": tax_amt,
                        }
                    )

                cdnur_json_inv["itms"].append(cdnur_json_item)

        return {"status": 0, "data": cdnur, "json": cdnur_json_arr}
    except:
        print(traceback.format_exc())
        return {"status": 3}


def hsn_r1(con, orgcode, start, end):
    """
    Retrieve all products data including product code,product description , hsn code, UOM.
    Loop through product code and retrive all sale invoice related data[ppu,tax,taxtype,sourceState,destinationState] for that particular product code.

    Store this data in following formats:
    {'SGSTamt': '40.50', 'uqc': u'PCS', 'qty': '11.00', 'prodctname': u'Madhura Sugar', 'IGSTamt': '9.90', 'hsnsac': u'45678', 'taxableamt': '505.00', 'totalvalue': '541.10', 'CESSamt': '10.10'},................, {'grand_Value': '6089.20', 'grand_CESSValue': '68.20', 'grand_CGSTValue': '158.00', 'hsnNo': 2, 'grand_ttl_TaxableValue': '6260.00', 'grand_IGSTValue': '69.80'}]
    """
    try:
        orgcode = orgcode
        start = start
        end = end
        Final = []
        hsn_json = {"data": []}
        prod_counter = 0

        prodData = con.execute(
            select(
                [
                    product.c.productcode,
                    product.c.gscode,
                    product.c.productdesc,
                    product.c.gsflag,
                    product.c.uomid,
                ]
            ).where(product.c.orgcode == orgcode)
        )
        prodData_result = prodData.fetchall()
        for products in prodData_result:
            hsn = products["gscode"] or ""
            if "{" in hsn:
                hsn = loads(hsn)
                if type(hsn) == dict:
                    if "hsn_code" in hsn:
                        hsn = hsn["hsn_code"] or ""
            prodHSN = {
                "hsnsac": hsn,
                "prodctname": products["productdesc"],
            }
            invData = con.execute(
                text("select contents ->> ':productcode' as content ,sourcestate,taxstate,discount ->>':productcode' as disc,cess ->> ':productcode' as cess,tax ->> ':productcode' as tax from invoice where contents ? ':productcode' and orgcode = ':orgcode' and inoutflag = ':inoutflag' and taxflag = ':taxflag' and icflag = ':icflag' and invoicedate >= :start and invoicedate <= :end"),
                    productcode = products["productcode"],
                    orgcode = orgcode,
                    inoutflag = 15,
                    taxflag = 7,
                    icflag = 9,
                    start = start,
                    end = end,
            )
            invoice_Data = invData.fetchall()

            ttl_Value = 0.00
            ttl_TaxableValue = 0.00
            ttl_CGSTval = 0.00
            ttl_IGSTval = 0.00
            ttl_CESSval = 0.00
            ttl_qty = 0.00

            if invoice_Data != None and len(invoice_Data) > 0:
                taxRate = 0
                for inv in invoice_Data:
                    taxable_Value = 0.00
                    cn = literal_eval(inv["content"])
                    ds = float(literal_eval(inv["disc"]))
                    ppu = float(list(cn.keys())[0])
                    tx = taxRate = float(literal_eval(inv["tax"]))
                    cs = float(literal_eval(inv["cess"]))
                    # check condition for product and service
                    if products["gsflag"] == 7:
                        price = list(cn.keys())[0]
                        qty = float(cn[price])
                        # qty = float(cn["%.2f" % float(ppu)])
                        ttl_qty += qty
                        taxable_Value = (ppu * qty) - ds
                        um = con.execute(
                            select([unitofmeasurement.c.unitname]).where(
                                unitofmeasurement.c.uomid == int(products["uomid"])
                            )
                        )
                        unitrow = um.fetchone()
                        prodHSN["uqc"] = unitrow["unitname"]
                    else:
                        taxable_Value = ppu - ds
                        prodHSN["uqc"] = "OTH"
                    ttl_TaxableValue += taxable_Value

                    # calculate state level and center level GST
                    if inv["sourcestate"] == inv["taxstate"]:
                        cgst = tx / 2.00
                        cgst_amt = taxable_Value * (cgst / 100.00)
                        ttl_CGSTval += cgst_amt
                    else:
                        igst_amt = taxable_Value * (tx / 100.00)
                        ttl_IGSTval += igst_amt

                    cess_amount = taxable_Value * (cs / 100.00)
                    ttl_CESSval += cess_amount

                    ttl_Value = (
                        float(taxable_Value)
                        + float(2 * (ttl_CGSTval))
                        + float(ttl_CESSval)
                    )

                prodHSN["qty"] = "%.2f" % float(ttl_qty)
                prodHSN["totalvalue"] = "%.2f" % float(
                    float(ttl_TaxableValue)
                    + (2 * ttl_CGSTval)
                    + float(ttl_IGSTval)
                    + float(ttl_CESSval)
                )
                prodHSN["taxableamt"] = "%.2f" % float(ttl_TaxableValue)
                prodHSN["SGSTamt"] = "%.2f" % float(ttl_CGSTval)
                prodHSN["IGSTamt"] = "%.2f" % float(ttl_IGSTval)
                prodHSN["CESSamt"] = "%.2f" % float(ttl_CESSval)
                Final.append(prodHSN)

                prod_counter += 1
                hsn_json["data"].append(
                    {
                        "num": prod_counter,
                        "hsn_sc": str(prodHSN["hsnsac"]),
                        "desc": prodHSN["prodctname"],
                        "uqc": prodHSN["uqc"],
                        "qty": prodHSN["qty"],
                        "rt": taxRate,
                        "txval": prodHSN["taxableamt"],
                        "iamt": prodHSN["IGSTamt"],
                        "samt": prodHSN["SGSTamt"],
                        "camt": prodHSN["SGSTamt"],
                        "csamt": prodHSN["CESSamt"],
                    }
                )

        return {"status": 0, "data": Final, "json": hsn_json}
    except:
        print(traceback.format_exc())
        return {"status": 3}


"""
generate_gstr_3b_data: generates the data required for creating gstr3b json and spreadsheet

"""


def generate_gstr_3b_data(con, orgcode, fromDate, toDate):
    try:
        outward_taxable_supplies = {
            "taxable_value": 0.0,
            "igst": 0.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "cess": 0.0,
        }
        outward_taxable_zero_rated = {
            "taxable_value": 0.0,
            "igst": 0.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "cess": 0.0,
        }
        outward_taxable_exempted = {
            "taxable_value": 0.0,
            "igst": 0.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "cess": 0.0,
        }
        outward_non_gst = {
            "taxable_value": 0.0,
            "igst": 0.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "cess": 0.0,
        }

        inward_reverse_charge = {
            "taxable_value": 0.0,
            "igst": 0.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "cess": 0.0,
        }
        import_goods = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}
        import_service = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}
        inward_isd = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}
        all_itc = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}
        itc_reversed_1 = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}
        itc_reversed_2 = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}
        net_itc = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}
        ineligible_1 = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}
        ineligible_2 = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}

        inward_zero_gst = {"inter": 0.0, "intra": 0.0}
        non_gst = {"inter": 0.0, "intra": 0.0}

        interest = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}

        g3b_invs = {
            "outward_taxable_supplies": [],
            "outward_taxable_zero_rated": [],
            "outward_taxable_exempted": [],
            "outward_non_gst": [],
            "inward_reverse_charge": [],
            "import_goods": [],
            "import_service": [],
            "inward_isd": [],
            "all_itc": [],
            "net_itc": [],
            "itc_reversed_1": [],
            "itc_reversed_2": [],
            "ineligible_1": [],
            "ineligible_2": [],
            "inward_zero_gst": [],
            "non_gst": [],
            "interest": [],
            "pos_unreg_comp_uin_igst": {"unreg": {}, "compos": {}, "uin": {}},
        }

        g3b_inv_map = {
            "outward_taxable_supplies": {},
            "outward_taxable_zero_rated": {},
            "outward_taxable_exempted": {},
            "outward_non_gst": {},
            "inward_reverse_charge": {},
            "import_goods": {},
            "import_service": {},
            "inward_isd": {},
            "all_itc": {},
            "net_itc": {},
            "itc_reversed_1": {},
            "itc_reversed_2": {},
            "ineligible_1": {},
            "ineligible_2": {},
            "inward_zero_gst": {},
            "non_gst": {},
            "interest": {},
            "pos_unreg_comp_uin_igst": {"unreg": {}, "compos": {}, "uin": {}},
        }

        pos_unreg_comp_uin_igst = (
            {}
        )  # {PoS: Unreg_Taxable_Amt, Unreg_IGST, Composition_Taxable_Amt, Composition_IGST, UIN_Taxamble_Amt, UIN_IGST}

        # For invoice in invoices
        #   For product in invoice.products

        invoices = getInvoiceList(
            con, orgcode, {"fromdate": fromDate, "todate": toDate, "flag": "0"}
        )

        for invoice in invoices:
            inv_data = getInvoiceData(
                con, orgcode, {"inv": "single", "invid": invoice["invid"]}
            )
            if len(inv_data):
                # print(inv_data.keys())
                gst_reg_type = (
                    inv_data["custSupDetails"]["gst_reg_type"]
                    if "gst_reg_type" in inv_data["custSupDetails"]
                    else -1
                )
                gst_party_type = (
                    inv_data["custSupDetails"]["gst_party_type"]
                    if "gst_party_type" in inv_data["custSupDetails"]
                    else -1
                )
                for prod_id in inv_data["invcontents"]:
                    prod = inv_data["invcontents"][prod_id]
                    line_uom = prod["uom"]
                    line_qty = prod["qty"]
                    line_amount = float(prod["taxableamount"])
                    # line_price = invoice_line.price_unit * (1 - (invoice_line.discount or 0.0) / 100.0)
                    # line_taxes = invoice_line.invoice_line_tax_ids.compute_all(line_price, invoice_line.invoice_id.currency_id, invoice_line.quantity, prod_id, invoice_line.invoice_id.partner_id)
                    # _logger.info(line_taxes)
                    igst_amount = cgst_amount = sgst_amount = cess_amount = 0.0

                    # tax_obj = self.env['account.tax'].browse(tax_line['id'])
                    tax_name = prod["taxname"]
                    if tax_name == "IGST":  # tax_obj.gst_type == 'igst':
                        igst_amount += float(prod["taxamount"])
                    elif tax_name == "CGST":  # tax_obj.gst_type == 'cgst':
                        cgst_amount += float(prod["taxamount"])
                    elif (
                        tax_name == "SGST" or tax_name == "UTGST"
                    ):  # tax_obj.gst_type == 'sgst':
                        sgst_amount += float(prod["taxamount"])
                        cgst_amount += float(
                            prod["taxamount"]
                        )  # Currently since CGST and SGST are the same, gkcore only stores SGST.

                    if "cess" in prod:
                        cess_amount += float(prod["cess"])

                    # cgst_amount = invoice_line.invoice_line_tax_ids.filtered(lambda r: r.gst_type == 'cgst').amount
                    # sgst_amount = invoice_line.invoice_line_tax_ids.filtered(lambda r: r.gst_type == 'sgst').amount
                    line_total_amount = float(prod["totalAmount"])
                    # _logger.info(invoice_line.invoice_line_tax_ids)
                    if line_amount < 0:
                        line_total_amount = line_total_amount * -1
                    if inv_data["inoutflag"] == 15:  # Customer Invoice
                        if (
                            line_total_amount > line_amount
                        ):  # Taxable item, not zero rated/nil rated/exempted
                            outward_taxable_supplies["taxable_value"] += line_amount
                            outward_taxable_supplies["igst"] += igst_amount
                            outward_taxable_supplies["cgst"] += cgst_amount
                            outward_taxable_supplies["sgst"] += sgst_amount
                            outward_taxable_supplies["cess"] += cess_amount
                            if (
                                invoice["invid"]
                                not in g3b_inv_map["outward_taxable_supplies"]
                            ):
                                g3b_invs["outward_taxable_supplies"].append(invoice)
                                g3b_inv_map["outward_taxable_supplies"][
                                    invoice["invid"]
                                ] = 1

                            # 3.2 Of the supplies shown in 3.1 (a) above, details of inter-State supplies made to unregisterd persons, composition taxable persons and UIN holders
                            if inv_data["taxstatecode"] != inv_data["sourcestatecode"]:
                                if pos_unreg_comp_uin_igst.get(
                                    inv_data["taxstatecode"]
                                ):
                                    pos_unreg_comp_uin_igst[inv_data["taxstatecode"]][
                                        "unreg_taxable_amt"
                                    ] += line_amount
                                    pos_unreg_comp_uin_igst[inv_data["taxstatecode"]][
                                        "unreg_igst"
                                    ] += igst_amount
                                    if (
                                        invoice["invid"]
                                        not in g3b_inv_map["pos_unreg_comp_uin_igst"][
                                            "unreg"
                                        ][inv_data["taxstatecode"]]
                                    ):
                                        g3b_invs["pos_unreg_comp_uin_igst"]["unreg"][
                                            inv_data["taxstatecode"]
                                        ].append(invoice)
                                        g3b_inv_map["pos_unreg_comp_uin_igst"]["unreg"][
                                            inv_data["taxstatecode"]
                                        ][invoice["invid"]] = 1
                                else:
                                    pos_unreg_comp_uin_igst[
                                        inv_data["taxstatecode"]
                                    ] = {
                                        "unreg_taxable_amt": line_amount,
                                        "unreg_igst": igst_amount,
                                        "comp_taxable_amt": 0,
                                        "comp_igst": 0,
                                        "uin_taxable_amt": 0,
                                        "uin_igst": 0,
                                    }  # TODO: Handle Composition & UIN holders
                                    g3b_invs["pos_unreg_comp_uin_igst"]["unreg"][
                                        inv_data["taxstatecode"]
                                    ] = []
                                    g3b_invs["pos_unreg_comp_uin_igst"]["unreg"][
                                        inv_data["taxstatecode"]
                                    ].append(invoice)

                                    g3b_inv_map["pos_unreg_comp_uin_igst"]["unreg"][
                                        inv_data["taxstatecode"]
                                    ] = {}
                                    g3b_inv_map["pos_unreg_comp_uin_igst"]["unreg"][
                                        inv_data["taxstatecode"]
                                    ][invoice["invid"]] = 1

                        else:  # Tream them all as zero rated for now
                            outward_taxable_zero_rated["taxable_value"] += line_amount
                            outward_taxable_zero_rated["igst"] += igst_amount
                            outward_taxable_zero_rated["cgst"] += cgst_amount
                            outward_taxable_zero_rated["sgst"] += sgst_amount
                            outward_taxable_zero_rated["cess"] += cess_amount
                            if (
                                invoice["invid"]
                                not in g3b_inv_map["outward_taxable_zero_rated"]
                            ):
                                g3b_invs["outward_taxable_zero_rated"].append(invoice)
                                g3b_inv_map["outward_taxable_zero_rated"][
                                    invoice["invid"]
                                ] = 1

                    # TODO: Vendor Bills with reverse charge doesn't have tax lines filled, so it must be calculated
                    elif (
                        inv_data["inoutflag"] == 9
                    ):  # and invoice.reverse_charge: #Vendor Bills with Reverse Charge applicablle
                        if int(inv_data["reversecharge"]) == 1:
                            inward_reverse_charge["taxable_value"] += line_amount
                            inward_reverse_charge["igst"] += igst_amount
                            inward_reverse_charge["cgst"] += cgst_amount
                            inward_reverse_charge["sgst"] += sgst_amount
                            inward_reverse_charge["cess"] += cess_amount
                            if (
                                invoice["invid"]
                                not in g3b_inv_map["inward_reverse_charge"]
                            ):
                                g3b_invs["inward_reverse_charge"].append(invoice)
                                g3b_inv_map["inward_reverse_charge"][
                                    invoice["invid"]
                                ] = 1
                        else:
                            if line_total_amount == line_amount:  # Zero GST taxes
                                # 5. From a supplier under composition scheme, Exempt and Nil rated
                                if gst_reg_type == GST_REG_TYPE["composition"]:
                                    if (
                                        inv_data["taxstatecode"]
                                        != inv_data["sourcestatecode"]
                                    ):
                                        inward_zero_gst["inter"] += line_amount
                                    else:
                                        inward_zero_gst["intra"] += line_amount
                                    if (
                                        invoice["invid"]
                                        not in g3b_inv_map["inward_zero_gst"]
                                    ):
                                        g3b_invs["inward_zero_gst"].append(invoice)
                            else:  # Taxable purchase, eligible for ITC
                                all_itc["igst"] += igst_amount
                                all_itc["cgst"] += cgst_amount
                                all_itc["sgst"] += sgst_amount
                                if invoice["invid"] not in g3b_inv_map["all_itc"]:
                                    g3b_invs["all_itc"].append(invoice)
                                    g3b_inv_map["all_itc"][invoice["invid"]] = 1
        for tax_type in net_itc:
            net_itc[tax_type] = (
                import_goods[tax_type]
                + import_service[tax_type]
                + inward_reverse_charge[tax_type]
                + inward_isd[tax_type]
                + all_itc[tax_type]
            ) - (itc_reversed_1[tax_type] + itc_reversed_2[tax_type])
        return {
            "invoices": g3b_invs,
            "data": {
                "outward_taxable_supplies": outward_taxable_supplies,
                "outward_taxable_zero_rated": outward_taxable_zero_rated,
                "outward_taxable_exempted": outward_taxable_exempted,
                "outward_non_gst": outward_non_gst,
                "inward_reverse_charge": inward_reverse_charge,
                "import_goods": import_goods,
                "import_service": import_service,
                "inward_isd": inward_isd,
                "all_itc": all_itc,
                "net_itc": net_itc,
                "itc_reversed_1": itc_reversed_1,
                "itc_reversed_2": itc_reversed_2,
                "ineligible_1": ineligible_1,
                "ineligible_2": ineligible_2,
                "inward_zero_gst": inward_zero_gst,
                "non_gst": non_gst,
                "interest": interest,
                "pos_unreg_comp_uin_igst": pos_unreg_comp_uin_igst,
            },
        }
    except:
        print(traceback.format_exc())
        return {}
