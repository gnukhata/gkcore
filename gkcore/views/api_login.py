

#login function
from gkcore import eng
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json 
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result

con= Connection
con= eng.connect()

@view_config(route_name='login',request_method='post',renderer='json')
def gkLogin(request):
	dataset = request.json_body
	result = con.execute(select([gkdb.users.c.userid,gkdb.users.c.userrole]).where(gkdb.users.c.username==dataset["username"] and gkdb.users.c.userpassword== dataset["userpassword"] and gkdb.users.c.orgcode==dataset["orgcode"]) )
	if result.rowcount == 1:
		record = result.fetchone()
		return {"status":"ok","token":request.create_jwt_token({"orgcode":dataset["orgcode"],"userid":record["userid"]}) }