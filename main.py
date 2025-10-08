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



api="AQ.Ab8RN6LSq6dWF-l7yz2bzZu-B2ZesZcpyOk4uQUAppQJ2cNVrw"

# === Gemini (Vertex AI) Client Setup ===
genai_client = genai.Client(
    vertexai=True,
    api_key=api
)

# === Gemini System Prompt (SSML Instruction) ===
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
    root.attributes("-fullscreen", True)  # πλήρης οθόνη

    visualizer = FaceVisualizer(root)
    threading.Thread(target=smartbot_loop, args=(visualizer, root), daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    main()
