import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import threading
import time
from pathlib import Path
import uuid

class AudioRecorder:
    def __init__(self, dir_to_save_wav, sample_rate=16000, channels=1):
        self.dir_to_save_wav = dir_to_save_wav
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.recorded_frames = []
        self.temp_file = None
        self.save_full_filename = None

    def start_recording(self):
        self.recording = True
        self.recorded_frames = []
        self.save_full_filename = Path(self.dir_to_save_wav) / f"{uuid.uuid4()}.wav"
        self.temp_file = self.save_full_filename.open('wb')

        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()

    def stop_recording(self):
        self.recording = False
        self.recording_thread.join()
        
        audio_data = np.concatenate(self.recorded_frames, axis=0)

        sf.write(self.temp_file, audio_data, self.sample_rate, subtype='PCM_16')
        self.temp_file.close()
        print(f"Recording saved to {self.temp_file.name}")
        return self.save_full_filename

    def _record(self):
        with sd.InputStream(samplerate=self.sample_rate, 
                            channels=self.channels, 
                            callback=self._audio_callback):
            while self.recording:
                time.sleep(0.1)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.recording:
            indata = (indata * 32767).astype(np.int16)
            self.recorded_frames.append(indata.copy())
