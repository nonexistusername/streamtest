import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkFont
import threading
import time
import os
import requests
import subprocess

class StreamCheckerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("STREAMTEST ADVANCED")
        self.master.geometry("700x500")

        self.filename = ""
        self.speed = tk.IntVar(value=3)
        self.running = False
        self.paused = False
        self.streams = []
        self.valid_count = 0
        self.invalid_count = 0

        self.result_widgets = []
        self.build_gui()
        self.build_menu()

        # Cross-platform default output path
        self.output_dir = os.path.join(os.path.expanduser("~"), "STREAMTEST")
        self.valid_file = os.path.join(self.output_dir, "valid_streams.m3u")
        self.invalid_file = os.path.join(self.output_dir, "invalid_streams.m3u")

        os.makedirs(self.output_dir, exist_ok=True)
        open(self.valid_file, 'w').close()
        open(self.invalid_file, 'w').close()

    def build_gui(self):
        label_font = ("Arial", 11, "bold")

        tk.Label(self.master, text="Selected File:", font=label_font).pack()
        self.file_label = tk.Label(self.master, text="No file loaded", font=label_font)
        self.file_label.pack()

        tk.Label(self.master, text="TESTING SPEED (THREADS)", font=label_font).pack(pady=5)

        tk.Scale(
            self.master,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.speed,
            length=300,
            width=18,
            sliderlength=20,
            showvalue=True,
            font=("Courier", 11, "bold"),
            troughcolor="lightgray",
            fg="black",
            bg="white",
            highlightthickness=0
        ).pack(pady=5)

        self.count_label = tk.Label(self.master, text="Total: 0 | Functional: 0 | Broken: 0", font=("Arial", 13, "bold"))
        self.count_label.pack(pady=5)

        self.result_frame = tk.Frame(self.master)
        self.result_frame.pack(fill="both", expand=True)

        self.result_canvas = tk.Canvas(self.result_frame)
        self.scrollbar = tk.Scrollbar(self.result_frame, command=self.result_canvas.yview)
        self.scrollable_frame = tk.Frame(self.result_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.result_canvas.configure(
                scrollregion=self.result_canvas.bbox("all")
            )
        )

        self.result_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.result_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.result_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def build_menu(self):
        menubar = tk.Menu(self.master)

        custom_font = tkFont.Font(family="Arial", size=12, weight="bold")

        options_menu = tk.Menu(menubar, tearoff=0, font=custom_font)
        options_menu.add_command(label="📂 Load File", command=self.load_file, font=custom_font)
        options_menu.add_command(label="🚀 Start Testing", command=self.start_testing, font=custom_font)
        options_menu.add_command(label="⏸️ Pause / Resume", command=self.pause_resume, font=custom_font)

        menubar.add_cascade(label="OPTIONS", menu=options_menu, font=custom_font)
        self.master.config(menu=menubar)

    def load_file(self):
        self.filename = filedialog.askopenfilename(filetypes=[("M3U files", "*.m3u")])
        if self.filename:
            self.file_label.config(text=self.filename)
            self.load_streams()

    def load_streams(self):
        self.streams = []
        with open(self.filename, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    full_extinf = lines[i].strip()
                    try:
                        display_name = lines[i].split(",", 1)[1].strip()
                    except IndexError:
                        display_name = "Unknown"
                    if i + 1 < len(lines) and lines[i+1].startswith("http"):
                        url = lines[i + 1].strip()
                        self.streams.append((display_name, full_extinf, url))
        self.update_ui()

    def start_testing(self):
        if not self.streams:
            messagebox.showerror("Error", "Please load a .m3u file before starting the test.")
            return
        if not self.running:
            self.running = True
            self.paused = False
            self.valid_count = 0
            self.invalid_count = 0
            self.clear_results()
            threading.Thread(target=self.process_streams).start()

    def pause_resume(self):
        self.paused = not self.paused

    def process_streams(self):
        for name, extinf, url in self.streams:
            while self.paused:
                time.sleep(0.5)

            status = self.check_stream(url)
            if status:
                self.valid_count += 1
                self.display_result(name, url, valid=True)
                self.save_stream(extinf, url, self.valid_file)
            else:
                self.invalid_count += 1
                self.display_result(name, url, valid=False)
                self.save_stream(extinf, url, self.invalid_file)

            self.update_ui()
            time.sleep(1 / self.speed.get())

        self.running = False

    def check_stream(self, url):
        try:
            response = requests.get(url, timeout=5, stream=True)
            return response.status_code == 200
        except:
            return False

    def display_result(self, name, url, valid):
        frame = tk.Frame(self.scrollable_frame)
        label = tk.Label(
            frame,
            text=f"✅ {name}" if valid else f"❌ {name}",
            fg="green" if valid else "red",
            font=("Courier", 11, "bold")
        )
        label.pack(side="left", padx=5)

        btn = tk.Button(
            frame,
            text="▶ OPEN IN VLC",
            font=("Arial", 10, "bold"),
            command=lambda u=url: self.open_in_vlc(u)
        )
        btn.pack(side="right", padx=10)

        frame.pack(anchor="w", pady=2)
        self.result_widgets.append(frame)

    def open_in_vlc(self, url):
        try:
            subprocess.Popen(["vlc", url])
        except Exception as e:
            messagebox.showerror("VLC Error", f"Could not launch VLC: {str(e)}")

    def update_ui(self):
        total = len(self.streams)
        self.count_label.config(text=f"Total: {total} | Functional: {self.valid_count} | Broken: {self.invalid_count}")

    def save_stream(self, extinf, url, filepath):
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"{extinf}\n{url}\n")

    def clear_results(self):
        for widget in self.result_widgets:
            widget.destroy()
        self.result_widgets = []

# Run
if __name__ == "__main__":
    root = tk.Tk()
    app = StreamCheckerApp(root)
    root.mainloop()
