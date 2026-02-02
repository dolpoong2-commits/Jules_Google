import tkinter as tk

class SubtitleOverlay:
    def __init__(self, master, region):
        """
        Initialize the overlay window.
        :param master: The root tkinter window.
        :param region: dict {'top': int, 'left': int, 'width': int, 'height': int}
        """
        self.top = tk.Toplevel(master)

        # Remove window decorations (frameless)
        self.top.overrideredirect(True)

        # Set geometry
        self.top.geometry(f"{region['width']}x{region['height']}+{region['left']}+{region['top']}")

        # Keep on top
        self.top.attributes('-topmost', True)

        # Background style (semi-transparent black to cover underlying subtitles)
        self.top.config(bg='black')
        self.top.attributes('-alpha', 0.8)

        # Label for text
        # wraplength ensures text doesn't flow out of the box
        self.label = tk.Label(self.top, text="", fg="white", bg="black",
                              font=("Arial", 20, "bold"), wraplength=region['width'])
        self.label.pack(expand=True, fill="both")

    def update_text(self, text):
        """
        Update the displayed text.
        """
        self.label.config(text=text)

    def close(self):
        """
        Close the overlay.
        """
        self.top.destroy()
