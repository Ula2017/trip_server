from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base, engine, Session
from models.Participant import Participant
from models.Trip import Trip
from models.User import User


def run_database():
    e = create_engine("sqlite:///../trip_communicator.db")
    Ses = sessionmaker(bind=engine)
    return e, Ses


def commit_and_close(session):
    session.commit()
    session.close()


def prepare_database():
    Base.metadata.create_all(engine)
    session = Session()
    commit_and_close(session)


def add_initial_values():
    _, Ses = run_database()
    session = Ses()

    user1 = User("aala", "test")
    user2 = User("ela", "password")
    user3 = User("ala", "test")
    user4 = User("ela2", "kot")

    session.add(user1)
    session.add(user2)
    session.add(user3)
    session.add(user4)

    trip = [Trip("Paris", date(2020, 6, 5), date(2020, 6, 10), user1),
            Trip("Warsaw", date(2020, 5, 30), date(2020, 6, 7), user1),
            Trip("Cracow", date(2020, 7, 10), date(2020, 7, 12), user2),
            Trip("Brussels", date(2020, 6, 11), date(2020, 6, 13), user2),
            Trip("Warsaw", date(2020, 6, 15), date(2020, 6, 20), user3),
            Trip("Liverpool", date(2020, 8, 10), date(2020, 8, 15), user3),
            Trip("Malta", date(2020, 6, 5), date(2020, 6, 7), user3),
            Trip("London", date(2020, 6, 9), date(2020, 6, 10), user3)]

    for t in trip:
        session.add(t)

    participants = [Participant(user1, trip[2]), Participant(user4, trip[3]), Participant(user3, trip[2]),
                    Participant(user2, trip[0]), Participant(user4, trip[0]), Participant(user2, trip[1]),
                    Participant(user4, trip[1]),
                    Participant(user3, trip[1])]

    for p in participants:
        session.add(p)

    commit_and_close(session)


def test_queries():
    _, Ses = run_database()
    session = Ses()
    users = session.query(User).all()
    print('\n### All users:')
    for u in users:
        print(f'User name: {u.username} , user hashed password: {u.password_hash}')

    trips = session.query(Trip).all()
    print('\n### All trips:')
    for t in trips:
        print(f'Trip id: {t.trip_id} , trip name: {t.trip_name} , owner: {t.owner.username}')

    trips_june = session.query(Trip).filter(Trip.date_from.between(date(2020, 6, 1), date(2020, 6, 30))).all()
    print('\n### All trips starting in June:')
    for t in trips_june:
        print(f'Trip id: {t.trip_id} , trip name: {t.trip_name} , owner: {t.owner.username}, start_date: {t.date_from}')

    trips_ala = session.query(Trip).join(User, Trip.owner).filter(User.username == 'ala').all()
    print('\n### All Ala\'s trips:')
    for t in trips_ala:
        print(f'Trip id: {t.trip_id} , trip name: {t.trip_name} , owner: {t.owner.username}')
    trip_part = session.query(Participant).all()
    print('\n### Participants:')
    for t in trip_part:
        print(f'Participant: {t}')
    trip_participants = session.query(Participant).filter(Participant.trip_id == '1').all()
    print('\n### Participants for trip 1:')
    for t in trip_participants:
        print(f'Participant: {t.user.username}')

    commit_and_close(session)


if __name__ == '__main__':
    # prepare_database()
    # add_initial_values()
    test_queries()
