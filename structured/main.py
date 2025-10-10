# === main.py ===
import tkinter as tk
import threading
from visualizer import FaceVisualizer
from conversation_loop import smartbot_loop

def main():
    root = tk.Tk()
    root.title("SmartBot Speaking")
    root.geometry("220x220")
    root.configure(bg="black")
    root.attributes("-fullscreen", True)  # πλήρης οθόνη

    visualizer = FaceVisualizer(root)
    threading.Thread(target=smartbot_loop, args=(visualizer, root), daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
