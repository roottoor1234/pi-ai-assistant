# === conversation_loop.py ===
import time
from google.genai import types
from speech_stt import recognize_speech
from llm_gemini import ask_gemini
from speech_tts import speak_with_azure_tts
from arduino_control import wave_right_hand  

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
            
        # === ΕΛΕΓΧΟΣ ΓΙΑ "ΚΑΛΗΜΕΡΑ" ===
        print(f"Ερώτηση χρήστη: {query.strip().lower()}")
        if query.strip().lower() in ["καλημέρα.", "καλημέρα!", "καλημέρα σας", "καλημέρα σας!", "γεια σου", "γεια σου!", "γεια σας", "γεια σας!", "χαίρομαι που σε βλέπω", "χαίρομαι που σε βλέπω!"]:
            fixed_answer = (
                "<speak version=\"1.0\" xmlns:mstts=\"https://www.w3.org/2001/mstts\" xml:lang=\"el-GR\">"
                "<voice name=\"el-GR-NestorasNeural\">"
                "<mstts:express-as style=\"chat\">"
                "<prosody rate=\"0.85\" pitch=\"+2.2st\">"
                "Καλημέρα! <break time=\"200ms\"/> Πως μπορώ να σας βοηθήσω;"
                "</prosody>"
                "</mstts:express-as>"
                "</voice>"
                "</speak>"
            )
            print("🤖 Fixed απάντηση (Καλημέρα):", fixed_answer)
            # visualizer.start_speaking()
            time.sleep(0.5)  # Μικρή καθυστέρηση πριν το κύμα
            wave_right_hand()
            speak_with_azure_tts(fixed_answer, visualizer)
            # visualizer.stop_speaking()
            time.sleep(1)
            continue  # ❌ μην μπαίνεις στο Gemini

        history.append(types.Content(role="user", parts=[types.Part.from_text(text=query)]))
        visualizer.start_thinking()
        start_time = time.time()
        answer = ask_gemini(history, visualizer)
        visualizer.stop_thinking()

        # 🖐️ Αν η απάντηση ξεκινά με 'R', κάνε χαιρετισμό
        if answer.startswith("R"):
            print("🤖 Gesture detected: right hand wave (R)")
            answer = answer.replace("R", "", 1)
            # wave_right_hand()

        print(f"🤖 Απάντηση SSML:\n{answer}\n⏱️ Χρόνος: {time.time() - start_time:.2f}s")
        history.append(types.Content(role="model", parts=[types.Part.from_text(text=answer)]))

        speak_with_azure_tts(answer, visualizer)
        time.sleep(1)
