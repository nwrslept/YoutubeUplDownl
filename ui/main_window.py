from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QComboBox, QCheckBox, QProgressBar
)
from PyQt6.QtCore import Qt
from qasync import asyncSlot
from services.downloader import async_download_youtube_video
from services.uploader import upload_video_to_youtube

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Video Uploader")
        self.setFixedSize(600, 400)
        self.video_path = None

        layout = QVBoxLayout()
        self.url_input = QLineEdit()
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.quality_selector = QComboBox()
        self.no_audio_checkbox = QCheckBox("Завантажити без звуку")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self._last_progress = 0

        self.init_ui(layout)
        self.setLayout(layout)

    def init_ui(self, layout):
        layout.addWidget(QLabel("🔗 Встав посилання на відео YouTube:"))
        layout.addWidget(self.url_input)

        self.quality_selector.addItems(["480p", "720p", "1080p", "Максимальна якість"])
        layout.addWidget(QLabel("📺 Обрати якість відео:"))
        layout.addWidget(self.quality_selector)

        layout.addWidget(self.no_audio_checkbox)

        download_btn = QPushButton("⬇️ Завантажити з YouTube")
        download_btn.clicked.connect(self.download_video)
        layout.addWidget(download_btn)

        choose_btn = QPushButton("📂 Вибрати локальний відеофайл")
        choose_btn.clicked.connect(self.choose_video)
        layout.addWidget(choose_btn)

        upload_btn = QPushButton("⤴️ Завантажити на YouTube")
        upload_btn.clicked.connect(self.upload_video)
        layout.addWidget(upload_btn)

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

    def get_format(self):
        quality = self.quality_selector.currentText()
        no_audio = self.no_audio_checkbox.isChecked()

        height = None
        if quality == "480p":
            height = 480
        elif quality == "720p":
            height = 720
        elif quality == "1080p":
            height = 1080

        if quality == "Максимальна якість":
            return 'best[ext=mp4]' if no_audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'

        if no_audio:
            return f"bestvideo[height<={height}][ext=mp4]"
        else:
            return f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"

    def update_progress(self, percent: float):
        percent_int = int(percent)
        if percent_int > self._last_progress:
            self.progress_bar.setValue(percent_int)
            self._last_progress = percent_int

    @asyncSlot()
    async def download_video(self):
        url = self.url_input.text().strip()
        if not url:
            self.status_label.setText("⚠️ Введіть посилання на відео")
            return

        fmt = self.get_format()

        self._last_progress = 0
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("⏳ Завантаження...")

        try:
            self.video_path = await async_download_youtube_video(url, fmt, progress_hook=self.update_progress)
            self.progress_bar.setValue(100)
            self.status_label.setText(f"✅ Завантажено: {self.video_path}")
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"❌ Помилка: {e}")

    def choose_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Вибрати відео", "", "Video Files (*.mp4 *.mov *.avi *.mkv)"
        )
        if file_path:
            self.video_path = file_path
            self.status_label.setText(f"📁 Вибрано: {file_path}")

    def upload_video(self):
        if not self.video_path:
            self.status_label.setText("⚠️ Виберіть або завантажте відео")
            return
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(20)
            video_id = upload_video_to_youtube(self.video_path)
            self.progress_bar.setValue(100)
            self.status_label.setText(f"✅ Завантажено. ID: {video_id}")
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"❌ Помилка при завантаженні: {e}")
