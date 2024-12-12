from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from fastapi.responses import RedirectResponse

app = FastAPI()

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourfrontend.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/playlist")
async def playlist():
    try:
        # Create Spotify client using our OAuth manager
        sp = spotipy.Spotify(auth_manager=oauth_manager)
        
        # Get current user's profile
        user = sp.current_user()
        user_id = user['id']

        # Create a new playlist
        playlist = sp.user_playlist_create(user_id, "My Generated Playlist", public=False, description="Generated via API")
        playlist_id = playlist['id']

        # Add tracks to the playlist
        tracks_to_add = ["spotify:track:4uLU6hMCjMI75M1A2tKUQC", "spotify:track:1301WleyT98MSxVHPZCA6M"]
        sp.playlist_add_items(playlist_id, tracks_to_add)
        
        return {"message": "Playlist created successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/user/playlist/randomize/{playlist_id}")
async def randomize(playlist_id: str):
    try:
        # Create Spotify client using our OAuth manager
        sp = spotipy.Spotify(auth_manager=oauth_manager)
        
        # Get all tracks from the playlist
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        
        # Handle pagination to get all tracks
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
        
        # Extract track information and shuffle
        from random import shuffle
        track_info = [{
            'id': track['track']['id'],
            'name': track['track']['name'],
            'uri': track['track']['uri'],
            'artists': [artist['name'] for artist in track['track']['artists']],
            'duration_ms': track['track']['duration_ms']
        } for track in tracks]
        shuffle(track_info)
        
        # Extract URIs from shuffled tracks and replace playlist items
        track_uris = [track['uri'] for track in track_info]
        sp.playlist_replace_items(playlist_id, track_uris)
        
        return {
            "message": "Playlist randomized and updated successfully",
            "tracks": track_info
        }
    except Exception as e:
        return {"error": str(e)}

# get user's playlists
@app.get("/api/user/playlists")
async def playlists():
    sp = spotipy.Spotify(auth_manager=oauth_manager)
    
    # Initialize variables
    all_playlists = []
    offset = 0
    limit = 50  # Spotify's max limit per request
    
    while True:
        # Get current batch of playlists
        response = sp.current_user_playlists(limit=limit, offset=offset)
        items = response.get('items', [])
        
        # If no more items, break the loop
        if not items:
            break
            
        all_playlists.extend(items)
        offset += limit
        
        # If we got fewer items than the limit, we've reached the end
        if len(items) < limit:
            break
    
    return all_playlists

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8888)