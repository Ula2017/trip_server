from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref

from base import Base


class Trip(Base):
    __tablename__ = 'trips'
    trip_id = Column(Integer, primary_key=True)
    trip_name = Column(String, index=True)
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    owner_id = Column(Integer, ForeignKey('users.user_id'))
    owner = relationship("User", backref="trips")

    def __init__(self, trip_name, date_from, date_to, owner_id):
        self.trip_name=trip_name
        self.date_from=date_from
        self.date_to=date_to
        self.owner_id=owner_id

    # def __repr__(self):
    #     return "<User(id='%s', name='%s', password='%s')>" % ( self.id, self.username, self.password_hash)
