from pyramid.request import Request
from pyramid.view import view_defaults, view_config
import requests

@view_defaults(route_name="ifsc")
class validate_ifsc(object):
    def __init__(self, request):
        self.request = Request
        self.request = request

    @view_config(request_method="GET", request_param="check", renderer="json")
    def validateIFSC(self):
        server = "http://localhost:3000"
        ifsc_code = self.request.params["check"]
        api_response = requests.get(f"{server}/{ifsc_code}")
        result = {"is_valid": "false"}
        if api_response.status_code == 200:
            result["is_valid"] = "true"
            result["gkresult"] = api_response.json()
        return result
