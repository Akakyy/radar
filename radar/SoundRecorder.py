import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import os
import threading
import time
from pathlib import Path
import uuid


class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.recorded_frames = []
        self.temp_file = None

    def start_recording(self):
        self.recording = True
        self.recorded_frames = []
        # Создаем уникальное имя для файла с использованием UUID
        filename = Path("C:/temp/") / f"{uuid.uuid4()}.wav"
        self.temp_file = filename.open('wb')

        # Запускаем поток для записи
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()
        
        
    def stop_recording(self):
        self.recording = False
        # Ожидаем завершения потока
        self.recording_thread.join()

        # Записываем аудио
        sf.write(self.temp_file, np.concatenate(self.recorded_frames), self.sample_rate)
        self.temp_file.close()
        print(f"Recording saved to {self.temp_file.name}")

    def _record(self):
        # Поток для записи с использованием sounddevice
        with sd.InputStream(samplerate=self.sample_rate, 
                            channels=self.channels, 
                            callback=self._audio_callback):
            while self.recording:
                time.sleep(0.1)

    def _audio_callback(self, indata, frames, time, status):
        # Обработка аудио данных
        if status:
            print(status)
        if self.recording:
            self.recorded_frames.append(indata.copy())
