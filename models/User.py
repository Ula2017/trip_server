from sqlalchemy import Column, Integer, String
from passlib.apps import custom_app_context as pwd_context

from db.base import Base


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, index=True, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.hash_password(password)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return "<User(id='%s', name='%s', password='%s')>" % (self.id, self.username, self.password_hash)


