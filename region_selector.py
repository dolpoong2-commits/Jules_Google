import tkinter as tk

class RegionSelector:
    def __init__(self, master=None):
        """
        Initialize the RegionSelector.
        :param master: The parent tkinter widget (e.g., root window). If None, creates a new Tk instance.
        """
        self.master = master
        self.selected_region = None
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.top = None

    def select_region(self):
        """
        Opens a full-screen transparent window to select a region.
        :return: dict {'top': int, 'left': int, 'width': int, 'height': int} or None
        """
        if self.master:
            self.top = tk.Toplevel(self.master)
        else:
            self.top = tk.Tk()

        # Configure full screen and transparency
        self.top.attributes('-fullscreen', True)
        self.top.attributes('-alpha', 0.3)  # Semi-transparent overlay
        self.top.attributes('-topmost', True)
        self.top.config(bg='black')

        # Canvas for drawing the selection rectangle
        self.canvas = tk.Canvas(self.top, cursor="cross", bg="grey11", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.top.bind("<Escape>", self.on_escape)

        # Wait for the user to interact
        if not self.master:
            self.top.mainloop()
        else:
            self.top.wait_window(self.top)

        return self.selected_region

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=3
        )

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        if self.current_rect:
            self.canvas.coords(self.current_rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)

        # Calculate region dimensions
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(self.start_x - end_x)
        height = abs(self.start_y - end_y)

        # Avoid zero-size selection
        if width > 5 and height > 5:
            self.selected_region = {'top': top, 'left': left, 'width': width, 'height': height}

        self.top.destroy()

    def on_escape(self, event):
        self.selected_region = None
        self.top.destroy()

if __name__ == "__main__":
    # Test standalone
    selector = RegionSelector()
    region = selector.select_region()
    print(f"Selected Region: {region}")
