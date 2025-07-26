from flask import Flask, render_template, request, send_file
import sounddevice as sd
import soundfile as sf
import requests
import time

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
        sd.default.device = 2  # À ajuster selon ton micro
        start_time = time.time()
        # 🔽 Réduit le buffer à 15 sec
        recording = sd.rec(int(15 * samplerate), samplerate=samplerate, channels=1)
        return "🎙️ Enregistrement démarré"
    except Exception as e:
        return f"❌ Micro erreur : {str(e)}"

@app.route('/stop', methods=['POST'])
def stop():
    global recording, start_time
    try:
        sd.stop()
        duration = time.time() - start_time
        trimmed = recording[:int(duration * samplerate)]
        sf.write(FILENAME_INPUT, trimmed, samplerate)

        with open(FILENAME_INPUT, 'rb') as audio_file:
            # ⚡ Optimisation latency ElevenLabs
            response = requests.post(
                "https://api.elevenlabs.io/v1/speech-to-speech/mcvkJ4Ey41TgzezOmykh/stream",
                headers={
                    "xi-api-key": "sk_ab5680bdff7ab38d58108eb3e0dcbf28b188593673dd1f33",
                    "Accept": "audio/mpeg"
                },
                data={
                    "model_id": "eleven_multilingual_sts_v2",
                    "optimize_streaming_latency": "2"
                },
                files={"audio": (FILENAME_INPUT, audio_file, 'audio/wav')}
            )

        if response.status_code == 200:
            with open(FILENAME_OUTPUT, 'wb') as f:
                f.write(response.content)
            return send_file(FILENAME_OUTPUT, as_attachment=False, mimetype='audio/mpeg')
        else:
            return f"❌ API erreur : {response.status_code} {response.text}"
    except Exception as e:
        return f"❌ Traitement erreur : {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
