from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from db.base import Base


class Participant(Base):
    __tablename__ = 'participants'
    participant_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Integer, ForeignKey('users.username'))
    user = relationship("User", backref='participants', cascade_backrefs=False, cascade="save-update, merge, delete")
    trip_id = Column(Integer, ForeignKey('trips.trip_id'))
    trip = relationship("Trip", backref='participants', cascade_backrefs=False, cascade="save-update, merge, delete")

    def __init__(self, user, trip):
        self.user = user
        self.trip = trip

    def convert_to_json(self):
        return self.username

    def __repr__(self):
        return "<User_id='%s'is participating in trip:'%s' having id: '%s')>" % (
            self.user.username, self.trip.trip_id, self.participant_id)
