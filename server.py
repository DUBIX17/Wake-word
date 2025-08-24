from flask import Flask, request, jsonify, render_template
import wave
import tempfile
import os
import struct
import pvporcupine

app = Flask(__name__)

# Init Porcupine
access_key = os.getenv("PICOVOICE_KEY")  # set in Render dashboard
ppn_file = "./wake_word.ppn"             # include in repo
porcupine = pvporcupine.create(access_key=access_key, keyword_paths=[ppn_file])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect", methods=["POST"])
def detect():
    """
    Accepts raw PCM audio (16-bit, mono, 16kHz) or WAV file via multipart.
    """
    # If form-data with a file
    if "audio" in request.files:
        audio_file = request.files["audio"]
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            audio_file.save(tmp.name)
            with wave.open(tmp.name, "rb") as wf:
                pcm_data = wf.readframes(wf.getnframes())
        os.unlink(tmp.name)
    else:
        # If raw body (application/octet-stream)
        pcm_data = request.data

    # Convert bytes -> int16 array
    frame_length = porcupine.frame_length
    audio_samples = struct.unpack_from("h" * (len(pcm_data) // 2), pcm_data)

    detected = False
    for i in range(0, len(audio_samples) - frame_length, frame_length):
        frame = audio_samples[i:i+frame_length]
        result = porcupine.process(frame)
        if result >= 0:
            detected = True
            break

    return jsonify({"wakeword": detected})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
