import os
import sys
import argparse
import wave
import numpy as np
import tokenizers
from pathlib import Path
import click, json
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from radar.Radar import Radar


def load_model(model_path):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f'Loading model on: {device}')
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    #model_id = "openai/whisper-large-v3"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_path, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_path)
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
    )
    return model, processor, pipe


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
            dir_to_save_wav = config_json['dir_to_save_wav']
            model, preprocessor, pipe = load_model(models_dir)
            print('Model loaded successfully')
            radar = Radar(dir_to_save_wav, pipe)
            radar.run()
    except Exception as e:
        #print(str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()