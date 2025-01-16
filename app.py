from flask import Flask, request, url_for, session, redirect, render_template, make_response
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "WOrnwofwcwfrer42"
app.config['SESSION_COOKIE_NAME'] = 'Spotify Calendar'
TOKEN_INFO = "token_info"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=url_for('redirectPage', _external=True),
        scope="user-top-read user-library-read",
        cache_path=None
    )

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise Exception("No token info found in session.")
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO] = token_info
    return token_info

@app.route('/')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    if not code:
        return "Authorization code not received.", 400
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('pickTopArtist'))

@app.route('/pickTopArtist')
def pickTopArtist():
    try:
        token_info = get_token()
        sp = spotipy.Spotify(auth=token_info['access_token'])
        top_artists = sp.current_user_top_artists(limit=12, time_range='medium_term')['items']
        return render_template('pick_top_artist.html', top_artists=top_artists)
    except Exception as e:
        print(f"Error: {e}")
        return redirect('/home')

@app.route('/selectArtist', methods=['POST'])
def selectArtist():
    selected_artist_id = request.form['artist_id']
    session['selected_artist_id'] = selected_artist_id
    return redirect(url_for('trivia'))

@app.route('/trivia')
def trivia():
    return render_template('trivia.html')

@app.route('/home')
def home():
    logged_in = TOKEN_INFO in session
    return render_template('home.html', logged_in=logged_in)

@app.route('/logout')
def logout():
    session.pop(TOKEN_INFO, None)
    session.clear()
    resp = make_response(redirect('/home'))
    resp.set_cookie(app.config['SESSION_COOKIE_NAME'], '', expires=0)
    return resp

if __name__ == '__main__':
    app.run(debug=True)
