#!/usr/bin/python3
"""
This file is part of GNUKhata:A modular,robust and Free Accounting System.

License: AGPLv3

Contributors:
"Sai Karthik" <kskarthik@disroot.org>
"Krishnakant Mane" <kkmane@riseup.net>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
'Prajkta Patkar'<prajakta@dff.org.in>
'Reshma Bhatwadekar'<reshma_b@riseup.net>
"Sanket Kolnoorkar"<Sanketf123@gmail.com>
'Aditya Shukla' <adityashukla9158.as@gmail.com>
'Pravin Dake' <pravindake24@gmail.com>

"""

# from pyramid.view import view_defaults, view_config
from requests import request
from gkcore import eng
from pyramid.request import Request
from gkcore.models import gkdb
from sqlalchemy.sql import select
from sqlalchemy import func, desc
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
import jwt
import gkcore
import json
from Crypto.PublicKey import RSA
from gkcore.models.meta import (
    inventoryMigration,
    addFields,
    columnExists,
    columnTypeMatches,
    tableExists,
    getOnDelete,
    uniqueConstraintExists,
)
from datetime import datetime, timedelta
import traceback
from gkcore.views.api_gkuser import getUserRole

con = Connection


class Migrate:
    def __init__(self, request):
        self.request = Request
        self.request = request
        self.con = Connection

    def db(self):
        """
        This function will be called only once while upgrading gnukhata.
        The function will be mostly concerned with adding new fields to the databse or altering those which are present.
        The columnExists() function will be used to check if a certain column exists.
        If the function returns False then the field is created.
        For example:
        We check if the field stockdate is present.
        If it is not present it means that this is an upgrade.
        """
        self.con = eng.connect()
        try:
            organisations = self.con.execute(select([gkdb.organisation.c.orgcode]))
            allorg = organisations.fetchall()
            if not tableExists("cslastprice"):
                self.con.execute(
                    "create table cslastprice(cslpid serial, lastprice numeric(13,2), inoutflag integer, custid integer NOT NULL,productcode integer NOT NULL,orgcode integer NOT NULL, primary key (cslpid), constraint cslastprice_orgcode_fkey FOREIGN KEY (orgcode) REFERENCES organisation(orgcode), constraint cslastprice_custid_fkey FOREIGN KEY (custid) REFERENCES customerandsupplier(custid),constraint cslastprice_productcode_fkey FOREIGN KEY (productcode) REFERENCES product(productcode), unique(orgcode, custid, productcode, inoutflag))"
                )
                inoutflags = [9, 15]
                for orgid in allorg:
                    numberOfInvoices = self.con.execute(
                        select([func.count(gkdb.invoice.c.invid).label("invoices")])
                    )
                    invoices = numberOfInvoices.fetchone()
                    if int(invoices["invoices"]) > 0:
                        customers = self.con.execute(
                            select([gkdb.customerandsupplier.c.custid]).where(
                                gkdb.customerandsupplier.c.orgcode
                                == int(orgid["orgcode"])
                            )
                        )
                        customerdata = customers.fetchall()
                        products = self.con.execute(
                            select([gkdb.product.c.productcode]).where(
                                gkdb.product.c.orgcode == int(orgid["orgcode"])
                            )
                        )
                        productdata = products.fetchall()
                        for customer in customerdata:
                            for product in productdata:
                                for inoutflag in inoutflags:
                                    try:
                                        lastInvoice = self.con.execute(
                                            "select max(invid) as invid from invoice where orgcode = %d and contents ? '%s' and inoutflag = %d and custid = %d"
                                            % (
                                                int(orgid["orgcode"]),
                                                str(product["productcode"]),
                                                int(inoutflag),
                                                int(customer["custid"]),
                                            )
                                        )
                                        lastInvoiceId = lastInvoice.fetchone()["invid"]
                                        if lastInvoiceId != None:
                                            lastPriceData = self.con.execute(
                                                select([gkdb.invoice.c.contents]).where(
                                                    and_(
                                                        gkdb.invoice.c.invid
                                                        == int(lastInvoiceId),
                                                        gkdb.product.c.orgcode
                                                        == int(orgid["orgcode"]),
                                                    )
                                                )
                                            )
                                            lastPriceDict = lastPriceData.fetchone()[
                                                "contents"
                                            ]
                                            productCode = product["productcode"]
                                            if (
                                                str(productCode).decode("utf-8")
                                                in lastPriceDict
                                            ):
                                                lastPriceValue = list(
                                                    lastPriceDict[
                                                        str(productCode).decode("utf-8")
                                                    ].keys()
                                                )[0]
                                                priceDetails = {
                                                    "custid": int(customer["custid"]),
                                                    "productcode": int(
                                                        product["productcode"]
                                                    ),
                                                    "orgcode": int(orgid["orgcode"]),
                                                    "inoutflag": int(inoutflag),
                                                    "lastprice": float(lastPriceValue),
                                                }
                                                lastPriceEntry = self.con.execute(
                                                    gkdb.cslastprice.insert(),
                                                    [priceDetails],
                                                )
                                    except:
                                        pass
            if not columnExists("unitofmeasurement", "description"):
                self.con.execute("alter table unitofmeasurement add description text")
                self.con.execute(
                    "alter table unitofmeasurement add sysunit integer default 0"
                )

                """ Following dictionary of uom, first try to insert single uqc if it fail means uqc is exists in table then updated its description and sysunit"""
                dictofuqc = {
                    "BAG": "BAGS",
                    "BAL": "BALE",
                    "BDL": "BUNDLES",
                    "BKL": "BUCKLES",
                    "BOU": "BILLIONS OF UNITS",
                    "BOX": "BOX",
                    "BTL": "BOTTLES",
                    "BUN": "BUNCHES",
                    "CAN": "CANS",
                    "CBM": "CUBIC METER",
                    "CCM": "CUBIC CENTIMETER",
                    "CMS": "CENTIMETER",
                    "CRT": "Carat",
                    "CTN": "CARTONS",
                    "DOZ": "DOZEN",
                    "DRM": "DRUM",
                    "GGK": "GREAT GROSS",
                    "GMS": "GRAMS",
                    "GRS": "GROSS",
                    "GYD": "GROSS YARDS",
                    "KGS": "KILOGRAMS",
                    "KLR": "KILOLITER",
                    "KME": "KILOMETERS",
                    "MLT": "MILLILITER",
                    "MTR": "METER",
                    "MTS": "METRIC TON",
                    "NOS": "NUMBER",
                    "OTH": "OTHERS",
                    "PAC": "PACKS",
                    "PCS": "PIECES",
                    "PRS": "PAIRS",
                    "QTL": "QUINTAL",
                    "ROL": "ROLLS",
                    "SET": "SETS",
                    "SQF": "SQUARE FEET",
                    "SQM": "SQUARE METER",
                    "SQY": "SQUARE YARDS",
                    "TBS": "TABLETS",
                    "TGM": "TEN GRAMS",
                    "THD": "THOUSANDS",
                    "TON": "GREAT BRITAIN TON",
                    "TUB": "TUBES",
                    "UGS": "US GALLONS",
                    "UNT": "UNITS",
                    "YDS": "YARDS",
                }
                for unit, desc in list(dictofuqc.items()):
                    try:
                        self.con.execute(
                            gkdb.unitofmeasurement.insert(),
                            [
                                {
                                    "unitname": unit,
                                    "description": desc,
                                    "conversionrate": 0.00,
                                    "sysunit": 1,
                                }
                            ],
                        )
                    except:
                        self.con.execute(
                            "update unitofmeasurement set sysunit=1, description='%s' where unitname='%s'"
                            % (desc, unit)
                        )
                    dictofuqc.pop(unit, 0)

            if not columnExists("unitofmeasurement", "uqc"):
                self.con.execute("alter table unitofmeasurement add uqc integer")

            # discount flag is use to check whether discount is in percent or in amount.
            # 1 = discount in amount, 16 = discount in percent.
            if not columnExists("delchal", "discflag"):
                self.con.execute(
                    "alter table invoicebin add column discflag integer default 1"
                )
                self.con.execute(
                    "alter table invoice add column discflag integer default 1"
                )
                self.con.execute(
                    "alter table delchal add column discflag integer default 1"
                )
                # in product following two collumns are added for discount in percent and in amount.
                self.con.execute(
                    "alter table product add column percentdiscount numeric(5,2) default 0.00"
                )
                self.con.execute(
                    "alter table product add column amountdiscount numeric(13,2) default 0.00"
                )

            # Round off is use to detect that total amount of invoice is rounded off or not.
            # If the field is not exist then it will create field.
            if not columnExists("purchaseorder", "roundoffflag"):
                self.con.execute(
                    "alter table purchaseorder add column roundoffflag integer default 0"
                )
                self.con.execute(
                    "alter table delchal add column roundoffflag integer default 0"
                )
                self.con.execute(
                    "alter table drcr add column roundoffflag integer default 0"
                )
            # remove goid if present
            if columnExists("purchaseorder", "goid"):
                self.con.execute("alter table purchaseorder drop column goid")
                self.con.execute("alter table rejectionnote drop column goid")
                self.con.execute("alter table drcr drop column goid")
                self.con.execute("alter table budget drop column goid")
                self.con.execute("alter table vouchers drop column goid")
                self.con.execute("alter table invoice drop column goid")
                self.con.execute("alter table delchal drop column goid")

            # Round off is use to detect that total amount of invoice is rounded off or not.
            # If the field is not exist then it will create field.
            # Round Off Paid and Round Off Received account will genrate which is use while creating voucher for that invoice.
            if not columnExists("invoice", "roundoffflag"):
                self.con.execute(
                    "alter table invoice add column roundoffflag integer default 0"
                )
                for orgcode in allorg:
                    result = self.con.execute(
                        select([gkdb.accounts.c.accountcode]).where(
                            and_(
                                gkdb.accounts.c.orgcode == orgcode["orgcode"],
                                gkdb.accounts.c.accountname == "Round Off Paid",
                            )
                        )
                    )
                    account = result.fetchone()
                    if account == None:
                        grpCodePaid = self.con.execute(
                            select([gkdb.groupsubgroups.c.groupcode]).where(
                                and_(
                                    gkdb.groupsubgroups.c.groupname
                                    == "Indirect Expense",
                                    gkdb.groupsubgroups.c.orgcode == orgcode["orgcode"],
                                )
                            )
                        )
                        grpCodeP = grpCodePaid.fetchone()
                        ropAdd = self.con.execute(
                            gkdb.accounts.insert(),
                            [
                                {
                                    "accountname": "Round Off Paid",
                                    "groupcode": grpCodeP["groupcode"],
                                    "orgcode": orgcode["orgcode"],
                                    "defaultflag": 180,
                                }
                            ],
                        )
                        grpCodeReceived = self.con.execute(
                            select([gkdb.groupsubgroups.c.groupcode]).where(
                                and_(
                                    gkdb.groupsubgroups.c.groupname
                                    == "Indirect Income",
                                    gkdb.groupsubgroups.c.orgcode == orgcode["orgcode"],
                                )
                            )
                        )
                        grpCodeR = grpCodeReceived.fetchone()
                        rorAdd = self.con.execute(
                            gkdb.accounts.insert(),
                            [
                                {
                                    "accountname": "Round Off Received",
                                    "groupcode": grpCodeR["groupcode"],
                                    "orgcode": orgcode["orgcode"],
                                    "defaultflag": 181,
                                }
                            ],
                        )

            # In Below query we are adding field pincode to invoice table
            if not columnExists("invoice", "pincode"):
                self.con.execute("alter table invoice add pincode text")
            # In Below query we are adding field pincode to invoicebin table
            if not columnExists("invoicebin", "pincode"):
                self.con.execute("alter table invoicebin add pincode text")
            # In Below query we are adding field pincode to customersupplier table
            if not columnExists("customerandsupplier", "pincode"):
                self.con.execute("alter table customerandsupplier add pincode text")
            if not columnExists("customerandsupplier", "gst_reg_type"):
                self.con.execute(
                    "alter table customerandsupplier add gst_reg_type integer"
                )
            if not columnExists("customerandsupplier", "gst_party_type"):
                self.con.execute(
                    "alter table customerandsupplier add gst_party_type integer"
                )
            # Below query is to remove gbflag if it exists.
            if columnExists("godown", "gbflag"):
                self.con.execute("alter table godown drop column gbflag")
            # In Below query we are adding field pincode to purchaseorder table
            if not columnExists("purchaseorder", "pincode"):
                self.con.execute("alter table purchaseorder add pincode text")

            # In Below query we are adding field invnarration to invoicebin table
            if not columnExists("invoicebin", "invnarration"):
                self.con.execute("alter table invoicebin add invnarration text")

            # In Below query we are adding field dcinfo to invoicebin table
            if not columnExists("invoicebin", "dcinfo"):
                self.con.execute("alter table invoicebin add dcinfo jsonb")

            # In Below query we are adding field dcnarration to delchal table
            if not columnExists("delchal", "dcnarration"):
                self.con.execute("alter table delchal add dcnarration text")

            # In Below query we are adding field dcnarration to delchalbin table
            if not columnExists("delchalbin", "dcnarration"):
                self.con.execute("alter table delchalbin add dcnarration text")

            if not columnExists("organisation", "avnoflag"):
                self.con.execute(
                    "alter table organisation add avnoflag integer default 0"
                )
            if not columnExists("organisation", "ainvnoflag"):
                self.con.execute(
                    "alter table organisation add ainvnoflag integer default 0"
                )
            if not columnExists("organisation", "modeflag"):
                self.con.execute(
                    "alter table organisation add modeflag integer default 1"
                )
            if not columnExists("organisation", "avflag"):
                self.con.execute(
                    "alter table organisation add avflag integer default 1"
                )
            if not columnExists("organisation", "maflag"):
                self.con.execute(
                    "alter table organisation add maflag integer default 0"
                )
            if not columnExists("accounts", "sysaccount"):
                self.con.execute(
                    "alter table accounts add sysaccount integer default 0"
                )
                self.con.execute(
                    "update accounts set sysaccount=1 where accountname in ('Closing Stock', 'Opening Stock', 'Profit & Loss', 'Stock at the Beginning')"
                )
            if not columnExists("accounts", "defaultflag"):
                self.con.execute(
                    "alter table accounts add defaultflag integer default 0"
                )
                for orgcode in allorg:
                    try:
                        groupdata = self.con.execute(
                            select([gkdb.groupsubgroups.c.groupcode]).where(
                                and_(
                                    gkdb.groupsubgroups.c.orgcode == orgcode["orgcode"],
                                    gkdb.groupsubgroups.c.groupname
                                    == "Current Liabilities",
                                )
                            )
                        )
                        groupCode = groupdata.fetchone()
                        subGroup = {
                            "groupname": "Duties & Taxes",
                            "subgroupof": groupCode["groupcode"],
                            "orgcode": orgcode["orgcode"],
                        }
                        self.con.execute(gkdb.groupsubgroups.insert(), subGroup)

                        chartofacc = [
                            "Cash in hand",
                            "Krishi Kalyan Cess",
                            "Swachh Bharat Cess",
                            "Electricity Expense",
                            "Professional Fees",
                            "Bank A/C",
                            "Sale A/C",
                            "Purchase A/C",
                            "Discount Paid",
                            "Bonus",
                            "Depreciation Expense",
                            "Discount Received",
                            "Salary",
                            "Bank Charges",
                            "Rent",
                            "Travel Expense",
                            "Accumulated Depreciation",
                            "Miscellaneous Expense",
                            "VAT_OUT",
                            "VAT_IN",
                        ]
                        for acc in chartofacc:
                            accname = self.con.execute(
                                select([gkdb.accounts.c.accountcode]).where(
                                    and_(
                                        gkdb.accounts.c.orgcode == orgcode["orgcode"],
                                        gkdb.accounts.c.accountname == acc,
                                    )
                                )
                            )
                            acname = accname.fetchone()
                            if acname == None:
                                if acc == "Cash in hand":
                                    cash = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Cash",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    cashgrp = cash.fetchone()
                                    cashadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        {
                                            "accountname": "Cash in hand",
                                            "groupcode": cashgrp["groupcode"],
                                            "orgcode": orgcode["orgcode"],
                                            "defaultflag": 3,
                                        },
                                    )
                                elif acc == "Krishi Kalyan Cess":
                                    cess = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Duties & Taxes",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    cesscode = cess.fetchone()
                                    cessadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Krishi Kalyan Cess",
                                                "groupcode": cesscode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "VAT_OUT":
                                    vout = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Duties & Taxes",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    voutcode = vout.fetchone()
                                    voutadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "VAT_OUT",
                                                "groupcode": voutcode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                                "sysaccount": 1,
                                            }
                                        ],
                                    )
                                elif acc == "VAT_IN":
                                    vin = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Duties & Taxes",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    vincode = vin.fetchone()
                                    vinadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "VAT_IN",
                                                "groupcode": vincode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                                "sysaccount": 1,
                                            }
                                        ],
                                    )
                                elif acc == "Swachh Bharat Cess":
                                    bcess = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Duties & Taxes",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    cesscode = bcess.fetchone()
                                    bcessadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Swachh Bharat Cess",
                                                "groupcode": cesscode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Salary":
                                    sal = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Direct Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    salcode = sal.fetchone()
                                    saladd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Salary",
                                                "groupcode": salcode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Miscellaneous Expense":
                                    miscex = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Direct Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    miscexcode = miscex.fetchone()
                                    miscexadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Miscellaneous Expense",
                                                "groupcode": miscexcode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Bank Charges":
                                    bnkch = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Direct Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    bnkchcode = bnkch.fetchone()
                                    bnkchadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Bank Charges",
                                                "groupcode": bnkchcode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Rent":
                                    rent = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Direct Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    rentcode = rent.fetchone()
                                    rentadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Rent",
                                                "groupcode": rentcode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Travel Expense":
                                    travel = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Direct Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    travelcode = travel.fetchone()
                                    traveladd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Travel Expense",
                                                "groupcode": travelcode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Electricity Expense":
                                    elect = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Direct Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    electcode = elect.fetchone()
                                    electadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Electricity Expense",
                                                "groupcode": electcode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Professional Fees":
                                    fees = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Direct Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    feescode = fees.fetchone()
                                    feesadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Professional Fees",
                                                "groupcode": feescode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Bank A/C":
                                    bank = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Bank",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    bankgrp = bank.fetchone()
                                    bankadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        {
                                            "accountname": "Bank A/C",
                                            "groupcode": bankgrp["groupcode"],
                                            "orgcode": orgcode["orgcode"],
                                            "defaultflag": 2,
                                        },
                                    )
                                elif acc == "Discount Paid":
                                    disc = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Indirect Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    disccode = disc.fetchone()
                                    discadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Discount Paid",
                                                "groupcode": disccode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Bonus":
                                    bonus = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Indirect Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    bonuscode = bonus.fetchone()
                                    bonusadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Bonus",
                                                "groupcode": bonuscode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Depreciation Expense":
                                    depex = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Indirect Expense",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    depexcode = depex.fetchone()
                                    depexadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        [
                                            {
                                                "accountname": "Depreciation Expense",
                                                "groupcode": depexcode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            }
                                        ],
                                    )
                                elif acc == "Accumulated Depreciation":
                                    accdep = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Fixed Assets",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    accdepcode = accdep.fetchone()
                                    accdepadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        {
                                            "accountname": "Accumulated Depreciation",
                                            "groupcode": accdepcode["groupcode"],
                                            "orgcode": orgcode["orgcode"],
                                        },
                                    )
                                elif acc == "Discount Received":
                                    discpur = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Indirect Income",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    discpurcd = discpur.fetchone()
                                    discadd = self.con.execute(
                                        gkdb.accounts.insert(),
                                        {
                                            "accountname": "Discount Received",
                                            "groupcode": discpurcd["groupcode"],
                                            "orgcode": orgcode["orgcode"],
                                        },
                                    )
                                elif acc == "Sale A/C":
                                    sale = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Sales",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    salecode = sale.fetchone()
                                    if salecode == None:
                                        acsale = self.con.execute(
                                            select(
                                                [gkdb.groupsubgroups.c.groupcode]
                                            ).where(
                                                and_(
                                                    gkdb.groupsubgroups.c.groupname
                                                    == "Direct Income",
                                                    gkdb.groupsubgroups.c.orgcode
                                                    == orgcode["orgcode"],
                                                )
                                            )
                                        )
                                        saleCode = acsale.fetchone()
                                        saleData = self.con.execute(
                                            gkdb.groupsubgroups.insert(),
                                            {
                                                "groupname": "Sales",
                                                "subgroupof": saleCode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                            },
                                        )
                                        saleadd = self.con.execute(
                                            gkdb.accounts.insert(),
                                            {
                                                "accountname": "Sale A/C",
                                                "groupcode": salecode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                                "defaultflag": 19,
                                            },
                                        )
                                    else:
                                        saleadd = self.con.execute(
                                            gkdb.accounts.insert(),
                                            {
                                                "accountname": "Sale A/C",
                                                "groupcode": salecode["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                                "defaultflag": 19,
                                            },
                                        )
                                elif acc == "Purchase A/C":
                                    purch = self.con.execute(
                                        select([gkdb.groupsubgroups.c.groupcode]).where(
                                            and_(
                                                gkdb.groupsubgroups.c.groupname
                                                == "Purchase",
                                                gkdb.groupsubgroups.c.orgcode
                                                == orgcode["orgcode"],
                                            )
                                        )
                                    )
                                    purchcd = purch.fetchone()
                                    if purchcd == None:
                                        acpurc = self.con.execute(
                                            select(
                                                [gkdb.groupsubgroups.c.groupcode]
                                            ).where(
                                                and_(
                                                    gkdb.groupsubgroups.c.groupname
                                                    == "Direct Expense",
                                                    gkdb.groupsubgroups.c.orgcode
                                                    == orgcode["orgcode"],
                                                )
                                            )
                                        )
                                        purCode = acpurc.fetchone()
                                        insData = self.con.execute(
                                            gkdb.groupsubgroups.insert(),
                                            [
                                                {
                                                    "groupname": "Purchase",
                                                    "subgroupof": purCode["groupcode"],
                                                    "orgcode": orgcode["orgcode"],
                                                },
                                                {
                                                    "groupname": "Consumables",
                                                    "subgroupof": purCode["groupcode"],
                                                    "orgcode": orgcode["orgcode"],
                                                },
                                            ],
                                        )
                                        purchadd = self.con.execute(
                                            gkdb.accounts.insert(),
                                            {
                                                "accountname": "Purchase A/C",
                                                "groupcode": purchcd["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                                "defaultflag": 16,
                                            },
                                        )
                                    else:
                                        purchadd = self.con.execute(
                                            gkdb.accounts.insert(),
                                            {
                                                "accountname": "Purchase A/C",
                                                "groupcode": purchcd["groupcode"],
                                                "orgcode": orgcode["orgcode"],
                                                "defaultflag": 16,
                                            },
                                        )
                            elif acc == "Cash in hand":
                                self.con.execute(
                                    "update accounts set defaultflag = 3 where accountcode =%d"
                                    % int(acname["accountcode"])
                                )
                            elif acc == "Bank A/C":
                                self.con.execute(
                                    "update accounts set defaultflag = 2 where accountcode =%d"
                                    % int(acname["accountcode"])
                                )
                            elif acc == "Sale A/C":
                                self.con.execute(
                                    "update accounts set defaultflag = 19 where accountcode =%d"
                                    % int(acname["accountcode"])
                                )
                            elif acc == "Purchase A/C":
                                self.con.execute(
                                    "update accounts set defaultflag = 16 where accountcode =%d"
                                    % int(acname["accountcode"])
                                )
                            elif acc == "Round Off Paid":
                                self.con.execute(
                                    "update accounts set defaultflag = 180 where accountcode =%d"
                                    % int(acname["accountcode"])
                                )
                            elif acc == "Round Off Received":
                                self.con.execute(
                                    "update accounts set defaultflag = 181 where accountcode =%d"
                                    % int(acname["accountcode"])
                                )
                            elif acc == "VAT_IN":
                                self.con.execute(
                                    "update accounts set defaultflag = 0, sysaccount = 1 where accountcode =%d"
                                    % int(acname["accountcode"])
                                )
                            elif acc == "VAT_OUT":
                                self.con.execute(
                                    "update accounts set defaultflag = 0, sysaccount = 1 where accountcode =%d"
                                    % int(acname["accountcode"])
                                )
                            else:
                                self.con.execute(
                                    "update accounts set defaultflag = 0 where accountcode =%d"
                                    % int(acname["accountcode"])
                                )
                    except:
                        continue
            if not columnExists("organisation", "bankdetails"):
                self.con.execute("alter table organisation add bankdetails json")
            if not columnExists("purchaseorder", "purchaseordertotal"):
                self.con.execute("drop table purchaseorder cascade")
                self.con.execute(
                    "create table purchaseorder(orderid serial, orderno text not null, orderdate timestamp not null, creditperiod text, payterms text, modeoftransport text, issuername text, designation text, schedule jsonb, taxstate text, psflag integer not null, csid integer, togodown integer, taxflag integer default 22, tax jsonb, cess jsonb,purchaseordertotal numeric(13,2) not null, pototalwords text, sourcestate text, orgstategstin text, attachment json, attachmentcount integer default 0, consignee jsonb, freeqty jsonb, reversecharge text, bankdetails jsonb, vehicleno text, dateofsupply timestamp, discount jsonb, paymentmode integer default 22, address text, orgcode integer not null, primary key(orderid), foreign key (csid) references customerandsupplier(custid) ON DELETE CASCADE, foreign key (togodown) references godown(goid) ON DELETE CASCADE, foreign key (orgcode) references organisation(orgcode) ON DELETE CASCADE)"
                )
                self.con.execute(
                    "create index purchaseorder_orgcodeindex on purchaseorder using btree(orgcode)"
                )
                self.con.execute(
                    "create index purchaseorder_date on purchaseorder using btree(orderdate)"
                )
                self.con.execute(
                    "create index purchaseorder_togodown on purchaseorder using btree(togodown)"
                )
            if not columnExists("invoice", "invoicetotalword"):
                self.con.execute("alter table invoice add invoicetotalword text")
            if not columnExists("delchal", "taxflag"):
                self.con.execute(
                    "alter table delchal add taxflag integer, add contents jsonb, add tax jsonb, add cess jsonb, add taxstate text, add sourcestate text, add orgstategstin text, add freeqty jsonb, add discount jsonb, add delchaltotal numeric(13,2), add dateofsupply timestamp, add vehicleno text"
                )

            if not columnExists("delchal", "inoutflag"):
                self.con.execute("alter table delchal add inoutflag integer")
                # This code will assign inoutflag for delivery chalan where inoutflag is blank.
                alldelchal = self.con.execute(
                    select([gkdb.delchal.c.dcid]).where(
                        gkdb.delchal.c.inoutflag == None
                    )
                )
                # here we will be fetching all the delchal data
                delchals = alldelchal.fetchall()
                for delchal in delchals:
                    delchalid = int(delchal["dcid"])
                    stockdata = self.con.execute(
                        select([gkdb.stock.c.inout]).where(
                            and_(
                                gkdb.stock.c.dcinvtnid == delchalid,
                                gkdb.stock.c.dcinvtnflag == 4,
                            )
                        )
                    )
                    inout = stockdata.fetchone()
                    inoutflag = inout["inout"]
                    self.con.execute(
                        "update delchal set inoutflag = %d where dcid=%d"
                        % (int(inoutflag), int(delchalid))
                    )
            if not columnExists("invoice", "inoutflag"):
                self.con.execute("alter table invoice add inoutflag integer")
                # This code will assign inoutflag for invoice or cashmemo where inoutflag is blank.
                allinvoice = self.con.execute(
                    select(
                        [
                            gkdb.invoice.c.invid,
                            gkdb.invoice.c.custid,
                            gkdb.invoice.c.icflag,
                        ]
                    ).where(gkdb.invoice.c.inoutflag == None)
                )
                # Here we fetching all "custid", "icflag" and "invid".
                dict = allinvoice.fetchall()
                for singleinv in dict:
                    sincustid = singleinv["custid"]
                    invid = singleinv["invid"]
                    icflag = singleinv["icflag"]
                    # First we checking the icflag (i.e 3 for "cashmemo", 9 for "invoice")
                    if icflag == 3:
                        self.con.execute(
                            "update invoice set inoutflag = 15 where invid=%d"
                            % int(invid)
                        )
                    else:
                        cussupdata = self.con.execute(
                            select([gkdb.customerandsupplier.c.csflag]).where(
                                gkdb.customerandsupplier.c.custid == sincustid
                            )
                        )
                        # Here we fetching all "csflag" on the basis of "sincustid" (i.e "custid")
                        csflagsingle = cussupdata.fetchone()
                        for cussup in csflagsingle:
                            # if "csflag" is 19 (i.e "supplier") then set inoutflag=9 (i.e "in") else "csflag" is 3 (i.e "customer" and set "inoutflag=15" (i.e "out"))
                            if cussup == 19:
                                self.con.execute(
                                    "update invoice set inoutflag = 9 where invid=%d"
                                    % int(invid)
                                )
                            else:
                                self.con.execute(
                                    "update invoice set inoutflag = 15 where invid=%d"
                                    % int(invid)
                                )
            if not columnExists("invoice", "address"):
                self.con.execute("alter table invoice add address text")
            if not columnExists("customerandsupplier", "bankdetails"):
                self.con.execute(
                    "alter table customerandsupplier add bankdetails jsonb"
                )
            if not columnExists("invoice", "paymentmode"):
                self.con.execute("alter table invoice add paymentmode integer")
                # Code for assinging paymentmode where paymentmode is blank and bank details are present.
                bankresult = self.con.execute(
                    select([gkdb.invoice.c.invid, gkdb.invoice.c.bankdetails]).where(
                        gkdb.invoice.c.paymentmode == None
                    )
                )
                # Fetching invid,bankdetails using fetchall() method in list.for loop is used to fetch each record in bankresult.
                dict = bankresult.fetchall()
                for invdata in dict:
                    # Storing account number,ifsc number,invoice id in invaccno,invifsc,invoid respectively
                    invaccno = invdata["bankdetails"]["accountno"]
                    invifsc = invdata["bankdetails"]["ifsc"]
                    invoid = invdata["invid"]
                    # Checking for bankdetails,if accountno and ifsc are present then set paymentmode=2 else set paymentmode=3.
                    if invaccno == "" or invifsc == "":
                        self.con.execute(
                            "update invoice set paymentmode=3 where invid = %d"
                            % int(invoid)
                        )
                    else:
                        self.con.execute(
                            "update invoice set paymentmode=2 where invid = %d"
                            % int(invoid)
                        )
            if not columnExists("delchal", "consignee"):
                self.con.execute("alter table delchal add consignee jsonb")
            if not columnExists("invoice", "orgstategstin"):
                self.con.execute("alter table invoice add orgstategstin text")
            if not columnExists("invoice", "cess"):
                self.con.execute("alter table invoice add cess jsonb")
            if not tableExists("state"):
                self.con.execute(
                    "create table state( statecode integer,statename text,primary key (statecode))"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(1, 'Jammu and Kashmir')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(2, 'Himachal Pradesh')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(3, 'Punjab')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(4, 'Chandigarh')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(5, 'Uttranchal')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(6, 'Haryana')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(7, 'Delhi')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(8, 'Rajasthan')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(9, 'Uttar Pradesh')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(10, 'Bihar')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(11, 'Sikkim')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(12, 'Arunachal Pradesh')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(13, 'Nagaland')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(14, 'Manipur')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(15, 'Mizoram')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(16, 'Tripura')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(17, 'Meghalaya')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(18, 'Assam')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(19, 'West Bengal')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(20, 'Jharkhand')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(21, 'Odisha')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(22, 'Chhattisgarh')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(23, 'Madhya Pradesh')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(24, 'Gujarat')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(25, 'Daman and Diu (Old)')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(26, 'Daman and Diu & Dadra and Nagar Haveli (New)')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(27, 'Maharashtra')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(28, 'Andhra Pradesh')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(29, 'Karnataka')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(30, 'Goa')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(31, 'Lakshdweep')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(32, 'Kerala')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(33, 'Tamil Nadu')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(34, 'Pondicherry')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(35, 'Andaman and Nicobar Islands')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(36, 'Telangana')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(37, 'Andhra Pradesh (New)')"
                )
                self.con.execute(
                    "insert into state( statecode, statename)values(38, 'Ladakh')"
                )
            if not columnExists("state", "abbreviation"):
                self.con.execute("alter table state add abbreviation text")
                self.con.execute("update state set abbreviation='JK' where statecode=1")
                self.con.execute("update state set abbreviation='HP' where statecode=2")
                self.con.execute("update state set abbreviation='PB' where statecode=3")
                self.con.execute("update state set abbreviation='CH' where statecode=4")
                self.con.execute("update state set abbreviation='UK' where statecode=5")
                self.con.execute("update state set abbreviation='HR' where statecode=6")
                self.con.execute("update state set abbreviation='DL' where statecode=7")
                self.con.execute("update state set abbreviation='RJ' where statecode=8")
                self.con.execute("update state set abbreviation='UP' where statecode=9")

                self.con.execute(
                    "update state set abbreviation='BR' where statecode=10"
                )
                self.con.execute(
                    "update state set abbreviation='SK' where statecode=11"
                )
                self.con.execute(
                    "update state set abbreviation='AR' where statecode=12"
                )
                self.con.execute(
                    "update state set abbreviation='NL' where statecode=13"
                )
                self.con.execute(
                    "update state set abbreviation='MN' where statecode=14"
                )
                self.con.execute(
                    "update state set abbreviation='MZ' where statecode=15"
                )
                self.con.execute(
                    "update state set abbreviation='TR' where statecode=16"
                )
                self.con.execute(
                    "update state set abbreviation='ML' where statecode=17"
                )
                self.con.execute(
                    "update state set abbreviation='AS' where statecode=18"
                )
                self.con.execute(
                    "update state set abbreviation='WB' where statecode=19"
                )
                self.con.execute(
                    "update state set abbreviation='JH' where statecode=20"
                )
                self.con.execute(
                    "update state set abbreviation='OR' where statecode=21"
                )
                self.con.execute(
                    "update state set abbreviation='CG' where statecode=22"
                )
                self.con.execute(
                    "update state set abbreviation='MP' where statecode=23"
                )
                self.con.execute(
                    "update state set abbreviation='GJ' where statecode=24"
                )
                self.con.execute(
                    "update state set abbreviation='DD' where statecode=25"
                )
                self.con.execute(
                    "update state set abbreviation='DH' where statecode=26"
                )
                self.con.execute(
                    "update state set abbreviation='MH' where statecode=27"
                )
                self.con.execute(
                    "update state set abbreviation='AP' where statecode=28"
                )
                self.con.execute(
                    "update state set abbreviation='KA' where statecode=29"
                )
                self.con.execute(
                    "update state set abbreviation='GA' where statecode=30"
                )
                self.con.execute(
                    "update state set abbreviation='LD' where statecode=31"
                )
                self.con.execute(
                    "update state set abbreviation='KL' where statecode=32"
                )
                self.con.execute(
                    "update state set abbreviation='TN' where statecode=33"
                )
                self.con.execute(
                    "update state set abbreviation='PY' where statecode=34"
                )
                self.con.execute(
                    "update state set abbreviation='AN' where statecode=35"
                )
                self.con.execute(
                    "update state set abbreviation='TS' where statecode=36"
                )
                self.con.execute(
                    "update state set abbreviation='AP' where statecode=37"
                )
                self.con.execute(
                    "update state set abbreviation='LA' where statecode=38"
                )
            if columnExists("invoice", "reversecharge"):
                countResult = self.con.execute(
                    select([func.count(gkdb.invoice.c.reversecharge).label("revcount")])
                )
                countData = countResult.fetchone()
                if int(countData["revcount"]) > 0:
                    self.con.execute(
                        "update invoice set reversecharge = '0' where reversecharge=null"
                    )
            if columnExists("invoice", "cancelflag"):
                self.con.execute("alter table invoice drop column cancelflag")
            if columnExists("invoice", "canceldate"):
                self.con.execute("alter table invoice drop column canceldate")
            if columnExists("invoice", "taxstate"):
                self.con.execute(
                    "update invoice set taxstate = null where taxstate = '' or taxstate = 'none'"
                )
            if not columnExists("invoice", "consignee"):
                self.con.execute(
                    "alter table invoice add consignee jsonb, add sourcestate text ,add discount jsonb ,add taxflag integer default 22, add reversecharge text, add bankdetails jsonb,add transportationmode text,add vehicleno text,add dateofsupply timestamp"
                )
            if columnExists("invoice", "taxflag"):
                self.con.execute("update invoice set taxflag = 22 where taxflag=null")
            if columnExists("delchal", "issuerid"):
                self.con.execute("alter table delchal drop column issuerid")
            if not columnExists("organisation", "gstin"):
                self.con.execute("alter table organisation add gstin jsonb")
            if not columnExists("customerandsupplier", "gstin"):
                self.con.execute("alter table customerandsupplier add gstin jsonb")
            if not columnExists("product", "gscode"):
                self.con.execute("alter table product add gscode text")
            if not columnExists("product", "gsflag"):
                self.con.execute("alter table product add gsflag integer")
                self.con.execute("update product set gsflag = 7 where gsflag=null")
            if not columnExists("product", "prodsp"):
                self.con.execute("alter table product add prodsp numeric(13,2)")
            if not columnExists("product", "prodmrp"):
                self.con.execute("alter table product add prodmrp numeric(13,2)")
            if not tableExists("billwise"):
                self.con.execute(
                    "create table billwise(billid serial, vouchercode integer, invid integer, adjdate timestamp, adjamount numeric (12,2), orgcode integer, primary key (billid), foreign key (vouchercode) references vouchers(vouchercode), foreign key(invid) references invoice(invid), foreign key (orgcode) references organisation (orgcode))"
                )
            if not tableExists("rejectionnote"):
                self.con.execute(
                    "create table rejectionnote(rnid serial, rnno text not null, rndate timestamp not null, rejprods jsonb not null ,inout integer not null, dcid integer, invid integer, issuerid integer, orgcode integer not null, rejnarration text, primary key(rnid), foreign key (dcid) references delchal(dcid) ON DELETE CASCADE, foreign key (invid) references invoice(invid) ON DELETE CASCADE, foreign key (issuerid) references users(userid) ON DELETE CASCADE, foreign key (orgcode) references organisation(orgcode) ON DELETE CASCADE, unique(rnno, inout, orgcode))"
                )
            if not columnExists("rejectionnote", "rejprods"):
                self.con.execute(
                    "alter table rejectionnote add rejprods jsonb, add rejectedtotal numeric(13,2)"
                )
            if not tableExists("drcr"):
                self.con.execute(
                    "create table drcr(drcrid serial,drcrno text NOT NULL, drcrdate timestamp NOT NULL, dctypeflag integer default 3, totreduct numeric(13,2), reductionval jsonb, reference jsonb, attachment jsonb, drcrnarration text, attachmentcount integer default 0, userid integer,invid integer, rnid integer,orgcode integer NOT NULL, primary key (drcrid), constraint drcr_orgcode_fkey FOREIGN KEY (orgcode) REFERENCES organisation(orgcode), constraint drcr_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid),constraint drcr_invid_fkey FOREIGN KEY (invid) REFERENCES invoice(invid), constraint drcr_rnid_fkey FOREIGN KEY (rnid) REFERENCES rejectionnote(rnid),CONSTRAINT drcr_orgcode_drcrno_dctypeflag UNIQUE(orgcode,drcrno,dctypeflag), CONSTRAINT drcr_orgcode_invid_dctypeflag UNIQUE(orgcode,invid,dctypeflag), CONSTRAINT drcr_orgcode_rnid_dctypeflag UNIQUE(orgcode,rnid,dctypeflag))"
                )
            if not columnExists("drcr", "drcrmode"):
                self.con.execute("alter table drcr add drcrmode integer default 4")
            if not columnExists("vouchers", "drcrid"):
                self.con.execute("alter table vouchers add drcrid integer")
                self.con.execute(
                    "alter table vouchers add foreign key(drcrid) references drcr(drcrid)"
                )
            if not columnExists("organisation", "invsflag"):
                self.con.execute(
                    "alter table organisation add invsflag integer default 1"
                )
            if not columnExists("organisation", "billflag"):
                self.con.execute(
                    "alter table organisation add billflag integer default 1"
                )
            if not columnExists("vouchers", "instrumentno"):
                self.con.execute("alter table vouchers add instrumentno text")
            if not columnExists("vouchers", "branchname"):
                self.con.execute("alter table vouchers add branchname text")
            if not columnExists("vouchers", "bankname"):
                self.con.execute("alter table vouchers add bankname text")
            if not columnExists("vouchers", "instrumentdate"):
                self.con.execute("alter table vouchers add instrumentdate timestamp")
            if not columnExists("organisation", "logo"):
                self.con.execute("alter table organisation add logo json")
            if not columnExists("dcinv", "invprods"):
                self.con.execute("alter table dcinv add invprods jsonb")
            if not columnExists("transfernote", "duedate"):
                self.con.execute("alter table transfernote add duedate timestamp")
            if not columnExists("transfernote", "grace"):
                self.con.execute("alter table transfernote add grace integer")
            if not columnExists("transfernote", "fromgodown"):
                self.con.execute("alter table transfernote add fromgodown integer")
            if columnExists("product", "specs"):
                self.con.execute("alter table product alter specs drop not null")
            if columnExists("product", "uomid"):
                self.con.execute("alter table product alter uomid drop not null")
            if columnExists("transfernote", "canceldate"):
                self.con.execute("alter table transfernote drop column canceldate")
            if columnExists("transfernote", "cancelflag"):
                self.con.execute("alter table transfernote drop column cancelflag")
            if not columnExists("invoice", "freeqty"):
                self.con.execute("alter table invoice add freeqty jsonb")
            if not columnExists("invoice", "amountpaid"):
                self.con.execute(
                    "alter table invoice add amountpaid numeric default 0.00"
                )
            if not columnExists("stock", "stockdate"):
                self.con.execute("alter table stock add stockdate timestamp")
            if not columnExists("delchal", "attachment"):
                self.con.execute("alter table delchal add attachment json")
            if not columnExists("delchal", "attachmentcount"):
                self.con.execute(
                    "alter table delchal add attachmentcount integer default 0"
                )
            if not columnExists("invoice", "attachment"):
                self.con.execute("alter table invoice add attachment json")
            if not columnExists("invoice", "attachmentcount"):
                self.con.execute(
                    "alter table invoice add attachmentcount integer default 0"
                )
            if not columnExists("invoice", "ewaybillno"):
                self.con.execute("alter table invoice add ewaybillno text")
            if not columnExists("drcr", "drcrnarration"):
                self.con.execute("alter table drcr add drcrnarration text")
            if not columnExists("invoice", "invnarration"):
                self.con.execute("alter table invoice add invnarration text")
            if not columnExists("purchaseorder", "psnarration"):
                self.con.execute("alter table purchaseorder add psnarration text")
            if not columnExists("rejectionnote", "rejnarration"):
                self.con.execute("alter table rejectionnote add rejnarration text")
            if not columnExists("delchal", "totalinword"):
                self.con.execute("alter table delchal add totalinword text")
            if not columnExists("delchalbin", "totalinword"):
                self.con.execute("alter table delchalbin add totalinword text")
            if not columnExists("rejectionnote", "rejnarration"):
                self.con.execute("alter table rejectionnote add rejnarration text")
            if not tableExists("usergodown"):
                self.con.execute(
                    "create table usergodown(ugid serial, goid integer, userid integer, orgcode integer, primary key(ugid), foreign key (goid) references godown(goid),  foreign key (userid) references users(userid), foreign key (orgcode) references organisation(orgcode))"
                )
            if not tableExists("log"):
                self.con.execute(
                    "create table log(logid serial, time timestamp, activity text, userid integer, orgcode integer,  primary key (logid), foreign key(userid) references users(userid), foreign key (orgcode) references organisation(orgcode))"
                )
                self.con.execute(
                    "ALTER TABLE delchal DROP CONSTRAINT delchal_custid_fkey, ADD CONSTRAINT delchal_custid_fkey FOREIGN KEY (custid) REFERENCES customerandsupplier(custid)"
                )
                self.con.execute(
                    "ALTER TABLE invoice DROP CONSTRAINT invoice_custid_fkey, ADD CONSTRAINT invoice_custid_fkey FOREIGN KEY (custid) REFERENCES customerandsupplier(custid)"
                )
                self.con.execute(
                    "alter table goprod add UNIQUE(goid,productcode,orgcode)"
                )
                self.con.execute("alter table product add UNIQUE(productdesc,orgcode)")
                self.con.execute(
                    "alter table customerandsupplier add UNIQUE(orgcode,custname,gstin)"
                )
                self.con.execute(
                    "alter table transfernote add foreign key(fromgodown) references godown(goid)"
                )
            if not tableExists("budget"):
                self.con.execute(
                    "create table budget (budid serial, budname text not null,budtype int not null, startdate timestamp not null,enddate timestamp not null,contents jsonb not null,gaflag int not null,projectcode int, orgcode int not null, primary key(budid),foreign key(projectcode) references projects(projectcode) , foreign key(orgcode) references organisation(orgcode) ON DELETE CASCADE)"
                )
                # In Below query we are removing company preference option Accounting with Invoicing. This query is written under above condition because we want to run the query only once while migrating to version 6.0
                self.con.execute(
                    "update organisation set billflag=1 where invflag=0 and invsflag=1 and billflag=0"
                )

                # Below query is to create a new table to store cancelled deliverynotes.
            if not tableExists("delchalbin"):
                self.con.execute(
                    "create table delchalbin(dcid serial, dcno text NOT NULL, dcdate timestamp NOT NULL, dcflag integer NOT NULL, taxflag integer default 7, discflag integer default 1,contents jsonb, tax jsonb, cess jsonb, issuername text, designation text, noofpackages integer, modeoftransport text, attachment json, consignee jsonb, taxstate text,sourcestate text, orgstategstin text, freeqty jsonb, discount jsonb, vehicleno text, dateofsupply timestamp, delchaltotal numeric(13,2) NOT NULL, goid integer, attachmentcount integer default 0, orgcode integer NOT NULL, custid integer, orderid integer, inoutflag integer NOT NULL, roundoffflag integer default 0, totalinword text, dcnarration text, primary key(dcid), foreign key(orderid) references purchaseorder(orderid), foreign key(custid) references customerandsupplier(custid), foreign key(orgcode) references organisation(orgcode) ON DELETE CASCADE,foreign key(goid) references godown(goid))"
                )
                self.con.execute(
                    "create index delchalbin_orgcodeindex on delchalbin using btree(orgcode)"
                )
                self.con.execute(
                    "create index delchalbin_dcnoindex on delchalbin using btree(dcno)"
                )

                # In Below queries we are creating new table invoivebin which is act as bin for cancelled invoices.
            if not tableExists("invoicebin"):
                self.con.execute(
                    "create table invoicebin(invid serial, invoiceno text NOT NULL, invoicedate  timestamp NOT NULL, taxflag integer default 22, contents jsonb, issuername text, designation text, tax jsonb, cess jsonb, amountpaid numeric(13,2) default 0.00, invoicetotal numeric(13,2) NOT NULL, icflag integer default 9, taxstate text, sourcestate text, orgstategstin text, attachment json, attachmentcount integer default 0, orderid integer,orgcode integer NOT NULL, custid integer, consignee jsonb, freeqty jsonb, reversecharge text, bankdetails jsonb, transportationmode text,vehicleno text, dateofsupply timestamp, discount jsonb, paymentmode integer default 2,address text, inoutflag integer,invoicetotalword text, primary key(invid),foreign key(orderid) references purchaseorder(orderid),foreign key(custid) references customerandsupplier(custid), foreign key (orgcode) references organisation(orgcode) ON DELETE CASCADE)"
                )
                self.con.execute(
                    "create index invoicebin_orgcodeindex on invoicebin using btree(orgcode)"
                )
                self.con.execute(
                    "create index invoicebin_invoicenoindex on invoicebin using btree(invoiceno)"
                )
            else:
                # below code is for add forign key constraint to orgcode when it is not available in invoicebin table
                fkeyavlb = getOnDelete("invoicebin", "invoicebin_orgcode_fkey")
                if fkeyavlb == None:
                    # this condition is apply for forign key available but not ondelete cascade
                    self.con.execute(
                        "alter table invoicebin drop constraint invoicebin_orgcode_fkey"
                    )
                    self.con.execute(
                        "alter table invoicebin add constraint invoicebin_orgcode_fkey foreign key(orgcode) references organisation(orgcode) on delete cascade"
                    )
                if fkeyavlb == False:
                    # this condition is apply for forign key and ondelete cascade both are not available
                    self.con.execute(
                        "alter table invoicebin add constraint invoicebin_orgcode_fkey foreign key(orgcode) references organisation(orgcode) on delete cascade"
                    )
                if fkeyavlb == "CASCADE":
                    pass
            # Add config columns for user and organisation if not present and init to {}
            if not columnExists("users", "userconf"):
                self.con.execute("alter table users add userconf jsonb default '{}'")
            if not columnExists("organisation", "orgconf"):
                self.con.execute(
                    "alter table organisation add orgconf jsonb default '{}'"
                )

            if tableExists("tax2"):
                # A table called tax2 was created for dev purpose and was in use for a while, so rename this table if it exists
                if tableExists("tax"):
                    oldTaxLength = self.con.execute(
                        "select COUNT(taxid) as count from tax"
                    ).fetchone()
                    newTaxLength = self.con.execute(
                        "select COUNT(taxid) as count from tax2"
                    ).fetchone()
                    if oldTaxLength["count"] > 0 and newTaxLength["count"] == 0:
                        # If tax2 table was created but the data in tax was not migrated to tax2
                        # delete tax2 table and just add the column taxfromdate to table tax and add org yearstart dates in that column
                        self.con.execute("drop table if exists tax2")
                        self.con.execute("alter table tax add taxfromdate date")

                        orgs = self.con.execute(
                            "select orgcode, yearstart, yearend from organisation"
                        ).fetchall()
                        dates = {}
                        for org in orgs:
                            dates[org["orgcode"]] = {
                                "from": org["yearstart"],
                                "to": org["yearend"],
                            }

                        taxes = self.con.execute("select orgcode from tax").fetchall()
                        for tax in taxes:
                            from_date = dates[tax["orgcode"]]["from"]
                            to_date = dates[tax["orgcode"]]["to"]
                            self.con.execute(
                                "insert into tax(taxfromdate)values('%s')"
                                % (str(from_date),)
                            )
                    else:
                        self.con.execute("drop table if exists tax")
                # If the table tax didn't exists rename tax2 to tax and rename the indexes
                self.con.execute("alter table if exists tax2 rename to tax")
                self.con.execute("alter index if exists taxindex2 rename to taxindex")
                self.con.execute(
                    "alter index if exists tax_taxindex2 rename to tax_taxindex"
                )
            elif tableExists("tax") and (not columnExists("tax", "taxfromdate")):
                # If the old tax table did not have taxfromdate column, add the column and fill it with org yearstart dates
                self.con.execute("alter table tax add taxfromdate date")

                orgs = self.con.execute(
                    "select orgcode, yearstart, yearend from organisation"
                ).fetchall()
                dates = {}
                for org in orgs:
                    dates[org["orgcode"]] = {
                        "from": org["yearstart"],
                        "to": org["yearend"],
                    }

                taxes = self.con.execute("select orgcode from tax").fetchall()
                for tax in taxes:
                    from_date = dates[tax["orgcode"]]["from"]
                    to_date = dates[tax["orgcode"]]["to"]
                    self.con.execute(
                        "insert into tax(taxfromdate)values('%s')" % (str(from_date),)
                    )

            if not columnExists("invoice", "supinvno"):
                self.con.execute("alter table invoice add supinvno text")
            if not columnExists("invoice", "supinvdate"):
                self.con.execute("alter table invoice add supinvdate date")

            if uniqueConstraintExists(
                "invoice", ["orgcode", "invoiceno", "custid", "icflag"]
            ):
                print("Invoice Unique Constraint Update")
                # rename invoice numbers that will violate the new constraint
                orgs = self.con.execute(
                    select([gkdb.organisation.c.orgcode])
                ).fetchall()
                rename_success = True
                for org in orgs:
                    if not rename_inv_no_uniquely(self.con, org["orgcode"]):
                        rename_success = False
                # drop the old constraint
                if rename_success:
                    self.con.execute(
                        "ALTER TABLE invoice DROP CONSTRAINT IF EXISTS invoice_orgcode_invoiceno_custid_icflag_key"
                    )
                    self.con.execute(
                        "ALTER TABLE invoice DROP CONSTRAINT IF EXISTS invoice_orgcode_invoiceno_key"
                    )
                    self.con.execute(
                        "ALTER TABLE invoice ADD CONSTRAINT invoice_orgcode_invoiceno_key UNIQUE(orgcode, invoiceno)"
                    )

            if not columnExists("stock", "rate"):
                self.con.execute(
                    "alter table stock add rate numeric(13,2) default 0.00"
                )

            # return 0

            # Migration for users -> gkusers
            # Decoupling users and organisations
            gkusersExist = tableExists("gkusers")
            usersExist = tableExists("users")
            oldUsersLength = 0
            gkusersLength = 0
            if usersExist:
                oldUsersLength = self.con.execute(
                    "select COUNT(userid) as count from users"
                ).fetchone()
                # print("Old users length = %d"%(oldUsersLength["count"]))
            if gkusersExist:
                gkusersLength = self.con.execute(
                    select([func.count(gkdb.gkusers.c.userid).label("count")])
                ).fetchone()
                # print("GK users length = %d"%(gkusersLength["count"]))
            if (not gkusersExist and usersExist) or (
                gkusersExist
                and usersExist
                and oldUsersLength["count"] > 0
                and gkusersLength["count"] == 0
            ):
                self.con.execute(
                    "create table if not exists gkusers(userid serial, username text NOT NULL, userpassword text NOT NULL, userquestion text NOT NULL, useranswer text NOT NULL, orgs jsonb default '{}', primary key (userid), unique(username))"
                )
                if not columnExists("organisation", "users"):
                    self.con.execute(
                        "alter table organisation add users jsonb default '{}'"
                    )

                # prepare the tables that have userid as their Foreign Key for step 6
                # remove the old fkey constraints, change the old column name,
                # create the new column without fk pointing to users2 (must be done after the data migration),
                # update the old indexes with new fk
                self.con.execute("drop index if exists logindex")

                self.con.execute(
                    "alter table log drop constraint if exists log_userid_fkey"
                )
                self.con.execute(
                    "alter table rejectionnote drop constraint if exists rejectionnote_issuerid_fkey"
                )
                self.con.execute(
                    "alter table drcr drop constraint if exists drcr_userid_fkey"
                )
                self.con.execute(
                    "alter table usergodown drop constraint if exists usergodown_userid_fkey"
                )

                if not columnExists("log", "_userid"):
                    print("renaming old userid columns to _userid")
                    self.con.execute("alter table log rename column userid to _userid")
                    self.con.execute("alter table drcr rename column userid to _userid")
                    self.con.execute(
                        "alter table usergodown rename column userid to _userid"
                    )
                    self.con.execute(
                        "alter table rejectionnote rename column issuerid to _issuerid"
                    )
                if not columnExists("log", "userid"):
                    print("Adding a new column called userid, to store the new userid")
                    self.con.execute("alter table log add userid integer default -1")
                    self.con.execute(
                        "alter table rejectionnote add issuerid integer default -1"
                    )
                    self.con.execute("alter table drcr add userid integer default -1")
                    self.con.execute(
                        "alter table usergodown add userid integer default -1"
                    )

                    self.con.execute("create index logindex on log (userid, activity)")

                allUserData = list(self.con.execute(select([gkdb.users])).fetchall())
                # (1) Loop through all the users
                notUniqueUsers = {}
                for uindex, udata in enumerate(allUserData):
                    orgcode = udata["orgcode"]
                    # print(1)
                    orgData = self.con.execute(
                        select(
                            [gkdb.organisation.c.orgname, gkdb.organisation.c.orgtype]
                        ).where(gkdb.organisation.c.orgcode == orgcode)
                    ).fetchone()

                    # print(2)
                    # (2) Find entries in allUserData with the same username and orgname
                    # (same org, multiple Financial Years)
                    otherFY = []
                    orgs = {}
                    orgs[udata["orgcode"]] = {
                        "userconf": udata["userconf"],
                        "invitestatus": True,
                        "userrole": udata["userrole"],
                    }
                    for uindex2 in range(uindex + 1, len(allUserData)):
                        # print(uindex2)
                        udata2 = allUserData[uindex2]
                        if udata["username"] == udata2["username"]:
                            orgData2 = self.con.execute(
                                select(
                                    [
                                        gkdb.organisation.c.orgname,
                                        gkdb.organisation.c.orgtype,
                                    ]
                                ).where(
                                    gkdb.organisation.c.orgcode == udata2["orgcode"]
                                )
                            ).fetchone()
                            if (
                                orgData["orgname"] == orgData2["orgname"]
                                and orgData["orgtype"] == orgData2["orgtype"]
                            ):
                                print("FY org found %s" % (str(udata2["orgcode"])))
                                otherFY.append(
                                    {
                                        "orgcode": udata2["orgcode"],
                                        "olduserid": udata2["userid"],
                                        "index": uindex2,
                                    }
                                )
                                orgs[udata2["orgcode"]] = {
                                    "userconf": udata2["userconf"],
                                    "invitestatus": True,
                                    "userrole": udata2["userrole"],
                                }
                            else:
                                # if user name is not unique across orgs
                                notUniqueUsers[udata2["username"]] = True
                                print(
                                    "username: %s not unique, has to be renamed"
                                    % (udata2["username"])
                                )

                    if udata["username"] in notUniqueUsers:
                        # (3) create a unique user name (org name + user name)
                        orgname = "_".join(orgData["orgname"].split(" "))
                        orgtype = "p" if orgData["orgtype"] == "Profit Making" else "np"
                        uname = orgname + "_" + orgtype + "_" + udata["username"]
                    else:
                        uname = udata["username"]

                    # (4) create a table entry in users2 and userorg tables
                    newUserData = {
                        "username": uname,
                        "userpassword": udata["userpassword"],
                        "userquestion": udata["userquestion"],
                        "useranswer": udata["useranswer"],
                        "userconf": {},
                        "orgs": orgs,
                    }

                    self.con.execute(gkdb.gkusers.insert(), [newUserData])

                    # remove data from users table, if the user has a unique name
                    """ Deletes old DB data, so commenting it out till dev is completed
                    if udata["username"] not in notUniqueUsers:
                        self.con.execute(gkdb.users.delete().where(gkdb.users.c.userid == udata["userid"]))
                    """

                    newUserId = self.con.execute(
                        select([gkdb.gkusers.c.userid]).where(
                            gkdb.gkusers.c.username == uname
                        )
                    ).fetchone()

                    # ToDo: Update orgs table with userid
                    self.con.execute(
                        "update organisation set users = jsonb_set(users, '{%s}', 'true') where orgcode = %d;"
                        % (
                            str(newUserId["userid"]),
                            udata["orgcode"],
                        )
                    )

                    # (5) If for the same org, multiple financial years are found,
                    # add them to userorg table with the above created userid and
                    # remove those entries from the allUserData array
                    print("OtherFY len = %d" % (len(otherFY)))
                    for udata3 in otherFY:
                        # remove data from users table, if the user has a unique name
                        """Deletes old DB data, so commenting it out till dev is completed
                        if udata["username"] not in notUniqueUsers:
                            self.con.execute(gkdb.users.delete().where(gkdb.users.c.userid == udata3["olduserid"]))
                        """
                        allUserData.pop(udata3["index"])
                        # Update orgs table with userid
                        self.con.execute(
                            "update organisation set users = jsonb_set(users, '{%s}', 'true') where orgcode = %d;"
                            % (
                                str(newUserId["userid"]),
                                udata3["orgcode"],
                            )
                        )

                        # (6.1) Update the tables where userid from users table was a Foreign Key
                        # tables to update log, rejectionnote, drcr, usergodown
                        self.con.execute(
                            "update log set userid = %d where _userid = %d"
                            % (newUserId["userid"], udata3["olduserid"])
                        )

                        self.con.execute(
                            "update rejectionnote set issuerid = %d where _issuerid = %d"
                            % (newUserId["userid"], udata3["olduserid"])
                        )

                        self.con.execute(
                            "update drcr set userid = %d where _userid = %d"
                            % (newUserId["userid"], udata3["olduserid"])
                        )

                        self.con.execute(
                            "update usergodown set userid = %d where _userid = %d"
                            % (newUserId["userid"], udata3["olduserid"])
                        )

                    # (6.2) Update the tables where userid from users table was a Foreign Key
                    # tables to update log, rejectionnote, drcr, usergodown
                    self.con.execute(
                        "update log set userid = %d where _userid = %d"
                        % (newUserId["userid"], udata["userid"])
                    )

                    self.con.execute(
                        "update rejectionnote set issuerid = %d where _issuerid = %d"
                        % (newUserId["userid"], udata["userid"])
                    )

                    self.con.execute(
                        "update drcr set userid = %d where _userid = %d"
                        % (newUserId["userid"], udata["userid"])
                    )

                    self.con.execute(
                        "update usergodown set userid = %d where _userid = %d"
                        % (newUserId["userid"], udata["userid"])
                    )
                # (7) After updating all the tables where userid was a fkey, add back the fkey constraint pointing to users2 table
                self.con.execute(
                    "alter table log drop constraint if exists log_userid_fkey"
                )
                self.con.execute(
                    "alter table log add constraint log_userid_fkey foreign key(userid) references gkusers(userid)"
                )

                self.con.execute(
                    "alter table rejectionnote drop constraint if exists rejectionnote_issuerid_fkey"
                )
                self.con.execute(
                    "alter table rejectionnote add constraint rejectionnote_issuerid_fkey foreign key(issuerid) references gkusers(userid)"
                )

                self.con.execute(
                    "alter table drcr drop constraint if exists drcr_userid_fkey"
                )
                self.con.execute(
                    "alter table drcr add constraint drcr_userid_fkey foreign key(userid) references gkusers(userid)"
                )

                self.con.execute(
                    "alter table usergodown drop constraint if exists usergodown_userid_fkey"
                )
                self.con.execute(
                    "alter table usergodown add constraint usergodown_userid_fkey foreign key(userid) references gkusers(userid) on delete cascade"
                )

            # End of Migration for users -> gkusers

            # Add opening stock value that corresponds to the product opening stock qty that has been entered
            if not columnExists("goprod", "openingstockvalue"):
                self.con.execute(
                    "alter table goprod add openingstockvalue numeric(13,2) default 0.00"
                )

            try:
                self.con.execute(
                    "alter table organisation alter column orgstate set NOT NULL"
                )
            except:
                print("exception ", 2)
                orgDatum = self.con.execute(
                    "select orgcode, orgstate from organisation"
                ).fetchall()
                for orgData in orgDatum:
                    if not orgData["orgstate"]:
                        self.con.execute(
                            "update organisation set orgstate = '0'  where orgcode = %d"
                            % (orgData["orgcode"])
                        )
                self.con.execute(
                    "alter table organisation alter column orgstate set NOT NULL"
                )
            try:
                self.con.execute(
                    "alter table product alter column gsflag set NOT NULL, alter column productdesc set NOT NULL"
                )
            except:
                print("exception ", 3)
                counter = 0
                self.con.execute("update product set gsflag = 7  where gsflag = NULL")
                prodDatum = self.con.execute(
                    "select productcode, productdesc from product"
                ).fetchall()
                for prodData in prodDatum:
                    if not prodData["productdesc"]:
                        self.con.execute(
                            "update product set productdesc = 'gk-product-%s'  where productcode = %d"
                            % (str(counter), prodData["productcode"])
                        )
                        counter = counter + 1
                self.con.execute(
                    "alter table product alter column gsflag set NOT NULL, alter column productdesc set NOT NULL"
                )
            with eng.begin() as conn:
                conn.execute("alter table bankrecon drop constraint if exists bankrecon_vouchercode_accountcode_key")
                conn.execute("alter table bankrecon add column if not exists entry_type text")
                conn.execute("alter table bankrecon add column if not exists amount float")
                conn.execute("alter table customerandsupplier add column if not exists country text")
                conn.execute("alter table customerandsupplier add column if not exists tin text")

            print("Database migration successful")

        except:
            print("exception ", traceback.format_exc())
            # print(e)
            return 0
        finally:
            self.con.close()
            return 0


if __name__ == "__main__":
    Migrate(request).db()
