import pyaudio
import webrtcvad
import wave
import time
from pydub import AudioSegment

# Audio settings
FORMAT = pyaudio.paInt16  # 16-bit audio format
CHANNELS = 1  # Mono audio
RATE = 16000  # 16kHz sample rate (preferred by VAD)
CHUNK = 320  # 20ms frame size (16000 Hz * 0.02s = 320 samples)
SILENCE_THRESHOLD = 1  # Seconds of silence to stop recording
RECORD_SECONDS = 10  # Max recording time per file

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Open microphone stream
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

# Initialize WebRTC VAD
vad = webrtcvad.Vad()
vad.set_mode(2)  # Sensitivity: 0 (Least Sensitive) to 3 (Most Sensitive)

# Storage for recorded audio
frames = []
recording = False
output_filename = f"voice_{int(time.time())}.wav"
last_speech_time = time.time()

print("Listening for voice activity... Speak now!")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)

        # Check for voice activity
        is_speech = vad.is_speech(data, RATE)

        if is_speech:
            if not recording:
                print("Voice detected! Recording started...")
                recording = True
                frames = []  # Reset frames to start fresh
            frames.append(data)
            last_speech_time = time.time()  # Reset silence timer

        elif recording:
            # Check if silence has been detected for the threshold time
            silence_duration = time.time() - last_speech_time
            if silence_duration > SILENCE_THRESHOLD:
                print(f"Silence detected for {SILENCE_THRESHOLD} seconds! Saving file...")
                # Save as WAV
                with wave.open(output_filename, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(audio.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))

                # Convert to MP3
                mp3_filename = output_filename.replace(".wav", ".mp3")
                sound = AudioSegment.from_wav(output_filename)
                sound.export(mp3_filename, format="mp3")

                print(f"Saved: {mp3_filename}")
                break  # Exit after saving the file

except KeyboardInterrupt:
    print("\nStopping...")
    stream.stop_stream()
    stream.close()
    audio.terminate()



