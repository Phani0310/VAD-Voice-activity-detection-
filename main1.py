import pyaudio
import webrtcvad
import wave
import time
import sys
import keyboard  # For detecting Cmd + C / Ctrl + C
from pydub import AudioSegment

# Audio settings
FORMAT = pyaudio.paInt16  # 16-bit audio format 
CHANNELS = 1  # Mono audio
RATE = 16000  # 16kHz sample rate 
CHUNK = 320  # 20ms frame size 
SILENCE_THRESHOLD = 1  # Seconds of silence to stop recording

# Initialize PyAudio
audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

# Initialize WebRTC VAD with highest noise filtering
vad = webrtcvad.Vad()
vad.set_mode(3)  # 0 = Least aggressive, 3 = Most aggressive (best for noise filtering)

frames = []
recording = False
output_filename = f"voice_{int(time.time())}.wav"
last_speech_time = time.time()

print(" Listening for voice activity... Speak now! (Press Ctrl+C or Cmd+C to exit)")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)

        # Check for voice activity
        is_speech = vad.is_speech(data, RATE)

        if is_speech:
            if not recording:
                print("VOICE detected! Recording started...")
                recording = True
                frames = []  # Start fresh
            frames.append(data)
            last_speech_time = time.time()

        elif recording:
            silence_duration = time.time() - last_speech_time
            if silence_duration > SILENCE_THRESHOLD:
                print(f"SILENCE detected for {SILENCE_THRESHOLD} seconds! Saving file...")

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

                print(f" Saved: {mp3_filename}")
                recording = False  # Reset state
                output_filename = f"voice_{int(time.time())}.wav"

        # **Check for Ctrl+C / Cmd+C exit command**
        if keyboard.is_pressed("ctrl+c") or keyboard.is_pressed("command+c"):
            print("\n Stopped...")

            # Save last recording if in progress
            if recording and frames:
                print(" Saving last recording...")
                with wave.open(output_filename, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(audio.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))

                mp3_filename = output_filename.replace(".wav", ".mp3")
                sound = AudioSegment.from_wav(output_filename)
                sound.export(mp3_filename, format="mp3")
                print(f" Final file saved: {mp3_filename}")

            print(" Exiting program.")
            break

except KeyboardInterrupt:
    print("\n Stopping...")

# Cleanup
stream.stop_stream()
stream.close()
audio.terminate()
sys.exit(0)  

