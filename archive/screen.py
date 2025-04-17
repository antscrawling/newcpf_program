import tkinter as tk
from tkinter import messagebox

def start_simulation():
    salary = float(salary_entry.get())
    # Call your simulation logic here with the new salary value
    messagebox.showinfo("Run", f"Simulation started with salary {salary}")

root = tk.Tk()
root.title("CPF Simulator")

tk.Label(root, text="Monthly Salary:").pack()
salary_entry = tk.Entry(root)
salary_entry.pack()
salary_entry.insert(0, "7400")

tk.Button(root, text="Run Simulation", command=start_simulation).pack()

root.mainloop()
