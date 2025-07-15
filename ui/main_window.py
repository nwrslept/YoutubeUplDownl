# main_window.py

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QFileDialog, QTextEdit, QFrame
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from qasync import asyncSlot
from services.downloader import async_get_video_info, async_download_youtube_video
import aiohttp
import asyncio


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader & Uploader")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("background-color: #2e2e2e; color: white;")
        self.cancel_flag = {"cancel": False}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # ======= LEFT SIDE (Downloader) =======
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_frame.setStyleSheet("border-right: 2px solid #444444;")

        # Preview
        self.left_preview_label = QLabel("Превʼю відео")
        self.left_preview_label.setFixedHeight(200)
        self.left_preview_label.setStyleSheet("background-color: #444;")
        self.left_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.left_preview_label)

        # URL Input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Вставте посилання на відео YouTube...")
        self.url_input.textChanged.connect(self.on_url_changed)
        left_layout.addWidget(self.url_input)

        # Quality Selection
        self.quality_box = QComboBox()
        self.quality_box.addItem("1080p", "bestvideo[height<=1080]+bestaudio/best[height<=1080]")
        self.quality_box.addItem("720p", "bestvideo[height<=720]+bestaudio/best[height<=720]")
        self.quality_box.addItem("480p", "bestvideo[height<=480]+bestaudio/best[height<=480]")
        self.quality_box.addItem("360p", "bestvideo[height<=360]+bestaudio/best[height<=360]")
        self.quality_box.addItem("Аудіо", "bestaudio")
        left_layout.addWidget(self.quality_box)

        # Choose Folder
        self.folder_btn = QPushButton("Вибрати папку збереження")
        self.folder_btn.clicked.connect(self.select_folder)
        left_layout.addWidget(self.folder_btn)

        # Download Button
        self.download_btn = QPushButton("Завантажити")
        self.download_btn.setStyleSheet("background-color: #007acc;")
        self.download_btn.clicked.connect(self.download_video)
        left_layout.addWidget(self.download_btn)

        # Cancel Button
        self.cancel_btn = QPushButton("❌ Скасувати")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setEnabled(False)
        left_layout.addWidget(self.cancel_btn)

        left_layout.addStretch()

        # ======= RIGHT SIDE (Uploader) =======
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)

        # Top row: Preview and Drop Zone
        top_right_row = QHBoxLayout()

        self.right_preview_label = QLabel("Превʼю відео")
        self.right_preview_label.setFixedSize(320, 180)
        self.right_preview_label.setStyleSheet("background-color: #444;")
        self.right_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.drag_drop_area = QLabel("Перетягніть сюди відео")
        self.drag_drop_area.setFixedSize(320, 180)
        self.drag_drop_area.setStyleSheet("border: 2px dashed #666; background-color: #333;")
        self.drag_drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_right_row.addWidget(self.right_preview_label)
        top_right_row.addWidget(self.drag_drop_area)

        right_layout.addLayout(top_right_row)

        # Upload preview image
        self.thumbnail_btn = QPushButton("Завантажити превʼю")
        right_layout.addWidget(self.thumbnail_btn)

        # Title input
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Назва відео")
        right_layout.addWidget(self.title_input)

        # Description input
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Опис відео")
        self.description_input.setFixedHeight(120)
        right_layout.addWidget(self.description_input)

        # Upload button
        self.upload_btn = QPushButton("Завантажити на YouTube")
        self.upload_btn.setStyleSheet("background-color: #28a745;")
        right_layout.addWidget(self.upload_btn)

        right_layout.addStretch()

        # ======= Add frames to main layout =======
        main_layout.addWidget(left_frame, 1)
        main_layout.addWidget(right_frame, 1)

    @asyncSlot()
    async def on_url_changed(self):
        url = self.url_input.text().strip()
        if not url:
            self.left_preview_label.setText("Превʼю відео")
            return

        try:
            info = await async_get_video_info(url)
            self.left_preview_label.setText("Завантажую превʼю...")
            async with aiohttp.ClientSession() as session:
                async with session.get(info['thumbnail']) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        image = QImage.fromData(data)
                        pixmap = QPixmap.fromImage(image).scaled(
                            self.left_preview_label.width(),
                            self.left_preview_label.height(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.left_preview_label.setPixmap(pixmap)
                    else:
                        self.left_preview_label.setText("Не вдалося завантажити превʼю")
        except Exception as e:
            print("Помилка при отриманні превʼю:", e)
            self.left_preview_label.setText("Невірне посилання")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Оберіть папку")
        if folder:
            self.selected_folder = folder
            self.folder_btn.setText(f"📁 {folder}")
        else:
            self.selected_folder = "."

    def cancel_download(self):
        self.cancel_flag["cancel"] = True
        self.cancel_btn.setEnabled(False)
        self.download_btn.setText("Скасування...")

    @asyncSlot()
    async def download_video(self):
        url = self.url_input.text().strip()
        quality = self.quality_box.currentData()
        folder = getattr(self, "selected_folder", ".")

        if not url:
            self.download_btn.setText("❌ Немає посилання")
            return

        self.download_btn.setText("Завантаження...")
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_flag["cancel"] = False

        def on_progress(percent):
            self.download_btn.setText(f"Завантаження {percent:.0f}%")

        try:
            path = await async_download_youtube_video(
                url, quality, on_progress, folder, self.cancel_flag
            )
            if not self.cancel_flag["cancel"]:
                self.download_btn.setText("✅ Завантажено")
                print(f"Файл збережено як: {path}")
            else:
                self.download_btn.setText("🚫 Скасовано")
        except Exception as e:
            print("❌ Помилка при завантаженні:", e)
            self.download_btn.setText("❌ Скасовано")
        finally:
            await asyncio.sleep(2)
            self.download_btn.setText("Завантажити")
            self.download_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
