import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import subprocess

class GPTShellGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GPT-OS NLP Shell")
        self.input = tk.Entry(root, width=100)
        self.input.pack(pady=10)
        self.output = ScrolledText(root, height=20)
        self.output.pack()
        tk.Button(root, text="Run", command=self.execute).pack(pady=5)

    def execute(self):
        prompt = self.input.get()
        self.output.insert(tk.END, f"\n>> {prompt}\n")
        result = subprocess.getoutput(f"./llama.cpp/main -m models/model.gguf -p \"{prompt}\"")
        self.output.insert(tk.END, result + "\n")

if __name__ == '__main__':
    root = tk.Tk()
    app = GPTShellGUI(root)
    root.mainloop()
