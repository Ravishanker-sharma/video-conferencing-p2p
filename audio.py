
import pyaudio
import threading

class AudioManager:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream_in = None
        self.stream_out = None
        self.running = False

        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        self.RATE = 44100
        
        self.input_callback = None
        self.is_mic_muted = False
        self.is_speaker_muted = False

    def start_streams(self, input_callback):
        """
        Starts input and output streams.
        input_callback(data) called when audio is recorded.
        """
        self.input_callback = input_callback
        self.running = True

        try:
            # Input Stream (Microphone)
            self.stream_in = self.p.open(format=self.FORMAT,
                                         channels=self.CHANNELS,
                                         rate=self.RATE,
                                         input=True,
                                         frames_per_buffer=self.CHUNK,
                                         stream_callback=self._mic_callback)
            
            # Output Stream (Speaker)
            self.stream_out = self.p.open(format=self.FORMAT,
                                          channels=self.CHANNELS,
                                          rate=self.RATE,
                                          output=True,
                                          frames_per_buffer=self.CHUNK)
            
            self.stream_in.start_stream()
            self.stream_out.start_stream()
            
        except Exception as e:
            print(f"Audio Start Error: {e}")
            self.stop_streams()

    def _mic_callback(self, in_data, frame_count, time_info, status):
        if self.running and self.input_callback and not self.is_mic_muted:
            self.input_callback(in_data)
        return (None, pyaudio.paContinue)

    def write_audio(self, data):
        """
        Writes received audio data to the speakers.
        """
        if self.running and self.stream_out and not self.is_speaker_muted:
            try:
                self.stream_out.write(data)
            except Exception as e:
                print(f"Audio Write Error: {e}")

    def stop_streams(self):
        self.running = False
        if self.stream_in:
            self.stream_in.stop_stream()
            self.stream_in.close()
            self.stream_in = None
            
        if self.stream_out:
            self.stream_out.stop_stream()
            self.stream_out.close()
            self.stream_out = None

    def close(self):
        self.stop_streams()
        self.p.terminate()
