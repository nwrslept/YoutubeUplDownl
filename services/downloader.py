import asyncio
import os
from yt_dlp import YoutubeDL

async def async_download_youtube_video(url: str, format_str: str, progress_hook=None, output_dir=".") -> str:
    loop = asyncio.get_running_loop()

    def blocking_download():
        output_path = os.path.join(output_dir, "%(title)s.%(ext)s")

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
                        loop.call_soon_threadsafe(progress_hook, percent)
                    else:
                        # Якщо total_bytes немає, можеш показувати 0 або пропускати оновлення
                        print("No total_bytes info — прогрес не оновлюється")

                elif status == 'finished':
                    print("Download finished")
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
            # Перейменування до .mp4, якщо треба
            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"
            return filename

    return await loop.run_in_executor(None, blocking_download)
