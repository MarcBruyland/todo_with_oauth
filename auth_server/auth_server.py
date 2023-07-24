import json
#import ssl


from auth import (authenticate_client, retrieve_user_data,
                  generate_access_token, generate_authorization_code, 
                  verify_authorization_code, verify_client_info,
                  JWT_LIFE_SPAN)
from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
import urllib.parse as urlparse
from urllib.parse import urlencode
from flask_bootstrap import Bootstrap
from forms import LoginForm
import os
import bcrypt       # hash password

app = Flask(__name__)
bootstrap = Bootstrap(app)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY #needed for form.csrf

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = "SECRET_KEY"


# User TABLE Configuration
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


def authenticate_user_credentials(email, password):
    user_from_db = db.session.query(User).filter_by(email=email).first()
    if user_from_db and bcrypt.checkpw(password.encode('utf8'), user_from_db.password):
        return user_from_db.id
    else:
        return -1


# def process_redirect_url(url, authorization_code):
#     # Prepare the redirect URL
#     url_parts = list(urlparse.urlparse(url))
#     queries = dict(urlparse.parse_qsl(url_parts[4]))
#     queries.update({ "authorization_code": authorization_code })
#     url_parts[4] = urlencode(queries)
#     url = urlparse.urlunparse(url_parts)
#     return url


def insert_cookie_with_authorization_code(url, authorization_code):
    # Prepare the redirect URL
    url_parts = list(urlparse.urlparse(url))
    queries = dict(urlparse.parse_qsl(url_parts[4]))
    queries.update({"authorization_code": authorization_code})
    url_parts[4] = urlencode(queries)
    url = urlparse.urlunparse(url_parts)
    return url


@app.route('/auth')
def auth():
    # Describe the access request of the client and ask user for approval
    print("auth_server - route /auth")
    client_id = request.args.get('client_id')
    redirect_url = request.args.get('redirect_url')

    if None in [client_id, redirect_url]:
        return json.dumps({
          "error": "invalid_request"
        }), 400

    if not verify_client_info(client_id, redirect_url):
        return json.dumps({
          "error": "invalid_client"
        })

    form = LoginForm()
    return render_template('login.html', client_id=client_id, redirect_url=redirect_url, form=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    print("auth_server - route /login")
    form = LoginForm()
    if form.validate_on_submit():
        client_id = form.client_id.data
        redirect_url = form.redirect_url.data
        if not verify_client_info(client_id, redirect_url):
            return json.dumps({
                "error": "invalid_client"
            })

        email = form.email.data
        password = form.password.data
        uid = authenticate_user_credentials(email, password)
        if uid == -1:
            error_msg = "invalid user credentials"
            return render_template('login.html',
                                   client_id=client_id,
                                   redirect_url=redirect_url,
                                   form=form, msg=error_msg)
        else:
            authorization_code = generate_authorization_code(client_id, redirect_url, uid, email)
            url = insert_cookie_with_authorization_code(redirect_url, authorization_code)
            return redirect(url)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    print("auth_server - route /signup")
    error_msg = ""
    form = LoginForm()
    if form.validate_on_submit():
        new_user = User(
            email=form.email.data,
            password=bcrypt.hashpw(form.password.data.encode('utf8'), bcrypt.gensalt())
        )
        client_id = form.client_id.data
        redirect_url = form.redirect_url.data
        if db.session.query(User.id).filter_by(email=form.email.data).first() is None:
            db.session.add(new_user)
            db.session.commit()
            db.session.refresh(new_user)  # to get the auto-generated id from the db into our new_user object

            authorization_code = generate_authorization_code(client_id, redirect_url, new_user.id, new_user.email)
            url = insert_cookie_with_authorization_code(redirect_url, authorization_code)
            return redirect(url)
        else:
            error_msg = "User already exists"
            return render_template("signup.html", form=form, msg=error_msg, client_id=client_id, redirect_url=redirect_url)

    client_id = request.args.get('client_id')
    redirect_url = request.args.get('redirect_url')
    return render_template("signup.html", form=form, msg=error_msg, client_id=client_id, redirect_url=redirect_url)


@app.route('/token', methods=['POST'])
def exchange_for_token():
    # Issues access token
    print("auth_server - route /token")
    authorization_code = request.form.get('authorization_code')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    redirect_url = request.form.get('redirect_url')

    if None in [ authorization_code, client_id, client_secret, redirect_url ]:
        return json.dumps({
            "error": "invalid_request"
        }), 400

    if not authenticate_client(client_id, client_secret):
        return json.dumps({
            "error": "invalid_client"
        }), 400

    uid, email = retrieve_user_data(authorization_code)

    if not verify_authorization_code(authorization_code, client_id, redirect_url):
        return json.dumps({
            "error": "access_denied"
        }), 400

    access_token = generate_access_token(uid, email)
    print(f"***/token - new access_token: {access_token}, expires in {JWT_LIFE_SPAN}")
    return json.dumps({
        "access_token": access_token,
        "token_type": "JWT",
        "expires_in": JWT_LIFE_SPAN
    })

if __name__ == '__main__':
  #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
  #context.load_cert_chain('domain.crt', 'domain.key')
  #app.run(port = 5000, debug = True, ssl_context = context)
  app.run(port=5001, debug=True)