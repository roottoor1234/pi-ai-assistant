# === speech_stt.py ===
import azure.cognitiveservices.speech as speechsdk
from config import AZURE_SPEECH_KEY, AZURE_REGION

def recognize_speech(visualizer):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    speech_config.speech_recognition_language = "el-GR"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("🎤 Μίλησε τώρα...")
    visualizer.listening_effect()

    result = recognizer.recognize_once()
    visualizer.stop_listening_effect()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.Canceled:
        print("❌ Ακύρωση:", result.cancellation_details.reason)
        return None
    else:
        print("⚠️ Άγνωστος λόγος:", result.reason)
        return None
