import azure.cognitiveservices.speech as speechsdk

# === ΡΥΘΜΙΣΕΙΣ AZURE ===
AZURE_SPEECH_KEY = "2Vji5jcQETXZ5Mo8x8Ruvjt5sTpjvgmfkWcVGv7DfoejKsBcW3wHJQQJ99BDAC5RqLJXJ3w3AAAYACOG2cxY"
AZURE_REGION = "westeurope"

# === STT: Αναγνώριση φωνής ===
def recognize_speech():
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    print("🎤 Μίλα τώρα...")
    result = speech_recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"👉 Είπες: {result.text}")
        return result.text.lower()
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("Δεν κατάλαβα τι είπες.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"Ακυρώθηκε: {cancellation.reason}")
    return None

# === TTS: Ομιλία απάντησης ===
def speak_text(text):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    # Ελληνική φωνή
    speech_config.speech_synthesis_voice_name = "el-GR-AthinaNeural"

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    print(f"💬 Βοηθός: {text}")
    speech_synthesizer.speak_text_async(text).get()

# === ΚΥΡΙΟ LOOP ===
def main():
    print("🤖 Ο βοηθός είναι έτοιμος! Πες κάτι...")
    while True:
        text = recognize_speech()
        if not text:
            continue

        # Αν πεις "έξοδος" ή "σταμάτα" τερματίζει
        if "έξοδος" in text or "σταμάτα" in text:
            speak_text("Αντίο!")
            break

        # Απλές απαντήσεις
        if "καλημέρα" in text:
            speak_text("Καλημέρα! Πώς είσαι;")
        elif "καλησπέρα" in text:
            speak_text("Καλησπέρα! Τι κάνεις;")
        elif "πως" in text and "εισαι" in text:
            speak_text("Είμαι πολύ καλά, ευχαριστώ!")
        else:
            speak_text("Δεν είμαι σίγουρη τι εννοείς.")

if __name__ == "__main__":
    main()
