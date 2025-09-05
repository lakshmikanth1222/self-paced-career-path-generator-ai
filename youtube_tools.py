# youtube_tools.py (Updated with better error logging)

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from langchain_core.tools import tool

def get_youtube_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json',
                scopes=['https://www.googleapis.com/auth/youtube.force-ssl']
            )
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

@tool
def search_youtube(query: str, max_results: int = 5) -> dict:
    """
    Searches YouTube for videos based on a query and returns a list of video details,
    including videoId, title, and description. Useful for finding relevant video resources.
    """
    try:
        credentials = get_youtube_credentials()
        youtube = build('youtube', 'v3', credentials=credentials)
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
        # ADDED PRINT STATEMENT FOR DEBUGGING
        print(f"--- ERROR IN search_youtube: {e} ---")
        return {"error": f"Failed to search YouTube: {str(e)}"}

@tool
def create_youtube_playlist(title: str, description: str = "A playlist created by the Learning Path Generator.") -> dict:
    """
    Creates a new public YouTube playlist with a specified title and description.
    Returns the ID of the created playlist, which is needed to add videos to it.
    """
    try:
        credentials = get_youtube_credentials()
        youtube = build('youtube', 'v3', credentials=credentials)
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
        # ADDED PRINT STATEMENT FOR DEBUGGING
        print(f"--- ERROR IN create_youtube_playlist: {e} ---")
        return {"error": f"Failed to create playlist: {str(e)}"}

@tool
def add_videos_to_youtube_playlist(playlist_id: str, video_ids: list[str]) -> dict:
    """
    Adds a list of videos, identified by their videoIds, to a specified YouTube playlist.
    You must provide the playlist_id and a list of video_ids.
    """
    try:
        credentials = get_youtube_credentials()
        youtube = build('youtube', 'v3', credentials=credentials)
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
        # ADDED PRINT STATEMENT FOR DEBUGGING
        print(f"--- ERROR IN add_videos_to_youtube_playlist: {e} ---")
        return {"error": f"Failed to add videos to playlist: {str(e)}"}
