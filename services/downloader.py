import asyncio
import os
from yt_dlp import YoutubeDL

async def async_download_youtube_video(url: str, format_str: str, progress_hook=None) -> str:
    loop = asyncio.get_running_loop()

    def blocking_download():
        output_path = os.path.join(os.getcwd(), "%(title)s.%(ext)s")

        def yt_progress_hook(d):
            if progress_hook:
                status = d.get('status')
                if status == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    if total_bytes:
                        percent = downloaded_bytes / total_bytes * 100
                        loop.call_soon_threadsafe(progress_hook, percent)

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
            if progress_hook:
                loop.call_soon_threadsafe(progress_hook, 100)
            return filename

    return await loop.run_in_executor(None, blocking_download)
