from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QComboBox, QCheckBox, QProgressBar, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from qasync import asyncSlot
from services.downloader import async_download_youtube_video, async_get_video_info
import os
import requests
from functools import partial
import asyncio


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Video Uploader")
        self.setMinimumSize(900, 550)
        self.video_path = None
        self.download_folder = os.getcwd()
        self._last_progress = 0

        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(30)

        # Left column: URL input, video preview, download button
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        left_layout.addWidget(QLabel("🔗 Paste YouTube video link:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setMinimumHeight(36)
        left_layout.addWidget(self.url_input)

        self.video_title_label = QLabel()
        self.video_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_title_label.setWordWrap(True)
        self.video_title_label.setVisible(False)
        left_layout.addWidget(self.video_title_label)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setVisible(False)
        self.thumbnail_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.thumbnail_label.setFixedHeight(180)
        left_layout.addWidget(self.thumbnail_label)

        left_layout.addSpacerItem(QSpacerItem(20, 20))  # Visual spacing

        self.download_btn = QPushButton("⬇️ Download from YouTube")
        self.download_btn.setMinimumHeight(36)
        left_layout.addWidget(self.download_btn)

        left_layout.addStretch()

        # Right column: download options
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)

        folder_btn = QPushButton("📁 Choose download folder")
        folder_btn.setMinimumHeight(36)
        right_layout.addWidget(folder_btn)

        right_layout.addWidget(QLabel("📺 Select video quality:"))
        self.quality_selector = QComboBox()
        self.quality_selector.addItems(["480p", "720p", "1080p", "Max quality"])
        self.quality_selector.setMinimumHeight(30)
        right_layout.addWidget(self.quality_selector)

        self.no_audio_checkbox = QCheckBox("Download without audio")
        right_layout.addWidget(self.no_audio_checkbox)

        right_layout.addStretch()

        # Bottom layout: progress and status
        bottom_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        bottom_layout.addWidget(self.status_label)

        # Combine all layouts
        container_layout = QVBoxLayout()
        container_layout.addLayout(main_layout)
        container_layout.addLayout(bottom_layout)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.setLayout(container_layout)

        # Connect buttons and signals
        folder_btn.clicked.connect(self.choose_download_folder)
        self.download_btn.clicked.connect(self.download_video)

        self.url_check_timer = QTimer()
        self.url_check_timer.setInterval(200)
        self.url_check_timer.setSingleShot(True)
        self.url_check_timer.timeout.connect(self.fetch_video_info)

        self.url_input.textChanged.connect(self.on_url_changed)

        self.load_styles("styles.qss")

    def load_styles(self, path):
        """Load and apply external QSS stylesheet."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Failed to load styles: {e}")

    def choose_download_folder(self):
        """Open folder dialog to select download destination."""
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if folder:
            self.download_folder = folder
            self.status_label.setText(f"📁 Save to: {folder}")

    def get_format(self):
        """Return yt-dlp format string based on selected options."""
        quality = self.quality_selector.currentText()
        no_audio = self.no_audio_checkbox.isChecked()

        height = None
        if quality == "480p":
            height = 480
        elif quality == "720p":
            height = 720
        elif quality == "1080p":
            height = 1080

        if quality == "Max quality":
            return 'best[ext=mp4]' if no_audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'

        if no_audio:
            return f"bestvideo[height<={height}][ext=mp4]"
        else:
            return f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"

    def update_progress(self, percent: float):
        """Update download progress bar."""
        percent_int = int(percent)
        if percent_int == 100:
            self.progress_bar.setValue(100)
        elif percent_int > self._last_progress:
            self.progress_bar.setValue(percent_int)
            self._last_progress = percent_int
            self.status_label.setText("⏳ Downloading...")

    def on_url_changed(self):
        """Start timer to fetch video info after URL changes."""
        self.url_check_timer.start()

    @asyncSlot()
    async def fetch_video_info(self):
        """Fetch video title and thumbnail from YouTube."""
        url = self.url_input.text().strip()
        if not url or ("youtube.com" not in url and "youtu.be" not in url):
            self.video_title_label.setVisible(False)
            self.thumbnail_label.setVisible(False)
            return

        try:
            self.status_label.setText("🔍 Fetching video info...")
            info = await async_get_video_info(url)

            self.video_title_label.setText(f"🎬 {info['title']}")
            self.video_title_label.setVisible(True)

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, partial(requests.get, info['thumbnail'], timeout=5))

            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            self.thumbnail_label.setPixmap(pixmap.scaledToWidth(320))
            self.thumbnail_label.setVisible(True)

            self.status_label.setText("ℹ️ Video found")
        except Exception as e:
            self.video_title_label.setVisible(False)
            self.thumbnail_label.setVisible(False)
            self.status_label.setText(f"⚠️ Failed to load video: {e}")

    @asyncSlot()
    async def download_video(self):
        """Download the selected YouTube video asynchronously."""
        url = self.url_input.text().strip()
        if not url:
            self.status_label.setText("⚠️ Please enter a video URL")
            return

        fmt = self.get_format()

        self._last_progress = 0
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("⏳ Downloading...")

        try:
            self.video_path = await async_download_youtube_video(
                url, fmt, progress_hook=self.update_progress, output_dir=self.download_folder
            )
            self.progress_bar.setValue(100)
            self.status_label.setText(f"✅ Downloaded to: {self.video_path}")
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"❌ Error: {e}")

    def choose_video(self):
        """Select a local video file manually."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose a video file", "", "Video Files (*.mp4 *.mov *.avi *.mkv)"
        )
        if file_path:
            self.video_path = file_path
            self.status_label.setText(f"📁 Selected: {file_path}")
