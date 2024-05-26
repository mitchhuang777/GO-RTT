import pytesseract
from pytesseract import Output
import cv2
import time
import mss
import win32gui
import win32con
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
from translate import Translator

custom_config = r'-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz --psm 11 --oem 3'

class OverlayWindow(QtWidgets.QWidget):
    def __init__(self, hwnd):
        super().__init__()
        self.hwnd = hwnd
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        # 获取窗口位置和大小
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        self.setGeometry(left, top, right - left, bottom - top)

        # 初始化 boxes 属性
        self.boxes = []

        # 设置快捷键
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("q"), self)
        self.shortcut.activated.connect(self.close_app)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

        # 画OCR检测的边界框和翻译后的文字
        for box in self.boxes:
            # 灰色遮罩
            painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 127)))  # 半透明黑色
            painter.drawRect(box['left'], box['top'], box['width'], box['height'])

            # 翻译后的文字
            painter.setPen(QtGui.QPen(QtCore.Qt.red))
            painter.setFont(QtGui.QFont('Arial', 12))
            painter.drawText(box['left'], box['top'] + box['height'], box['translated_text'])

    def update_boxes(self, boxes):
        self.boxes = boxes
        self.update()

    def close_app(self):
        QtCore.QCoreApplication.quit()

class RealTimeOCR(QtCore.QObject):
    update_signal = QtCore.pyqtSignal(list)

    def __init__(self, hwnd):
        super().__init__()
        self.hwnd = hwnd
        self.translator = Translator(to_lang="zh")

    def start(self):
        while True:
            self.process()
            time.sleep(0.1)  # 每0.1秒截屏一次

    def process(self):
        screen_image = self.capture_window()
        if screen_image is not None:
            boxes = self.extract_text_with_boxes(screen_image)
            self.update_signal.emit(boxes)

    def capture_window(self):
        # 如果窗口被最小化，则恢复窗口
        if win32gui.IsIconic(self.hwnd):
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)

        # 将窗口置于顶层
        try:
            win32gui.SetForegroundWindow(self.hwnd)
        except Exception as e:
            print(f"Error bringing window {self.hwnd} to foreground: {e}")
            return None

        # 确保窗口完全恢复并显示
        time.sleep(0.1)

        # 获取窗口的截图边界
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)

        # 如果宽度或高度为零，则跳过
        if right - left == 0 or bottom - top == 0:
            return None

        # 使用 mss 截取窗口画面
        with mss.mss() as sct:
            monitor = {
                "top": top,
                "left": left,
                "width": right - left,
                "height": bottom - top,
            }
            sct_img = sct.grab(monitor)
            img = np.array(sct_img)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # 将 BGRA 转换为 BGR
            return img

    def extract_text_with_boxes(self, image):
        # 使用 tesseract 来提取图像中的文字并获取边界框
        data = pytesseract.image_to_data(image, config=custom_config, output_type=Output.DICT)
        boxes = []
        amount_boxes = len(data['text'])
        for i in range(amount_boxes):
            (x, y, width, height) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            text = data['text'][i]
            if text.strip() != "":
                try:
                    translated_text = self.translator.translate(text)
                except Exception as e:
                    translated_text = text  # 如果翻译失败，显示原文
                boxes.append({
                    'left': x,
                    'top': y,
                    'width': width,
                    'height': height,
                    'translated_text': translated_text
                })
        return boxes

if __name__ == "__main__":
    import sys
    hwnd = int(input("Enter the hwnd of the window you want to capture: "))
    app = QtWidgets.QApplication(sys.argv)
    overlay_window = OverlayWindow(hwnd)
    overlay_window.show()

    ocr = RealTimeOCR(hwnd)
    ocr.update_signal.connect(overlay_window.update_boxes)
    ocr_thread = threading.Thread(target=ocr.start)
    ocr_thread.daemon = True
    ocr_thread.start()

    sys.exit(app.exec_())
