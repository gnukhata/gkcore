"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
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


Contributors:
"Vaibhav Kurhe" <vaibhav.kurhe@gmail.com>
"""

import requests, json

class TestAccountsByRule:
	@classmethod
	def setup_class(self):
		""" Organization Initialization Data """
		orgdata = {"orgdetails":{'orgname': 'Test Organisation', 'yearend': '2016-03-31', 'yearstart': '2015-04-01', 'orgtype': 'Profit Making', 'invflag': 1}, "userdetails":{"username":"admin", "userpassword":"admin","userquestion":"who am i?", "useranswer":"hacker"}}
		result = requests.post("http://127.0.0.1:6543/organisations",data=json.dumps(orgdata))
		self.key = result.json()["token"]
		self.header={"gktoken":self.key}


	@classmethod
	def teardown_class(self):
		result = requests.delete("http://127.0.0.1:6543/organisations", headers=self.header)

	def setup(self):
		""" Create an account of each type """
		result = requests.get("http://127.0.0.1:6543/groupsubgroups", headers=self.header)
		groups = result.json()["gkresult"]
		self.demoaccountcode = {}
		i = 1
		accountname = "India Bank" + str(i)
		for group in groups:
			self.groupname = group["groupname"]
			self.groupcode = group["groupcode"]
			result = requests.get("http://127.0.0.1:6543/groupDetails/%s"%(self.groupcode), headers=self.header)
			subgrouplist = result.json()["gkresult"]
			if len(subgrouplist) == 0:
				gkdata = {"accountname": accountname,"openingbal":500,"groupcode":self.groupcode}
				result = requests.post("http://127.0.0.1:6543/accounts", data =json.dumps(gkdata),headers=self.header)
				result = requests.get("http://127.0.0.1:6543/accounts", headers=self.header)
				for record in result.json()["gkresult"]:
					if record["accountname"] == accountname:
						subgroupof = None
						self.demoaccountcode.update({record["accountcode"]: [accountname, self.groupname, subgroupof]})
						break
				i = i + 1
				accountname = "India Bank" + str(i)
				continue
			for subgroup in subgrouplist:
				self.grpname = subgroup["subgroupname"]
				self.grpcode = subgroup["groupcode"]
				gkdata = {"accountname": accountname,"openingbal":500,"groupcode":self.grpcode}
				result = requests.post("http://127.0.0.1:6543/accounts", data =json.dumps(gkdata),headers=self.header)
				result = requests.get("http://127.0.0.1:6543/accounts", headers=self.header)
				accountlist = result.json()["gkresult"]
				for account in accountlist:
					if account["accountname"] == accountname:
						subgroupof = self.groupname
						self.demoaccountcode.update({account["accountcode"]: [accountname, self.grpname, subgroupof]})
						break
				i = i + 1
				accountname = "India Bank" + str(i)

		print "no of accounts created: ", i - 1

	def teardown(self):
		for accountcode in self.demoaccountcode.keys():
			gkdata={"accountcode": accountcode}
			result = requests.delete("http://127.0.0.1:6543/accounts",data =json.dumps(gkdata), headers=self.header)
