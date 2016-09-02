import requests, json
from nose import with_setup

class TestAccount(object):

    @classmethod
    def setup_class(self):
        orgdata = {"orgdetails":{'orgname': 'Test Organisation', 'yearend': '2016-03-31', 'yearstart': '2015-04-01', 'orgtype': 'Profit Making'}, "userdetails":{"username":"admin", "userpassword":"admin","userquestion":"who am i?", "useranswer":"hacker"}}
    	result = requests.post("http://127.0.0.1:6543/organisations", data =json.dumps(orgdata))
    	self.key = result.json()["token"]
        self.header={"gktoken":self.key}
        result = requests.get("http://127.0.0.1:6543/groupsubgroups", headers=self.header)
        for record in result.json()["gkresult"]:
            if record["groupname"] == "Current Assets":
                self.groupcode = record["groupcode"]
                break
        result = requests.get("http://127.0.0.1:6543/groupDetails/%s"%(self.groupcode), headers=self.header)
        for record in result.json()["gkresult"]:
            if record["subgroupname"] == "Bank":
                self.grpcode = record["groupcode"]
                break

    @classmethod
    def teardown_class(self):
        result = requests.delete("http://127.0.0.1:6543/organisations", headers=self.header)

    def setup(self):
        gkdata = {"accountname":"Bank Of India","openingbal":5,"groupcode":self.grpcode}
        result = requests.post("http://127.0.0.1:6543/accounts", data =json.dumps(gkdata),headers=self.header)
        result = requests.get("http://127.0.0.1:6543/accounts", headers=self.header)
        for record in result.json()["gkresult"]:
            if record["accountname"] == "Bank Of India":
                self.demoaccountcode = record["accountcode"]
                break

    def teardown(self):
        gkdata={"accountcode":self.demoaccountcode}
        result = requests.delete("http://127.0.0.1:6543/accounts",data =json.dumps(gkdata), headers=self.header)

    def test_create_account(self):
        gkdata = {"accountname":"State Bank Of India","openingbal":100,"groupcode":self.grpcode}
        result = requests.post("http://127.0.0.1:6543/accounts", data =json.dumps(gkdata),headers=self.header)
        assert result.json()["gkstatus"]==0

    def test_update_account(self):
        gkdata = {"accountname":"YES Bank","openingbal":6,"accountcode":self.demoaccountcode}
        result = requests.put("http://127.0.0.1:6543/accounts", data =json.dumps(gkdata),headers=self.header)
        assert result.json()["gkstatus"]==0
