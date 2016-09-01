import requests, json
from nose.tools import with_setup

key = ""
def my_setup_function():
	pass

def my_teardown_function():
	global key
	header={"gktoken":key}
	result = requests.delete("http://127.0.0.1:6543/organisations", headers=header)

def test_organisations_exists():
	result = requests.get("http://127.0.0.1:6543/organisations")
	assert result.json()["gkstatus"] == 0

@with_setup(my_setup_function,my_teardown_function)
def test_create_organisation():
	orgdata = {"orgdetails":{'orgname': 'Test Organisation', 'yearend': '2016-03-31', 'yearstart': '2015-04-01', 'orgtype': 'Profit Making'}, "userdetails":{"username":"admin", "userpassword":"admin","userquestion":"who am i?", "useranswer":"hacker"}}
	result = requests.post("http://127.0.0.1:6543/organisations", data =json.dumps(orgdata))
	global key
	key = result.json()["token"]
	assert result.json()["gkstatus"] == 0
