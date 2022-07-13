from pyramid.view import view_config, view_defaults


@view_defaults(route_name="index")
class api_state(object):
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET", renderer="json")
    def main(self):
        return {"gkstatus": 0, "msg": "gkcore is running!"}
