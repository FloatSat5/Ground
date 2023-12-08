import sys
import qdarkstyle
import os
# 1. Import QApplication and all the required widgets
from PyQt5.QtWidgets import QApplication, QLabel, QWidget


def main():
    os.environ['QT_API'] = 'pyqt5'
    # 2. Create an instance of QApplication
    app = QApplication(sys.argv + ['-platform', 'windows:darkmode=1'])


    # 3. Create your application's GUI
    window = QWidget()
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    window.setWindowTitle("PyQt App")
    window.setGeometry(100, 100, 280, 80)
    helloMsg = QLabel("<h1>Hello, World!</h1>", parent=window)
    helloMsg.move(60, 15)

    # 4. Show your application's GUI
    window.show()

    # 5. Run your application's event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()