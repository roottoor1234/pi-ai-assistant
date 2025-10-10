import time
import azure.cognitiveservices.speech as speechsdk
from google import genai
from google.genai import types

# === Azure credentials ===
AZURE_SPEECH_KEY = "2Vji5jcQETXZ5Mo8x8Ruvjt5sTpjvgmfkWcVGv7DfoejKsBcW3wHJQQJ99BDAC5RqLJXJ3w3AAAYACOG2cxY"
AZURE_REGION = "westeurope"

# === Gemini credentials ===
api_key = "AQ.Ab8RN6LSq6dWF-l7yz2bzZu-B2ZesZcpyOk4uQUAppQJ2cNVrw"

genai_client = genai.Client(
    vertexai=True,
    api_key=api_key
)

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

# === Azure Speech-to-Text ===
def recognize_speech():
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    speech_config.speech_recognition_language = "el-GR"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("🎤 Μίλα τώρα (έχεις 5 δευτερόλεπτα)...")
    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        print("⚠️ Δεν αναγνωρίστηκε ομιλία.")
        return None

# === Gemini ===
def ask_gemini(text):
    history = [types.Content(role="user", parts=[types.Part.from_text(text=text)])]

    config = types.GenerateContentConfig(
        temperature=0.8,
        max_output_tokens=1024,
        system_instruction=[types.Part.from_text(text=system_prompt)]
    )

    response = genai_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=history,
        config=config
    )

    return response.text

# === Azure Text-to-Speech ===
def speak_with_azure_tts(ssml_text):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    print("🗣️ Εκφώνηση...")
    result = synthesizer.speak_ssml_async(ssml_text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("✅ Ολοκληρώθηκε η εκφώνηση.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print("❌ Η εκφώνηση ακυρώθηκε:", cancellation.reason, cancellation.error_details)

# === Main Loop ===
def main():
    print("🤖 Ο SmartBot είναι έτοιμος (χωρίς GUI). Πες 'τέλος' για έξοδο.\n")

    while True:
        query = recognize_speech()
        if not query:
            continue

        if query.lower() in ["τέλος", "σταμάτα", "exit", "stop"]:
            print("👋 Αντίο!")
            break

        print("🧠 Ερώτηση:", query)

        start_time = time.time()
        answer = ask_gemini(query)
        elapsed = time.time() - start_time
        print(f"⏱️ Χρόνος απόκρισης Gemini: {elapsed:.2f} δευτερόλεπτα")

        print("🤖 SSML απάντηση:\n", answer)
        speak_with_azure_tts(answer)
        print("-" * 40)

if __name__ == "__main__":
    main()
