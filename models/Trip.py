from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship

from db.base import Base


class Trip(Base):
    __tablename__ = 'trips'
    trip_id = Column(Integer, primary_key=True)
    trip_name = Column(String, index=True)
    date_from = Column(Date)
    date_to = Column(Date)
    owner_name = Column(Integer, ForeignKey('users.username'))
    owner = relationship("User")

    def __init__(self, trip_name, date_from, date_to, owner):
        self.trip_name = trip_name
        self.date_from = date_from
        self.date_to = date_to
        self.owner = owner

    def is_owner(self, user):
        return self.owner_name == user.username

    def convert_to_json_for_user(self, participants):
        return {"trip_id": self.trip_id, "trip_name": self.trip_name,
                "date_from": str(self.date_from), "date_to": str(self.date_to),
                "participants": [p.convert_to_json() for p in participants], "owner": self.owner_name}

    def convert_to_json(self):
        return {"trip_id": self.trip_id, "trip_name": self.trip_name,
                "date_from": str(self.date_from), "date_to": str(self.date_to), "owner": self.owner_name}

    def set_new_trip_name(self, t):
        self.trip_name = t

    def __repr__(self):
        return "<Trip(id='%s', name='%s', is from='%s to ='%s')>" % (
            self.trip_id, self.trip_name, str(self.date_from), str(self.date_to))
