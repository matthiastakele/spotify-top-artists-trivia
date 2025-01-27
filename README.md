🎵 Spotify Top Artist Trivia Game

A dynamic web application that generates a personalized trivia game based on a user’s top artists, albums, and tracks using the Spotify Web API. Test your knowledge of your favorite artists while enjoying an interactive and engaging experience!

🚀 Features

Dynamic Question Generation: Trivia questions are created based on user-specific Spotify data.
OAuth 2.0 Authentication: Securely log in using your Spotify account.
Personalized Gameplay: Questions are tailored to your top artists, tracks, and albums.
Interactive UI: Responsive and user-friendly interface built with Jinja templating.
Seamless Backend Logic: Powered by Python and Flask for efficient data processing.
Deployed for Scalability: Hosted on Vercel for fast and reliable performance.

📖 How It Works

User Authentication:
Users log in with their Spotify account via OAuth 2.0. The app retrieves their top artists, albums, and tracks using the Spotify Web API.
Question Generation:
Questions are dynamically generated based on the user's listening habits and preferences.
Gameplay:
Users answer trivia questions in a clean, interactive interface. Their answers are validated, and scores are displayed at the end.
Results Display:
A detailed breakdown of the user’s performance, including correct and incorrect answers, is provided at the end of the game.

🖥️ Installation

1. Clone the Repository
git clone https://github.com/yourusername/spotify-trivia-game.git  
cd spotify-trivia-game  
2. Set Up Environment
Ensure you have Python 3.8+ installed.
Install dependencies:
pip install -r requirements.txt  
3. Create a Spotify App
Go to the Spotify Developer Dashboard.
Create a new app and note the Client ID and Client Secret.
Set the redirect URI to http://127.0.0.1:5000/callback.
4. Configure Environment Variables
Create a .env file in the project root and add the following:

SPOTIFY_CLIENT_ID=your_spotify_client_id  
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret  
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback  
FLASK_APP=app.py  
FLASK_ENV=development  
SECRET_KEY=your_secret_key  
5. Run the Application
flask run  
