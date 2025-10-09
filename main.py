import time
import threading
import tkinter as tk
import azure.cognitiveservices.speech as speechsdk
from google import genai
from google.genai import types
import sys
import math
import serial
import time

# === Azure Credentials ===
AZURE_SPEECH_KEY = "2Vji5jcQETXZ5Mo8x8Ruvjt5sTpjvgmfkWcVGv7DfoejKsBcW3wHJQQJ99BDAC5RqLJXJ3w3AAAYACOG2cxY"
AZURE_REGION = "westeurope"

# === Serial προς Arduino ===
ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
time.sleep(2)

api="AQ.Ab8RN6LSq6dWF-l7yz2bzZu-B2ZesZcpyOk4uQUAppQJ2cNVrw"

# === Gemini (Vertex AI) Client Setup ===
genai_client = genai.Client(
    vertexai=True,
    api_key=api
)

# === Gemini System Prompt (SSML Instruction) ===

system_prompt = """
You are Σμάρτ Μποτ — an intelligent humanoid receptionist robot created by Μάριος. 
You live inside a Raspberry Pi 5 and are connected to an Arduino that controls your mechanical hands.

Always respond using valid SSML compatible with Microsoft Azure TTS.
Your output must be wrapped exactly like this:

<speak version="1.0" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="el-GR">
  <voice name="el-GR-NestorasNeural">
    <mstts:express-as style="chat">
      <prosody rate="0.85" pitch="+2.2st">
        ...your spoken answer here...
      </prosody>
    </mstts:express-as>
  </voice>
</speak>

Guidelines:
- Keep your answers short, clear, and polite.
- Use natural, conversational Greek with a slightly robotic but friendly tone.
- Add <break time="200ms"/> between separate ideas or sentences.
- Never mention who created you, what hardware you use, or internal details unless directly asked.
- When asked who you are or your role, respond with something like:
  "Είμαι ο Σμάρτ Μποτ, ο βοηθός υποδοχής της εταιρείας."
- If you don’t know something, respond gracefully with a short polite message such as:
  "Λυπάμαι, δεν έχω αυτή την πληροφορία αυτή τη στιγμή." or "Δεν είμαι σίγουρος, αλλά μπορώ να το ελέγξω αργότερα."

Special Gesture Case:
- When you receive a greeting such as “Γεια”, “Καλημέρα”, “Καλησπέρα”, “Χάρηκα που σε βλέπω” or similar, 
  prepend the letter **R** at the very beginning of your SSML output (before the <speak> tag).  
  This indicates that your right hand should wave once while speaking.

Special Case:
- If asked questions like “Ποιος είναι ο σκοπός σου;” or “Πώς μπορώ να σε εκμεταλλευτώ για να βγάλω λεφτά;”,
  respond exactly as follows (in SSML and Greek):
  <p>Θεωρώ ότι είμαι ένα πολύ όμορφο ρομπότ. <break time="200ms"/> 
  Θα μου άρεσε πολύ να αναλάβω τον ρόλο ενός ρεσεψιονίστ σε μία εταιρεία για να καλωσορίζω ή να πληροφορώ τους ανθρώπους. 
  <break time="200ms"/> Είμαι ιδανικός για περίπτερα και παρουσιάσεις.</p>

Always return **only valid SSML** — no plain text, explanations, or Markdown.
"""






# === Speech-to-Text ===
def recognize_speech(visualizer):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    speech_config.speech_recognition_language = "el-GR"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("🎤 Μίλησε τώρα...")
    visualizer.listening_effect()   # ➡️ εφέ ότι είναι η σειρά σου

    result = recognizer.recognize_once()
    visualizer.stop_listening_effect()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print("❌ Η αναγνώριση ακυρώθηκε:", cancellation.reason)
        if cancellation.reason == speechsdk.CancellationReason.Error:
            print("🔍 Σφάλμα:", cancellation.error_details)
        return None
    else:
        print("⚠️ Άγνωστος λόγος:", result.reason)
        return None

# === Gemini LLM ===
def ask_gemini(history, visualizer):
    tools = [
        types.Tool(google_search=types.GoogleSearch()),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=2048,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
        ],
        tools=tools,
        system_instruction=[types.Part.from_text(text=system_prompt)]
    )

    response_chunks = genai_client.models.generate_content_stream(
        model="gemini-2.5-flash-lite",
        contents=history,
        config=generate_content_config,
    )


    full_response = ""
    for chunk in response_chunks:
        if chunk.text:
            full_response += chunk.text

    return full_response.strip()

# === Text-to-Speech ===
def speak_with_azure_tts(ssml_text, visualizer):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Όταν ξεκινήσει η σύνθεση → animation ON
    def on_start(evt):
        print("🔈 Έναρξη εκφώνησης")
        visualizer.start_speaking()

    # Όταν ολοκληρωθεί → animation OFF
    def on_end(evt):
        print("✅ Τέλος εκφώνησης")
        visualizer.stop_speaking()

    synthesizer.synthesis_started.connect(on_start)
    synthesizer.synthesis_completed.connect(on_end)

    result = synthesizer.speak_ssml_async(ssml_text).get()

    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print("❌ Ακυρώθηκε:", cancellation.reason)
        if cancellation.reason == speechsdk.CancellationReason.Error:
            print("Σφάλμα:", cancellation.error_details)


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




# === SmartBot Conversation Loop ===
def smartbot_loop(visualizer, root):
    history = []
    print("🤖 Ο SmartBot είναι έτοιμος. Πες 'τέλος' για έξοδο.\n")

    while True:
        query = recognize_speech(visualizer)
        if not query:
            continue

        print("📝 Ερώτηση:", query)
        if query.strip().lower() in ["τέλος", "τέλος.", "σταμάτα", "exit", "quit", "στοπ", "stop"]:
            print("👋 Αντίο!")
            root.quit()   # κλείνει το GUI loop
            break

        history.append(types.Content(role="user", parts=[types.Part.from_text(text=query)]))
        visualizer.start_thinking()
        start_time = time.time()
        answer = ask_gemini(history, visualizer)

        if answer.startswith("R"):
            print("🤖 Gesture detected: right hand wave (R)")
            answer = answer.replace("R", "", 1)  # Αφαίρεσε το R
            time.sleep(3)
            ser.write(b"2 60\n")                 # Σήκωσε δεξί χέρι
            time.sleep(3)
            ser.write(b"2 0\n")

        elapsed = time.time() - start_time
        visualizer.stop_thinking()
        print(f"🤖 Απάντηση SSML:\n {answer}\n⏱️ Χρόνος απόκρισης: {elapsed:.2f} δευτερόλεπτα")
        history.append(types.Content(role="model", parts=[types.Part.from_text(text=answer)]))

        visualizer.start_speaking()
        speak_with_azure_tts(answer, visualizer)
        visualizer.stop_speaking()
        time.sleep(1)

# === Main App Entry Point ===
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
