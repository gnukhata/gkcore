"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020 Digital Freedom Foundation & Accion Labs Pvt. Ltd.

  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.

  GNUKhata is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License along with GNUKhata (COPYING); if not, write to the
  Free Software Foundation, Inc.,51 Franklin Street,
  Fifth Floor, Boston, MA 02110, United States


Contributors:
"AKhil KP" <akhilkpdasan@protonmail.com>
'Prajkta Patkar' <prajakta@dff.org.in>
"""

from datetime import datetime
from ast import literal_eval
from copy import deepcopy
from sqlalchemy.engine.base import Connection
from collections import defaultdict
from sqlalchemy.sql import select, and_
from pyramid.request import Request
from pyramid.view import view_defaults, view_config
from gkcore.views.api_login import authCheck
from gkcore.views.api_invoice import getInvoiceList, getInvoiceData
from gkcore import eng, enumdict
from gkcore.models.gkdb import (
    invoice,
    customerandsupplier,
    state,
    product,
    drcr,
    unitofmeasurement,
)
from ast import literal_eval
import requests
from base64 import b64decode, b64encode
from json import dumps, loads
from gkcore.enum import GST_REG_TYPE, GST_PARTY_TYPE

import traceback  # for printing detailed exception logs


def taxable_value(inv, productcode, con, drcr=False):
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


def cess_amount(inv, productcode, con, drcr=False):
    """
    Returns cess amount of product given invoice/drcr note and productcode
    """
    try:
        if inv["cess"].get(productcode) == 0 or inv["cess"] == {}:
            return 0
        else:
            cess_rate = float(inv["cess"][productcode])

            t_value = taxable_value(inv, productcode, con, drcr=drcr)
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


def product_level(inv, con, drcr=False):
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
            data[rate]["taxable_value"] += taxable_value(inv, prod, con, drcr)
            data[rate]["cess"] += cess_amount(inv, prod, con, drcr)
        else:
            data[rate] = {}
            data[rate]["taxable_value"] = taxable_value(inv, prod, con, drcr)
            data[rate]["cess"] = cess_amount(inv, prod, con, drcr)

    return data


def b2b_r1(invoices, con):
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

            for rate, tax_cess in list(product_level(inv, con).items()):
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
                prod_row["rate"] = "%.2f" % rate
                prod_row["cess"] = "%.2f" % tax_cess["cess"]
                b2b.append(prod_row)

        return {"status": 0, "data": b2b}
    except:
        print(traceback.format_exc())
        return {"status": 3}


def b2cl_r1(invoices, con):
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
        for inv in invs:

            ts_code = state_name_code(con, statename=inv["taxstate"])

            row = {}
            row["invid"] = inv["invid"]
            row["invoice_number"] = inv["invoiceno"]
            row["invoice_date"] = inv["invoicedate"].strftime("%d-%b-%y")
            row["invoice_value"] = "%.2f" % float(inv["invoicetotal"])
            row["place_of_supply"] = "%d-%s" % (ts_code, inv["taxstate"])
            row["applicable_tax_rate"] = ""
            row["ecommerce_gstin"] = ""
            row["sale_from_bonded_wh"] = "N"

            for rate, tax_cess in list(product_level(inv, con).items()):
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
                prod_row["rate"] = "%.2f" % rate
                prod_row["cess"] = "%.2f" % tax_cess["cess"]
                b2cl.append(prod_row)

        return {"status": 0, "data": b2cl}
    except:
        print(traceback.format_exc())
        return {"status": 3}


def b2cs_r1(invoices, con, drcr):
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
        for inv in invs:

            ts_code = state_name_code(con, statename=inv["taxstate"])
            if int(ts_code) < 10:
                ts_code = "0" + str(ts_code)
            row = {}
            row["invid"] = inv["invid"]
            row["invoice_number"] = inv["invoiceno"]
            # icflag = 9 -> invoice, 3 -> cash memo
            row["icflag"] = inv["icflag"] if "icflag" in inv else 9
            row["type"] = "OE"
            row["place_of_supply"] = "%s-%s" % (str(ts_code), inv["taxstate"])
            row["applicable_tax_rate"] = ""
            row["ecommerce_gstin"] = ""
            for prod in inv["contents"]:
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = taxable_value(inv, prod, con, drcr)
                prod_row["rate"] = "%.2f" % float(inv["tax"][prod])
                cess = cess_amount(inv, prod, con, drcr)
                prod_row["cess"] = cess_amount(inv, prod, con, drcr) if cess != "" else 0

                # for existing in b2cs:
                #     if (
                #         existing["place_of_supply"] == prod_row["place_of_supply"]
                #         and existing["rate"] == prod_row["rate"]
                #     ):

                #         existing["taxable_value"] += prod_row["taxable_value"]
                #         existing["cess"] += prod_row["cess"]
                #         break

                b2cs.append(prod_row)

        for row in b2cs:
            row["drcr_flag"] = 1 if drcr else 0
            if drcr:
                row["taxable_value"] *= -1
            row["taxable_value"] = "%.2f" % row["taxable_value"]
            if row["cess"] == 0:
                row["cess"] = "0.00"
            else:
                row["cess"] = "%.2f" % row["cess"]
        return {"status": 0, "data": b2cs}
    except:
        print(traceback.format_exc())
        return {"status": 3, "data": []}


def cdnr_r1(drcr_all, con):
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
            for rate, tax_cess in list(product_level(note, con, drcr=True).items()):
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
                prod_row["rate"] = "%.2f" % rate
                prod_row["cess"] = "%.2f" % tax_cess["cess"]
                cdnr.append(prod_row)

        return {"status": 0, "data": cdnr}
    except:
        print(traceback.format_exc())
        return {"status": 3}


def cdnur_r1(drcr_all, con):
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
            for rate, tax_cess in list(product_level(note, con, drcr=True).items()):
                prod_row = deepcopy(row)
                prod_row["taxable_value"] = "%.2f" % tax_cess["taxable_value"]
                prod_row["rate"] = "%.2f" % rate
                prod_row["cess"] = "%.2f" % tax_cess["cess"]
                cdnur.append(prod_row)

        return {"status": 0, "data": cdnur}
    except:
        print(traceback.format_exc())
        return {"status": 3}


def hsn_r1(orgcode, start, end, con):

    """
    Retrieve all products data including product code,product description , hsn code, UOM.
    Loop through product code and retrive all sale invoice related data[ppu,tax,taxtype,sourceState,destinationState] for that particular product code.

    Store this data in following formats:
    {'SGSTamt': '40.50', 'uqc': u'PCS', 'qty': '11.00', 'prodctname': u'Madhura Sugar', 'IGSTamt': '9.90', 'hsnsac': u'45678', 'taxableamt': '505.00', 'totalvalue': '541.10', 'CESSamt': '10.10'},................, {'grand_Value': '6089.20', 'grand_CESSValue': '68.20', 'grand_CGSTValue': '158.00', 'hsnNo': 2, 'grand_ttl_TaxableValue': '6260.00', 'grand_IGSTValue': '69.80'}]"""
    try:
        orgcode = orgcode
        start = start
        end = end
        Final = []

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
                "select contents ->> '%s' as content ,sourcestate,taxstate,discount ->>'%s' as disc,cess ->> '%s' as cess,tax ->> '%s' as tax from invoice where contents ? '%s' and orgcode = '%d' and inoutflag = '%d'and taxflag = '%d' and icflag = '%d' and invoicedate >= '%s' and invoicedate <= '%s'"
                % (
                    products["productcode"],
                    products["productcode"],
                    products["productcode"],
                    products["productcode"],
                    products["productcode"],
                    int(orgcode),
                    15,
                    7,
                    9,
                    str(start),
                    str(end),
                )
            )
            invoice_Data = invData.fetchall()

            ttl_Value = 0.00
            ttl_TaxableValue = 0.00
            ttl_CGSTval = 0.00
            ttl_IGSTval = 0.00
            ttl_CESSval = 0.00
            ttl_qty = 0.00

            if invoice_Data != None and len(invoice_Data) > 0:
                for inv in invoice_Data:
                    taxable_Value = 0.00
                    cn = literal_eval(inv["content"])
                    ds = float(literal_eval(inv["disc"]))
                    ppu = float(list(cn.keys())[0])
                    tx = float(literal_eval(inv["tax"]))
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

        return {"status": 0, "data": Final}
    except:
        # print(traceback.format_exc())
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


@view_defaults(route_name="gstreturns")
class GstReturn(object):
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    @view_config(request_method="GET", request_param="type=r1", renderer="json")
    def r1(self):

        """
        Returns JSON with b2b, b2cl, b2cs, cdnr, cdnur data required
        to file GSTR1
        Note: In sheets b2b, b2cl, cdnr, cdnur entries are according to
        GST tax rate
        Example:
            If Invoice contains 3 products with taxrates 6%, 12%, 6%
            respectively taxable value of Product 1 and Product 3 will be
            combined into single entry (taxable value and cess amount of these
            products will be added)
            Product 2 will have a separate entry
        """

        token = self.request.headers.get("gktoken", None)
        print("GST return")
        if token == None:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        try:
            self.con = eng.connect()
            dataset = self.request.params
            start_period = datetime.strptime(dataset["start"], "%Y-%m-%d")
            end_period = datetime.strptime(dataset["end"], "%Y-%m-%d")
            orgcode = authDetails["orgcode"]

            # All Sale Invoices
            inv_all_query = select([invoice]).where(
                and_(
                    invoice.c.invoicedate.between(
                        start_period.strftime("%Y-%m-%d"),
                        end_period.strftime("%Y-%m-%d"),
                    ),
                    invoice.c.inoutflag == 15,
                    invoice.c.taxflag == 7,
                    invoice.c.orgcode == orgcode,
                )
            )
            inv_all = self.con.execute(inv_all_query).fetchall()
            invoices = []
            inv_map = {}

            counter = 0
            for inv in inv_all:
                invoices.append(dict(inv))
                invoices[counter]["gstin"] = {}
                invoices[counter]["custname"] = ""
                inv_map[inv["invid"]] = counter
                counter += 1

            # All sale invoices that have customers
            cust_inv_query = select(
                [invoice, customerandsupplier.c.gstin, customerandsupplier.c.custname]
            ).where(
                and_(
                    invoice.c.invoicedate.between(
                        start_period.strftime("%Y-%m-%d"),
                        end_period.strftime("%Y-%m-%d"),
                    ),
                    invoice.c.inoutflag == 15,
                    invoice.c.taxflag == 7,
                    invoice.c.orgcode == orgcode,
                    invoice.c.custid == customerandsupplier.c.custid,
                )
            )
            cust_invoices = self.con.execute(cust_inv_query).fetchall()

            for inv in cust_invoices:
                id = inv["invid"]
                index = inv_map[id]
                invoices[index]["gstin"] = inv["gstin"]
                invoices[index]["custname"] = inv["custname"]

            # debit/credit notes
            query1 = (
                select(
                    [
                        drcr,
                        invoice.c.invoiceno,
                        invoice.c.invoicedate,
                        invoice.c.invoicetotal,
                        invoice.c.taxstate,
                        invoice.c.sourcestate,
                        invoice.c.tax,
                        invoice.c.cess,
                        invoice.c.taxflag,
                        invoice.c.contents,
                        customerandsupplier.c.gstin,
                        customerandsupplier.c.custname,
                    ]
                )
                .select_from(drcr.join(invoice).join(customerandsupplier))
                .where(
                    and_(
                        drcr.c.drcrdate.between(
                            start_period.strftime("%Y-%m-%d"),
                            end_period.strftime("%Y-%m-%d"),
                        ),
                        invoice.c.inoutflag == 15,
                        drcr.c.orgcode == orgcode,
                    )
                )
            )

            drcrs_all = self.con.execute(query1).fetchall()

            gkdata = {}
            gkdata["b2b"] = b2b_r1(invoices, self.con).get("data", [])
            gkdata["b2cl"] = b2cl_r1(invoices, self.con).get("data", [])
            gkdata["b2cs"] = b2cs_r1(invoices, self.con, False).get("data", [])
            neg_b2cs = b2cs_r1(drcrs_all, self.con, True).get("data", [])
            gkdata["b2cs"] += neg_b2cs
            gkdata["cdnr"] = cdnr_r1(drcrs_all, self.con).get("data", [])
            gkdata["cdnur"] = cdnur_r1(drcrs_all, self.con).get("data", [])
            gkdata["hsn1"] = hsn_r1(
                orgcode, dataset["start"], dataset["end"], self.con
            ).get("data", [])

            self.con.close()
            return {"gkstatus": enumdict["Success"], "gkdata": gkdata}

        except:
            print(traceback.format_exc())
            return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(request_method="GET", request_param="type=r3b", renderer="json")
    def r3b(self):
        token = self.request.headers.get("gktoken", None)
        print("GST return")
        if token == None:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        try:
            self.con = eng.connect()

            gst_result = generate_gstr_3b_data(
                self.con,
                authDetails["orgcode"],
                self.request.params["calculatefrom"],
                self.request.params["calculateto"],
            )

            gst_data = gst_result["data"]
            gst_invoices = gst_result["invoices"]

            date_split = self.request.params["calculateto"].split("-")
            ret_period = date_split[1] + date_split[0]

            gst_json = {
                "gstin": self.request.params["gstin"],
                "ret_period": ret_period,
            }

            # 3.1 Details of Outward Supplies and inward supplies liable to reverse charge
            gst_json["sup_details"] = {
                "osup_zero": {
                    "txval": round(
                        gst_data["outward_taxable_zero_rated"]["taxable_value"], 2
                    ),
                    "iamt": round(gst_data["outward_taxable_zero_rated"]["igst"], 2),
                    "camt": round(gst_data["outward_taxable_zero_rated"]["cgst"], 2),
                    "samt": round(gst_data["outward_taxable_zero_rated"]["sgst"], 2),
                    "csamt": round(gst_data["outward_taxable_zero_rated"]["cess"], 2),
                },
                "osup_nil_exmp": {
                    "txval": round(
                        gst_data["outward_taxable_exempted"]["taxable_value"], 2
                    ),
                    "iamt": round(gst_data["outward_taxable_exempted"]["igst"], 2),
                    "camt": round(gst_data["outward_taxable_exempted"]["cgst"], 2),
                    "samt": round(gst_data["outward_taxable_exempted"]["sgst"], 2),
                    "csamt": round(gst_data["outward_taxable_exempted"]["cess"], 2),
                },
                "osup_det": {
                    "txval": round(
                        gst_data["outward_taxable_supplies"]["taxable_value"], 2
                    ),
                    "iamt": round(gst_data["outward_taxable_supplies"]["igst"], 2),
                    "camt": round(gst_data["outward_taxable_supplies"]["cgst"], 2),
                    "samt": round(gst_data["outward_taxable_supplies"]["sgst"], 2),
                    "csamt": round(gst_data["outward_taxable_supplies"]["cess"], 2),
                },
                "isup_rev": {
                    "txval": round(
                        gst_data["inward_reverse_charge"]["taxable_value"], 2
                    ),
                    "iamt": round(gst_data["inward_reverse_charge"]["igst"], 2),
                    "camt": round(gst_data["inward_reverse_charge"]["cgst"], 2),
                    "samt": round(gst_data["inward_reverse_charge"]["sgst"], 2),
                    "csamt": round(gst_data["inward_reverse_charge"]["cess"], 2),
                },
                "osup_nongst": {
                    "txval": round(gst_data["outward_non_gst"]["taxable_value"], 2),
                    "iamt": round(gst_data["outward_non_gst"]["igst"], 2),
                    "camt": round(gst_data["outward_non_gst"]["cgst"], 2),
                    "samt": round(gst_data["outward_non_gst"]["sgst"], 2),
                    "csamt": round(gst_data["outward_non_gst"]["cess"], 2),
                },
            }

            # 3.2  Of the supplies shown in 3.1 (a), details of inter-state supplies made to unregistered persons, composition taxable person and UIN
            gst_json["inter_sup"] = {
                "unreg_details": [],
                "comp_details": [],
                "uin_details": [],
            }

            for state_code in gst_data["pos_unreg_comp_uin_igst"]:
                item = gst_data["pos_unreg_comp_uin_igst"][state_code]
                gst_json["inter_sup"]["unreg_details"].append(
                    {
                        "pos": state_code,
                        "txval": round(item["unreg_taxable_amt"], 2),
                        "iamt": round(item["unreg_igst"], 2),
                    }
                )
                gst_json["inter_sup"]["comp_details"].append(
                    {
                        "pos": state_code,
                        "txval": round(item["comp_taxable_amt"], 2),
                        "iamt": round(item["comp_igst"], 2),
                    }
                )
                gst_json["inter_sup"]["uin_details"].append(
                    {
                        "pos": state_code,
                        "txval": round(item["uin_taxable_amt"], 2),
                        "iamt": round(item["uin_igst"], 2),
                    }
                )

            # 4. Eligible ITC
            gst_json["itc_elg"] = {
                "itc_avl": [
                    {
                        "ty": "IMPG",
                        "samt": round(gst_data["import_goods"]["sgst"], 2),
                        "csamt": round(gst_data["import_goods"]["cess"], 2),
                        "camt": round(gst_data["import_goods"]["cgst"], 2),
                        "iamt": round(gst_data["import_goods"]["igst"], 2),
                    },
                    {
                        "ty": "IMPS",
                        "samt": round(gst_data["import_service"]["sgst"], 2),
                        "csamt": round(gst_data["import_service"]["cess"], 2),
                        "camt": round(gst_data["import_service"]["cgst"], 2),
                        "iamt": round(gst_data["import_service"]["igst"], 2),
                    },
                    {
                        "ty": "ISRC",
                        "samt": round(gst_data["inward_reverse_charge"]["sgst"], 2),
                        "csamt": round(gst_data["inward_reverse_charge"]["cess"], 2),
                        "camt": round(gst_data["inward_reverse_charge"]["cgst"], 2),
                        "iamt": round(gst_data["inward_reverse_charge"]["igst"], 2),
                    },
                    {
                        "ty": "ISD",
                        "samt": round(gst_data["inward_isd"]["sgst"], 2),
                        "csamt": round(gst_data["inward_isd"]["cess"], 2),
                        "camt": round(gst_data["inward_isd"]["cgst"], 2),
                        "iamt": round(gst_data["inward_isd"]["igst"], 2),
                    },
                    {
                        "ty": "OTH",
                        "samt": round(gst_data["all_itc"]["sgst"], 2),
                        "csamt": round(gst_data["all_itc"]["cess"], 2),
                        "camt": round(gst_data["all_itc"]["cgst"], 2),
                        "iamt": round(gst_data["all_itc"]["igst"], 2),
                    },
                ],
                "itc_net": {
                    "samt": round(gst_data["net_itc"]["sgst"], 2),
                    "csamt": round(gst_data["net_itc"]["cess"], 2),
                    "camt": round(gst_data["net_itc"]["cgst"], 2),
                    "iamt": round(gst_data["net_itc"]["igst"], 2),
                },
                "itc_rev": [
                    {
                        "ty": "RUL",
                        "samt": round(gst_data["itc_reversed_1"]["sgst"], 2),
                        "csamt": round(gst_data["itc_reversed_1"]["cess"], 2),
                        "camt": round(gst_data["itc_reversed_1"]["cgst"], 2),
                        "iamt": round(gst_data["itc_reversed_1"]["igst"], 2),
                    },
                    {
                        "ty": "OTH",
                        "samt": round(gst_data["itc_reversed_2"]["sgst"], 2),
                        "csamt": round(gst_data["itc_reversed_2"]["cess"], 2),
                        "camt": round(gst_data["itc_reversed_2"]["cgst"], 2),
                        "iamt": round(gst_data["itc_reversed_2"]["igst"], 2),
                    },
                ],
                "itc_inelg": [
                    {
                        "ty": "RUL",
                        "samt": round(gst_data["ineligible_1"]["sgst"], 2),
                        "csamt": round(gst_data["ineligible_1"]["cess"], 2),
                        "camt": round(gst_data["ineligible_1"]["cgst"], 2),
                        "iamt": round(gst_data["ineligible_1"]["igst"], 2),
                    },
                    {
                        "ty": "OTH",
                        "samt": round(gst_data["ineligible_2"]["sgst"], 2),
                        "csamt": round(gst_data["ineligible_2"]["cess"], 2),
                        "camt": round(gst_data["ineligible_2"]["cgst"], 2),
                        "iamt": round(gst_data["ineligible_2"]["igst"], 2),
                    },
                ],
            }

            # 5. Values of exempt, Nil-rated and non-GST inward supplies
            gst_json["inward_sup"] = {
                "isup_details": [
                    {
                        "ty": "GST",
                        "inter": round(gst_data["inward_zero_gst"]["inter"], 2),
                        "intra": round(gst_data["inward_zero_gst"]["intra"], 2),
                    },
                    {
                        "ty": "NONGST",
                        "inter": round(gst_data["non_gst"]["inter"], 2),
                        "intra": round(gst_data["non_gst"]["intra"], 2),
                    },
                ]
            }

            # 5.1 Interest & late fee payable
            gst_json["intr_ltfee"] = {
                "intr_details": {
                    "samt": round(gst_data["interest"]["sgst"], 2),
                    "csamt": round(gst_data["interest"]["cess"], 2),
                    "camt": round(gst_data["interest"]["cgst"], 2),
                    "iamt": round(gst_data["interest"]["igst"], 2),
                },
                "ltfee_details": {},
            }

            return {
                "gkstatus": enumdict["Success"],
                "gkresult": {"json": gst_json, "invoice": gst_invoices},
            }
        except:
            # print(traceback.format_exc())
            return {"gkstatus": enumdict["ConnectionFailed"]}

    @view_config(
        request_method="GET", request_param="type=gstin_captcha", renderer="json"
    )
    def getGstinCaptcha(self):
        req1 = requests.get("https://www.gst.gov.in/")
        if req1.status_code == 200:
            cookie1 = {}
            for cookie in req1.cookies:
                cookie1[cookie.name] = cookie.value
            URL = "https://services.gst.gov.in/services/captcha"
            # print(req1.cookies)
            headers = {
                "User-Agent": "GNUKhata_devel_0",  # The GST API maintainers have blocked the default python user agent. In the future they may add more restrictions, so must move to a better API
            }
            req = requests.get(url=URL, cookies=cookie1, headers=headers)
            if req.status_code == 200:
                # print(req.content)
                cookieString = "Lang=en;"
                for cookie in req.cookies:
                    cookieString += cookie.name + "=" + cookie.value + ";"
                img = b64encode(req.content).decode("utf-8")
                payload = {
                    "gkstatus": enumdict["Success"],
                    "gkresult": {
                        "captcha": img,
                        "cookie": cookieString,
                    },
                }
            else:
                print(req.status_code)
                payload = {"gkstatus": enumdict["ConnectionFailed"]}
        else:
            print(req.status_code)
            payload = {"gkstatus": enumdict["ConnectionFailed"]}
        return payload

    @view_config(
        request_method="POST", request_param="type=gstin_captcha", renderer="json"
    )
    def validateGstinCaptcha(self):
        dataset = self.request.json_body
        URL = "https://services.gst.gov.in/services/api/search/taxpayerDetails"
        headers = {
            "Referer": "https://services.gst.gov.in/services/searchtp",
            "Cookie": dataset["cookie"],
            "Content-Type": "application/json",
            "User-Agent": "GNUKhata_devel_0",  # The GST API maintainers have blocked the default python user agent. In the future they may add more restrictions, so must move to a better API
        }
        req = requests.post(url=URL, data=dumps(dataset["payload"]), headers=headers)
        if req.status_code == 200:
            resp = loads(req.text)
            if "errorCode" in resp:
                payload = {"gkstatus": enumdict["ConnectionFailed"], "gkerror": resp}
            else:
                payload = {"gkstatus": enumdict["Success"], "gkresult": resp}
        else:
            payload = {"gkstatus": enumdict["ConnectionFailed"]}
        return payload
