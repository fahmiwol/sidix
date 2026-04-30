"""SDXL smoke test — fit RTX 3060 6GB via CPU offload."""
import time, torch
from diffusers import StableDiffusionXLPipeline

print(f"CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}")
t0 = time.time()
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16, variant="fp16", use_safetensors=True,
)
pipe.enable_model_cpu_offload()
pipe.enable_attention_slicing()
print(f"Load: {time.time()-t0:.1f}s")

t0 = time.time()
img = pipe("a serene masjid at dawn, golden hour", num_inference_steps=25,
           height=1024, width=1024).images[0]
dt = time.time()-t0
img.save(r"D:\sidix-local\output\test.png")
print(f"Generate: {dt:.1f}s -> D:\\sidix-local\\output\\test.png")
print(f"VRAM peak: {torch.cuda.max_memory_allocated()/1e9:.1f} GB")
