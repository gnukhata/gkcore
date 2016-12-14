import requests, json

class TestSupplier:
	@classmethod
	def setup_class(self):
		orgdata = {"orgdetails":{'orgname': 'Test Organisation', 'yearend': '2016-03-31', 'yearstart': '2015-04-01', 'orgtype': 'Profit Making', 'invflag': 1}, "userdetails":{"username":"admin", "userpassword":"admin","userquestion":"who am i?", "useranswer":"hacker"}}
		result = requests.post("http://127.0.0.1:6543/organisations",data=json.dumps(orgdata))
		print result.json()["gkstatus"]
		self.key = result.json()["token"]
		self.header={"gktoken":self.key}

	@classmethod
	def teardown_class(self):
		result = requests.delete("http://127.0.0.1:6543/organisations", headers=self.header)

	def setup(self):
		custdata = {"custname":"rahul_mahi","custaddr":"goregaon","custphone":"432123","custemail":"rahulkande@gmail.com","custfax":"FAX212345","state":"Maharashtra","custpan":"IDPAN1234","custtan":"IDTAN1234","csflag":19}
		result = requests.post("http://127.0.0.1:6543/customersupplier",data=json.dumps(custdata),headers=self.header)
		print result.json()["gkstatus"]
		result = requests.get("http://127.0.0.1:6543/customersupplier?qty=supall", headers=self.header)
		print result.json()
		for record in result.json()["gkresult"]:
			if record["custname"] == "rahul_mahi":
				self.democustid = record["custid"]
				break

	def teardown(self):
		custdata = {"custid": int(self.democustid)}
		result = requests.delete("http://127.0.0.1:6543/customersupplier", data=json.dumps(custdata), headers=self.header)

	def test_create_customer(self):
		custdata = {"custname":"sunil tamate","custaddr":"borivali, mumbai west","custphone":"432156","custemail":"suniltamate@gmail.com","custfax":"FAX334433","state":"Maharashtra","custpan":"IDPAN1235","custtan":"IDTAN1235","csflag":19}
		result = requests.post("http://127.0.0.1:6543/customersupplier", data =json.dumps(custdata),headers=self.header)
		assert result.json()["gkstatus"] == 0

	def test_delete_customer(self):
		custdata = {"custname":"sunil tamate","custaddr":"borivali, mumbai west","custphone":"432156","custemail":"suniltamate@gmail.com","custfax":"FAX334433","state":"Maharashtra","custpan":"IDPAN1235","custtan":"IDTAN1235","csflag":19}
		result = requests.get("http://127.0.0.1:6543/customersupplier?qty=supall", headers=self.header)
		for record in result.json()["gkresult"]:
			if record["custname"] == "sunil tamate":
				custid = record["custid"]
				break
		custdata1 = {"custid":int(custid)}
		result = requests.delete("http://127.0.0.1:6543/customersupplier",data =json.dumps(custdata1), headers=self.header)
		assert result.json()["gkstatus"] == 0

	def test_get_single_customer(self):
		result = requests.get("http://127.0.0.1:6543/customersupplier?qty=single&custid=%d"%(int(self.democustid)), headers=self.header)
		assert result.json()["gkresult"]["custname"]=="rahul_mahi" and result.json()["gkresult"]["custemail"] == "rahulkande@gmail.com"

	def test_update_customer(self):
		custdata = {"custname":"rahul mande","custaddr":"goregaon, mumbai west","custphone":"023524","custemail":"rahulmande@gmail.com","custfax":"FAX212345","state":"Maharashtra","custpan":"IDPAN1234","custtan":"IDTAN1234","csflag":19, "custid": int(self.democustid)}
		result = requests.put("http://127.0.0.1:6543/customersupplier",data=json.dumps(custdata),headers=self.header)
		assert result.json()["gkstatus"] == 0

	def test_get_all_suppliers(self):
		result = requests.get("http://127.0.0.1:6543/customersupplier?qty=supall", headers=self.header)
		assert result.json()["gkstatus"] == 0
