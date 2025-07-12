import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def upload_video_to_youtube(video_path: str) -> str:
    flow = InstalledAppFlow.from_client_secrets_file("resources/client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": "Автоматичне відео",
            "description": "Завантажено через Python + yt_dlp",
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "private"
        }
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    response = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    ).execute()

    return response["id"]
