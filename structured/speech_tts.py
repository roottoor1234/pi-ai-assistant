# === speech_tts.py ===
import threading
import azure.cognitiveservices.speech as speechsdk
from config import AZURE_SPEECH_KEY, AZURE_REGION


# --- Singleton Synthesizer Initialization ---
try:
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    print("[Azure TTS] Synthesizer initialized.")
except Exception as e:
    synthesizer = None
    print("[Azure TTS] Initialization failed:", e)


def clean_gesture_marker(ssml_text):
    """
    Αν το SSML ξεκινά με 'R<', αφαίρεσε το R και επιστρέφει (ssml, True).
    Αλλιώς επιστρέφει (ssml, False).
    """
    s = ssml_text.lstrip()
    if s.startswith('R<'):
        # Αφαίρεσε το πρώτο R μόνο αν ακολουθεί <
        idx = ssml_text.find('R<')
        cleaned = ssml_text[:idx] + ssml_text[idx+1:]
        return cleaned, True
    return ssml_text, False

def speak_with_azure_tts(ssml_text, visualizer):
    def _speak():
        import time
        try:
            if synthesizer is None:
                print("[Azure TTS] Synthesizer not available!")
                visualizer.stop_speaking()
                return

            # Καθαρισμός gesture marker (R) πριν το TTS
            ssml_clean, gesture = clean_gesture_marker(ssml_text)
            if gesture:
                print("🤖 Gesture detected: right hand wave (R)")
                try:
                    from arduino_control import wave_right_hand
                    wave_right_hand()
                except Exception as e:
                    print("⚠️ Gesture error:", e)

            visualizer.start_speaking()
            print("🔈 [TTS] Μιλάει τώρα...")
            tts_start = time.time()
            result_future = synthesizer.speak_ssml_async(ssml_clean)

            def check_done():
                result = result_future.get()
                tts_time = time.time() - tts_start
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    print(f"✅ [TTS] Τελείωσε η εκφώνηση. ⏱️ Χρόνος TTS: {tts_time:.2f}s")
                elif result.reason == speechsdk.ResultReason.Canceled:
                    print("❌ [TTS] Ακυρώθηκε:", result.cancellation_details.reason)
                visualizer.stop_speaking()

            threading.Thread(target=check_done, daemon=True).start()

        except Exception as e:
            print("⚠️ Σφάλμα στο Azure TTS:", e)
            visualizer.stop_speaking()

    threading.Thread(target=_speak, daemon=True).start()



# # === speech_tts.py ===
# import threading
# import azure.cognitiveservices.speech as speechsdk
# from config import AZURE_SPEECH_KEY, AZURE_REGION


# # --- Singleton Synthesizer Initialization ---
# try:
#     speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
#     audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
#     synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
#     print("[Azure TTS] Synthesizer initialized.")
# except Exception as e:
#     synthesizer = None
#     print("[Azure TTS] Initialization failed:", e)

# def speak_with_azure_tts(ssml_text, visualizer):
#     def _speak():
#         import time
#         try:
#             if synthesizer is None:
#                 print("[Azure TTS] Synthesizer not available!")
#                 visualizer.stop_speaking()
#                 return

#             visualizer.start_speaking()
#             print("🔈 [TTS] Μιλάει τώρα...")
#             tts_start = time.time()
#             result_future = synthesizer.speak_ssml_async(ssml_text)

#             def check_done():
#                 result = result_future.get()
#                 tts_time = time.time() - tts_start
#                 if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
#                     print(f"✅ [TTS] Τελείωσε η εκφώνηση. ⏱️ Χρόνος TTS: {tts_time:.2f}s")
#                 elif result.reason == speechsdk.ResultReason.Canceled:
#                     print("❌ [TTS] Ακυρώθηκε:", result.cancellation_details.reason)
#                 visualizer.stop_speaking()

#             threading.Thread(target=check_done, daemon=True).start()

#         except Exception as e:
#             print("⚠️ Σφάλμα στο Azure TTS:", e)
#             visualizer.stop_speaking()

#     threading.Thread(target=_speak, daemon=True).start()
