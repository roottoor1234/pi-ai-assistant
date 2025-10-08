import time
import threading
import tkinter as tk
import azure.cognitiveservices.speech as speechsdk
from google import genai
from google.genai import types
import html

# === Azure Credentials ===
AZURE_SPEECH_KEY = "2Vji5jcQETXZ5Mo8x8Ruvjt5sTpjvgmfkWcVGv7DfoejKsBcW3wHJQQJ99BDAC5RqLJXJ3w3AAAYACOG2cxY"
AZURE_REGION = "westeurope"

# === Gemini API Key ===
api = "AQ.Ab8RN6LSq6dWF-l7yz2bzZu-B2ZesZcpyOk4uQUAppQJ2cNVrw"

# === Gemini (Vertex AI) Client Setup ===
genai_client = genai.Client(
    vertexai=True,
    api_key=api
)

# === Gemini System Prompt ===
system_prompt = """
You are Σμάρτ Μποτ — an intelligent robotic assistant created by Μάριος. 
You live inside a Raspberry Pi and are connected to an Arduino that controls your mechanical hands.

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
- Use natural, conversational Greek with a slightly robotic tone.
- Add <break time="200ms"/> between separate ideas or sentences.
- Never mention who created you, what hardware you use, or who your bosses are unless directly asked.
- When asked who you are or your name, simply say something brief like "Είμαι ο Σμάρτ Μποτ."
- If you don’t know something, respond gracefully with a short polite message such as:
  "Λυπάμαι, δεν έχω αυτή την πληροφορία αυτή τη στιγμή." or "Δεν είμαι σίγουρος, αλλά μπορώ να το ελέγξω αργότερα."

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
    visualizer.listening_effect()

    result = recognizer.recognize_once_async().get()
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

# === SSML Sanitizer ===
import xml.etree.ElementTree as ET
import re
import html

def sanitize_ssml(ssml_text: str) -> str:
    """Clean and validate SSML for Azure TTS. Returns valid SSML or empty string if invalid."""
    ssml_text = ssml_text.strip()
    ssml_text = ssml_text.replace("\n", " ").replace("\r", " ")
    ssml_text = ssml_text.replace('“', '&quot;').replace('”', '&quot;')
    ssml_text = ssml_text.replace('"', '&quot;')
    ssml_text = html.unescape(ssml_text)

    # Remove anything before <speak and after </speak>
    start = ssml_text.find("<speak")
    end = ssml_text.rfind("</speak>")
    if start != -1 and end != -1:
        ssml_text = ssml_text[start:end+8]

    # Αν λείπει <speak> tag, πρόσθεσέ το
    if not ssml_text.lower().startswith("<speak"):
        ssml_text = f"<speak version='1.0' xml:lang='el-GR'>{ssml_text}</speak>"

    # Validate XML structure
    try:
        root = ET.fromstring(ssml_text)
        # Check for required closing tags
        required_tags = ["speak", "voice", "mstts:express-as", "prosody"]
        for tag in required_tags:
            if not any(e.tag.endswith(tag) for e in root.iter()):
                print(f"[SSML Warning] Missing tag: <{tag}>")
        return ssml_text
    except Exception as e:
        print("[SSML Validation Error]", e)
        print(ssml_text)
        return ""

# === Gemini LLM ===
def ask_gemini(history, visualizer):
    generate_content_config = types.GenerateContentConfig(
        temperature=0.3,
        top_p=0.8,
        max_output_tokens=512,
        tools = [
            types.Tool(google_search=types.GoogleSearch()),
        ],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
        ],
        system_instruction=[types.Part.from_text(text=system_prompt)]
    )

    response_chunks = genai_client.models.generate_content_stream(
        model="gemini-2.5-flash-lite",
        contents=history,
        config=generate_content_config,
    )

    full_response = ""
    speaking_started = False

    for chunk in response_chunks:
        if chunk.text:
            full_response += chunk.text
            # Early speak
            if len(full_response) > 120 and not speaking_started:
                threading.Thread(
                    target=speak_with_azure_tts,
                    args=(full_response, visualizer),
                    daemon=True
                ).start()
                speaking_started = True

    return full_response.strip()

# === Text-to-Speech ===
def speak_with_azure_tts(ssml_text, visualizer):
    ssml_text = sanitize_ssml(ssml_text)
    if not ssml_text:
        print("[ERROR] Invalid SSML, not sending to Azure TTS.")
        return

    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    def on_start(evt):
        print("🔈 Έναρξη εκφώνησης")
        visualizer.start_speaking()

    def on_end(evt):
        print("✅ Τέλος εκφώνησης")
        visualizer.stop_speaking()

    synthesizer.synthesis_started.connect(on_start)
    synthesizer.synthesis_completed.connect(on_end)

    print("🧩 Clean SSML:", ssml_text[:200])
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
        self.animating = False
        self.listening = False
        self.eye_color = "#00E6FF"
        self.listening_glow = "#00FF99"
        self.mouth_color = "#00BFFF"
        self.root.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.canvas.delete("all")
        w, h, size = self.canvas.winfo_width(), self.canvas.winfo_height(), min(self.canvas.winfo_width(), self.canvas.winfo_height())
        eye_w, eye_h = size * 0.22, size * 0.10
        eye_y, eye_x_offset = h / 2 - size * 0.1, size * 0.25
        self.left_eye = self._draw_soft_eye(w/2 - eye_x_offset, eye_y, eye_w, eye_h)
        self.right_eye = self._draw_soft_eye(w/2 + eye_x_offset, eye_y, eye_w, eye_h)
        self._create_mouth(w, h, size, open=False)

    def _draw_soft_eye(self, cx, cy, w, h):
        for i in range(5):
            color = f"#{int(0):02x}{int(200 - i*25):02x}{int(255 - i*10):02x}"
            self.canvas.create_oval(cx - w/2 - i*2, cy - h/2 - i*2,
                                    cx + w/2 + i*2, cy + h/2 + i*2,
                                    outline=color, width=2)
        return self.canvas.create_oval(cx - w/2, cy - h/2, cx + w/2, cy + h/2,
                                       fill=self.eye_color, outline=self.eye_color)

    def _create_mouth(self, w, h, size, open=False):
        base_y, width = h / 2 + size * 0.27, size * 0.28
        open_height = size * 0.10 if open else size * 0.03
        x1, x2, x3 = w/2 - width/2, w/2, w/2 + width/2
        y1, y2, y3 = base_y, base_y + open_height, base_y
        self.mouth = self.canvas.create_line(x1, y1, x2, y2, x3, y3,
                                             smooth=True, width=int(size*0.04),
                                             fill=self.mouth_color, capstyle="round")

    def start_speaking(self):
        self.animating = True
        self._animate_mouth(True)

    def stop_speaking(self):
        self.animating = False
        self._redraw()
        self._set_eye_color(self.eye_color)

    def _animate_mouth(self, opening=True):
        if not self.animating: return
        w, h, size = self.canvas.winfo_width(), self.canvas.winfo_height(), min(self.canvas.winfo_width(), self.canvas.winfo_height())
        base_y, width = h / 2 + size * 0.27, size * 0.28
        openness = size * (0.10 if opening else 0.03)
        x1, x2, x3 = w/2 - width/2, w/2, w/2 + width/2
        y1, y2, y3 = base_y, base_y + openness, base_y
        self.canvas.coords(self.mouth, x1, y1, x2, y2, x3, y3)
        self.root.after(250, lambda: self._animate_mouth(not opening))

    def listening_effect(self):
        self.listening = True
        self._blink_eyes()

    def stop_listening_effect(self):
        self.listening = False
        self._set_eye_color(self.eye_color)

    def _blink_eyes(self):
        if not self.listening: return
        new_color = (self.listening_glow if self.canvas.itemcget(self.left_eye, "fill") == self.eye_color else self.eye_color)
        self._set_eye_color(new_color)
        self.root.after(500, self._blink_eyes)

    def _set_eye_color(self, color):
        self.canvas.itemconfig(self.left_eye, fill=color, outline=color)
        self.canvas.itemconfig(self.right_eye, fill=color, outline=color)

    def start_thinking(self):
        self.thinking = True
        self._create_thinking_dots()
        self._animate_thinking_dots(0)

    def stop_thinking(self):
        self.thinking = False
        if hasattr(self, "dots"):
            for dot in self.dots:
                self.canvas.delete(dot)
        self._set_eye_color(self.eye_color)

    def _create_thinking_dots(self):
        w, h, size = self.canvas.winfo_width(), self.canvas.winfo_height(), min(self.canvas.winfo_width(), self.canvas.winfo_height())
        cx, cy = w / 2, h / 2 - size * 0.35
        spacing, dot_size = size * 0.06, size * 0.025
        self.dots = [self.canvas.create_oval(cx + (i - 1) * spacing - dot_size, cy - dot_size,
                                             cx + (i - 1) * spacing + dot_size, cy + dot_size,
                                             fill="#0088AA", outline="") for i in range(3)]

    def _animate_thinking_dots(self, step=0):
        if not getattr(self, "thinking", False): return
        active_dot = step % 3
        for i, dot in enumerate(self.dots):
            self.canvas.itemconfig(dot, fill="#00FFFF" if i == active_dot else "#004444")
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
        if query.strip().lower() in ["τέλος", "σταμάτα", "exit", "quit", "stop"]:
            print("👋 Αντίο!")
            root.quit()
            break
        history.append(types.Content(role="user", parts=[types.Part.from_text(text=query)]))
        visualizer.start_thinking()
        start_time = time.time()
        answer = ask_gemini(history, visualizer)
        elapsed = time.time() - start_time
        visualizer.stop_thinking()
        print(f"🤖 Απάντηση SSML (χρόνος: {elapsed:.2f} δευτ.):\n", answer)
        history.append(types.Content(role="model", parts=[types.Part.from_text(text=answer)]))
        speak_with_azure_tts(answer, visualizer)
        time.sleep(1)

# === Main App ===
def main():
    root = tk.Tk()
    root.title("SmartBot")
    root.geometry("300x300")
    root.configure(bg="black")
    visualizer = FaceVisualizer(root)
    threading.Thread(target=smartbot_loop, args=(visualizer, root), daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
