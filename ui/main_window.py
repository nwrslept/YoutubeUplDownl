from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QFileDialog, QTextEdit, QFrame
)
from PyQt6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QMouseEvent
from PyQt6.QtCore import Qt
from qasync import asyncSlot
from services.downloader import async_get_video_info, async_download_youtube_video
from services.uploader import upload_video
import aiohttp
import asyncio
import os


class ClickableDropLabel(QLabel):
    def __init__(self, text="", parent=None, file_types=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 2px dashed #666; background-color: #333; color: #ccc;")
        self.setFixedSize(320, 180)
        self.file_path = None
        self.file_types = file_types or []

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_file_dialog()

    def open_file_dialog(self):
        filter_str = "Files (" + " ".join(f"*.{ext}" for ext in self.file_types) + ")"
        path, _ = QFileDialog.getOpenFileName(self, "Select a file", filter=filter_str)
        if path:
            self.set_file(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(tuple(self.file_types)):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isfile(path):
                self.set_file(path)
        event.acceptProposedAction()

    def set_file(self, path: str):
        self.file_path = path
        self.setText(os.path.basename(path))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Downloader & Uploader")
        self.setGeometry(100, 100, 1600, 900)

        # Load external stylesheet
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of this script
            style_path = os.path.join(base_dir, "..", "styles.qss")  # Stylesheet located one level up
            style_path = os.path.abspath(style_path)

            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"⚠️ Unable to load styles.qss: {e}")

        self.cancel_flag = {"cancel": False}
        self.selected_folder = "."
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # === LEFT PANEL ===
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_frame.setStyleSheet("border-right: 2px solid #444;")

        self.left_preview_label = QLabel("Video Preview")
        self.left_preview_label.setFixedHeight(200)
        self.left_preview_label.setStyleSheet("background-color: #444;")
        self.left_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.left_preview_label)

        self.left_title_label = QLabel("")
        self.left_title_label.setStyleSheet("color: #ddd; font-weight: bold; font-size: 16px;")
        left_layout.addWidget(self.left_title_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube video URL here...")
        self.url_input.textChanged.connect(self.on_url_changed)
        left_layout.addWidget(self.url_input)

        self.quality_box = QComboBox()
        self.quality_box.addItem("1080p", "bestvideo[height<=1080]+bestaudio/best[height<=1080]")
        self.quality_box.addItem("720p", "bestvideo[height<=720]+bestaudio/best[height<=720]")
        self.quality_box.addItem("480p", "bestvideo[height<=480]+bestaudio/best[height<=480]")
        self.quality_box.addItem("360p", "bestvideo[height<=360]+bestaudio/best[height<=360]")
        self.quality_box.addItem("Audio only", "bestaudio")
        left_layout.addWidget(self.quality_box)

        self.folder_btn = QPushButton("Select download folder")
        self.folder_btn.clicked.connect(self.select_folder)
        left_layout.addWidget(self.folder_btn)

        self.download_btn = QPushButton("Download")
        self.download_btn.setStyleSheet("background-color: #007acc;")
        self.download_btn.clicked.connect(self.download_video)
        left_layout.addWidget(self.download_btn)

        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setEnabled(False)
        left_layout.addWidget(self.cancel_btn)

        left_layout.addStretch()

        # === RIGHT PANEL ===
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)

        top_right_row = QHBoxLayout()

        self.right_preview_label = QLabel("Video Preview")
        self.right_preview_label.setFixedSize(480, 270)
        self.right_preview_label.setStyleSheet("background-color: #444;")
        self.right_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_right_row.addWidget(self.right_preview_label)

        self.drag_drop_video_area = ClickableDropLabel("Drag and drop or click to select video", file_types=['mp4', 'avi', 'mov', 'mkv'])
        top_right_row.addWidget(self.drag_drop_video_area)

        right_layout.addLayout(top_right_row)

        self.thumbnail_btn = QPushButton("Upload thumbnail image")
        self.thumbnail_btn.clicked.connect(self.load_thumbnail_from_file)
        right_layout.addWidget(self.thumbnail_btn)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Video title")
        right_layout.addWidget(self.title_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Video description")
        self.description_input.setFixedHeight(120)
        right_layout.addWidget(self.description_input)

        self.privacy_box = QComboBox()
        self.privacy_box.addItem("Public", "public")
        self.privacy_box.addItem("Private", "private")
        self.privacy_box.addItem("Unlisted", "unlisted")
        right_layout.addWidget(self.privacy_box)

        # Upload button and progress label
        self.upload_btn = QPushButton("Upload to YouTube")
        self.upload_btn.setStyleSheet("background-color: #28a745;")
        self.upload_btn.clicked.connect(self.upload_video_async)
        right_layout.addWidget(self.upload_btn)

        self.upload_percent_label = QLabel("")
        self.upload_percent_label.setStyleSheet("color: #ddd; font-weight: bold; padding: 4px 0;")
        right_layout.addWidget(self.upload_percent_label)

        self.video_url_field = QLineEdit()
        self.video_url_field.setReadOnly(True)
        self.video_url_field.setPlaceholderText("Video link will appear here...")
        right_layout.addWidget(self.video_url_field)

        right_layout.addStretch()

        main_layout.addWidget(left_frame, 1)
        main_layout.addWidget(right_frame, 1)

    def load_thumbnail_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select image", filter="Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.right_preview_label.width(),
                    self.right_preview_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.right_preview_label.setPixmap(scaled)
            else:
                self.right_preview_label.setText("Unable to display image")

    @asyncSlot()
    async def on_url_changed(self):
        url = self.url_input.text().strip()
        if not url:
            self.left_preview_label.setText("Video Preview")
            self.left_title_label.setText("")
            return
        try:
            info = await async_get_video_info(url)
            self.left_title_label.setText(info.get("title", ""))
            async with aiohttp.ClientSession() as session:
                async with session.get(info["thumbnail"]) as resp:
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
        except Exception as e:
            print("Error getting video preview:", e)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if folder:
            self.selected_folder = folder
            self.folder_btn.setText(f"📁 {folder}")

    def cancel_download(self):
        self.cancel_flag["cancel"] = True
        self.cancel_btn.setEnabled(False)
        self.download_btn.setText("Cancelling...")

    @asyncSlot()
    async def download_video(self):
        url = self.url_input.text().strip()
        quality = self.quality_box.currentData()
        folder = getattr(self, "selected_folder", ".")

        if not url:
            self.download_btn.setText("❌ No URL provided")
            return

        self.download_btn.setText("Downloading...")
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_flag["cancel"] = False

        def on_progress(percent):
            self.download_btn.setText(f"Downloading {percent:.0f}%")

        try:
            path = await async_download_youtube_video(
                url, quality, on_progress, folder, self.cancel_flag
            )
            if not self.cancel_flag["cancel"]:
                self.download_btn.setText("✅ Downloaded")
                print(f"File saved as: {path}")
            else:
                self.download_btn.setText("🚫 Cancelled")
        except Exception as e:
            print("❌ Download error:", e)
            self.download_btn.setText("❌ Error")
        finally:
            await asyncio.sleep(2)
            self.download_btn.setText("Download")
            self.download_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

    @asyncSlot()
    async def upload_video_async(self):
        video_path = self.drag_drop_video_area.file_path
        title = self.title_input.text().strip()
        description = self.description_input.toPlainText().strip()
        privacy_status = self.privacy_box.currentData()

        if not video_path or not os.path.isfile(video_path):
            self.upload_btn.setText("❌ No video selected")
            return

        if not title:
            self.upload_btn.setText("❌ Enter a title")
            return

        self.upload_btn.setEnabled(False)
        self.upload_btn.setText("Uploading... 0%")
        self.video_url_field.clear()

        def progress_callback(pct):
            self.upload_btn.setText(f"Uploading... {pct}%")

        try:
            response = await asyncio.to_thread(
                upload_video, video_path, title, description, None, "22", privacy_status, progress_callback
            )
            self.upload_btn.setText("✅ Uploaded")
            video_id = response.get("id")
            if video_id:
                self.video_url_field.setText(f"https://youtu.be/{video_id}")
        except Exception as e:
            print("❌ Upload error:", e)
            self.upload_btn.setText("❌ Error")
        finally:
            await asyncio.sleep(2)
            self.upload_btn.setEnabled(True)
            self.upload_btn.setText("Upload to YouTube")
