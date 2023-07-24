import base64
import json
import jwt
import time
from cryptography.fernet import Fernet

# KEY = Fernet.generate_key()
KEY = b'YHD1m3rq3K-x6RxT1MtuGzvyLz4EWIJAEkRtBRycDHA='
f = Fernet(KEY)

CLIENT_ID = 'sample-client-id'
CLIENT_SECRET = 'sample-client-secret'
REDIRECT_URL = 'http://localhost:5000/callback'

ISSUER = 'sample-auth-server'
CODE_LIFE_SPAN = 600
JWT_LIFE_SPAN = 1800

authorization_codes = {}

with open('private.pem', 'rb') as file:
    private_key = file.read()


def authenticate_client(client_id, client_secret):
    if client_id == CLIENT_ID and client_secret == CLIENT_SECRET:
        return True
    else:
        return False


def verify_client_info(client_id, redirect_url):
    if client_id == CLIENT_ID and redirect_url == REDIRECT_URL:
        return True
    else:
        return False


def retrieve_user_data(authorization_code):
    record = authorization_codes.get(authorization_code)
    uid = record.get('uid')
    email = record.get('email')
    return uid, email


def generate_access_token(uid, email):
    payload = {
        "iss": ISSUER,
        "exp": time.time() + JWT_LIFE_SPAN,
        "uid": uid,
        "email": email
    }
    access_token = jwt.encode(payload, private_key, algorithm='RS256')
    return access_token


def generate_authorization_code(client_id, redirect_url, uid, email):
    # f = Fernet(KEY)
    authorization_code = f.encrypt(json.dumps({
        "client_id": client_id,
        "redirect_url": redirect_url
    }).encode())
    authorization_code = base64.b64encode(authorization_code, b'-_').decode().replace('=', '')
    expiration_date = time.time() + CODE_LIFE_SPAN
    authorization_codes[authorization_code] = {
        "client_id": client_id,
        "redirect_url": redirect_url,
        "exp": expiration_date,
        "uid": uid,
        "email": email
    }
    return authorization_code


def verify_authorization_code(authorization_code, client_id, redirect_url):
    # f = Fernet(KEY)
    record = authorization_codes.get(authorization_code)
    if not record:
        return False
    client_id_in_record = record.get('client_id')
    redirect_url_in_record = record.get('redirect_url')
    exp = record.get('exp')
    if client_id != client_id_in_record or redirect_url != redirect_url_in_record:
        return False
    if exp < time.time():
        return False
    del authorization_codes[authorization_code]
    return True
