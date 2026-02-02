import tkinter as tk
import threading
import time
import platform
from subtitle_processor import SubtitleProcessor
from region_selector import RegionSelector
from subtitle_overlay import SubtitleOverlay

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Subtitle Translator")
        self.root.geometry("350x300")
        self.root.attributes('-topmost', True) # Keep controls on top initially

        self.input_region = None
        self.output_region = None
        self.overlay = None
        self.processor = SubtitleProcessor()

        self.running = False
        self.paused = False
        self.thread = None
        self.last_text = ""

        # Handle Window Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # UI Elements
        tk.Label(root, text="Step 1: Select Regions", font=("Arial", 12, "bold")).pack(pady=5)

        self.btn_input = tk.Button(root, text="1. Drag Input Area (English Subtitles)", command=self.select_input)
        self.btn_input.pack(pady=5)

        self.btn_output = tk.Button(root, text="2. Drag Output Area (Korean Translation)", command=self.select_output)
        self.btn_output.pack(pady=5)

        tk.Label(root, text="Step 2: Controls", font=("Arial", 12, "bold")).pack(pady=10)

        self.btn_start = tk.Button(root, text="Start", command=self.start_translation, state=tk.DISABLED, bg="green", fg="white", width=10)
        self.btn_start.pack(pady=5)

        self.btn_pause = tk.Button(root, text="Pause", command=self.pause_translation, state=tk.DISABLED, width=10)
        self.btn_pause.pack(pady=5)

        self.btn_stop = tk.Button(root, text="Stop", command=self.stop_translation, state=tk.DISABLED, bg="red", fg="white", width=10)
        self.btn_stop.pack(pady=5)

        self.status_label = tk.Label(root, text="Ready", fg="blue")
        self.status_label.pack(side=tk.BOTTOM, pady=5)

    def select_input(self):
        # Hide main window during selection to not interfere
        self.root.withdraw()
        selector = RegionSelector(self.root)
        self.input_region = selector.select_region()
        self.root.deiconify()

        if self.input_region:
            print(f"Input Region: {self.input_region}")
            self.btn_input.config(bg="lightgray")
            self.check_ready()

    def select_output(self):
        self.root.withdraw()
        selector = RegionSelector(self.root)
        self.output_region = selector.select_region()
        self.root.deiconify()

        if self.output_region:
            print(f"Output Region: {self.output_region}")
            self.btn_output.config(bg="lightgray")
            self.check_ready()

    def check_ready(self):
        if self.input_region and self.output_region:
            self.btn_start.config(state=tk.NORMAL)
            self.status_label.config(text="Regions Selected. Ready to Start.")

    def start_translation(self):
        if not self.input_region or not self.output_region:
            return

        if self.paused:
            self.paused = False
            self.btn_start.config(state=tk.DISABLED, text="Start")
            self.btn_pause.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
            self.status_label.config(text="Running...")
            return

        self.running = True
        self.paused = False

        # Create overlay if not exists
        if not self.overlay:
            self.overlay = SubtitleOverlay(self.root, self.output_region)

        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_input.config(state=tk.DISABLED)
        self.btn_output.config(state=tk.DISABLED)
        self.status_label.config(text="Running...")

        self.thread = threading.Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.start()

    def pause_translation(self):
        self.paused = True
        self.btn_start.config(state=tk.NORMAL, text="Resume")
        self.btn_pause.config(state=tk.DISABLED)
        self.status_label.config(text="Paused")

    def stop_translation(self):
        self.running = False
        self.paused = False
        if self.overlay:
            self.overlay.close()
            self.overlay = None

        self.btn_start.config(state=tk.NORMAL, text="Start")
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_input.config(state=tk.NORMAL)
        self.btn_output.config(state=tk.NORMAL)
        self.status_label.config(text="Stopped")
        self.last_text = ""

    def loop(self):
        while self.running:
            if self.paused:
                time.sleep(0.5)
                continue

            try:
                # 1. Capture
                img = self.processor.capture_region(self.input_region)

                # 2. Extract
                text = self.processor.extract_text(img)

                # 3. Translate if new
                if text and text != self.last_text:
                    self.last_text = text
                    print(f"Detected: {text}")
                    translated = self.processor.translate_text(text)
                    print(f"Translated: {translated}")

                    # 4. Update UI (Thread safe)
                    self.root.after(0, self.overlay.update_text, translated)
                elif not text:
                    # Optional: handle empty text?
                    pass

            except Exception as e:
                print(f"Loop Error: {e}")

            time.sleep(0.5) # Adjust polling frequency

    def on_close(self):
        self.running = False
        if self.overlay:
            self.overlay.close()
        self.root.destroy()

if __name__ == "__main__":
    # Enable DPI Awareness on Windows to ensure coordinates match screen pixels
    if platform.system() == "Windows":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception as e:
            print(f"DPI Awareness failed: {e}")

    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()
