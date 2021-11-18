from pyramid.request import Request
from gkcore import enumdict
from pyramid.view import view_defaults, view_config
# from gkcore.views.api_login import authCheck
import requests, os

@view_defaults(route_name="ifsc")
class IFSC(object):
    def __init__(self, request):
        self.request = Request
        self.request = request

    @view_config(request_method="GET", request_param="check", renderer="json")
    def validate_ifsc(self):
        """
        Validate provided IFSC code

        This method first checks the user auth status, Then validates given
        ifsc code with the razorpay/ifsc docker server & get's the response
        """
        # try:
        #     token = self.request.headers["gktoken"]
        # except:
        #     return {"gkstatus": enumdict["UnauthorisedAccess"]}

        # auth_details = authCheck(token)

        # if auth_details["auth"] == False:
        #     return {"gkstatus": enumdict["UnauthorisedAccess"]}

        ifsc_server = "http://127.0.0.1:6545"

        # check for custom IFSC server URL & set it when provided
        # custom_ifsc_server = os.getenv('GKCORE_IFSC_SERVER')

        # if custom_ifsc_server != None:
        #     ifsc_server = custom_ifsc_server

        ifsc_code = self.request.params["check"]
        api_response = requests.get(f"{ifsc_server}/{ifsc_code}")
        result = {"gkstatus": enumdict['ConnectionFailed']}

        if api_response.status_code == 200:
            result["gkstatus"] = enumdict['Success']
            result["gkresult"] = api_response.json()
        return result
