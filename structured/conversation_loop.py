# === conversation_loop.py ===
import time
from google.genai import types
from speech_stt import recognize_speech
from llm_gemini import ask_gemini
from speech_tts import speak_with_azure_tts
from arduino_control import wave_right_hand  
from arduino_control import wave_left_hand


def smartbot_loop(visualizer, root):
    history = []
    print("🤖 Ο SmartBot είναι έτοιμος. Πες 'τέλος' για έξοδο.\n")

    while True:
        query = recognize_speech(visualizer)
        if not query:
            continue

        user_text = query.strip().lower()
        print("📝 Ερώτηση:", user_text)

        # === Έξοδος ===
        if user_text in ["τέλος", "σταμάτα", "exit", "quit", "stop", "στοπ"]:
            print("👋 Αντίο!")
            root.quit()
            break

        # === ΕΛΕΓΧΟΣ ΓΙΑ "ΚΑΛΗΜΕΡΑ" ΚΑΙ ΠΑΡΟΜΟΙΑ ===
        greetings = [
            "καλημέρα", "καλημέρα.", "καλημέρα!",
            "καλημέρα σας", "καλημέρα σας!",
            "γεια σου", "γεια σου!", "γεια σας", "γεια σας!",
            "χαίρομαι που σε βλέπω", "χαίρομαι που σε βλέπω!"
        ]

        if user_text in greetings:
            fixed_answer = (
                "<speak version=\"1.0\" xmlns:mstts=\"https://www.w3.org/2001/mstts\" xml:lang=\"el-GR\">"
                "<voice name=\"el-GR-NestorasNeural\">"
                "<mstts:express-as style=\"chat\">"
                "<prosody rate=\"0.85\" pitch=\"+2.2st\">"
                "Καλημέρα! <break time=\"200ms\"/> Πώς μπορώ να σας βοηθήσω;"
                "</prosody>"
                "</mstts:express-as>"
                "</voice>"
                "</speak>"
            )

            print("🤖 Fixed απάντηση (Καλημέρα):", fixed_answer)
            speak_with_azure_tts(fixed_answer, visualizer)
            wave_right_hand()
            time.sleep(3)

            continue  # ⛔ Μην μπαίνεις στο Gemini για χαιρετισμό

        # === Αποστολή στο Gemini ===
        history.append(types.Content(role="user", parts=[types.Part.from_text(text=query)]))
        visualizer.start_thinking()
        start_time = time.time()
        answer = ask_gemini(history, visualizer)
        visualizer.stop_thinking()


        # === Εκφώνηση ===
        elapsed = time.time() - start_time
        print(f"🤖 Απάντηση SSML:\n{answer}\n⏱️ Χρόνος απόκρισης: {elapsed:.2f}s")

        history.append(types.Content(role="model", parts=[types.Part.from_text(text=answer)]))
        speak_with_azure_tts(answer, visualizer)

        # Μικρή παύση για αποφυγή “echo” στη φωνή
        time.sleep(3)

