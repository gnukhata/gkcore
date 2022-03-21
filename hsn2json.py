#!/usr/bin/env python3
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
Copyright (C) 2017, 2018, 2019, 2020, 2021 Digital Freedom Foundation & Accion Labs Pvt. Ltd.

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
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,


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
    for i in sac_array:
        hsn_array.append(i)

    print("💾 Saving to file ...")
    with open(f"{gkcore_root}/static/gst-hsn.json", "w") as f:
        json.dump(hsn_array, f, indent=1)

    print("total generated hsn/sac items: ", len(hsn_array))
except Exception as e:
    print(e)
