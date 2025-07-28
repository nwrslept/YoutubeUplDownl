import asyncio
import os
from yt_dlp import YoutubeDL


async def async_download_youtube_video(
    url: str,
    format_str: str,
    progress_hook=None,
    output_dir=".",
    cancel_flag=None
) -> str:
    """
    Asynchronously download a YouTube video using yt_dlp.

    Args:
        url (str): YouTube video URL.
        format_str (str): Desired download format string.
        progress_hook (Callable, optional): Callback for progress updates.
        output_dir (str, optional): Directory to save downloaded video.
        cancel_flag (dict, optional): Flag to cancel download if cancel_flag["cancel"] is True.

    Returns:
        str: Final video file path.
    """
    loop = asyncio.get_running_loop()

    def blocking_download():
        output_path = os.path.join(output_dir, "%(title).100s.%(ext)s")

        def yt_progress_hook(d):
            if cancel_flag and cancel_flag.get("cancel", False):
                raise Exception("Download cancelled by user")

            if progress_hook:
                status = d.get("status")
                if status == "downloading":
                    total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
                    downloaded_bytes = d.get("downloaded_bytes", 0)
                    if total_bytes:
                        percent = downloaded_bytes / total_bytes * 100
                        loop.call_soon_threadsafe(progress_hook, percent)
                elif status == "finished":
                    loop.call_soon_threadsafe(progress_hook, 100)

        ydl_opts = {
            "format": format_str,
            "outtmpl": output_path,
            "overwrites": True,
            "windowsfilenames": True,
            "progress_hooks": [yt_progress_hook],
            "postprocessors": [
                {"key": "FFmpegMerger"},
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",  # yt_dlp uses this exact spelling
                }
            ],
            "concurrent_fragment_downloads": 3,
            "playlist_items": "1",

        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except KeyError as e:
            print("❌ KeyError:", e)
            print("⚠️ Falling back to format='best'")
            ydl_opts["format"] = "best"
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

        final_path = info.get("_filename")

        # Ensure the file has .mp4 extension (after ffmpeg conversion)
        if final_path and not final_path.lower().endswith(".mp4"):
            base, _ = os.path.splitext(final_path)
            final_path = base + ".mp4"

        return final_path

    return await loop.run_in_executor(None, blocking_download)


async def async_get_video_info(url: str) -> dict:
    """
    Asynchronously fetch basic YouTube video metadata (title and thumbnail URL).

    Args:
        url (str): YouTube video URL.

    Returns:
        dict: Dictionary with 'title' and 'thumbnail' keys.
    """
    loop = asyncio.get_running_loop()

    def blocking_info():
        try:
            ydl_opts = {
                "quiet": True,
                "skip_download": True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title"),
                    "thumbnail": info.get("thumbnail"),
                }
        except Exception as e:
            print("❌ Error fetching video info:", e)
            return {}

    return await loop.run_in_executor(None, blocking_info)
