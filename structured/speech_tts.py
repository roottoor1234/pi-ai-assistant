# === speech_tts.py ===
import threading
import azure.cognitiveservices.speech as speechsdk
from config import AZURE_SPEECH_KEY, AZURE_REGION
import os

# --- Singleton Synthesizer Initialization ---
try:
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    print("[Azure TTS] Synthesizer initialized.")
except Exception as e:
    synthesizer = None
    print("[Azure TTS] Initialization failed:", e)

# === Flag για έλεγχο φωνής ===
is_speaking = False


def clean_gesture_marker(ssml_text):
    """
    Αν το SSML περιέχει 'R<' ή 'L<' (ακόμα κι αν είναι μέσα στο SSML), 
    αφαιρεί το γράμμα και επιστρέφει (ssml, gesture).
    Επίσης καθαρίζει stray 'L' ή 'R' που βρίσκονται σε λάθος θέση.
    """
    s = ssml_text.strip()

    # --- Αν το γράμμα είναι μέσα στο SSML (π.χ. "L\n <speak>")
    if "\nL" in s or "L\n" in s or "L <" in s or "L<" in s:
        s = s.replace("L", "", 1)
        return s.strip(), "L"

    if "\nR" in s or "R\n" in s or "R <" in s or "R<" in s:
        s = s.replace("R", "", 1)
        return s.strip(), "R"

    # --- Αν το γράμμα είναι στην αρχή (σωστή περίπτωση)
    if s.startswith("R<"):
        cleaned = s.replace("R<", "<", 1)
        return cleaned.strip(), "R"
    if s.startswith("L<"):
        cleaned = s.replace("L<", "<", 1)
        return cleaned.strip(), "L"

    # --- Αν το γράμμα είναι στο τέλος (π.χ. "</speak>L")
    if s.endswith("L"):
        return s[:-1].strip(), "L"
    if s.endswith("R"):
        return s[:-1].strip(), "R"

    return s, None


def speak_with_azure_tts(ssml_text, visualizer):
    def _speak():
        import time
        global is_speaking

        try:
            if synthesizer is None:
                print("[Azure TTS] Synthesizer not available!")
                visualizer.stop_speaking()
                return

            # === Απενεργοποίηση μικροφώνου πριν ξεκινήσει η εκφώνηση ===
            os.system("amixer set Capture nocap")

            # Καθαρισμός SSML και εύρεση gesture marker
            ssml_clean, gesture = clean_gesture_marker(ssml_text)
            if gesture:
                print(f"🤖 Gesture marker found: {gesture} (will run after TTS)")

            is_speaking = True
            visualizer.start_speaking()
            print("🔈 [TTS] Μιλάει τώρα...")
            tts_start = time.time()
            result_future = synthesizer.speak_ssml_async(ssml_clean)

            def check_done():
                global is_speaking
                result = result_future.get()
                tts_time = time.time() - tts_start

                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    print(f"✅ [TTS] Τελείωσε η εκφώνηση. ⏱️ {tts_time:.2f}s")

                    # === Εκτέλεση gesture ΜΕΤΑ το TTS ===
                    if gesture == "R":
                        print("🖐️ Εκτελεί gesture: δεξί χέρι (R)")
                        try:
                            from arduino_control import wave_right_hand
                            wave_right_hand()
                        except Exception as e:
                            print("⚠️ Gesture error:", e)

                    elif gesture == "L":
                        print("👈 Εκτελεί gesture: αριστερό χέρι (L)")
                        try:
                            from arduino_control import wave_left_hand
                            wave_left_hand()
                        except Exception as e:
                            print("⚠️ Gesture error:", e)

                elif result.reason == speechsdk.ResultReason.Canceled:
                    print("❌ [TTS] Ακυρώθηκε:", result.cancellation_details.reason)
                    # Εμφάνιση ευγενικού fallback μηνύματος
                    fallback = (
                        "<speak version=\"1.0\" xmlns:mstts=\"https://www.w3.org/2001/mstts\" xml:lang=\"el-GR\">"
                        "<voice name=\"el-GR-NestorasNeural\">"
                        "<mstts:express-as style=\"chat\">"
                        "<prosody rate=\"0.85\" pitch=\"+2.2st\">"
                        "Μπορείτε να επαναλάβετε παρακαλώ;"
                        "</prosody>"
                        "</mstts:express-as>"
                        "</voice>"
                        "</speak>"
                    )
                    try:
                        print("🔁 [TTS] Παίζει fallback μήνυμα (επανάληψη)...")
                        synthesizer.speak_ssml_async(fallback).get()
                    except Exception as e:
                        print("⚠️ Fallback error:", e)

                time.sleep(0.2)
                visualizer.stop_speaking()
                is_speaking = False

                # === Επανενεργοποίηση μικροφώνου ===
                os.system("amixer set Capture cap")

            threading.Thread(target=check_done, daemon=True).start()

        except Exception as e:
            print("⚠️ Σφάλμα στο Azure TTS:", e)
            visualizer.stop_speaking()
            is_speaking = False
            os.system("amixer set Capture cap")  # ασφάλεια: ενεργοποίησε ξανά το mic

    threading.Thread(target=_speak, daemon=True).start()
