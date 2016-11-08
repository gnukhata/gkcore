
"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

  GNUKhata is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License along with GNUKhata (COPYING); if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,


Contributors:
"Krishnakant Mane" <kk@gmail.com>

"""

from gkcore import eng, enumdict
from gkcore.views.api_login import authCheck
from gkcore.models.gkdb import tax,users, organisation
from sqlalchemy.sql import select
import json
from sqlalchemy.engine.base import Connection
from sqlalchemy import and_, exc
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_defaults,  view_config
from sqlalchemy.ext.baked import Result
import gkcore
import os
from sqlalchemy.sql.functions import func
import base64

@view_defaults(route_name='backuprestore')
class api_backuprestore(object):
	def __init__(self,request):
		self.request = Request
		self.request = request
		self.con = Connection
		print "backup initialized"
		
	@view_config(request_method='GET',renderer='json',request_param='fulldb=1')
	def backupdatabase(self):
		""" This method backsup entire database with organisation.
		First it checks the user role if the user is admin then only user can do the backup					  """
		try:
			token = self.request.headers["gktoken"]
		except:
			return  {"gkstatus":  gkcore.enumdict["UnauthorisedAccess"]}

		authDetails = authCheck(token)
		if authDetails["auth"] == False:
			return  {"gkstatus":  enumdict["UnauthorisedAccess"]}
		else:
			try:
				self.con = eng.connect()
				user=self.con.execute(select([users.c.userrole]).where(users.c.userid == authDetails["userid"] ))
				userRole = user.fetchone()
				if userRole[0]==-1:
					os.system("pg_dump -a -Ft -t organisations -t groupsubgroups -t accounts -t users -t projects -t bankercon -t customerandsupplier -t categorysubcategories -t categoryspecs -t unitofmeasurement -t product -t tax -t godown -t purchaseorder -t delchal -t invoice -t dcinv -t stock -t transfernote -t discrepancynote -t vouchers -t vouchersbin  gkdata -f /tmp/gkbackup.tar")
					backupfile = open("/tmp/gkbackup.tar","r")
					
					backup_str = base64.b64encode(backupfile.read())
				   
					backupfile.close()
					return {"gkstatus":enumdict["Success"],"gkdata":backup_str}
				else:
					return {"gkstatus":  enumdict["BadPrivilege"]}
			except exc.IntegrityError:
				return {"gkstatus":enumdict["DuplicateEntry"]}
			except:
				return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			finally:
				self.con.close()
				
	@view_config(request_method='POST',renderer='json')
	def Restoredatabase(self):
		""" This method restore entire database with organisation.
		First it checks the user role if the user is admin then only user can do the backup					  """
		try:
			self.con = eng.connect()
			orgcount = self.con.execute(select([func.count(organisation.c.orgcode).label('orgcount')]))
			countrow = orgcount.fetchone()
			if int(countrow["orgcount"]) > 0:
				print "data detected"
				return {"gkstatus":enumdict["ActionDisallowed"]}

			print "about to restore "
			dataset = self.request.json_body
			datasource = dataset["datasource"]
			restore_str = base64.b64decode(datasource)
			print datasource
			restorefile = open("/tmp/restore.tar","w")
			restorefile.write(datasource)
			restorefile.close()
			os.system("pg_restore -t organisations -t groupsubgroups -t accounts -t users -t projects -t bankercon -t customerandsupplier -t categorysubcategories -t categoryspecs -t unitofmeasurement -t product -t tax -t godown -t purchaseorder -t delchal -t invoice -t dcinv -t stock -t transfernote -t discrepancynote -t vouchers -t vouchersbin --dbname=gkdata  /tmp/gkbackup.tar")
			#os.system("psql -f /tmp/restore.sql gkdata")
			return {"gkstatus":enumdict["Success"]}
		except:
			return {"gkstatus":gkcore.enumdict["ConnectionFailed"]}
			
				
			
					
