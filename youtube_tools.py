# youtube_tools.py

import os
import pickle
import base64
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from langchain_core.tools import tool

def get_youtube_credentials():
    """
    Handles YouTube API authentication securely for both local and deployed environments.
    - In a deployed Streamlit environment, it rebuilds credentials from base64-encoded secrets.
    - Locally, it uses the 'token.pickle' and 'client_secret.json' files.
    """
    creds = None
    
    # Deployed on Streamlit Cloud: Rebuild credentials from secrets
    if hasattr(st, 'secrets'):
        client_secret_b64 = st.secrets.get("CLIENT_SECRET_B64")
        token_pickle_b64 = st.secrets.get("TOKEN_PICKLE_B64")

        if not client_secret_b64 or not token_pickle_b64:
            st.error("Missing CLIENT_SECRET_B64 or TOKEN_PICKLE_B64 in Streamlit secrets.")
            return None
        
        try:
            # Decode the token from base64
            token_pickle_bytes = base64.b64decode(token_pickle_b64)
            creds = pickle.loads(token_pickle_bytes)

            # If token is expired, use the client secret to refresh it
            if creds and creds.expired and creds.refresh_token:
                client_config = json.loads(base64.b64decode(client_secret_b64))
                creds.refresh(Request(client_config=client_config))
            return creds
        except Exception as e:
            st.error(f"Failed to load credentials from secrets: {e}")
            return None

    # Local Development: Use token.pickle and client_secret.json files
    else:
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('client_secret.json'):
                    raise FileNotFoundError("client_secret.json not found. Run 'python generate_token.py' to create your token.")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json',
                    scopes=['https://www.googleapis.com/auth/youtube.force-ssl']
                )
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

def get_youtube_service():
    """Builds and returns the YouTube API service object."""
    try:
        credentials = get_youtube_credentials()
        if credentials:
            return build('youtube', 'v3', credentials=credentials)
    except Exception as e:
        print(f"--- ERROR building YouTube service: {e} ---")
    return None

# Your @tool decorated functions (search_youtube, create_youtube_playlist, etc.) remain below
# Make sure they all call get_youtube_service() at the beginning like this:

@tool
def search_youtube(query: str, max_results: int = 5) -> dict:
    """
    Searches YouTube for videos based on a query. Returns video details including
    videoId, title, and description.
    """
    youtube = get_youtube_service()
    if not youtube:
        return {"error": "Failed to authenticate with YouTube API."}
    try:
        # ... (rest of the function is the same)
        request = youtube.search().list(
            part="snippet",
            q=query,
            maxResults=max_results,
            type="video"
        )
        response = request.execute()
        videos = [
            {"videoId": item["id"]["videoId"], "title": item["snippet"]["title"], "description": item["snippet"]["description"]}
            for item in response.get("items", [])
        ]
        return {"videos": videos}
    except Exception as e:
        return {"error": f"Failed to search YouTube: {str(e)}"}

@tool
def create_youtube_playlist(title: str, description: str = "AI-Generated Learning Path") -> dict:
    """
    Creates a new public YouTube playlist. Returns the ID of the new playlist.
    """
    youtube = get_youtube_service()
    if not youtube:
        return {"error": "Failed to authenticate with YouTube API."}
    try:
        # ... (rest of the function is the same)
        request = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": description},
                "status": {"privacyStatus": "public"}
            }
        )
        response = request.execute()
        return {"playlistId": response["id"]}
    except Exception as e:
        return {"error": f"Failed to create playlist: {str(e)}"}

@tool
def add_videos_to_youtube_playlist(playlist_id: str, video_ids: list[str]) -> dict:
    """
    Adds a list of videos to a specific YouTube playlist using their videoIds.
    """
    youtube = get_youtube_service()
    if not youtube:
        return {"error": "Failed to authenticate with YouTube API."}
    try:
        # ... (rest of the function is the same)
        for video_id in video_ids:
            request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id}
                    }
                }
            )
            request.execute()
        return {"status": "success", "message": f"Added {len(video_ids)} videos to playlist {playlist_id}."}
    except Exception as e:
        return {"error": f"Failed to add videos to playlist: {str(e)}"}
