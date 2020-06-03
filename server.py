import json
from datetime import datetime

from flask import Flask, request, jsonify, make_response
from flask_restful import Api
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

    Get all users from database
    Example: curl -i -X GET -H "Content-Type: application/json" -d http://127.0.0.1:5000/api/users
    Params: None
    Response: 
        - {'Users': <list off users>}

"""


@app.route('/api/users', methods=['GET'])
def get_users():
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    users = session.query(User).all()
    r = [u.convert_to_json() for u in users]
    commit_and_close(session)
    return make_response(jsonify({'Users': r}), 201)


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


@app.route('/api/user/login', methods=['POST'])
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

    Change password for existing user. 
    Example: curl -i -X PUT -H "Content-Type: application/json" -d '{"password": 
    "korona", "new_password": "pwd"}' http://127.0.0.1:5000/api/user/iza/change-password 
    Params: new_password, password 
    
    Response:
        - {'Response': 'OK'} if password successfully changed 
        - HTTP Error 422 'Missing required parameter' - if some params is missing 
        -HTTP Error 400 Incorrect username if user doesn't exist 
        -HTTP Error 403 if user provided wrong current password 
        
"""


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

    Add new trip for user. 
    Example: curl -i -X POST -H "Content-Type: application/json" -d '{"trip_name": "test trip3", 
    "date_to": "2020-06-12", "date_from": "2020-06-10", "participants": [{"username": "ela"}, {"username": "aala"}]}'
     http://127.0.0.1:5000/api/user/ela2/create-trip 

    Params: trip_name, date_from, date_to (dates must be in format '%Y-%m-%d' -> 2020-06-12)
    Response: 
        - {'Trip id': '<trip_id>'} if trip was created successfully 
        -HTTP Error 400 Incorrect username if user doesn't exist
"""


@app.route('/api/user/<string:username>/create-trip', methods=['POST'])
def add_trip(username):
    if not request.json or ('trip_name' not in request.json or 'date_from' not in request.json
                            or 'date_to' not in request.json or 'participants' not in request.json):
        return make_response(jsonify({'error': 'Missing required parameter'}), 422)

    datetime_format = '%Y-%m-%d'  # The format
    participants = request.json.get('participants')
    date_from = datetime.strptime(request.json.get('date_from'), datetime_format).date()
    date_to = datetime.strptime(request.json.get('date_to'), datetime_format).date()
    trip_name = request.json.get('trip_name')

    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Incorrect username'}), 400)

    trip = Trip(trip_name, date_from, date_to, user)
    session.add(trip)
    session.commit()
    for p in participants:
        participant = add_participant_from_response(session, p, trip)
        if participant is not None:
            session.add(participant)
    owner_participant = Participant(user, trip)
    session.add(owner_participant)
    session.commit()
    trip_id = trip.trip_id

    session.close()
    return make_response(jsonify({'Trip id': trip_id}), 201)


"""

    Get all trips for user where the user is owner. 
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
    trips = session.query(Trip).filter(Trip.owner_name == username).all()
    participants = []
    for t in trips:
        participants.append(session.query(Participant).filter(Participant.trip_id == t.trip_id).all())

    return make_response(jsonify([trips[i].convert_to_json_for_user(participants[i]) for i in range(len(trips))]), 201)


"""

    Get all trips for user. 
    Example: curl -i -X GET -H "Content-Type: application/json" http://127.0.0.1:5000/api/user/ala/all-trips 
    Params: None
    Response: 
        - {'Trips: '<list of trip for user>'} if user exists
        -HTTP Error 400 Incorrect username if user doesn't exist
"""


@app.route('/api/user/<string:username>/all-trips', methods=['GET'])
def get_trips(username):
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Incorrect username'}), 400)
    trips_participated = session.query(Trip).join(Participant, Trip.trip_id == Participant.trip_id).\
        filter(Participant.username == username).all()

    participants = []
    for t in trips_participated:
        participants.append(session.query(Participant).filter(Participant.trip_id == t.trip_id).all())
    response = [trips_participated[i].convert_to_json_for_user(participants[i]) for i in range(len(trips_participated))]
    commit_and_close(session)
    return make_response(jsonify(response), 201)


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

    Update trip with provided new trip_name or date_to and date_form 
    Example: curl -i -X PUT -H "Content-Type: application/json" -d '{ "trip_name": "hohonewtrip"}'
     http://127.0.0.1:5000/api/user/aala/trip/1/update
     
    Params: trip_name or (date_to and date_form) 
    Response: 
    - {'Response': 'OK'} if trip was updated successfully 
    - HTTP Error 422 'Missing required parameter' - if some params is missing 
    -HTTP Error 400 Incorrect username if user doesn't exist 
    -HTTP Error 403 if user is not the owner of trip or trip doesn't exist 
    
