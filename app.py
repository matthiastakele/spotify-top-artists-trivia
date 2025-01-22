from typing import List, Dict, Any
from flask import Flask, request, url_for, session, redirect, render_template, make_response
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import time
import datetime
import random
import copy 
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
    is_expired = int(token_info['expires_at'] - now) < 60
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

class TriviaQuestionGenerator:
    def __init__(self, spotify_client: spotipy.Spotify, artist_id: str):
        self.sp = spotify_client
        self.artist_id = artist_id
        self.artist_info = self.sp.artist(artist_id)
        self.top_tracks = self.sp.artist_top_tracks(artist_id, country='US')['tracks']
        self.albums = self.sp.artist_albums(artist_id, album_type='album')['items']
        self.albums_with_tracks = self._prepare_albums_with_tracks()

    def _prepare_albums_with_tracks(self) -> Dict:
        """Prepare nested album and track data."""
        albums_with_tracks = {}
        for album in self.albums:
            tracks = self.sp.album_tracks(album['id'])['items']
            albums_with_tracks[album['name']] = {
                "release_date": album['release_date'],
                "tracks": [{"name": track['name'], "duration_ms": track['duration_ms']} 
                          for track in tracks]
            }
        return albums_with_tracks

    def _generate_diff_album_tracks(self, current_album: str, num_of_tracks: int = 3) -> List[str]:
        """Generate tracks from different albums for wrong options."""
        tracks = []
        shuffled_albums = random.sample(list(self.albums_with_tracks.keys()), len(self.albums_with_tracks))
        for album in shuffled_albums:
            if album == current_album or album.startswith(current_album) or current_album.startswith(album):
                shuffled_albums.remove(album)
    
        if len(shuffled_albums) >= 1:
            selected_tracks = set()
            while len(tracks) != num_of_tracks:
                diff_album = random.choice(shuffled_albums)
                diff_track = random.choice(self.albums_with_tracks[diff_album]['tracks'])['name']

                if diff_track not in selected_tracks:
                    selected_tracks.add(diff_track)
                    tracks.append(diff_track)

        return tracks

    def generate_followers_question(self) -> Dict:
        """Generate question about artist's follower count."""
        followers = self.artist_info['followers']['total']
        return {
            "question": f"How many Spotify followers does {self.artist_info['name']} have?",
            "options": [
                "{:,}".format(int(followers * multiplier))
                for multiplier in [0.5, 0.7, 1.0, 1.3]
            ],
            "answer": followers
        }
    
    def generate_genre_question(self) -> Dict:
        """Generate question about artist's genre."""
        artist_genres = self.artist_info.get('genres')
        if artist_genres:
            artist_genre = artist_genres[0]
            all_genres = {'rock', 'pop', 'r&b', 'jazz', 'hip hop'}
            other_genres = [genre for genre in random.sample(all_genres - {artist_genre}, 3)]
            return {
                "question": f"What genre is {self.artist_info['name']}'s music?",
                "options": [artist_genre] + other_genres,
                "answer": artist_genre
            }
        else:
            return {}

    def generate_recent_album_question(self) -> Dict:
        """Generate question about most recent album."""
        most_recent = max(self.albums, key=lambda x: x['release_date'])
        other_albums = random.sample([a for a in self.albums if a != most_recent], min(3, len(self.albums)-1))
        if other_albums:
            return {
                "question": f"What is the most recently released album by {self.artist_info['name']}?",
                "options": [most_recent['name']] + [a['name'] for a in other_albums],
                "answer": most_recent['name']
            }
        return {}

    def generate_track_album_questions(self) -> List[Dict]:
        """Generate questions about which tracks belong to which albums."""
        questions = []
        for album_name, details in self.albums_with_tracks.items():
            if details['tracks']:
                correct_track = random.choice(details['tracks'])['name']
                diff_tracks = self._generate_diff_album_tracks(album_name)
                if not diff_tracks:
                    return {}
                questions.append({
                    "question": f"Which track is on the album '{album_name}'?",
                    "options": [correct_track] + diff_tracks,
                    "answer": correct_track
                })

        return questions

    def generate_album_year_questions(self) -> List[Dict]:
        """Generate questions about various album release years."""
        questions = []
        for album in self.albums:
            release_year = int(album['release_date'][:4])
            current_year = datetime.datetime.now().year

            diff_years = [
                release_year + i
                for i in range(-4, 4) 
                if i != 0 and (release_year + i) <= current_year
            ]
            
            options = random.sample(diff_years, 3) + [release_year]
            questions.append({
                "question": f"In what year was the album '{album['name']}' released?",
                "options": options,
                "answer": release_year
            })

        return questions
    
    def generate_album_track_count_questions(self) -> List[Dict]:
        """Generate questions about the track abount of various albums"""
        questions = []
        for album_name, album_data in self.albums_with_tracks.items():
            track_count = len(album_data['tracks'])
            diff_track_counts = [
                max(1, track_count + i)
                for i in range(-4, 5)
                if i != 0 and (track_count + i) > 0
            ]

            options = random.sample(diff_track_counts, 3) + [track_count]
            questions.append({
                "question": f"How many tracks are on '{album_name}'?",
                "options": options,
                "answer": track_count
            })

        return questions

    def get_questions(self, num_questions: int = 10) -> List[Dict]:
        """Generate a set of trivia questions."""
        all_questions = []
        
        # Add one of each question type
        question_generators = [
            self.generate_followers_question,
            self.generate_recent_album_question,
            self.generate_genre_question
        ]

        multiple_question_generators = [
            self.generate_track_album_questions,
            self.generate_album_year_questions,
            self.generate_album_track_count_questions
        ]

        for generator in question_generators:
            all_questions.append(generator())
        
        other_questions = [generator() for generator in multiple_question_generators]
        all_other_questions = [q for questions in other_questions for q in questions]

        if len(all_questions) + len(all_other_questions) < 10:
            all_questions.extend(all_other_questions)
            random.shuffle(all_questions)
            return all_questions

        i = 0
        while len(all_questions) < 10:
            try:
                all_questions.extend([questions[i] for questions in other_questions])
                i += 1
            except:
                break
        
        # Shuffle and limit to desired number
        random.shuffle(all_questions)
        return all_questions[:num_questions]

@app.route('/trivia')
def trivia():
    selected_artist_id = session.get('selected_artist_id')
    if not selected_artist_id:
        return redirect(url_for('pickTopArtist'))

    try:
        token_info = get_token()
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Generate questions using the new class
        generator = TriviaQuestionGenerator(sp, selected_artist_id)
        questions = generator.get_questions()
        questions = [q for q in questions if q]
        for q in questions:
            random.shuffle(q['options'])
        
        # Store albums_with_tracks in session for potential future use
        session['albums_with_tracks'] = generator.albums_with_tracks
        
        return render_template('trivia.html', 
                             artist=generator.artist_info, 
                             questions=questions)
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
