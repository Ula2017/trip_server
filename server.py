import json
from datetime import datetime

from flask import Flask, request, jsonify, url_for, make_response
from flask_restful import Resource, Api, abort
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import and_

from db.database import commit_and_close
from models.Participant import Participant
from models.Trip import Trip
from models.User import User

app = Flask(__name__)
api = Api(app)


@app.errorhandler(422)
def not_found():
    return make_response(jsonify({'error': 'Missing required parameter'}), 422)


@app.errorhandler(400)
def not_found():
    return make_response(jsonify({'error': 'Bad Request'}), 400)


"""

    Adding user to database, username need to be unique
    Example: curl -i -X POST -H "Content-Type: application/json" -d '{"username": "iza", "password": "korona"}' 
    http://127.0.0.1:5000/api/user/create
    Params: username, password
    Response: 
        - username if user created successfully {"username":"iza"}
        - HTTP Error 422 'Missing required parameter' - if some params is missing
        - HTTP Error 400 ' Bad request' if username exists
"""


@app.route('/api/user/create', methods=['POST'])
def add_user():
    if not request.json or ('username' not in request.json or 'password' not in request.json):
        return make_response(jsonify({'error': 'Missing required parameter'}), 422)
    username = request.json.get('username')
    password = request.json.get('password')

    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    if session.query(User).filter_by(username=username).first() is not None:
        commit_and_close(session)
        return make_response(jsonify({'error': 'Bad Request'}), 400)
    user = User(username, password)
    session.add(user)
    commit_and_close(session)

    return make_response(jsonify({'username': username}), 201)


"""

    Authenticate user with password
    Example: curl -i -X GET -H "Content-Type: application/json" -d '{"username": "iza", "password": "korona"}' 
    http://127.0.0.1:5000/api/user/login
    Params: username, password
    Response: 
        - {'Response': 'OK'} if password is correct
        - HTTP Error 422 'Missing required parameter' - if some params is missing
        -HTTP Error 401  'Unauthorized' - if password is incorrect
        - HTTP Error 400 ' Bad request' if username doesn't exist
"""


@app.route('/api/user/login', methods=['GET'])
def authenticate_user():
    if not request.json or ('username' not in request.json or 'password' not in request.json):
        return make_response(jsonify({'error': 'Missing required parameter'}), 422)

    username = request.json.get('username')
    password = request.json.get('password')

    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'error': 'Bad Request'}), 400)
    if not user.verify_password(password):
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Wrong password'}), 401)
    commit_and_close(session)
    return make_response(jsonify({'Response': 'OK'}), 201)


"""

    Join existing trip chat. You need to be participant to join trip chat
    Example: curl -i -X GET -H "Content-Type: application/json" http://127.0.0.1:5000/api/user/ala/join-chat/6
    Params: None
    Response: 
        - {'Response': 'OK'} if user can join chat
        - HTTP Error 422 'Missing required parameter' - if some params is missing
        -HTTP Error 403  if user can not join chat
"""


@app.route('/api/user/<string:username>/join-chat/<int:trip_id>', methods=['GET'])
def join_chat(username, trip_id):
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    participant = session.query(Participant).filter(
        and_(Participant.trip_id == trip_id, Participant.username == username)).first()
    owner = session.query(Trip).filter(
        and_(Trip.trip_id == trip_id, Trip.owner_name == username)).first()

    if participant is None and owner is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Can not join to this chat'}), 403)

    return make_response(jsonify({'Response': 'OK'}), 201)


"""

    Change password for existing user. Example: curl -i -X PUT -H "Content-Type: application/json" -d '{"password": 
    "korona", "new_password": "pwd"}' http://127.0.0.1:5000/api/user/iza/change-password Params: new_password,
    password Response: - {'Response': 'OK'} if password successfully changed - HTTP Error 422 'Missing required 
    parameter' - if some params is missing -HTTP Error 400 Incorrect username if user doesn't exist -HTTP Error 403 
    if user provided wrong current password """


@app.route('/api/user/<string:username>/change-password', methods=['PUT'])
def change_password(username):
    if not request.json or ('new_password' not in request.json or 'password' not in request.json):
        return make_response(jsonify({'error': 'Missing required parameter'}), 422)

    current_password = request.json.get('password')
    new_password = request.json.get('new_password')

    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Incorrect username'}), 400)

    if user.verify_password(current_password):
        user.hash_password(new_password)
        commit_and_close(session)
        return make_response(jsonify({'Response': 'OK'}), 201)
    commit_and_close(session)
    return make_response(jsonify({'Response': 'Incorrect current password'}), 403)


