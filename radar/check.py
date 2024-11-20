from transformers import WhisperForConditionalGeneration, WhisperProcessor, pipeline
import torch

torch_dtype = torch.bfloat16 # set your preferred type here 

device = 'cpu'
if torch.cuda.is_available():
    device = 'cuda'
elif torch.backends.mps.is_available():
    device = 'mps'
    setattr(torch.distributed, "is_initialized", lambda : False) # monkey patching
device = torch.device(device)

whisper = WhisperForConditionalGeneration.from_pretrained(
    "D:\\downloads\\radar_commit\\radar\\radar\\whisper-large-v3-russian", 
    torch_dtype=torch_dtype, 
    low_cpu_mem_usage=True, use_safetensors=True,
    # add attn_implementation="flash_attention_2" if your GPU supports it
)

processor = WhisperProcessor.from_pretrained("D:\\downloads\\radar_commit\\radar\\radar\\whisper-large-v3-russian")

asr_pipeline = pipeline(
    "automatic-speech-recognition",
    model=whisper,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=256,
    chunk_length_s=30,
    batch_size=16,
    return_timestamps=True,
    torch_dtype=torch_dtype,
    device=device,
)

# read your wav file into variable wav. For example:
from io import BufferIO
wav = BytesIO()
with open('record-normalized.wav', 'rb') as f:
    wav.write(f.read())
wav.seek(0)

# get the transcription
asr = asr_pipeline(wav, generate_kwargs={"language": "russian", "max_new_tokens": 256}, return_timestamps=False)

print(asr['text'])