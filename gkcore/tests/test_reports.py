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
"Bhavesh Bawadhane " <bbhavesh07@gmail.com>
"""
import requests, json

class TestReports:

	@classmethod
	def setup_class(self):
		orgdata = {"orgdetails":{'orgname': 'Test Organisation', 'yearend': '2017-03-31', 'yearstart': '2016-04-01', 'orgtype': 'Profit Making', 'invflag': 1}, "userdetails":{"username":"admin", "userpassword":"admin","userquestion":"who am i?", "useranswer":"hacker"}}
		result = requests.post("http://127.0.0.1:6543/organisations", data =json.dumps(orgdata))
		self.key = result.json()["token"]
		self.header={"gktoken":self.key}
		""" Project Initialization Data """
		gkdata = {"projectname":"dff","sanctionedamount":float(5000)}
		result = requests.post("http://127.0.0.1:6543/projects",data=json.dumps(gkdata), headers=self.header)
		result = requests.get("http://127.0.0.1:6543/projects", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["projectname"] == "dff":
				self.projectcode = record["projectcode"]
				break
		""" Initialization of a group-subgroup """
		result = requests.get("http://127.0.0.1:6543/groupsubgroups", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["groupname"] == "Current Assets":
				self.demo_groupcode = record["groupcode"]
				break
		result = requests.get("http://127.0.0.1:6543/groupDetails/%s"%(self.demo_groupcode), headers=self.header)
		for record in result.json()["gkresult"]:
			if record["subgroupname"] == "Bank":
				self.demo_grpcode = record["groupcode"]
				break
		""" Initialization of two Accounts for creating a voucher """
		gkdata = {"accountname":"Bank Of India","openingbal":500,"groupcode":self.demo_grpcode}
		result = requests.post("http://127.0.0.1:6543/accounts", data =json.dumps(gkdata),headers=self.header)
		result = requests.get("http://127.0.0.1:6543/accounts", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["accountname"] == "Bank Of India":
				self.demo_accountcode1 = record["accountcode"]
				break
		gkdata = {"accountname":"Bank Of Badoda","openingbal":1000,"groupcode":self.demo_grpcode}
		result = requests.post("http://127.0.0.1:6543/accounts", data =json.dumps(gkdata),headers=self.header)
		result = requests.get("http://127.0.0.1:6543/accounts", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["accountname"] == "Bank Of Badoda":
				self.demo_accountcode2 = record["accountcode"]
				break
		""" Preparing gkdata to pass to Create Voucher """
		drs = {self.demo_accountcode1: 100}
		crs = {self.demo_accountcode2: 100}
		gkdata={"invid": None,"vouchernumber":100,"voucherdate":"2016-12-16","narration":"Demo Narration","drs":drs,"crs":crs,"vouchertype":"purchase","projectcode":int(self.projectcode)}
		result = requests.post("http://127.0.0.1:6543/transaction",data=json.dumps(gkdata) , headers=self.header)
		result = requests.get("http://127.0.0.1:6543/transaction?searchby=vnum&voucherno=100", headers=self.header)
		self.demo_vouchercode = result.json()["gkresult"][0]["vouchercode"]

	@classmethod
	def teardown_class(self):
		gkdata={"vouchercode": self.demo_vouchercode}
		result = requests.delete("http://127.0.0.1:6543/transaction",data =json.dumps(gkdata), headers=self.header)
		gkdata = {"projectcode":self.projectcode}
		result = requests.delete("http://127.0.0.1:6543/projects",data=json.dumps(gkdata), headers=self.header)
		gkdata={"accountcode":self.demo_accountcode1}
		result = requests.delete("http://127.0.0.1:6543/accounts",data =json.dumps(gkdata), headers=self.header)
		gkdata={"accountcode":self.demo_accountcode2}
		result = requests.delete("http://127.0.0.1:6543/accounts",data =json.dumps(gkdata), headers=self.header)
		result = requests.delete("http://127.0.0.1:6543/organisations", headers=self.header)

	def test_monthly_ledger(self):
		result = requests.get("http://127.0.0.1:6543/report?type=monthlyledger&accountcode=%d"%(self.demo_accountcode1), headers=self.header)
		monthlyledger = result.json()["gkresult"]
		assert result.json()["gkstatus"] == 0 and monthlyledger[0]["month"] == "April" and monthlyledger[0]["Dr"] == "500.00" and monthlyledger[8]["month"] == "December" and monthlyledger[8]["Dr"] == "600.00" and monthlyledger[8]["vcount"] == 1

	def test_ledger(self):
		drs = {self.demo_accountcode1: 10}
		crs = {self.demo_accountcode2: 10}
		gkdata={"invid": None,"vouchernumber":101,"voucherdate":"2016-12-16","narration":"Demo Narration","drs":drs,"crs":crs,"vouchertype":"purchase","projectcode":int(self.projectcode)}
		result = requests.post("http://127.0.0.1:6543/transaction",data=json.dumps(gkdata) , headers=self.header)
		result = requests.get("http://127.0.0.1:6543/transaction?searchby=vnum&voucherno=101", headers=self.header)
		vcode = result.json()["gkresult"][0]["vouchercode"]
		result1 = requests.get("http://127.0.0.1:6543/report?type=ledger&accountcode=%d&calculatefrom=%s&calculateto=%s&financialstart=%s&projectcode=%d"%(self.demo_accountcode1, "2016-04-01", "2017-03-31", "2016-04-01", int(self.projectcode)), headers=self.header)
		ledger = result1.json()["gkresult"]
		gkdata={"vouchercode": vcode}
		result = requests.delete("http://127.0.0.1:6543/transaction",data =json.dumps(gkdata), headers=self.header)
		assert result1.json()["gkstatus"] == 0 and ledger[0]["vouchernumber"] == "100" and ledger[0]["vouchertype"] == "purchase" and ledger[0]["Dr"] == "100.00" and ledger[1]["vouchernumber"] == "101" and ledger[1]["vouchertype"] == "purchase" and ledger[1]["Dr"] == "10.00" and ledger[2]["Dr"] == "110.00" and ledger[2]["particulars"][0] == "Total of Transactions"

	def test_crdrledger(self):
		result = requests.get("http://127.0.0.1:6543/report?type=crdrledger&accountcode=%d&calculatefrom=%s&calculateto=%s&financialstart=%s&projectcode=%d&side=%s"%(self.demo_accountcode1, "2016-04-01", "2017-03-31", "2016-04-01", int(self.projectcode),"cr"), headers=self.header)
		result1 = requests.get("http://127.0.0.1:6543/report?type=crdrledger&accountcode=%d&calculatefrom=%s&calculateto=%s&financialstart=%s&projectcode=%d&side=%s"%(self.demo_accountcode1, "2016-04-01", "2017-03-31", "2016-04-01", int(self.projectcode),"dr"), headers=self.header)
		assert result.json()["gkstatus"] == 0 and result1.json()["gkstatus"] == 0

	def test_netTrialBalance(self):
		result = requests.get("http://127.0.0.1:6543/report?type=nettrialbalance&calculateto=%s&financialstart=%s"%("2017-03-31", "2016-04-01"), headers=self.header)
		assert result.json()["gkstatus"] == 0

	def test_grossTrialBalance(self):
		result = requests.get("http://127.0.0.1:6543/report?type=grosstrialbalance&calculateto=%s&financialstart=%s"%("2017-03-31", "2016-04-01"), headers=self.header)
		assert result.json()["gkstatus"] == 0

	def test_extendedTrialBalance(self):
		result = requests.get("http://127.0.0.1:6543/report?type=extendedtrialbalance&calculateto=%s&financialstart=%s"%("2017-03-31", "2016-04-01"), headers=self.header)
		assert result.json()["gkstatus"] == 0

	def test_cashflow(self):
		result = requests.get("http://127.0.0.1:6543/report?type=cashflow&calculateto=%s&financialstart=%s&calculatefrom=%s"%("2017-03-31", "2016-04-01", "2016-04-01",), headers=self.header)
		assert result.json()["gkstatus"] == 0

	def test_projectStatement(self):
		result = requests.get("http://127.0.0.1:6543/report?type=projectstatement&calculateto=%s&financialstart=%s&projectcode=%d"%("2017-03-31", "2016-04-01", self.projectcode), headers=self.header)
		assert result.json()["gkstatus"] == 0

	def test_balanceSheet(self):
		result = requests.get("http://127.0.0.1:6543/report?type=balancesheet&calculateto=%s&baltype=1"%("2017-03-31"), headers=self.header)
		result1 = requests.get("http://127.0.0.1:6543/report?type=balancesheet&calculateto=%s&baltype=2"%("2017-03-31"), headers=self.header)
		assert result.json()["gkstatus"] == 0 and result1.json()["gkstatus"] == 0

	def test_profitLoss(self):
		result = requests.get("http://127.0.0.1:6543/report?type=profitloss&calculateto=%s"%("2017-03-31"), headers=self.header)
		assert result.json()["gkstatus"] == 0

	def test_get_deleted_vouchers(self):
		drs = {self.demo_accountcode1: 1000}
		crs = {self.demo_accountcode2: 1000}
		gkdata={"invid": None,"vouchernumber":11,"voucherdate":"2016-12-16","narration":"Demo Narration","drs":drs,"crs":crs,"vouchertype":"purchase","projectcode":int(self.projectcode)}
		""" Create a Voucher """
		result = requests.post("http://127.0.0.1:6543/transaction",data=json.dumps(gkdata) , headers=self.header)
		result = requests.get("http://127.0.0.1:6543/transaction?searchby=vnum&voucherno=11", headers=self.header)
		vouchercode = result.json()["gkresult"][0]["vouchercode"]
		""" Delete a Voucher """
		gkdata={"vouchercode": vouchercode}
		result = requests.delete("http://127.0.0.1:6543/transaction",data =json.dumps(gkdata), headers=self.header)
		result = requests.get("http://127.0.0.1:6543/report?type=deletedvoucher", headers=self.header)
		assert result.json()["gkresult"][0]["vouchercode"] == vouchercode

	def test_stockReport(self):
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
		gkdata = {"goname":"Test Godown", "state":"Maharashtra", "goaddr":"Pune", "contactname":"Bhavesh Bavdhane", "designation":"Designation", "gocontact":"8446611103"}
		result = requests.post("http://127.0.0.1:6543/godown", data =json.dumps(gkdata),headers=self.header)
		result = requests.get("http://127.0.0.1:6543/godown", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["goname"] == "Test Godown":
				self.godownid = record["goid"]
				break
		proddetails = {"productdesc":"Sugar","specs":{self.demospeccode: "Pure"}, "uomid":self.demouomid, "categorycode": self.democategorycode}
		productdetails = {"productdetails":proddetails, "godetails":{self.godownid:100}, "godownflag":True}
		result = requests.post("http://127.0.0.1:6543/products", data=json.dumps(productdetails),headers=self.header)
		demoproductcode = result.json()["gkresult"]
		stockresult = requests.get("http://127.0.0.1:6543/report?type=stockreport&productcode=%d&startdate=%s&enddate=%s"%(demoproductcode, "2016-04-01", "2017-03-31"),headers=self.header)
		result = requests.delete("http://127.0.0.1:6543/products", data=json.dumps({"productcode":int(demoproductcode)}),headers=self.header)
		result = requests.delete("http://127.0.0.1:6543/categoryspecs",data=json.dumps({"spcode": int(self.demospeccode)}) ,headers=self.header)
		result = requests.delete("http://127.0.0.1:6543/unitofmeasurement", data = json.dumps({"uomid":self.demouomid}), headers=self.header)
		gkdata={"categorycode": self.democategorycode}
		result = requests.delete("http://127.0.0.1:6543/categories", data =json.dumps(gkdata), headers=self.header)
		gkdata={"goid":self.godownid}
		result = requests.delete("http://127.0.0.1:6543/godown",data =json.dumps(gkdata), headers=self.header)
		assert stockresult.json()["gkstatus"] == 0 and stockresult.json()["gkresult"][0]["inward"] == "100.00"

	def test_godown_stock_report(self):
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
		gkdata = {"goname":"Test Godown", "state":"Maharashtra", "goaddr":"Pune", "contactname":"Bhavesh Bavdhane", "designation":"Designation", "gocontact":"8446611103"}
		result = requests.post("http://127.0.0.1:6543/godown", data =json.dumps(gkdata),headers=self.header)
		result = requests.get("http://127.0.0.1:6543/godown", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["goname"] == "Test Godown":
				self.godownid = record["goid"]
				break
		proddetails = {"productdesc":"Sugar","specs":{self.demospeccode: "Pure"}, "uomid":self.demouomid, "categorycode": self.democategorycode}
		productdetails = {"productdetails":proddetails, "godetails":{self.godownid:100}, "godownflag":True}
		result = requests.post("http://127.0.0.1:6543/products", data=json.dumps(productdetails),headers=self.header)
		demoproductcode = result.json()["gkresult"]
		gostockreport = requests.get("http://127.0.0.1:6543/report?type=godownstockreport&goid=%d&productcode=%d&startdate=%s&enddate=%s"%(self.godownid, demoproductcode, "2016-04-01", "2017-03-31"),headers=self.header)
		result = requests.delete("http://127.0.0.1:6543/products", data=json.dumps({"productcode":int(demoproductcode)}),headers=self.header)
		result = requests.delete("http://127.0.0.1:6543/categoryspecs",data=json.dumps({"spcode": int(self.demospeccode)}) ,headers=self.header)
		result = requests.delete("http://127.0.0.1:6543/unitofmeasurement", data = json.dumps({"uomid":self.demouomid}), headers=self.header)
		gkdata={"categorycode": self.democategorycode}
		result = requests.delete("http://127.0.0.1:6543/categories", data =json.dumps(gkdata), headers=self.header)
		gkdata={"goid":self.godownid}
		result = requests.delete("http://127.0.0.1:6543/godown",data =json.dumps(gkdata), headers=self.header)
		assert gostockreport.json()["gkstatus"] == 0 and gostockreport.json()["gkresult"][0]["inward"] == "100.00"
