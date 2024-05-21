from tkinter import Tk
from monitor_screen.monitor_screen_app import MonitorScreenApp

def main():
    root = Tk()
    app = MonitorScreenApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
