import tkinter as tk

class MainWindowGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Main Window")
        tk.Label(self.root, text="Hello, World!").pack(padx=20, pady=20)
        tk.Button(self.root, text="Exit", command=self.root.quit).pack(pady=10)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    MainWindowGUI().run()