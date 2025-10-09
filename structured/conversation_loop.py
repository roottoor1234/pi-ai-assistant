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
            break

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
