# === visualizer.py ===
import tkinter as tk
import time

# === Face Visualizer ===
class FaceVisualizer:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.left_eye = None
        self.right_eye = None
        self.mouth = None
        self.listening_ring_left = None
        self.listening_ring_right = None

        self.animating = False
        self.listening = False
        self.breathing = False

        # Χρώματα
        self.eye_color = "#00E6FF"       # soft cyan
        self.eye_glow = "#0088AA"        # softer outer glow
        self.listening_glow = "#00FF99"  # green glow when listening
        self.mouth_color = "#00BFFF"     # blue mouth
        self.mouth_dim = "#003355"

        self.root.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        size = min(w, h)

        # --- Μάτια ---
        eye_w = size * 0.22
        eye_h = size * 0.10
        eye_y = h / 2 - size * 0.1
        eye_x_offset = size * 0.25

        self.left_eye = self._draw_soft_eye(w/2 - eye_x_offset, eye_y, eye_w, eye_h)
        self.right_eye = self._draw_soft_eye(w/2 + eye_x_offset, eye_y, eye_w, eye_h)

        # --- Στόμα ---
        self._create_mouth(w, h, size, open=False)

        # --- Υπογραφή κάτω δεξιά ---
        self.canvas.create_text(
            w - 10, h - 10,
            text="made by smartrep",
            fill="#00A0A0",
            font=("Arial", int(size * 0.04)),
            anchor="se"
        )

    def _draw_soft_eye(self, cx, cy, w, h):
        # Εξωτερικό glow (ήπιο, “μαλακό”)
        for i in range(6):
            color = f"#{int(0):02x}{int(230 - i*30):02x}{int(255 - i*10):02x}"
            self.canvas.create_oval(cx - w/2 - i*2, cy - h/2 - i*2,
                                    cx + w/2 + i*2, cy + h/2 + i*2,
                                    outline=color, width=2)
        # Εσωτερικός πυρήνας
        return self.canvas.create_oval(cx - w/2, cy - h/2, cx + w/2, cy + h/2,
                                       fill=self.eye_color, outline=self.eye_color)

    # === Δημιουργία ρεαλιστικού στόματος (καμπύλη) ===
    def _create_mouth(self, w, h, size, open=False):
        base_y = h / 2 + size * 0.27
        width = size * 0.28
        open_height = size * 0.10 if open else size * 0.03  # μικρό χαμόγελο όταν κλειστό

        x1 = w/2 - width/2
        x2 = w/2
        x3 = w/2 + width/2
        y1 = base_y
        y2 = base_y + open_height
        y3 = base_y

        # Καμπύλη με 3 σημεία (ομαλή)
        self.mouth = self.canvas.create_line(
            x1, y1, x2, y2, x3, y3,
            smooth=True,
            width=int(size * 0.04),
            fill="#00BFFF",
            capstyle="round"
        )

    def start_speaking(self):
        self.animating = True
        self._animate_mouth(opening=True)

    def stop_speaking(self):
        self.animating = False
        self._redraw()
        self._set_eye_color(self.eye_color)


    def _animate_mouth(self, opening=True):
        if not self.animating:
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        size = min(w, h)
        base_y = h / 2 + size * 0.27
        width = size * 0.28

        # πιο φυσικό άνοιγμα – καμπύλη κίνησης
        openness = size * (0.10 if opening else 0.03)

        x1 = w/2 - width/2
        x2 = w/2
        x3 = w/2 + width/2
        y1 = base_y
        y2 = base_y + openness
        y3 = base_y

        self.canvas.coords(self.mouth, x1, y1, x2, y2, x3, y3)

        # Εναλλαγή ανοιχτό / κλειστό
        self.root.after(250, lambda: self._animate_mouth(not opening))

    # === Listening Animation ===
    def listening_effect(self):
        self.listening = True
        # self._animate_listening_rings()
        self._blink_eyes()

    def stop_listening_effect(self):
        self.listening = False
        # self.canvas.itemconfig(self.listening_ring_left, outline="")
        # self.canvas.itemconfig(self.listening_ring_right, outline="")
        self._set_eye_color(self.eye_color)

    def _animate_listening_rings(self):
        if not self.listening:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        size = min(w, h)
        eye_w = size * 0.22
        eye_h = size * 0.10
        eye_y = h / 2 - size * 0.1
        eye_x_offset = size * 0.25
        ring_size = eye_w + 30

        # Rings γύρω από τα μάτια
        for (ring, cx) in [(self.listening_ring_left, w/2 - eye_x_offset),
                           (self.listening_ring_right, w/2 + eye_x_offset)]:
            self.canvas.coords(ring,
                               cx - ring_size/2, eye_y - ring_size/2,
                               cx + ring_size/2, eye_y + ring_size/2)
            self.canvas.itemconfig(ring, outline=self.listening_glow, width=2)

        # "Pulse" rings (fade in/out)
        alpha = int(time.time() * 4) % 2
        new_color = self.listening_glow if alpha == 0 else "#003322"
        self.canvas.itemconfig(self.listening_ring_left, outline=new_color)
        self.canvas.itemconfig(self.listening_ring_right, outline=new_color)

        self.root.after(300, self._animate_listening_rings)

    def _blink_eyes(self):
        if not self.listening:
            return
        new_color = (self.listening_glow
                     if self.canvas.itemcget(self.left_eye, "fill") == self.eye_color
                     else self.eye_color)
        self._set_eye_color(new_color)
        self.root.after(500, self._blink_eyes)

    def _set_eye_color(self, color):
        self.canvas.itemconfig(self.left_eye, fill=color, outline=color)
        self.canvas.itemconfig(self.right_eye, fill=color, outline=color)

    # === Όταν “σκέφτεται” (μόνο με τελείες) ===
    def start_thinking(self):
        """Εμφανίζει 3 κυανές τελείες πάνω από τα μάτια"""
        self.thinking = True
        self._create_thinking_dots()
        self._animate_thinking_dots(step=0)

    def stop_thinking(self):
        """Αφαιρεί τις τελείες όταν ολοκληρωθεί η σκέψη"""
        self.thinking = False
        if hasattr(self, "dots"):
            for dot in self.dots:
                self.canvas.delete(dot)
        self._set_eye_color(self.eye_color)

    def _create_thinking_dots(self):
        """Σχεδιάζει τις τρεις τελείες πάνω από τα μάτια"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        size = min(w, h)
        cx = w / 2
        cy = h / 2 - size * 0.35

        spacing = size * 0.06
        dot_size = size * 0.025

        self.dots = [
            self.canvas.create_oval(cx - spacing - dot_size, cy - dot_size,
                                    cx - spacing + dot_size, cy + dot_size,
                                    fill="#0088AA", outline=""),
            self.canvas.create_oval(cx - dot_size, cy - dot_size,
                                    cx + dot_size, cy + dot_size,
                                    fill="#0088AA", outline=""),
            self.canvas.create_oval(cx + spacing - dot_size, cy - dot_size,
                                    cx + spacing + dot_size, cy + dot_size,
                                    fill="#0088AA", outline="")
        ]

    def _animate_thinking_dots(self, step=0):
        """Κάνει τις τελείες να αναβοσβήνουν διαδοχικά"""
        if not getattr(self, "thinking", False):
            return

        active_dot = step % 3
        colors = ["#004444", "#00FFFF"]

        for i, dot in enumerate(self.dots):
            color = colors[1] if i == active_dot else colors[0]
            self.canvas.itemconfig(dot, fill=color)

        self.root.after(300, lambda: self._animate_thinking_dots(step + 1))
