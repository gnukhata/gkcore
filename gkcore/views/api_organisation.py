from cornice.resource import resource, view 
from gkcore import eng
from gkcore.models import gkdb
from sqlalchemy.sql import select
import json 
from sqlalchemy.engine.base import Connection
con = Connection
con = eng.connect()

@resource(collection_path='/organisation',path='/organisation/{name}')
class api_organisation(object):
	def __init__(self,request):
		self.request = request

	def collection_get(self):
		result = con.execute(select([gkdb.organisation.c.orgcode, gkdb.organisation.c.orgname, gkdb.organisation.c.orgtype]))
		orgs = []
		for row in result:
			orgs.append({"orgcode":row["orgcode"], "orgname":row["orgname"], "orgtype":row["orgtype"]	})
		print orgs
		return orgs
		
	@view(renderer='json', accept='text/json')
	def collection_post(self):
		result = self.request.json_body
		con.execute(gkdb.organisation.insert(),[result])

		print result
		return True