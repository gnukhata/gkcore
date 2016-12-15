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

		custdata = {"custname":"rahul kande","custaddr":"goregaon","custphone":"432123","custemail":"rahulkande@gmail.com","custfax":"FAX212345","state":"Maharashtra","custpan":"IDPAN1234","custtan":"IDTAN1234","csflag":3}
		result = requests.post("http://127.0.0.1:6543/customersupplier",data=json.dumps(custdata),headers=self.header)
		result = requests.get("http://127.0.0.1:6543/customersupplier?qty=custall", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["custname"] == "rahul kande":
				self.custid = record["custid"]
				break

	@classmethod
	def teardown_class(self):
		result = requests.delete("http://127.0.0.1:6543/organisations", headers=self.header)
