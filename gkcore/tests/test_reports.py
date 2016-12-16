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
		orgdata = {"orgdetails":{'orgname': 'Test Organisation', 'yearend': '2016-03-31', 'yearstart': '2015-04-01', 'orgtype': 'Profit Making', 'invflag': 1}, "userdetails":{"username":"admin", "userpassword":"admin","userquestion":"who am i?", "useranswer":"hacker"}}
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
		#print result.json()["gkstatus"], "India status"
		result = requests.get("http://127.0.0.1:6543/accounts", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["accountname"] == "Bank Of India":
				#print result.json()["gkstatus"], "Bank of India"
				self.demo_accountcode1 = record["accountcode"]
				break
		gkdata = {"accountname":"Bank Of Badoda","openingbal":1000,"groupcode":self.demo_grpcode}
		result = requests.post("http://127.0.0.1:6543/accounts", data =json.dumps(gkdata),headers=self.header)
		#print result.json()["gkstatus"], "Badoda status"
		result = requests.get("http://127.0.0.1:6543/accounts", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["accountname"] == "Bank Of Badoda":
				#print result.json()["gkstatus"], "Bank of Badoda"
				self.demo_accountcode2 = record["accountcode"]
				break
		""" Preparing gkdata to pass to Create Voucher """
		drs = {self.demo_accountcode1: 100}
		crs = {self.demo_accountcode2: 100}
		gkdata={"invid": None,"vouchernumber":100,"voucherdate":"2016-03-30","narration":"Demo Narration","drs":drs,"crs":crs,"vouchertype":"purchase","projectcode":int(self.projectcode)}
		result = requests.post("http://127.0.0.1:6543/transaction",data=json.dumps(gkdata) , headers=self.header)
		#print "gkstatus: post ", result.json()["gkstatus"]
		vnum = "100"#string or integer?
		searchby = "vnum"
		result = requests.get("http://127.0.0.1:6543/transaction?searchby=%s&voucherno=%s"%(searchby,vnum), headers=self.header)
		#print "gkstatus: get ", result.json()["gkstatus"]
		#print "list: ", result.json()["gkresult"]
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

	def test_monthly_ledget(self):
		result = requests.get("http://127.0.0.1:6543/report?type=monthlyledger&accountcode=%d"%(self.demo_accountcode1), headers=self.header)
		assert result.json()["gkstatus"] == 0
