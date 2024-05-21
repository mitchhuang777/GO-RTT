import time
import mss
import pytesseract
import win32gui
import win32con
from PIL import Image
from googletrans import Translator
from tkinter import Tk, Frame, Label, Button, messagebox, BOTH, TOP, X

class RealTimeOCR:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time OCR and Translation")
        self.root.geometry("800x600")
        
        self.initUI()
        self.translator = Translator()
        self.selected_hwnd = None
        
    def initUI(self):
        self.buttonFrame = Frame(self.root)
        self.buttonFrame.pack(side=TOP, fill=X)
        
        self.selectButton = Button(self.buttonFrame, text="Select Window", command=self.select_window)
        self.selectButton.pack(side=LEFT, padx=10, pady=10)
        
        self.startButton = Button(self.buttonFrame, text="Start OCR", command=self.start_ocr)
        self.startButton.pack(side=LEFT, padx=10, pady=10)
        
        self.stopButton = Button(self.buttonFrame, text="Stop OCR", command=self.stop_ocr)
        self.stopButton.pack(side=LEFT, padx=10, pady=10)
        
        self.textLabel = Label(self.root, text="", wraplength=700)
        self.textLabel.pack(side=TOP, fill=BOTH, expand=True, padx=10, pady=10)
        
        self.ocr_running = False
        
    def select_window(self):
        # 获取用户选中的窗口句柄
        self.selected_hwnd = win32gui.GetForegroundWindow()
        messagebox.showinfo("Window Selected", f"Selected window HWND: {self.selected_hwnd}")
        
    def start_ocr(self):
        if self.selected_hwnd:
            self.ocr_running = True
            self.perform_ocr()
        else:
            messagebox.showwarning("No Selection", "No window has been selected.")
            
    def stop_ocr(self):
        self.ocr_running = False
        
    def perform_ocr(self):
        if not self.ocr_running:
            return
        
        screenshot = self.capture_window(self.selected_hwnd)
        if screenshot:
            text = pytesseract.image_to_string(screenshot)
            translated_text = self.translate_text(text)
            self.textLabel.config(text=translated_text)
        
        self.root.after(1000, self.perform_ocr)
    
    def capture_window(self, hwnd):
        # 如果窗口被最小化，则恢复窗口
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        # 将窗口置于顶层
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"Error bringing window {hwnd} to foreground: {e}")
            return None
        
        # 确保窗口完全恢复并显示
        time.sleep(0.1)
        
        # 获取窗口的截图边界
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        
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
            img = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb)
            return img
    
    def translate_text(self, text):
        try:
            translated = self.translator.translate(text, src='auto', dest='en')
            return translated.text
        except Exception as e:
            print(f"Translation error: {e}")
            return "Translation error"

def main():
    root = Tk()
    app = RealTimeOCR(root)
    root.mainloop()

if __name__ == "__main__":
    main()
