# StemMP3Tagger
Python script to determine any Instrumentals, Acapellas, or TV Tracks in a given directory and convert the audio files to MP3 and automatically tag them with information from the Spotify API

## Installation
- ```pip install -r requirements.txt```
- Setup an application with the Spotify developer portal, then paste the client secret and ID in this code block in main.py:
- ```sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="YOUR_CLIENT_ID", client_secret="YOUR_CLIENT_SECRET"))```
- Follow further instructions in the console
