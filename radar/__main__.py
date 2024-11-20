import os
import sys
import argparse
import wave
import numpy as np
import tokenizers
from pathlib import Path
import click, json
import torch
#from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from transformers import WhisperForConditionalGeneration, WhisperProcessor, pipeline
from safetensors.torch import save_file
from faster_whisper import WhisperModel

from radar.Radar import Radar

def load_model_fast(model_path):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f'Loading model on: {device} from {model_path}')
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    # Run on GPU with FP16
    #model = WhisperModel(model_size, device="cuda", compute_type="float16")

    # or run on GPU with INT8
    # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
    # or run on CPU with INT8
    model = WhisperModel(model_path, device=device, compute_type="int8", language="ru")
    return model



def load_model(model_path):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f'Loading model on: {device}')
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    #model_id = "openai/whisper-large-v3"

    #model = AutoModelForSpeechSeq2Seq.from_pretrained(
    #    model_path, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    #)
    #model.to(device)
    
    torch_dtype = torch.bfloat16 # set your preferred type here 

    device = 'cpu'
    if torch.cuda.is_available():
        device = 'cuda'
    elif torch.backends.mps.is_available():
        device = 'mps'
        setattr(torch.distributed, "is_initialized", lambda : False) # monkey patching
    device = torch.device(device)

    model = WhisperForConditionalGeneration.from_pretrained(
        "D:\\downloads\\radar_commit\\radar\\radar\\whisper-large-v3-russian", 
        torch_dtype=torch_dtype, 
        low_cpu_mem_usage=True, use_safetensors=True,
        # add attn_implementation="flash_attention_2" if your GPU supports it
    )
    
    processor = WhisperProcessor.from_pretrained("D:\\downloads\\radar_commit\\radar\\radar\\whisper-large-v3-russian")
    asr_pipeline = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=256,
        chunk_length_s=30,
        batch_size=16,
        return_timestamps=True,
        torch_dtype=torch_dtype,
        device=device,
    )
    
    #processor = AutoProcessor.from_pretrained(model_path)
    #pipe = pipeline(
        #"automatic-speech-recognition",
        #model=model,
        #tokenizer=processor.tokenizer,
        #feature_extractor=processor.feature_extractor,
        #torch_dtype=torch_dtype,
        #device=device,
    #)
    return model, processor, asr_pipeline


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
            #model = load_model_fast(models_dir)
            print('Model loaded successfully')
            radar = Radar(dir_to_save_wav, pipe)
            radar.run()
    except Exception as e:
        #print(str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()