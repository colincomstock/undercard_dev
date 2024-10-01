from http.client import responses

from flask import Flask, redirect, request, jsonify, session
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
import os
import urllib.parse


# Load client id and secret
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

AUTH_URL = os.getenv('AUTH_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
API_BASE_URL = os.getenv('API_BASE_URL')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

@app.route('/')
def index():
    return"Welcome to my Spotify App <a href='/login'>Login with Spotify</a>"

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-top-read'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/top-tracks')

def token_expired():
    return datetime.now().timestamp() > session.get('expires_at', 0)

def refresh_access_token():
    if token_expired():
        response = requests.post(TOKEN_URL, data={
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        })

        # Error handling
        if response.status_code == 200:
            token_info = response.json()
            session['access_token'] = token_info['access_token']
            session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']
        else:
            return jsonify({
                "error": "Failed to refresh access token",
                "status_code": response.status_code,
                "response_text": response.text
            }), response.status_code


def ensure_token_valid():
    if token_expired():
        refresh_access_token()

@app.route('/playlists')
def get_playlists():
    ensure_token_valid()
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        try:
            playlists = response.json()
            return jsonify(playlists)
        except ValueError:
            return jsonify({"error": "Could not parse JSON", "response_text": response.text})
    else:
        return jsonify({
            "error": f"Failed to fetch playlists. Status code: {response.status_code}",
            "response_text": response.text
        })

@app.route('/top-tracks')
def get_top_tracks():
    ensure_token_valid()
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    params = {
        'time_range': 'medium_term',
        'limit': '50'
    }

    response = requests.get(API_BASE_URL + 'me/top/tracks', headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        try:
            top_tracks = response.json()
            return jsonify(top_tracks)
        except ValueError:
            return jsonify({"error": "Could not parse JSON", "response_text": response.text})
    else:
        return jsonify({
            "error": f"Failed to fetch playlists. Status code: {response.status_code}",
            "response_text": response.text
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

