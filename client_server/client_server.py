import json
#import ssl
import urllib.parse as urlparse

import requests
import jwt
from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlencode
from flask_bootstrap import Bootstrap
import os
import requests
from forms import TodoForm
from flask import (Flask, make_response, render_template, redirect, request, url_for)
from datetime import datetime

AUTH_PATH = 'http://localhost:5001/auth'
TOKEN_PATH = 'http://localhost:5001/token'
RES_PATH = 'http://localhost:5002'
REDIRECT_URL = 'http://localhost:5000/callback'

CLIENT_ID = 'sample-client-id'
CLIENT_SECRET = 'sample-client-secret'

ISSUER = 'sample-auth-server'
with open('public.pem', 'rb') as f:
    public_key = f.read()

app = Flask(__name__)
bootstrap = Bootstrap(app)

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = "SECRET_KEY"


SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY  # needed for form.csrf


def date_today():
    return datetime.today().strftime('%Y-%m-%d')


def get_user_data(access_token):
    decoded_token = jwt.decode(access_token, public_key, issuer=ISSUER, algorithms='RS256')
    return decoded_token["uid"], decoded_token["email"]


def insert_cookie_with_access_token(url, access_token):
    url_parts = list(urlparse.urlparse(url))
    queries = dict(urlparse.parse_qsl(url_parts[4]))
    queries.update({ "access_token": access_token })
    url_parts[4] = urlencode(queries)
    url = urlparse.urlunparse(url_parts)
    return url


@app.route('/')
def main():
    return redirect("/authenticate")


@app.route("/authenticate", methods=["GET"])
def authenticate():
    # render template with the link to the authorization server
    print("client_server - route /authenticate")
    return render_template("authenticate.html", dest=AUTH_PATH, client_id=CLIENT_ID, redirect_url=REDIRECT_URL)


@app.route('/callback')
def callback():
    # Accepts the authorization code and exchanges it for access token
    print("client_server - route /callback")
    authorization_code = request.args.get('authorization_code')
    print(f"***callback - authorization_code: {authorization_code}")

    if not authorization_code:
        return json.dumps({
            'error': 'No authorization code is received.'
        }), 500

    print(f"***callback - post: {TOKEN_PATH}")
    response = requests.post(TOKEN_PATH, data={
        "grant_type": "authorization_code",
        "authorization_code": authorization_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_url": REDIRECT_URL
    })
    print(f"***callback - response.status_code: {response.status_code}")
    if response.status_code != 200:
        return json.dumps({'error': 'The authorization server returns an error: \n{}'.format(response.text)}), 500

    access_token = json.loads(response.text).get('access_token')
    print(f"***callback - access_token: {access_token}")

    print(f"***callback - redirect(url_for('get_todos')): {url_for('get_todos')}")
    response = make_response(redirect(url_for('get_todos')))
    response.set_cookie('access_token', access_token)
    print(f"***callback (end)- response: {response}")
    return response


@app.route("/todos", methods=["GET"])
def get_todos():
    print("client_server - route /todos")
    access_token = request.cookies.get('access_token')
    uid, email = get_user_data(access_token)
    msg = ""
    if request.args.get("msg"):
        msg = request.args.get("msg")
    form = TodoForm(
        id=0,
        todo="",
        due=datetime.today()
    )
    todos = []
    response = requests.get(RES_PATH+"/todos", params={"access_token": access_token})
    result = response.json()["result"]
    if result["status"] == "200":
        todos = response.json()['todos']
    else:
        msg = result["msg"]
    return render_template("index.html", form=form, todos=todos, uid=uid, email=email, access_token=access_token, msg=msg)


# Create Todo
@app.route("/create", methods=["POST"])
def create_todo():
    print("client_server - route /create")
    msg = ""
    access_token = request.args.get("access_token")
    data = request.form
    todo = data["todo"]
    due = data["due"]
    response = requests.post(RES_PATH+"/todo", params={"todo": todo, "due": due, "access_token":access_token})
    result = response.json()["result"]
    print(f"result: {result}")

    if result["status"] != "200":
        msg = result["msg"]
    url = f"/todos?msg={msg}"
    url = insert_cookie_with_access_token(url, access_token)
    return redirect(url)


# Update Todo
@app.route("/update", methods=["GET", "POST"])
def update_todo():
    print("client_server - route /update")
    msg = ""
    access_token = request.args.get("access_token")
    uid, email = get_user_data(access_token)
    print(f"update_todo - uid {uid}, email: {email}")
    form = TodoForm()
    if form.validate_on_submit():
        # update the todo in the db based on the data submitted by the form
        data = request.form
        todo_id = data["id"]
        todo_todo = data["todo"]
        if data["due"]:
            todo_due = datetime.strptime(data["due"], '%Y-%m-%d').date()
        else:
            todo_due = None
        print(f"update_todo - data from form (2/2): todo_id: {todo_id}, todo_todo: {todo_todo}, todo_due:{todo_due}")

        update_url = RES_PATH+"/todo/"+str(todo_id)
        response = requests.put(update_url, params={"todo_todo": todo_todo, "todo_due": todo_due, "access_token": access_token})
        result = response.json()["result"]
        if result["status"] != "200":
            msg = result["msg"]
        url = f"/todos?msg={msg}"
        url = insert_cookie_with_access_token(url, access_token)
        return redirect(url)
    else:
        # render update.html with the content of the form fields
        todo_id = request.args.get("id")
        todo_todo = request.args.get("todo")
        todo_due = request.args.get("due")
        if todo_due:
            todo_due = datetime.strptime(todo_due, '%Y-%m-%d').date()
        form = TodoForm(
            id=todo_id,
            todo=todo_todo,
            due=todo_due
        )
        return render_template("update.html", form=form, uid=uid, email=email, access_token=access_token, msg=msg)


# Delete Todo
@app.route("/delete", methods=["GET"])
def delete_todo():
    print("client_server - route /delete")
    msg = ""
    access_token = request.args.get("access_token")
    todo_id = request.args.get("id")

    response = requests.delete(RES_PATH + "/todo/" + str(todo_id), params={"access_token": access_token})
    result = response.json()["result"]
    print(f"result: {result}")

    if result["status"] != "200":
        msg = result["msg"]
    url = f"/todos?msg={msg}"
    url = insert_cookie_with_access_token(url, access_token)
    return redirect(url)


if __name__ == "__main__":
    app.run(debug=True)
