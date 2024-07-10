from pyramid.view import view_config
import sys, traceback
from gkcore import enumdict


@view_config(context=Exception, renderer="json")
def exception_view(error, request):
    """To handle exceptions from views. This is a temperory solution untill a proper
    Exception handling mechanism is designed for both back end and front end.
    """
    traceback.print_exc(file=sys.stdout) # logs the exception
    if request.registry.settings.get('development'):
        return {
            "gkstatus": enumdict["ConnectionFailed"],
            "error": f"{error}"
        }
    return {
        "gkstatus": enumdict["ConnectionFailed"],
    }
