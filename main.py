import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QScrollArea, QRadioButton, QButtonGroup
from PyQt5.QtCore import QTimer, Qt
from pygetwindow import getWindowsWithTitle
import mss
import io
from PyQt5.QtGui import QPixmap, QImage
import win32gui
import win32con
import time

class ListAppTitlesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("List App Titles App")
        self.setGeometry(100, 100, 600, 400)
        
        self.initUI()
        
        # 保持对预览窗口的引用
        self.preview_windows = []
        
    def initUI(self):
        layout = QVBoxLayout()
        
        self.listButton = QPushButton("List Open Windows")
        self.listButton.clicked.connect(self.list_open_windows)
        layout.addWidget(self.listButton)
        
        self.selectButton = QPushButton("Select")
        self.selectButton.clicked.connect(self.select_window)
        layout.addWidget(self.selectButton)
        
        self.scrollArea = QScrollArea()
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout()
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        layout.addWidget(self.scrollArea)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.buttonGroup = QButtonGroup()
        
    def list_open_windows(self):
        windows = getWindowsWithTitle('')
        self.clear_scroll_layout()
        
        for window in windows:
            title = window.title
            if title:  # 只显示有标题的窗口
                radioButton = QRadioButton(title)
                self.buttonGroup.addButton(radioButton)
                self.scrollLayout.addWidget(radioButton)
    
    def select_window(self):
        selected_button = self.buttonGroup.checkedButton()
        if selected_button:
            selected_title = selected_button.text()
            windows = getWindowsWithTitle(selected_title)
            if windows:
                window = windows[0]
                hwnd = window._hWnd
                
                # 如果窗口被最小化，则恢复窗口
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # 将窗口置于顶层
                win32gui.SetForegroundWindow(hwnd)
                
                # 确保窗口完全恢复并显示
                time.sleep(0.5)
                
                # 再次检查窗口是否在最前面
                if hwnd != win32gui.GetForegroundWindow():
                    return
                
                # 获取窗口的截图边界
                bbox = (window.left, window.top, window.right, window.bottom)
                
                # 使用 mss 截取窗口画面
                with mss.mss() as sct:
                    monitor = {
                        "top": bbox[1],
                        "left": bbox[0],
                        "width": bbox[2] - bbox[0],
                        "height": bbox[3] - bbox[1],
                    }
                    sct_img = sct.grab(monitor)
                    
                    img_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
                    qimage = QImage.fromData(img_bytes)
                    pixmap = QPixmap.fromImage(qimage)
                
                # 缩放截图以适应 600x600 的预览框
                pixmap = pixmap.scaled(600, 600, Qt.KeepAspectRatio)
                
                preview_window = QMainWindow()
                preview_window.setWindowTitle(f"Preview - {selected_title}")
                preview_window.setGeometry(100, 100, 600, 600)
                
                label = QLabel()
                label.setPixmap(pixmap)
                preview_window.setCentralWidget(label)
                preview_window.show()
                
                self.preview_windows.append(preview_window)
                
                # 使用 QTimer 在预览窗口显示后将其置顶
                QTimer.singleShot(0, preview_window.raise_)

    def clear_scroll_layout(self):
        for i in reversed(range(self.scrollLayout.count())):
            widget = self.scrollLayout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

def main():
    app = QApplication(sys.argv)
    window = ListAppTitlesApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
