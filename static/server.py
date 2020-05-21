from flask import Flask, request, jsonify, url_for
from flask_restful import Resource, Api, abort

from db.database import User

app = Flask(__name__)
api = Api(app)

# class Users(Resource):
#     def get(self):
#         return {'hello': 'world'}
#     def put(self):
#         return {'hello'}
#
# api.add_resource(Users, '/<string:todo_id>')
@app.route('/api/users', methods = ['POST'])
def add_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400) # missing arguments
    if User.query.filter_by(username = username).first() is not None:
        abort(400) # existing user
    user = User(username = username)
    # user.hash_password(password)
    # db.session.add(user)
    # db.session.commit()
    return jsonify({ 'username': user.username }), 201, {'Location': url_for('get_user', id = user.id, _external = True)}

if __name__ == '__main__':
    app.run(debug=True, port=5000)