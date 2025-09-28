import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
import jlc_first_pipeline # Import our refactored pipeline script

class EasyEdaAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EasyEDA Interactive Automation Tool")
        self.root.geometry("1200x900")

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Live Search Frame ---
        search_frame = ttk.LabelFrame(main_frame, text="1. Live Part Search")
        search_frame.pack(fill=tk.X, expand=False, pady=5)
        self.create_search_ui(search_frame)

        # --- Part List Frame ---
        parts_frame = ttk.LabelFrame(main_frame, text="2. Project Component List")
        parts_frame.pack(fill=tk.X, expand=False, pady=5)
        self.project_parts_tree = self.create_parts_table(parts_frame, height=5)
        self.create_project_part_buttons(parts_frame)

        # --- Action Frame ---
        action_frame = ttk.LabelFrame(main_frame, text="3. Generate Design Scripts")
        action_frame.pack(fill=tk.X, expand=False, pady=5)
        self.create_action_buttons(action_frame)

        # --- Generated Scripts Frame ---
        scripts_frame = ttk.LabelFrame(main_frame, text="4. Generated Scripts (Copy from here)")
        scripts_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.create_script_display(scripts_frame)

        self.load_sample_data()

    def create_search_ui(self, parent):
        search_input_frame = ttk.Frame(parent)
        search_input_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(search_input_frame, text="Search Term:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_input_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(search_input_frame, text="Search JLCPCB (Mock)", command=self.search_jlc).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_input_frame, text="Search LCSC", command=self.search_lcsc).pack(side=tk.LEFT)

        search_results_frame = ttk.Frame(parent)
        search_results_frame.pack(fill=tk.X, expand=True, pady=5)
        self.search_results_tree = self.create_search_results_table(search_results_frame)

        add_to_project_button = ttk.Button(parent, text="Add Selected Part to Project List", command=self.add_searched_part_to_project)
        add_to_project_button.pack(pady=5)

    def create_search_results_table(self, parent):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(pady=5, fill=tk.X)
        columns = ("Supplier", "LCSC Part", "MPN", "Package", "Stock", "Price", "Description")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=6)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='w')
        tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

    def create_parts_table(self, parent, height):
        tree_frame = ttk.Frame(parent); tree_frame.pack(pady=5, fill=tk.X)
        columns = ("Designator", "MPN", "Value", "Package", "Footprint")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=height)
        for col in columns:
            tree.heading(col, text=col); tree.column(col, width=150, anchor='w')
        tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

    def create_project_part_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Remove Selected Part", command=self.remove_project_part).pack()

    def create_action_buttons(self, parent):
        run_button = ttk.Button(parent, text="Generate Schematic & PCB Placement Scripts", command=self.generate_design_scripts)
        run_button.pack(pady=5)

    def create_script_display(self, parent):
        display_frame = ttk.Frame(parent); display_frame.pack(fill=tk.BOTH, expand=True)
        display_frame.columnconfigure(0, weight=1); display_frame.columnconfigure(1, weight=1); display_frame.rowconfigure(1, weight=1)
        ttk.Label(display_frame, text="Script 1: Create Schematic").grid(row=0, column=0, padx=5, sticky="w")
        self.script1_text = tk.Text(display_frame, wrap="word", height=8, relief="solid", borderwidth=1)
        self.script1_text.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        ttk.Label(display_frame, text="Script 2: Place Footprints").grid(row=0, column=1, padx=5, sticky="w")
        self.script2_text = tk.Text(display_frame, wrap="word", height=8, relief="solid", borderwidth=1)
        self.script2_text.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

    def _execute_search(self, search_function):
        query = self.search_entry.get()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return

        messagebox.showinfo("Info", f"Searching for '{query}'...")
        self.root.update_idletasks()

        try:
            results = search_function(query)
            self.search_results_tree.delete(*self.search_results_tree.get_children()) # Clear previous results

            if not results:
                messagebox.showinfo("Info", "No results found.")
                return

            for part in results:
                self.search_results_tree.insert("", tk.END, values=(
                    part.supplier, part.supplier_part, part.mpn, part.pkg, part.stock, f"{part.price:.4f}" if part.price else "", part.desc
                ))
        except Exception as e:
            messagebox.showerror("Search Error", f"An error occurred during search:\n{e}")

    def search_jlc(self):
        self._execute_search(jlc_first_pipeline.search_jlc)

    def search_lcsc(self):
        self._execute_search(jlc_first_pipeline.search_lcsc)

    def add_searched_part_to_project(self):
        selected_item = self.search_results_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a part from the search results to add.")
            return

        part_data = self.search_results_tree.item(selected_item[0])['values']

        designator = simpledialog.askstring("Input", "Enter Designator (e.g., U1, R1):", parent=self.root)
        if not designator:
            return # User cancelled

        # (Supplier, LCSC Part, MPN, Package, Stock, Price, Description)
        mpn = part_data[2]
        pkg = part_data[3]
        # We need a 'Value' for the part. Let's try to get it from the description or MPN.
        # This is a simplification; a more robust solution would be better.
        value = part_data[2] # Fallback to MPN if no better value found

        project_part_values = (designator, mpn, value, pkg, pkg) # Use package as footprint for now
        self.project_parts_tree.insert("", tk.END, values=project_part_values)

    def remove_project_part(self):
        selected_items = self.project_parts_tree.selection()
        if not selected_items: messagebox.showwarning("Warning", "Please select a part to remove."); return
        for item in selected_items: self.project_parts_tree.delete(item)

    def generate_design_scripts(self):
        parts_data = [{"Designator": i['values'][0], "MPN": i['values'][1], "Value": i['values'][2], "Package": i['values'][3], "Footprint": i['values'][4], "Qty": "1"} for i in [self.project_parts_tree.item(item_id) for item_id in self.project_parts_tree.get_children()]]
        if not parts_data: messagebox.showerror("Error", "Component list is empty."); return
        try:
            with open("netlist_data.csv", "r", encoding="utf-8") as f: netlist_data = list(csv.DictReader(f))
        except FileNotFoundError: messagebox.showerror("Error", "netlist_data.csv not found!"); return
        try:
            messagebox.showinfo("Info", "Generating design scripts..."); self.root.update_idletasks()
            sch_script, pcb_script = jlc_first_pipeline.execute_design_pipeline(parts_data, netlist_data)
            self.script1_text.delete("1.0", tk.END); self.script1_text.insert(tk.END, sch_script)
            self.script2_text.delete("1.0", tk.END); self.script2_text.insert(tk.END, pcb_script)
            messagebox.showinfo("Success", "Design scripts generated successfully!")
        except Exception as e: messagebox.showerror("Pipeline Error", f"An error occurred:\n{e}")

    def load_sample_data(self):
        try:
            with open("input_parts.csv", "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader: self.project_parts_tree.insert("", tk.END, values=(row.get("Designator", ""), row.get("MPN", ""), row.get("Value", ""), row.get("Package", ""), row.get("Footprint", "")))
        except FileNotFoundError: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = EasyEdaAutomationApp(root)
    root.mainloop()