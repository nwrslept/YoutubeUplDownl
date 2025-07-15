import os
import pickle
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# OAuth 2.0 scope for uploading videos to YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Path to the client secrets JSON file
CLIENT_SECRETS_FILE = os.path.join('resources', 'client_secrets.json')

# File to store the user's access and refresh tokens
TOKEN_FILE = 'token.json'


def get_authenticated_service():
    """
    Authenticates the user with YouTube Data API v3 using OAuth 2.0.
    If token is already saved, it will be reused. Otherwise, the user will be prompted.

    Returns:
        googleapiclient.discovery.Resource: Authenticated YouTube API service.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('youtube', 'v3', credentials=creds)


def upload_video(
    video_file_path: str,
    title: str,
    description: str = "",
    tags: list[str] = None,
    category_id: str = "22",
    privacy_status: str = "private",
    progress_callback=None
):
    """
    Uploads a video to YouTube.

    Args:
        video_file_path (str): Path to the video file.
        title (str): Title of the video.
        description (str): Description of the video.
        tags (list[str], optional): List of tags.
        category_id (str, optional): YouTube category ID. Default is "22" (People & Blogs).
        privacy_status (str, optional): "public", "private", or "unlisted". Default is "private".
        progress_callback (function, optional): A function to receive upload progress in percent.

    Returns:
        dict: API response from YouTube containing video ID and other metadata.
    """
    youtube = get_authenticated_service()

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }

    # Use resumable upload to allow progress tracking and larger files
    media = MediaFileUpload(
        video_file_path,
        chunksize=1024*1024,
        resumable=True,
        mimetype='video/*'
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    if progress_callback:
        progress_callback(0)

    # Loop through upload chunks, updating progress if a callback is provided
    while response is None:
        status, response = request.next_chunk()
        if status and progress_callback:
            progress = int(status.progress() * 100)
            progress_callback(progress)

    print(f"Upload complete. Video ID: {response.get('id')}")
    return response
