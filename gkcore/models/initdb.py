
from gkcore.models.meta import dbconnect, Base


meta = Base.metadata
meta.create_all(dbconnect())