"""


def update_participants(participants, trip, session):
    for p in participants:
        user = session.query(User).filter_by(username=p).first()

        if user is not None:
            participant = session.query(Participant).filter_by(username=user.username, trip_id=trip.trip_id).first()
            if participant is None:
                new_participant = Participant(user, trip)
                session.add(new_participant)


@app.route('/api/user/<string:username>/trip/<string:trip_id>/update', methods=['PUT'])
def update_trip(username, trip_id):
    if request.json is None:
        return make_response(jsonify({'error': 'Missing required parameter'}), 422)

    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        commit_and_close(session)
        return make_response(jsonify({'error': 'Incorrect username'}), 400)

    trip = session.query(Trip).filter_by(trip_id=trip_id).first()

    datetime_format = '%Y-%m-%d'
    isChanged = False

    if trip is not None and trip.is_owner(user):

        if 'date_from' in request.json:
            isChanged = True
            trip.date_from = datetime.strptime(request.json['date_from'], datetime_format).date()
        if 'date_to' in request.json:
            isChanged = True
            trip.date_to = datetime.strptime(request.json['date_to'], datetime_format).date()
        if 'trip_name' in request.json:
            isChanged = True
            trip.trip_name = request.json['trip_name']
        if 'participants' in request.json:
            isChanged = True
            update_participants(request.json['participants'], trip, session)
        commit_and_close(session)
        if isChanged:
            return make_response(jsonify({'Response': 'OK'}), 201)
        return make_response(jsonify({'error': 'Missing at least one required parameter'}), 422)

    return make_response(jsonify({'Response': 'User is not the owner of trip or trip doesn\'t exist'}), 403)


"""

    Return all participants of trip. 
    Example: curl -i -X GET -H "Content-Type: application/json" http://127.0.0.1:5000/api/trip/1/participants
    Params: None
    Response: 
        - {'Participants: '<list of participants for trip>'} if trip exists
        -HTTP Error 400 Incorrect trip_id, trip doesn't exist
"""


def get_user_participants(participants):
    return [p.user for p in participants]


@app.route('/api/trip/<int:trip_id>/participants', methods=['GET'])
def get_participants(trip_id):
    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    trip = session.query(Trip).filter_by(trip_id=trip_id).first()
    if trip is None:
        commit_and_close(session)
        return make_response(jsonify({'Response': 'Incorrect trip_id '}), 400)
    participants = session.query(Participant).filter_by(trip_id=trip.trip_id).all()
    commit_and_close(session)
    return make_response(jsonify({"Participants": [p.convert_to_json() for p in participants]}), 201)


"""

    Add one or more participants to the trip. Only owner can add participants
    Example:  curl -i -X POST -H "Content-Type: application/json" -d '{"participants": [{"username": "pawel"}, 
    {"username": "ela2"}]}' http://127.0.0.1:5000/api/user/aala/trip/1/add-participants

    Params:participants list
    Response: 
        - {'Response': 'OK'} if users was added successfully 
        - HTTP Error 422 'Missing required parameter' - if some params is missing 
        -HTTP Error 403 if user is not the owner of trip or trip doesn't exist

"""


def add_participant_from_response(session, json_participant, trip):
    user = session.query(User).filter_by(username=json_participant).first()
    if user is not None:
        return Participant(user, trip)
    return None


@app.route('/api/user/<string:username>/trip/<int:trip_id>/add-participants', methods=['POST'])
def add_participants(username, trip_id):
    if not request.json or 'participants' not in request.json:
        return make_response(jsonify({'error': 'Missing required parameter'}), 422)
    participants = request.json.get('participants')

    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    trip = session.query(Trip).filter(and_(Trip.trip_id == trip_id, Trip.owner_name == username)).first()
    if trip is not None:
        for p in participants:
            participant = add_participant_from_response(session, p, trip)
            if participant is not None:
                session.add(participant)

        commit_and_close(session)
        return make_response(jsonify({'Response': 'OK'}), 201)

    commit_and_close(session)
    return make_response(jsonify({'Error': 'User is not the owner of trip or trip doesn\'t exist'}), 403)


"""

    Remove one or more participants from the trip. Only owner can remove participants
    Example:  
         curl -i -X DELETE -H "Content-Type: application/json" -d '{"participants": [{"username": "pawel"}, 
         {"username": "elaaa2"}]}' http://127.0.0.1:5000/api/user/aala/trip/1/delete-participants

    Params:participants list
    Response: 
        - {'Response': 'OK'} if users was deleted successfully 
        - HTTP Error 422 'Missing required parameter' - if some params is missing 
        -HTTP Error 403 if user is not the owner of trip or trip doesn't exist 

"""


@app.route('/api/user/<string:username>/trip/<int:trip_id>/delete-participants', methods=['DELETE'])
def delete_participants(username, trip_id):
    if not request.json or 'participants' not in request.json:
        return make_response(jsonify({'error': 'Missing required parameter'}), 422)
    participants = request.json.get('participants')

    e = create_engine("sqlite:///trip_communicator.db")
    Ses = sessionmaker(bind=e)
    session = Ses()

    trip = session.query(Trip).filter(and_(Trip.trip_id == trip_id, Trip.owner_name == username)).first()
    if trip is not None:
        for p in participants:
            session.query(Participant).filter(
                and_(Participant.username == p, Participant.trip_id == trip_id)).delete()
        commit_and_close(session)
        return make_response(jsonify({'Response': 'OK'}), 201)
    commit_and_close(session)
    return make_response(jsonify({'Error': 'User is not the owner of trip or trip doesn\'t exist'}), 403)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
