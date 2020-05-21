import importlib

from sqlalchemy import create_engine, MetaData, Table, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from model.User import User

engine = create_engine("sqlite:///trip_communicator.db")
Session = sessionmaker(bind=engine)

Base = declarative_base()
Base.metadata.create_all(engine)
session = Session()
user1 = User("ala", "test")
user2 = User("ela", "password")
session.add(user1)
session.add(user2)
session.commit()
session.close()