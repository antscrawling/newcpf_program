import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import subprocess

class ConfigFormApp:
    def __init__(self, master):
        self.master = master
        self.master.title("CPF Config Setup")
        self.frame = ttk.Frame(master)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.inputs = {}

        self.config_path = filedialog.askopenfilename(title="Select Config JSON", filetypes=[("JSON Files", "*.json")])
        if not self.config_path:
            sys.exit()

        with open(self.config_path, 'r') as f:
            self.config_data = json.load(f)

        self.flat_config = {}
        self.flatten_dict(self.config_data)

        self.canvas = tk.Canvas(self.frame)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        for key, value in self.flat_config.items():
            label = ttk.Label(self.scrollable_frame, text=key)
            entry = ttk.Entry(self.scrollable_frame)
            entry.insert(0, str(value))
            label.pack(fill='x', padx=5, pady=2)
            entry.pack(fill='x', padx=5, pady=2)
            self.inputs[key] = entry

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        run_button = ttk.Button(self.frame, text="Run Simulation", command=self.run_simulation)
        run_button.pack(pady=10)

    def flatten_dict(self, d, parent_key=''):
        for k, v in d.items():
            full_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                self.flatten_dict(v, full_key)
            elif isinstance(v, list):
                self.flat_config[full_key] = ",".join(map(str, v))
            else:
                self.flat_config[full_key] = v

    def unflatten_dict(self):
        result = {}
        for key, entry in self.inputs.items():
            keys = key.split('.')
            current = result
            for part in keys[:-1]:
                current = current.setdefault(part, {})
            try:
                current[keys[-1]] = json.loads(entry.get())
            except json.JSONDecodeError:
                current[keys[-1]] = entry.get()
        return result

    def run_simulation(self):
        new_config = self.unflatten_dict()
        with open(self.config_path, 'w') as f:
            json.dump(new_config, f, indent=4)

        try:
            subprocess.run([sys.executable, 'run_cpf_simulation_v7.py'], check=True)
            messagebox.showinfo("Success", "Simulation completed!")
            self.show_report_viewer()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Simulation failed: {str(e)}")

    def show_report_viewer(self):
        viewer = tk.Toplevel(self.master)
        viewer.title("Simulation Report")
        viewer.geometry("1000x600")

        report_text = tk.Text(viewer, wrap='none')
        report_text.pack(fill='both', expand=True)

        try:
            with open('cpf_simulation.db', 'rb') as f:
                report_text.insert('1.0', 'Simulation completed. Data written to cpf_simulation.db\n\n')
                report_text.insert('end', 'You can open the database using a SQLite viewer.\n')
        except FileNotFoundError:
            report_text.insert('1.0', 'No report file (cpf_simulation.db) found.')

if __name__ == '__main__':
    root = tk.Tk()
    app = ConfigFormApp(root)
    root.geometry("800x600")
    root.mainloop()