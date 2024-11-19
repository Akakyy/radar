import os
import sys
import argparse
import wave
import numpy as np
import tokenizers
from pathlib import Path
import click, json
from radar.onnx_model import MoonshineOnnxModel

from radar.Radar import Radar


def read_wav(wav_file: Path):
    with wave.open(wav_file) as f:
        params = f.getparams()
        assert (
            params.nchannels == 1
            and params.framerate == 16_000
            and params.sampwidth == 2
        ), f"wave file should have 1 channel, 16KHz, and int16"
        audio = f.readframes(params.nframes)
    
    return audio


def inference_audio(audio, model, tokenizer_path: Path):
    audio = np.frombuffer(audio, np.int16) / 32768.0
    audio = audio.astype(np.float32)[None, ...]
    tokens = model.generate(audio)
    print(tokens)
    tokenizer = tokenizers.Tokenizer.from_file(str(tokenizer_path))
    return tokenizer.decode_batch(tokens)


@click.command()
@click.option('--config', required=True, type=Path, default="config.json", help='Directory containing config for running model and other params.')
def main(config: Path):
    try:
        with open(config) as f:
            config_json = json.loads(f.read())
            models_dir = Path(config_json['model']['models_dir'])
            if not models_dir.exists():
                print(f'Folder with model {str(models_dir)} doesn\'t exist')
                exit(1)
            tokenizer_path = Path(config_json['model']['tokenizer_path'])
            dir_to_save_wav = config_json['dir_to_save_wav']
            (models_dir)
            model = MoonshineOnnxModel(models_dir=models_dir, use_gpu=False)
            print('Model loaded successfully')
            audio = read_wav('C:\\temp\\e94b1c30-6b41-407f-afab-958197da510e.wav')
            text = inference_audio(audio, model, tokenizer_path)
            print(text)
            #radar = Radar(dir_to_save_wav)
            #radar.run()
    except Exception as e:
        #print(str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()