"""

    Delete user and his/her dependencies
    Example: curl -i -X DELETE -H "Content-Type: application/json"  http://127.0.0.1:5000/api/user/iza/delete
    Params: None
    Response: 
        - {'Response': 'OK'} if password successfully changed
        -HTTP Error 400 Incorrect username if user doesn't exist
"""


@app.route('/api/user/<string:username>/delete', methods=['DELETE'])
def delete_user(username):
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Incorrect username'}), 400)
    trips = session.query(Trip).filter_by(owner_name=username).all()
    for trip in trips:
        session.query(Participant).filter_by(trip_id=trip.trip_id).delete()
    session.query(Trip).filter_by(owner_name=username).delete()
    session.query(User).filter_by(username=username).delete()
    session.query(Participant).filter_by(username=username).delete()

    commit_and_close(session)
    return make_response(jsonify({'Response': 'OK'}), 201)


"""

    Add new trip for user. Example: curl -i -X POST -H "Content-Type: application/json" -d '{"trip_name": "example 
    trip3", "date_to": "2020-06-12", "date_from": "2020-06-10"}' http://127.0.0.1:5000/api/user/ala/create-trip 

    Params: trip_name, date_from, date_to (dates must be in format '%Y-%m-%d' -> 2020-06-12)
    Response: 
        - {'Trip id': '<trip_id>'} if trip was created successfully 
        -HTTP Error 400 Incorrect username if user doesn't exist
"""


# datetime format example: "2020-06-12, 4:59:31"
@app.route('/api/user/<string:username>/create-trip', methods=['POST'])
def add_trip(username):
    if not request.json or (
            'trip_name' not in request.json or 'date_from' not in request.json or 'date_to' not in request.json):
        return make_response(jsonify({'error': 'Missing required parameter'}), 422)

    datetime_format = '%Y-%m-%d'  # The format
    trip_name = request.json.get('trip_name')
    date_from = datetime.strptime(request.json.get('date_from'), datetime_format)
    date_to = datetime.strptime(request.json.get('date_to'), datetime_format)

    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Incorrect username'}), 400)

    trip = Trip(trip_name, date_from, date_to, user)
    session.add(trip)
    session.flush()
    session.close()
    return make_response(jsonify({'Trip id': trip.trip_id}), 201)


"""

    Get all trips for user (user is owner). 
    Example: curl -i -X GET -H "Content-Type: application/json" http://127.0.0.1:5000/api/user/ala/trips 
    Params: None
    Response: 
        - {'Trips: '<list of trip for user>'} if user exists
        -HTTP Error 400 Incorrect username if user doesn't exist
"""


@app.route('/api/user/<string:username>/trips', methods=['GET'])
def get_user_trips(username):
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Incorrect username'}), 400)
    # todo make trips serializable and return with json
    trips = session.query(Trip).filter(Trip.owner_name == username).all()
    print(trips)
    return make_response(jsonify({'Trip': 'OK'}), 201)


"""

    Remove trip for specified trip_id.
    Example: curl -i -X DELETE -H "Content-Type: application/json" http://127.0.0.1:5000/api/user/ala/trip/10/delete
    Params: None
    Response: 
        - {'Response': 'OK'} if trip was removed successfully 
        -HTTP Error 400 Incorrect username if user doesn't exist
        -HTTP Error 403 if user isn't owner of trip so can't remove trip
"""


@app.route('/api/user/<string:username>/trip/<string:trip_id>/delete', methods=['DELETE'])
def delete_trip(username, trip_id):
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Incorrect username'}), 400)
    trip = session.query(Trip).filter_by(trip_id=trip_id).first()

    if trip is not None and trip.is_owner(user):
        session.query(Trip).filter_by(trip_id=trip_id).delete()
        session.query(Participant).filter_by(trip_id=trip_id).delete()
        commit_and_close(session)
        return make_response(jsonify({'Response': 'OK'}), 201)
    else:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'User is not the owner of trip or trip doesn\'t exist'}), 403)


"""

    Update trip with provided new tripname or date_to and date_form 
    Example: curl -i -X PUT -H "Content-Type: application/json" -d '{ "trip_name": "hohonewtrip"}'
     http://127.0.0.1:5000/api/user/aala/trip/1/update
     
    Params: tripname or (date_to and date_form) 
    Response: - {
    'Response': 'OK'} if trip was updated successfully - HTTP Error 422 'Missing required parameter' - if some params 
    is missing -HTTP Error 400 Incorrect username if user doesn't exist -HTTP Error 403 if user is not the owner of 
    trip or trip doesn't exist """


