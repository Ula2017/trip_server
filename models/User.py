from sqlalchemy import Column, String
from passlib.apps import custom_app_context as pwd_context

from db.base import Base


class User(Base):
    __tablename__ = 'users'
    username = Column(String, index=True, primary_key=True, nullable=False)
    password_hash = Column(String, nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.hash_password(password)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def convert_to_json(self):
        return {"username": self.username}

    def __repr__(self):
        return "<User( name='%s', password='%s')>" % (self.username, self.password_hash)
