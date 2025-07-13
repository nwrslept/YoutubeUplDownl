import asyncio
import os
from yt_dlp import YoutubeDL


async def async_download_youtube_video(url: str, format_str: str, progress_hook=None, output_dir=".") -> str:
    """
    Asynchronously downloads a YouTube video using yt-dlp.

    Args:
        url (str): The YouTube video URL.
        format_str (str): The desired video format string.
        progress_hook (callable, optional): A function to update download progress.
        output_dir (str): The output directory to save the video.

    Returns:
        str: The path to the downloaded video file.
    """
    loop = asyncio.get_running_loop()

    def blocking_download():
        # Define the output filename template
        output_path = os.path.join(output_dir, "%(title)s.%(ext)s")

        # Progress hook for yt-dlp
        def yt_progress_hook(d):
            if progress_hook:
                status = d.get('status')
                print(f"YT progress hook status: {status}, info keys: {list(d.keys())}")

                if status == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded_bytes = d.get('downloaded_bytes', 0)

                    if total_bytes:
                        percent = downloaded_bytes / total_bytes * 100
                        print(f"Progress: {percent:.2f}% ({downloaded_bytes}/{total_bytes})")
                        # Call the progress hook in the main thread
                        loop.call_soon_threadsafe(progress_hook, percent)
                    else:
                        print("No total_bytes info — progress is not updated.")

                elif status == 'finished':
                    print("Download finished")
                    loop.call_soon_threadsafe(progress_hook, 100)

        # yt-dlp options
        ydl_opts = {
            'outtmpl': output_path,
            'format': format_str,
            'merge_output_format': 'mp4',
            'quiet': True,
            'noplaylist': True,
            'progress_hooks': [yt_progress_hook],
        }

        # Run the download
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # Ensure file has .mp4 extension
            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"

            return filename

    # Run blocking download in separate thread
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
