import asyncio
import os
from yt_dlp import YoutubeDL


# services/downloader.py

async def async_download_youtube_video(url: str, format_str: str, progress_hook=None, output_dir=".", cancel_flag=None) -> str:
    """
    Asynchronously downloads a YouTube video with specified format,
    supports progress updates and cancellation.

    Args:
        url (str): YouTube video URL.
        format_str (str): Format string for yt-dlp download.
        progress_hook (callable, optional): Callback to report progress (percentage).
        output_dir (str): Directory to save downloaded file.
        cancel_flag (dict, optional): Dictionary with 'cancel' key to stop download.

    Returns:
        str: Path to the downloaded video file.
    """
    loop = asyncio.get_running_loop()

    def blocking_download():
        output_path = os.path.join(output_dir, "%(title)s.%(ext)s")

        def yt_progress_hook(d):
            if cancel_flag and cancel_flag.get("cancel", False):
                raise Exception("Download cancelled by user")

            if progress_hook:
                status = d.get('status')

                if status == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded_bytes = d.get('downloaded_bytes', 0)

                    if total_bytes:
                        percent = downloaded_bytes / total_bytes * 100
                        loop.call_soon_threadsafe(progress_hook, percent)

                elif status == 'finished':
                    loop.call_soon_threadsafe(progress_hook, 100)

        ydl_opts = {
            'outtmpl': output_path,
            'format': format_str,
            'merge_output_format': 'mp4',
            'quiet': True,
            'noplaylist': True,
            'progress_hooks': [yt_progress_hook],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"

            return filename

    return await loop.run_in_executor(None, blocking_download)


async def async_get_video_info(url: str) -> dict:
    """
    Asynchronously fetches basic video info (title and thumbnail) from YouTube.

    Args:
        url (str): The YouTube video URL.

    Returns:
        dict: A dictionary with 'title' and 'thumbnail' keys.
    """
    loop = asyncio.get_running_loop()

    def blocking_info():
        ydl_opts = {"quiet": True, "skip_download": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
            }

    return await loop.run_in_executor(None, blocking_info)
