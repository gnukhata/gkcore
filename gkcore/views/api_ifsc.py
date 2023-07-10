from pyramid.request import Request
from gkcore import enumdict
from pyramid.view import view_defaults, view_config
from gkcore.utils import authCheck
import requests, os, pathlib, csv


@view_defaults(route_name="ifsc")
class api_ifsc(object):
    def __init__(self, request):
        self.request = Request
        self.request = request

    def read_ifsc():
        """Read IFSC.csv"""
        try:
            gkcore_root = pathlib.Path("./././").resolve()
            print(gkcore_root)
            with open(f"{gkcore_root}/static/IFSC.csv", "r") as f:
                hsn_array = csv.reader(f)
            return hsn_array

        except Exception as e:
            print(e)
            raise e

    @view_config(request_method="GET", request_param="check", renderer="json")
    def validate_ifsc(self):
        """
        Validate provided IFSC code

        This method first checks the user auth status, Then validates given
        ifsc code with the razorpay/ifsc docker server & get's the response
        """
        # Check whether the user is registered & valid
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        auth_details = authCheck(token)

        if auth_details["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        ifsc_server = "http://ifsc-server:3000"

        # check for custom IFSC server URL & set it when provided
        custom_ifsc_server = os.getenv("GKCORE_IFSC_SERVER")

        if custom_ifsc_server != None:
            ifsc_server = custom_ifsc_server

        # grab the ifsc code provided in api params
        ifsc_code = self.request.params["check"]

        # validate the ifsc with razorpay ifsc server & return appropriate response
        result = {"gkstatus": enumdict["ConnectionFailed"]}

        try:
            api_response = requests.get(url=f"{ifsc_server}/{ifsc_code}")

            if api_response.status_code == 200:
                result["gkstatus"] = enumdict["Success"]
                result["gkresult"] = api_response.json()
                return result
            else:
                result["gkstatus"] = enumdict["ConnectionFailed"]
                return result
        except:
            result["gkstatus"] = enumdict["ProxyServerError"]
            return result
