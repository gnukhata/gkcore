import requests, json
from nose.tools import with_setup

class TestOrganistaion:
	@classmethod
	def setup_class(cls):
		orgdata = {"orgdetails":{'orgname': 'Class Test Organisation', 'yearend': '2016-03-31', 'yearstart': '2015-04-01', 'orgtype': 'Not For Profit'}, "userdetails":{"username":"admin", "userpassword":"admin","userquestion":"who am i?", "useranswer":"hacker"}}
		result = requests.post("http://127.0.0.1:6543/organisations", data =json.dumps(orgdata))
		cls.header = {"gktoken":result.json()["token"]}

	@classmethod
	def teardown_class(cls):
		result = requests.delete("http://127.0.0.1:6543/organisations", headers=cls.header)

	def test_organisations_list(self):
		result = requests.get("http://127.0.0.1:6543/organisations")
		assert result.json()["gkstatus"] == 0

	def test_create_delete_organisation(self):
		orgdata = {"orgdetails":{'orgname': 'Test Organisation', 'yearend': '2016-03-31', 'yearstart': '2015-04-01', 'orgtype': 'Profit Making'}, "userdetails":{"username":"admin", "userpassword":"admin","userquestion":"who am i?", "useranswer":"hacker"}}
		result = requests.post("http://127.0.0.1:6543/organisations", data =json.dumps(orgdata))
		header={"gktoken":result.json()["token"]}
		result1 = requests.delete("http://127.0.0.1:6543/organisations", headers=header)
		assert result.json()["gkstatus"] == 0 and result1.json()["gkstatus"] == 0

	def test_edit_organisation_details(self):
		gkdata= {"orgcity":"Mumbai","orgaddr":"A-63, Some address","orgpincode":"123456","orgstate":"Maharashtra", "orgcountry":"India","orgtelno":"1234567890", "orgfax":"123456789","orgwebsite":"www.dff.org.in","orgemail":"dff@dff.org.in","orgpan":"54s5AS45","orgmvat":"some vat","orgstax":"","orgregno":"","orgregdate":"", "orgfcrano":"","orgfcradate":""}
		result = requests.put("http://127.0.0.1:6543/organisations", headers=self.header, data=json.dumps(gkdata))
		assert result.json()["gkstatus"] == 0

	def test_get_financial_years_orgcode(self):
		result = requests.get("http://127.0.0.1:6543/orgyears/Class Test Organisation/Not For Profit")
		assert result.json()["gkstatus"] == 0

	def test_get_organisations_details(self):
		result = requests.get("http://127.0.0.1:6543/organisation", headers=self.header)
		details = result.json()["gkdata"]
		assert result.json()["gkstatus"] == 0 and details["orgcity"] == "Mumbai"

	def test_organisations_exists(self):
		duplicate_result = requests.get("http://127.0.0.1:6543/organisations?type=exists&orgname=Class Test Organisation&orgtype=Not For Profit&finstart=2015-04-01&finend=2016-03-31")
		unique_result = requests.get("http://127.0.0.1:6543/organisations?type=exists&orgname=Class Test Organisation&orgtype=Profit Making&finstart=2015-04-01&finend=2016-03-31")
		assert duplicate_result.json()["gkstatus"] == 1 and unique_result.json()["gkstatus"] == 0

	def test_organisations_getorgcode(self):
		result = requests.get("http://127.0.0.1:6543/organisations?orgcode", headers=self.header)
		assert result.json()["gkstatus"] == 0
