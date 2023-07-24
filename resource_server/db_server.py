from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from auth import verify_access_token
import jwt
#import ssl

#API_KEY = "TopSecretAPIKey"
ISSUER = 'sample-auth-server'
with open('public.pem', 'rb') as f:
    public_key = f.read()

app = Flask(__name__)

##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = "SECRET_KEY"


# Todo TABLE Configuration
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, nullable=False)
    todo = db.Column(db.String(50), nullable=False)
    due = db.Column(db.String(10), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


def get_uid(access_token):
    decoded_token = jwt.decode(access_token, public_key, issuer=ISSUER, algorithms='RS256')
    return decoded_token["uid"]


@app.route("/todos")
def get_todos():
    print("db_server - route /todos")
    access_token = request.args.get("access_token")
    if not verify_access_token(access_token):
        return jsonify(result={'msg': 'nok, issue with access token', 'status': '403'})
    uid = int(get_uid(access_token))
    print(f"uid: {uid} access_token: {access_token}")
    try:
        todos = db.session.query(Todo).filter_by(uid=uid).order_by(Todo.due.asc())
    except:
        return jsonify(result={'msg': 'nok, get todos failed', 'status': '500'})
    return jsonify(todos=[todo.to_dict() for todo in todos], result={'msg': 'ok', 'status': '200'})


## HTTP POST - Create Record
@app.route("/todo", methods=["POST"])
def create_todo():
    print("db_server - route /todo - POST (create)")
    access_token = request.args.get("access_token")
    if not verify_access_token(access_token):
        return jsonify(result={'msg': 'nok, issue with access token', 'status': '403'})
    uid = get_uid(access_token)
    new_todo = Todo(
        todo=request.args.get("todo"),
        due=request.args.get("due"),
        uid=uid
    )
    try:
        db.session.add(new_todo)
        db.session.commit()
    except:
        return jsonify(result={'msg': 'nok, creation failed', 'status': '500'})
    return jsonify(result={'msg': 'ok, creation succeeded', 'status': '200'})


## HTTP PUT - Update Record
@app.route("/todo/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    print("db_server - route /todo - PUT (update)")
    print(f"Update record - todo_id: {todo_id}")
    access_token = request.args.get("access_token")
    if not verify_access_token(access_token):
        return jsonify(result={'msg': 'nok, issue with access token', 'status': '403'})
    uid = get_uid(access_token)
    todo = db.session.query(Todo).filter_by(id=todo_id).first()
    print(f"uid: {uid}, todo.id: {todo.id}, todo.uid: {todo.uid}")

    if todo.uid == uid:
        todo.todo = request.args.get("todo_todo")
        if request.args.get("todo_due"):
            todo.due = request.args.get("todo_due")
        try:
            db.session.commit()
            return jsonify(result={'msg': 'ok, todo updated', 'status': '200'})
        except:
            return jsonify(result={'msg': 'nok, update failed', 'status': '500'})
    return jsonify(result={'msg': 'nok, update not authorised', 'status': '403'})


## HTTP DELETE - Delete Record
@app.route("/todo/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    print("db_server - route /todo - DELETE (delete)")
    access_token = request.args.get("access_token")
    if not verify_access_token(access_token):
        return jsonify(result={'msg': 'nok, issue with access token', 'status': '403'})
    uid = get_uid(access_token)
    todo = db.session.query(Todo).filter_by(id=todo_id).first()

    if todo.uid == uid:
        try:
            db.session.delete(todo)
            db.session.commit()
            return jsonify(result={'msg': 'ok, todo deleted', 'status': '200'})
        except:
            return jsonify(result={'msg': 'nok, delete failed', 'status': '500'})
    return jsonify(result={'msg': 'nok, delete not authorised', 'status': '403'})


if __name__ == '__main__':
  #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
  #context.load_cert_chain('domain.crt', 'domain.key')
  #app.run(port = 5000, debug = True, ssl_context = context)
  app.run(port=5002, debug=True)