def change_tripname(username, trip_id, trip_name):
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'error': 'Incorrect username'}), 400)
    trip = session.query(Trip).filter_by(trip_id=trip_id).first()
    if trip is not None and trip.is_owner(user):
        session.query(Trip).filter(Trip.trip_id == trip_id). \
            update({"trip_name": trip_name})
        commit_and_close(session)
        return make_response(jsonify({'Response': 'OK'}), 201)

    commit_and_close(session)
    return make_response(jsonify({'Response': 'User is not the owner of trip or trip doesn\'t exist'}), 403)


def change_trip_dates(username, trip_id, date_from, date_to):
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    datetime_format = '%Y-%m-%d'  # The format
    dtf = datetime.strptime(date_from, datetime_format)
    dtt = datetime.strptime(date_to, datetime_format)

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'error': 'Incorrect username'}), 400)

    trip = session.query(Trip).filter_by(trip_id=trip_id).first()
    if trip is not None and trip.is_owner(user):
        session.query(Trip).filter(Trip.trip_id == trip_id). \
            update({"date_from": dtf, "date_to": dtt})
        commit_and_close(session)
        return make_response(jsonify({'Response': 'OK'}), 201)

    commit_and_close(session)
    return make_response(jsonify({'Response': 'User is not the owner of trip or trip doesn\'t exist'}), 403)


@app.route('/api/user/<string:username>/trip/<string:trip_id>/update', methods=['PUT'])
def update_trip(username, trip_id):
    if request.json and 'trip_name' in request.json:
        return change_tripname(username, trip_id, request.json.get('trip_name'))
    elif request.json and 'date_from' in request.json and 'date_to' in request.json:
        return change_trip_dates(username, trip_id, request.json.get('date_from'), request.json.get('date_to'))
    else:
        return make_response(jsonify({'error': 'Missing required parameter'}), 422)


"""

    Return all participants of trip. 
    Example: curl -i -X GET -H "Content-Type: application/json" http://127.0.0.1:5000/api/trip/1/participants
    Params: None
    Response: 
        - {'Participants: '<list of participants for trip>'} if trip exists
        -HTTP Error 400 Incorrect trip_id, trip doesn't exist
"""


@app.route('/api/trip/<int:trip_id>/participants', methods=['GET'])
def get_participants(trip_id):

    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    trip = session.query(Trip).filter_by(trip_id=trip_id).first()
    if trip is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Incorrect trip_id'}), 400)
    participants = session.query(Participant).filter_by(trip_id=trip.trip_id).all()
    participants.append(trip.owner)
    print(participants)
    commit_and_close(session)
    # todo serialization
    return make_response(jsonify({'Participants': 'OK'}), 201)


#  todo need to rewrite 2 method below
@app.route('/api/add_participants', methods=['POST'])
def add_participants():
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()
    trip_id = request.json.get('trip_id')
    owner_name = request.json.get('owner_name')
    participants = request.json.get('participants')
    trip = session.query(Trip).filter(and_(Trip.trip_id == trip_id, Trip.owner_name == owner_name)).first()
    print(trip)
    if trip is not None:
        print("can add participants")
        for p in participants:
            user = session.query(User).filter_by(username=p["username"]).first()
            participant = Participant(user, trip)
            session.add(participant)

        commit_and_close(session)
        return {'hello': 'updated added'}

    commit_and_close(session)
    return {'hello': 'update not ok'}


@app.route('/api/delete_participants', methods=['DELETE'])
def delete_participants():
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()
    trip_id = request.json.get('trip_id')
    owner_name = request.json.get('owner_name')
    participants = request.json.get('participants')
    trip = session.query(Trip).filter(and_(Trip.trip_id == trip_id, Trip.owner_name == owner_name)).first()
    print(trip)
    if trip is not None:
        print("can be removed participants")
        for p in participants:
            session.query(Participant).filter(
                and_(Participant.username == p["username"], Participant.trip_id == trip_id)).delete()
        commit_and_close(session)
        return {'hello': 'delete ok'}

    commit_and_close(session)
    return {'hello': 'update not ok'}


if __name__ == '__main__':
    app.run(debug=True, port=5000)
