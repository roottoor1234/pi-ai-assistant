import time
import azure.cognitiveservices.speech as speechsdk
from google import genai
from google.genai import types
import tkinter as tk
import threading

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
def recognize_speech():
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    speech_config.speech_recognition_language = "el-GR"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("🎤 Μίλησε τώρα...")
    result = recognizer.recognize_once()

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
        contents=history,  # μόνο user/model ρόλοι
        config=generate_content_config,
    )

    full_response = ""
    for chunk in response_chunks:
        if chunk.text:
            full_response += chunk.text

    return full_response.strip()


# === Text-to-Speech ===
def speak_with_azure_tts(ssml_text, visualizer=None):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    print("🔈 Μιλάει ο SmartBot...")
    if visualizer:
        visualizer.start()

    result = synthesizer.speak_ssml_async(ssml_text).get()

    if visualizer:
        visualizer.stop()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("✅ Αναπαραγωγή ολοκληρώθηκε")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print("❌ Ακυρώθηκε:", cancellation.reason)
        if cancellation.reason == speechsdk.CancellationReason.Error:
            print("Σφάλμα:", cancellation.error_details)


# === Main Loop ===
def main():
    history = []
    visualizer = SpeakingVisualizer()

    print("🤖 Ο SmartBot είναι έτοιμος. Πες 'τέλος' ή 'σταμάτα' για να τερματίσεις τον διάλογο.\n")

    while True:
        query = recognize_speech()
        if not query:
            continue

        print("📝 Ερώτηση:", query)
        if query.strip().lower() in ["τέλος.", "σταμάτα.", "exit.", "quit.", "Τέλος.", "Σταμάτα.", "στοπ.", "stop."]:
            print("👋 Αντίο!")
            break

        # Προσθήκη ερώτησης στο ιστορικό
        history.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)]
            )
        )

        # Λήψη απάντησης από το Gemini
        answer = ask_gemini(history)
        print("🤖 Απάντηση SSML:\n", answer)

        # Προσθήκη απάντησης στο ιστορικό
        history.append(
            types.Content(
                role="model",
                parts=[types.Part.from_text(text=answer)]
            )
        )

        # Ομιλία με Azure TTS
        speak_with_azure_tts(answer, visualizer)

        time.sleep(1.5)  # Μικρή παύση πριν τον επόμενο γύρο

class SpeakingVisualizer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SmartBot Speaking")
        self.root.geometry("200x100")
        self.root.configure(bg="black")
        self.canvas = tk.Canvas(self.root, width=200, height=100, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.dots = [
            self.canvas.create_oval(30, 40, 50, 60, fill="gray"),
            self.canvas.create_oval(80, 40, 100, 60, fill="gray"),
            self.canvas.create_oval(130, 40, 150, 60, fill="gray")
        ]
        self.animating = False

        # Ξεκινά το Tkinter loop σε background thread
        threading.Thread(target=self.root.mainloop, daemon=True).start()

    def start(self):
        self.animating = True
        threading.Thread(target=self.animate, daemon=True).start()

    def stop(self):
        self.animating = False
        for dot in self.dots:
            self.canvas.itemconfig(dot, fill="gray")

    def animate(self):
        while self.animating:
            for i in range(3):
                self.canvas.itemconfig(self.dots[i], fill="white")
                time.sleep(0.2)
                self.canvas.itemconfig(self.dots[i], fill="gray")
            time.sleep(0.1)

if __name__ == "__main__":
    main()
