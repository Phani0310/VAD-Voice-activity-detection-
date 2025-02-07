 """Voice Recorder with VAD and MP3 Conversion.

This script records voice using WebRTC VAD and PyAudio.
It automatically detects speech, saves it as WAV, and converts it to MP3.

Libraries:
- pyaudio
- webrtcvad
- wave
- time
- pydub
"""

import pyaudio
import webrtcvad
import wave
import time
import sys
from pydub import AudioSegment


class VoiceRecorder:
    """Handles voice recording with VAD and saves it as an MP3 file."""

    def __init__(self, rate=16000, chunk_duration_ms=20, silence_threshold=1, vad_mode=3):
        """Initializes the voice recorder with audio and VAD settings.

        Args:
            rate (int): Sample rate (Hz).
            chunk_duration_ms (int): Chunk duration in milliseconds.
            silence_threshold (int): Silence duration before stopping recording.
            vad_mode (int): WebRTC VAD aggressiveness (0 to 3).
        """
        self.rate = rate
        self.chunk_duration_ms = chunk_duration_ms
        self.chunk_size = int(rate * chunk_duration_ms / 1000)
        self.silence_threshold = silence_threshold
        self.vad_mode = vad_mode

        self.audio = pyaudio.PyAudio()
        self.stream = self._init_audio_stream()
        self.vad = self._init_vad()

        self.frames = []
        self.recording = False
        self.output_filename = self._generate_filename()
        self.last_speech_time = time.time()

    def _init_audio_stream(self):
        """Initializes and returns the PyAudio stream."""
        return self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

    def _init_vad(self):
        """Initializes and returns the WebRTC VAD."""
        vad = webrtcvad.Vad()
        vad.set_mode(self.vad_mode)
        return vad

    def _generate_filename(self):
        """Generates a unique filename using the current timestamp."""
        return f"voice_{int(time.time())}.wav"

    def _save_wav_file(self, filename):
        """Saves recorded frames as a WAV file.

        Args:
            filename (str): The WAV file name.
        """
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))

    def _convert_to_mp3(self, wav_filename):
        """Converts a WAV file to MP3.

        Args:
            wav_filename (str): The WAV file to convert.

        Returns:
            str: The MP3 filename.
        """
        mp3_filename = wav_filename.replace(".wav", ".mp3")
        audio_segment = AudioSegment.from_wav(wav_filename)
        audio_segment.export(mp3_filename, format="mp3")
        return mp3_filename

    def _reset_for_next_recording(self):
        """Resets internal state for the next recording."""
        self.frames = []
        self.recording = False
        self.output_filename = self._generate_filename()

    def listen_and_record(self):
        """Main loop to listen and record voice based on VAD."""
        print("Listening for voice activity... Speak now! (Press Ctrl+C or Cmd+C to exit)")

        try:
            while True:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                is_speech = self.vad.is_speech(data, self.rate)

                if is_speech:
                    if not self.recording:
                        print("VOICE detected! Recording started...")
                        self.recording = True
                        self.frames = []
                    self.frames.append(data)
                    self.last_speech_time = time.time()

                elif self.recording:
                    silence_duration = time.time() - self.last_speech_time
                    if silence_duration > self.silence_threshold:
                        print(f"SILENCE detected for {self.silence_threshold} seconds! Saving file...")
                        self._save_wav_file(self.output_filename)
                        mp3_filename = self._convert_to_mp3(self.output_filename)
                        print(f"Saved: {mp3_filename}")
                        self._reset_for_next_recording()

        except KeyboardInterrupt:
            self._stop_recording()

        finally:
            self.cleanup()

    def _stop_recording(self):
        """Handles stopping the recording and saving the last file if needed."""
        print("\nStopped by user...")
        if self.recording and self.frames:
            print("Saving last recording...")
            self._save_wav_file(self.output_filename)
            mp3_filename = self._convert_to_mp3(self.output_filename)
            print(f"Final file saved: {mp3_filename}")

    def cleanup(self):
        """Closes the audio stream and terminates PyAudio."""
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        sys.exit(0)


if __name__ == "__main__":
    recorder = VoiceRecorder()
    recorder.listen_and_record()

