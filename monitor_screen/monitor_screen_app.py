import sys
import time
import mss
import win32gui
import win32con
import io
from PIL import Image, ImageTk
from tkinter import Tk, Frame, Label, Button, Scrollbar, Canvas, IntVar, VERTICAL, RIGHT, Y, LEFT, BOTH, X, TOP, BOTTOM, messagebox
from PyQt5 import QtWidgets
import threading
from monitor_screen.real_time_ocr import RealTimeOCR, OverlayWindow

class ScrollableFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)

        self.canvas = Canvas(self)
        self.scrollbar = Scrollbar(self, orient=VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        # 绑定鼠标滚轮事件
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

class MonitorScreenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor Screen App")
        self.root.geometry("800x600")

        self.initUI()

    def initUI(self):
        self.buttonFrame = Frame(self.root)
        self.buttonFrame.pack(side=TOP, fill=X)

        self.listButton = Button(self.buttonFrame, text="List and Preview Open Windows", command=self.list_and_preview_windows)
        self.listButton.pack(side=LEFT, padx=10, pady=10)

        self.confirmButton = Button(self.buttonFrame, text="Confirm Selection", command=self.confirm_selection)
        self.confirmButton.pack(side=LEFT, padx=10, pady=10)

        self.ocrButton = Button(self.buttonFrame, text="Start OCR", command=self.start_ocr)
        self.ocrButton.pack(side=LEFT, padx=10, pady=10)

        self.scrollable_frame = ScrollableFrame(self.root)
        self.scrollable_frame.pack(fill=BOTH, expand=True)

        self.selected_hwnd = None
        self.highlighted_label = None
        self.ocr_thread = None

    def list_and_preview_windows(self):
        for widget in self.scrollable_frame.scrollable_frame.winfo_children():
            widget.destroy()

        windows = self.get_open_windows()

        row = 0
        col = 0

        for hwnd, title in windows:
            screenshot = self.capture_window(hwnd)
            if screenshot:
                if len(title) > 15:
                    display_title = title[:15] + "..."
                else:
                    display_title = title

                img = ImageTk.PhotoImage(screenshot)
                labelImage = Label(self.scrollable_frame.scrollable_frame, image=img)
                labelImage.image = img
                labelImage.grid(row=row, column=col, padx=5, pady=5)
                labelImage.bind("<Button-1>", lambda e, hwnd=hwnd, label=labelImage: self.on_thumbnail_click(hwnd, label))

                textLabel = Label(self.scrollable_frame.scrollable_frame, text=display_title)
                textLabel.grid(row=row + 2, column=col, padx=5, pady=5)

                col += 1
                if col >= 3:  # 每行最多三列
                    col = 0
                    row += 3  # 每三行换行

    def get_open_windows(self):
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                class_name = win32gui.GetClassName(hwnd)
                if class_name not in ['Progman', 'WorkerW']:
                    windows.append((hwnd, win32gui.GetWindowText(hwnd)))
        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows

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
            img = img.resize((200, 200), Image.LANCZOS)
            return img

    def on_thumbnail_click(self, hwnd, label):
        # 移除之前的高亮效果
        if self.highlighted_label:
            self.highlighted_label.config(borderwidth=0, relief="flat")

        # 设置当前的高亮效果
        label.config(borderwidth=2, relief="solid")
        self.highlighted_label = label
        self.selected_hwnd = hwnd

    def confirm_selection(self):
        if self.selected_hwnd:
            try:
                # 将窗口置于顶层并显示
                if win32gui.IsIconic(self.selected_hwnd):
                    win32gui.ShowWindow(self.selected_hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(self.selected_hwnd)
                messagebox.showinfo("Selection Confirmed", f"Window with HWND {self.selected_hwnd} is now active.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to bring window to foreground: {e}")
        else:
            messagebox.showwarning("No Selection", "No window has been selected.")

    def start_ocr(self):
        if self.selected_hwnd:
            app = QtWidgets.QApplication(sys.argv)
            overlay_window = OverlayWindow(self.selected_hwnd)
            overlay_window.show()

            self.ocr = RealTimeOCR(self.selected_hwnd)
            self.ocr.update_signal.connect(overlay_window.update_boxes)
            self.ocr_thread = threading.Thread(target=self.ocr.start)
            self.ocr_thread.daemon = True
            self.ocr_thread.start()

            app.exec_()
        else:
            messagebox.showwarning("No Selection", "No window has been selected.")

if __name__ == "__main__":
    root = Tk()
    app = MonitorScreenApp(root)
    root.mainloop()
