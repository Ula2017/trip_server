from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker2

from model.User import User
from base import Session
# engine = create_engine("sqlite:///trip_communicator.db")
# Session = sessionmaker(bind=engine)


sessionmaker2 = Session()
# user1 = User("aala", "test")
# sessionmaker2.add(user1)
# user2 = User("ela", "password")
# sessionmaker2.add(user1)
# sessionmaker2.add(user2)
movies = sessionmaker2.query(User).all()
print('\n### All movies:')
for movie in movies:
    print(f'{movie.user_id} was released on {movie.username} {movie.password_hash}')
    test1 = movie.verify_password("test")
    test2= movie.verify_password("test2")
    print(test1)
    print(test2)
sessionmaker2.commit()
sessionmaker2.close()