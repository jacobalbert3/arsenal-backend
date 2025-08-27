# app/models/__init__.py

from sqlalchemy import MetaData


#SQLAlchemy metadata object acting as registry for database tables
#every can now use this
metadata = MetaData()
