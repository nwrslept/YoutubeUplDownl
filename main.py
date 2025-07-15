# main.py
import sys
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
import asyncio

def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.showMaximized()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
