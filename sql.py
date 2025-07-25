from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class MyObject(Base):
    __tablename__ = 'my_objects'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(Integer)
    
    
engine = create_engine("sqlite:///mydb.sqlite3")
Session = sessionmaker(bind=engine)