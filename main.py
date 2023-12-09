import sys
import qdarkstyle
import os
# 1. Import QApplication and all the required widgets
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QAction, QTabWidget,QVBoxLayout, QPushButton


def main():
    os.environ['QT_API'] = 'pyqt5'
    # 2. Create an instance of QApplication
    app = QApplication(sys.argv + ['-platform', 'windows:darkmode=1'])


    # 3. Create your application's GUI
    window = QWidget()
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    window.setWindowTitle("PyQt App")
    window.setGeometry(100, 100, 280, 80)
    #helloMsg = QLabel("<h1>Hello, World!</h1>", parent=window)
    #helloMsg.move(60, 15)
    
    layout = QVBoxLayout()
    window.setLayout(layout)
        
    # Initialize tab screen
    tabs = QTabWidget()
    tabOverview = QWidget()
    tabMission = QWidget()
    tabSensors = QWidget()
    tabCustom = QWidget()
    tabs.resize(800,450)
    tabs.move(0,0)
    # Set text size of tabs
    tabs.setStyleSheet("QTabBar::tab { height: 23px; width: 150px; font-size: 12pt; }")
    
    # Add tabs
    tabs.addTab(tabOverview, "Overview")
    tabs.addTab(tabMission, "Mission modes")
    tabs.addTab(tabSensors, "Sensors")
    tabs.addTab(tabCustom, "Custom")
    
    # Create first tab
    tabOverview.layout = QVBoxLayout()
    pushButton1 = QPushButton("PyQt5 button")
    tabOverview.layout.addWidget(pushButton1)
    tabOverview.setLayout(tabOverview.layout)
    
    # Add tabs to widget
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(tabs, 0)

    # 4. Show your application's GUI
    window.show()

    # 5. Run your application's event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()