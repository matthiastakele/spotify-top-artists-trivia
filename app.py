from flask import Flask, request, url_for, session, redirect, render_template, make_response
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import time
import random

# Load environment variables
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "WOrnwofwcwfrer42"
app.config['SESSION_COOKIE_NAME'] = 'Spotify Top Artist Trivia'
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
        return redirect(url_for('home'))

@app.route('/selectArtist', methods=['POST'])
def selectArtist():
    selected_artist_id = request.form['artist_id']
    if not selected_artist_id:
        return "No artist selected.", 400
    session['selected_artist_id'] = selected_artist_id
    return redirect(url_for('trivia'))

@app.route('/trivia')
def trivia():
    
    def generate_diff_album_tracks(current_album, num_of_tracks=3):
        shuffled_albums = random.sample(session["albums_with_tracks"].keys(), k=len(session["albums_with_tracks"]))
        tracks = []
        for album_name in shuffled_albums:
            if len(tracks) == num_of_tracks:
                break
            if album_name != current_album and not album_name.startswith(current_album):
                random_track_index = random.randint(0, len(session["albums_with_tracks"][album_name]['tracks']) - 1)
                tracks.append(session["albums_with_tracks"][album_name]['tracks'][random_track_index]["name"])
        return tracks

    selected_artist_id = session.get('selected_artist_id')
    if not selected_artist_id:
        return redirect(url_for('pickTopArtist'))

    try:
        token_info = get_token()
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Fetch artist details
        artist_info = sp.artist(selected_artist_id)
        top_tracks = sp.artist_top_tracks(selected_artist_id, country='US')['tracks']
        albums = sp.artist_albums(selected_artist_id, album_type='album')['items']

        # Prepare nested album and track data
        albums_with_tracks = {}
        for album in albums:
            album_name = album['name']
            album_id = album['id']
            tracks = sp.album_tracks(album_id)['items']
            albums_with_tracks[album_name] = {
                "release_date": album['release_date'],
                "tracks": [{"name": track['name'], "duration_ms": track['duration_ms']} for track in tracks]
            }
            session['albums_with_tracks'] = albums_with_tracks

        # Prepare data for questions
        questions = []

        # Question: How many followers does the artist have?
        questions.append({
            "question": f"How many Spotify followers does {artist_info['name']} have?",
            "options": [
                "{:,}".format(artist_info['followers']['total']),
                "{:,}".format(int(artist_info['followers']['total'] * 1.3)),
                "{:,}".format(int(artist_info['followers']['total'] * 0.7)),
                "{:,}".format(int(artist_info['followers']['total'] * 0.5)),
            ],
            "answer": artist_info['followers']['total']
        })

        # Question: What is the most recently released album?
        most_recent_album = max(albums, key=lambda x: x['release_date'])
        shuffled_albums = [album for album in random.sample(albums, k=len(albums)) if album != most_recent_album]
        questions.append({
            "question": f"What is the most recently released album by {artist_info['name']}?",
            "options": [
                most_recent_album['name'],
                shuffled_albums.pop()['name'],
                shuffled_albums.pop()['name'],
                shuffled_albums.pop()['name'],
            ],
            "answer": most_recent_album['name']
        })

        # Question: Which track is on a specific album?
        for album_name, details in albums_with_tracks.items():
            if details['tracks']:
                correct_track = random.choice(details['tracks'])['name']
                fake_tracks = generate_diff_album_tracks(album_name)
                questions.append({
                    "question": f"Which track is on the album '{album_name}'?",
                    "options": [correct_track, *fake_tracks],
                    "answer": correct_track
                })

        # Shuffle questions and options
        for question in questions:
            random.shuffle(question["options"])
        
        return render_template('trivia.html', artist=artist_info, questions=questions)
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while fetching artist data.", 500

@app.route('/submitTrivia', methods=['POST'])
def submitTrivia():
    # Retrieve questions from session
    questions = session.get('questions', [])

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
