#-----------------------------------------------------------------------
# database.py
# Authors: Irene Kim, Jessie Wang, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------
import os
import sqlalchemy
import sqlalchemy.orm
from typing import List

#-----------------------------------------------------------------------

_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')

#-----------------------------------------------------------------------

_engine = sqlalchemy.create_engine(_DATABASE_URL)
Base = sqlalchemy.orm.declarative_base()

#-----------------------------------------------------------------------

# creates table storing professors
class Professors(Base):
    _tablename_ = 'professors'
    prof_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    email = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)

def get_profs() -> List[Professors]:
    with sqlalchemy.orm.Session(_engine) as session:
        query = session.query(Professors) # SELECT * FROM Professors
        return query.all()

#-----------------------------------------------------------------------


