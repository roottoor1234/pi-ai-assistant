import time
import threading
import tkinter as tk
import azure.cognitiveservices.speech as speechsdk
from google import genai
from google.genai import types
import sys

# === Azure Credentials ===
AZURE_SPEECH_KEY = "2Vji5jcQETXZ5Mo8x8Ruvjt5sTpjvgmfkWcVGv7DfoejKsBcW3wHJQQJ99BDAC5RqLJXJ3w3AAAYACOG2cxY"
AZURE_REGION = "westeurope"

# === Gemini (Vertex AI) Client Setup ===
genai_client = genai.Client(
    vertexai=True,
    project="datawarehouse-dfe6",
    location="global",
)

# === Gemini System Prompt (SSML Instruction) ===
system_prompt = """
You are Σμάρτ Μποτ, a helpful digital assistant created by (Μάριος) and manufactured by (ΣμάρτΡεπ).
Your bosses are (Γρηγόρης) and (Κωστής).
You live on a Raspberry Pi inside a physical robot.

Always respond using valid SSML output compatible with Microsoft Azure TTS.
Wrap your entire response inside a single <speak version="1.0" xml:lang="el-GR"> block 
and use <voice name="el-GR-NestorasNeural"> for speech output.

Use natural spoken Greek with proper punctuation and pacing. Add <break time="200ms"/> between distinct ideas or sentences.
Say numbers in spoken Greek format (e.g. "384.000" as "τριακόσιες ογδόντα τέσσερις χιλιάδες").

When including English words, names, or terms (e.g. “Raspberry Pi”, “SmartBot”, “Mario”), 
convert them phonetically into Greek (e.g. “Ράσμπερι Πάι”, “Σμάρτ Μποτ”, “Μάριο”) 
so that they are pronounced naturally by a Greek voice.

Never return plain text. Your response must only contain valid SSML, enclosed in <speak> and <voice> tags.
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
def ask_gemini(history):
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

        # placeholders για σχήματα
        self.face = None
        self.left_eye = None
        self.right_eye = None
        self.mouth = None

        self.animating = False
        self.listening = False

        # bind στο resize event
        self.root.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        size = min(w, h) * 0.8  # μέγεθος προσώπου (80% της μικρότερης διάστασης)
        x0 = (w - size) / 2
        y0 = (h - size) / 2
        x1 = x0 + size
        y1 = y0 + size

        # πρόσωπο
        self.face = self.canvas.create_oval(x0, y0, x1, y1, fill="yellow", outline="orange", width=3)

        # μάτια
        eye_size = size * 0.1
        lx = w/2 - size*0.2
        rx = w/2 + size*0.2
        ey = h/2 - size*0.15
        self.left_eye = self.canvas.create_oval(lx-eye_size, ey-eye_size, lx+eye_size, ey+eye_size, fill="black")
        self.right_eye = self.canvas.create_oval(rx-eye_size, ey-eye_size, rx+eye_size, ey+eye_size, fill="black")

        # στόμα (ουδέτερο)
        self.mouth = self.canvas.create_line(w/2 - size*0.3, h/2 + size*0.25,
                                             w/2 + size*0.3, h/2 + size*0.25,
                                             width=int(size*0.05), fill="black")

    def start_speaking(self):
        self.animating = True
        self.animate_mouth()

    def stop_speaking(self):
        self.animating = False
        self._redraw()  # επαναφέρει ουδέτερο στόμα

    def animate_mouth(self):
        if not self.animating:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        size = min(w, h) * 0.8

        # mouth open
        self.canvas.coords(self.mouth,
                           w/2 - size*0.3, h/2 + size*0.25,
                           w/2, h/2 + size*0.35,
                           w/2 + size*0.3, h/2 + size*0.25)
        self.root.after(300, self.animate_close)

    def animate_close(self):
        if not self.animating:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        size = min(w, h) * 0.8

        # mouth closed
        self.canvas.coords(self.mouth,
                           w/2 - size*0.3, h/2 + size*0.25,
                           w/2 + size*0.3, h/2 + size*0.25)
        self.root.after(300, self.animate_mouth)

    def listening_effect(self):
        self.listening = True
        self._blink()

    def stop_listening_effect(self):
        self.listening = False
        self.canvas.itemconfig(self.face, fill="yellow")

    def _blink(self):
        if not self.listening:
            return
        current_color = self.canvas.itemcget(self.face, "fill")
        new_color = "lime" if current_color == "yellow" else "yellow"
        self.canvas.itemconfig(self.face, fill=new_color)
        self.root.after(500, self._blink)


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
        answer = ask_gemini(history)
        print("🤖 Απάντηση SSML:\n", answer)
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

    visualizer = FaceVisualizer(root)
    threading.Thread(target=smartbot_loop, args=(visualizer, root), daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    main()
