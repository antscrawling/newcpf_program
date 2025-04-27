import tkinter as tk
from tkinter import messagebox
import json
from src.xcpf_config_loader_v3 import ConfigLoader 


class CPFConfigApp:
    def __init__(self, root, config_file):
        self.root = root
        self.root.title("CPF Config Input")
        self.config_file = config_file
        self.config_data  = ConfigLoader(config_file)
        self.input_fields = {}

        self.create_input_fields()
        self.create_buttons()

    def create_input_fields(self):
        for key, value in self.config_data.items():
            tk.Label(self.root, text=f"{key}:").pack()
            entry = tk.Entry(self.root)
            entry.pack()
            entry.insert(0, str(value))
            self.input_fields[key] = entry

    def create_buttons(self):
        tk.Button(self.root, text="Submit", command=self.submit_config).pack()
        tk.Button(self.root, text="Amend", command=self.amend_config).pack()
        tk.Button(self.root, text="Cancel", command=self.cancel_config).pack()

    def submit_config(self):
        updated_config = {key: field.get() for key, field in self.input_fields.items()}
        with open(self.config_file, "w") as file:
            json.dump(updated_config, file, indent=2)
        messagebox.showinfo("Submit", f"Configuration submitted and saved:\n{json.dumps(updated_config, indent=2)}")

    def amend_config(self):
        for field in self.input_fields.values():
            field.config(state="normal")  # Enable editing of input fields
        messagebox.showinfo("Amend", "You can now amend the configuration.")

    def cancel_config(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CPFConfigApp('cpf_config.json')
    root.mainloop()

