from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.engine import create_engine

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

def dbconnect():
	stmt = 'postgresql+psycopg2:///gkdata?host=/var/run/postgresql'
#now we will create an engine instance to connect to the given database.
	engine = create_engine(stmt, echo=False)
	return engine
