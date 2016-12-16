"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

  GNUKhata is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License along with GNUKhata (COPYING); if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,


Contributors:
"Vaibhav Kurhe" <vaibhav.kurhe@gmail.com>
"""

import requests, json

class TestDelChal:
	@classmethod
	def setup_class(self):
		orgdata = {"orgdetails":{'orgname': 'Test Organisation', 'yearend': '2016-03-31', 'yearstart': '2015-04-01', 'orgtype': 'Profit Making', 'invflag': 1}, "userdetails":{"username":"admin", "userpassword":"admin","userquestion":"who am i?", "useranswer":"hacker"}}
		result = requests.post("http://127.0.0.1:6543/organisations",data=json.dumps(orgdata))
		self.key = result.json()["token"]
		self.header={"gktoken":self.key}

		userdata = {"username":"user","userpassword":"passwd","userrole":0,"userquestion":"what is my pet name?","useranswer":"cat"}
		result = requests.post("http://127.0.0.1:6543/users", data=json.dumps(userdata), headers=self.header)
		result = requests.get("http://127.0.0.1:6543/users", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["username"] == "user":
				self.userid = record["userid"]
				break
		""" Doubt: This should be a customer or supplier? """
		custdata = {"custname":"customer","custaddr":"goregaon","custphone":"22432123","custemail":"customer@gmail.com","custfax":"FAXCUST212345","state":"Maharashtra","custpan":"CUSTPAN1234","custtan":"CUSTTAN1234","csflag":3}
		result = requests.post("http://127.0.0.1:6543/customersupplier",data=json.dumps(custdata),headers=self.header)
		result = requests.get("http://127.0.0.1:6543/customersupplier?qty=custall", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["custname"] == "customer":
				self.custid = record["custid"]
				break

		""" supid is used to store custid attribute """
		custdata = {"custname":"supplier","custaddr":"borivali","custphone":"44432123","custemail":"supplier@gmail.com","custfax":"FAXSUP212345","state":"Maharashtra","custpan":"SUPPAN1234","custtan":"SUPTAN1234","csflag":19}
		result = requests.post("http://127.0.0.1:6543/customersupplier",data=json.dumps(custdata),headers=self.header)
		result = requests.get("http://127.0.0.1:6543/customersupplier?qty=supall", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["custname"] == "supplier":
				self.supid = record["custid"]
				break

	@classmethod
	def teardown_class(self):
		result = requests.delete("http://127.0.0.1:6543/organisations", headers=self.header)

	def setup(self):
		""" Product generation code """
		categorydata = {"categoryname":"Test Category", "subcategoryof": None}
		result = requests.post("http://127.0.0.1:6543/categories",data=json.dumps(categorydata) ,headers=self.header)
		result = requests.get("http://127.0.0.1:6543/categories", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["categoryname"] == "Test Category":
				self.democategorycode = record["categorycode"]
				break
		uomdata = {"unitname":"kilogram"}
		result = requests.post("http://127.0.0.1:6543/unitofmeasurement", data = json.dumps(uomdata), headers=self.header)
		result = requests.get("http://127.0.0.1:6543/unitofmeasurement?qty=all", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["unitname"] == "kilogram":
				self.demouomid = record["uomid"]
				break
		specdata= {"attrname":"Type","attrtype":0,"categorycode":self.democategorycode}
		specresult = requests.post("http://127.0.0.1:6543/categoryspecs",data=json.dumps(specdata) ,headers=self.header)
		result = requests.get("http://127.0.0.1:6543/categoryspecs?categorycode=%d"%(int(self.democategorycode)), headers=self.header)
		for record in result.json()["gkresult"]:
			if record["attrname"] == "Type":
				self.demospeccode = record["spcode"]
				break
		proddetails = {"productdesc":"Sugar","specs":{self.demospeccode: "Pure"}, "uomid":self.demouomid, "categorycode": self.democategorycode}
		productdetails = {"productdetails":proddetails, "godetails":None, "godownflag":False}
		result = requests.post("http://127.0.0.1:6543/products", data=json.dumps(productdetails),headers=self.header)
		self.demoproductcode = result.json()["gkresult"]

		result = requests.get("http://127.0.0.1:6543/products", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["productdesc"] == "jaggery":
				self.qty = record["qty"]
				break

		""" In this testcase, godown is not linked with Delivery Challan """
		products = {self.demoproductcode: self.qty}
		delchaldata = {"custid":self.custid,"dcno":"15","dcdate":"2016-03-30","dcflag":3, "issuername": "Mr. Sanjeev"}
		""" inout=9 means IN and inout=15 means OUT """
		stockdata = {"inout": 9, "items": products}
		delchalwholedata = {"delchaldata":delchaldata,"stockdata":stockdata}
		result=requests.post("http://127.0.0.1:6543/delchal",data=json.dumps(delchalwholedata),headers=self.header)
		delchals = requests.get("http://127.0.0.1:6543/delchal?delchal=all", headers=header)
		for record in delchals.json()["gkresult"]:
			if record["dcno"] == "15":
				self.demo_delchalid = record["dcid"]
				break

	def teardown(self):
		result = requests.delete("http://127.0.0.1:6543/products", data=json.dumps({"productcode":int(self.demoproductcode)}),headers=self.header)
		result = requests.delete("http://127.0.0.1:6543/categoryspecs",data=json.dumps({"spcode": int(self.demospeccode)}) ,headers=self.header)
		result = requests.delete("http://127.0.0.1:6543/unitofmeasurement", data = json.dumps({"uomid":self.demouomid}), headers=self.header)
		gkdata = {"categorycode": self.democategorycode}
		result = requests.delete("http://127.0.0.1:6543/categories", data =json.dumps(gkdata), headers=self.header)
		deldata = {"dcid": self.demo_delchalid,"cancelflag": 1}
		result = requests.delete("http://127.0.0.1:6543/delchal",data=json.dumps(deldata), headers=self.header)
