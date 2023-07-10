#!/usr/bin/env python3
"""
This file is part of GNUKhata: A modular,robust and Free Accounting System.
License: GPLv3 https://www.gnu.org/licenses/gpl-3.0-standalone.html

Summary:
========
Convert the hsn/sac spreadhseet provided by the GST portal
into valid json file to use within gkcore

Contributors
============
Sai Karthik <kskarthik@disroot.org>
"""

import requests, io, json, pathlib, openpyxl

try:
    print("📡 Getting HSN/SAC file from GST portal ...")

    gkcore_root = pathlib.Path("./").resolve()
    r = requests.get("https://tutorial.gst.gov.in/downloads/HSN_SAC.xlsx").content
    b = io.BytesIO(r)
    wb = openpyxl.load_workbook(b)
    hsn = wb["HSN"]
    sac = wb["SAC"]
    hsn_array = []
    sac_array = []

    print("⚙ Extracting HSN/SAC from the spreadsheet ...")

    for i in hsn.values:
        hsn_array.append({"hsn_code": i[0], "hsn_desc": i[1]})

    for i in sac.values:
        sac_array.append({"hsn_code": str(i[0]), "hsn_desc": i[1]})

    # remove table column names
    hsn_array.pop(0)
    sac_array.pop(0)

    print("HSN codes: ", len(hsn_array))
    print("SAC codes: ", len(sac_array))

    # join SAC & HSN arrays
    # for i in sac_array:
    #     hsn_array.append(i)
    hsn_array.extend(sac_array)

    print("💾 Saving to file ...")
    with open(f"{gkcore_root}/static/gst-hsn.json", "w") as f:
        json.dump(hsn_array, f)

    print("total generated hsn/sac items: ", len(hsn_array))
except Exception as e:
    print(e)
