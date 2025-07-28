# 🎬 YouTube Video Downloader & Uploader

This is a **modern desktop application** built with **Python + PyQt6** that allows you to:

- ✅ Download videos from **YouTube and hundreds of other sites** (thanks to `yt-dlp`)
- 📤 Upload videos directly to **your YouTube channel**
- 🖼 Add custom thumbnails, set title, description, and privacy
- 🌙 Switch between dark and light themes

---

## ⚙️ Features

- Drag & Drop or click to select video and thumbnail
- Choose video quality (1080p, 720p, etc.) or audio-only
- Live progress bars for both download and upload
- Asynchronous operations with `asyncio` and `qasync`
- Clean and responsive GUI powered by `PyQt6`
- Supports downloading from: YouTube, Vimeo, TikTok, Twitter, Facebook, SoundCloud, and many more.

---

## 🧰 Technologies Used

- [Python 3.10+](https://www.python.org/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [PyQt6](https://pypi.org/project/PyQt6/)
- [qasync](https://github.com/CabbageDevelopment/qasync)
- [aiohttp](https://docs.aiohttp.org/)
- [Google YouTube Data API v3](https://developers.google.com/youtube/registering_an_application)

---

## 🚀 Installation

1. **Clone this repo**:

```bash
git clone https://github.com/yourusername/YoutubeUploader.git
cd YoutubeUploader
```

2. **Create and activate virtual environment**:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Run the app**:

```bash
python main.py
```

---

## 🔐 Google API Setup (for Uploading)

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project and enable the **YouTube Data API v3**
3. Create **OAuth 2.0 Client ID** credentials
4. Download the `client_secrets.json` file and place it in the project root
5. The app will ask you to log in to your Google account on the first upload

Your token will be saved to `token.json` for future use.

---

## 📷 Screenshots

![App Screenshot](https://i.imgur.com/P3mvn7L.png)
![App Screenshot](https://i.imgur.com/Yk78gs8.png)



---

## 💡 Notes

- `yt-dlp` allows downloading from not just YouTube, but **hundreds of supported platforms**.
- Only valid YouTube URLs will display video thumbnails and titles.
- You can drag video or image files directly into the drop area.
- Tokens can expire — if upload fails with `invalid_grant`, delete `token.json` and reauthorize.

---

## 📝 License

This project is released under the MIT License.

---

## 🤝 Contributions

Pull requests and suggestions are welcome!