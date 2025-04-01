from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import spotipy
from fastapi.responses import RedirectResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourfrontend.com", "https://spotify-frontend-hazel.vercel.app/"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/callback")
async def callback(code: str = None):
    if code:
        # Get the token info
        token_info = oauth_manager.get_access_token(code)
        return {"message": "Authentication successful"}
    return {"error": "No code provided"}

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
async def randomize(playlist_id: str, request: Request):
    # Get the token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "No token provided"}
    
    access_token = auth_header.split(' ')[1]
    
    try:
        sp = spotipy.Spotify(auth=access_token)
        
        # Initialize variables for pagination
        all_tracks = []
        offset = 0
        limit = 100  # Spotify's maximum limit for playlist tracks
        
        while True:
            print(f"Fetching tracks with offset {offset} and limit {limit}")
            results = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            tracks = results['items']
            total = results.get('total', 0)
            print(f"total: {total}")
            
            if not tracks:
                break
                
            all_tracks.extend(tracks)
            
            offset += limit
            if offset >= results['total']:
                break
        
        # Extract track information and shuffle
        from random import shuffle
        track_info = [{
            'id': track['track']['id'],
            'name': track['track']['name'],
            'uri': track['track']['uri'],
            'artists': [artist['name'] for artist in track['track']['artists']],
            'duration_ms': track['track']['duration_ms']
        } for track in all_tracks]
        shuffle(track_info)
        
        # Extract URIs from shuffled tracks and replace playlist items in batches
        print("have the tracks, now going to replace order")
        track_uris = [track['uri'] for track in track_info]
        
        # First, clear the playlist
        sp.playlist_replace_items(playlist_id, [])
        
        # Then add tracks in batches of 100
        batch_size = 100
        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i + batch_size]
            sp.playlist_add_items(playlist_id, batch)
            print(f"Added batch {i//batch_size + 1} of {(len(track_uris) + batch_size - 1)//batch_size}")
        
        return {
            "message": "Playlist randomized and updated successfully",
            "tracks": track_info
        }
    except Exception as e:
        return {"error": str(e)}

# get user's playlists
@app.get("/api/user/playlists")
async def playlists(request: Request):
    # Get the token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "No token provided"}
    
    access_token = auth_header.split(' ')[1]
    sp = spotipy.Spotify(auth=access_token)
    
    # Get the current user's ID first
    current_user = sp.current_user()
    user_id = current_user['id']
    
    # Initialize variables
    all_playlists = []
    offset = 0
    limit = 50
    
    while True:
        response = sp.current_user_playlists(limit=limit, offset=offset)
        items = response.get('items', [])
        total = response.get('total', 0)
        
        if not items:
            break
            
        # Only add playlists owned by the current user
        owned_playlists = [
            playlist for playlist in items 
            if playlist['owner']['id'] == user_id
        ]
        all_playlists.extend(owned_playlists)
        
        offset += limit
        if offset >= total:
            break
    
    # Sort playlists alphabetically by name
    all_playlists.sort(key=lambda x: x['name'].strip().lower())
    
    return all_playlists

@app.get("/api/user")
async def get_user(request: Request):
    # Get the token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "No token provided"}
    
    access_token = auth_header.split(' ')[1]
    
    try:
        # Create Spotify client using the token directly
        sp = spotipy.Spotify(auth=access_token)
        
        # Get current user's profile with all available information
        user = sp.current_user()
        
        return user
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/user/playlists/{playlist_id}")
async def get_playlist(playlist_id: str, request: Request):
    # Get the token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "No token provided"}
    
    access_token = auth_header.split(' ')[1]
    sp = spotipy.Spotify(auth=access_token)

    
    playlist = sp.playlist(playlist_id)
    return playlist

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8888)