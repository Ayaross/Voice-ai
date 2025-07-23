from flask import Flask, render_template, request, send_file
import sounddevice as sd
import soundfile as sf
import requests
import time
import threading
import os

app = Flask(__name__)

FILENAME_INPUT = "temp_input.wav"
FILENAME_OUTPUT = "output.mp3"
samplerate = 44100
recording = None
start_time = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    global recording, start_time
    try:
        sd.default.device = 2  # À adapter si besoin
        start_time = time.time()
        recording = sd.rec(int(60 * samplerate), samplerate=samplerate, channels=1)
        return "🎙️ Enregistrement lancé"
    except Exception as e:
        return f"❌ Erreur micro : {str(e)}"

@app.route('/stop', methods=['POST'])
def stop():
    global recording, start_time
    try:
        sd.stop()
        duration = time.time() - start_time
        recording_trimmed = recording[:int(duration * samplerate)]
        sf.write(FILENAME_INPUT, recording_trimmed, samplerate)

        with open(FILENAME_INPUT, 'rb') as audio_file:
            response = requests.post(
                "https://api.elevenlabs.io/v1/speech-to-speech/mcvkJ4Ey41TgzezOmykh/stream",
                headers={"xi-api-key": "sk_ab5680bdff7ab38d58108eb3e0dcbf28b188593673dd1f33"},
                data={"model_id": "eleven_multilingual_sts_v2", "file_format": "other"},
                files={"audio": (FILENAME_INPUT, audio_file, 'audio/wav')}
            )

        if response.status_code == 200:
            with open(FILENAME_OUTPUT, 'wb') as f:
                f.write(response.content)

            # ✅ Lecture locale du fichier (sur PC)
            def safe_play_output():
                try:
                    time.sleep(1.5)
                    #os.startfile(FILENAME_OUTPUT)
                except Exception as e:
                    print("❌ Erreur lecture automatique :", e)

            threading.Thread(target=safe_play_output).start()

            return send_file(FILENAME_OUTPUT, as_attachment=True)
        else:
            return f"❌ Erreur API : {response.status_code} {response.text}"
    except Exception as e:
        return f"❌ Erreur traitement : {str(e)}"

if __name__ == '__main__':
    app.run()
