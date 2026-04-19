"""SDXL FastAPI server — listens localhost:8000/generate."""
import base64, io, time, torch
from fastapi import FastAPI
from pydantic import BaseModel
from diffusers import StableDiffusionXLPipeline

print("Loading SDXL...")
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16, variant="fp16", use_safetensors=True,
)
# Gunakan sequential offload untuk stabilitas lintas-request (hindari device mismatch bug)
pipe.enable_sequential_cpu_offload()
pipe.enable_attention_slicing()
pipe.enable_vae_tiling()
print("Ready.")

app = FastAPI()

class GenReq(BaseModel):
    prompt: str
    negative_prompt: str = ""
    steps: int = 25
    width: int = 1024
    height: int = 1024

@app.get("/health")
def health():
    return {"ok": True, "gpu": torch.cuda.get_device_name(0), "vram_gb": round(torch.cuda.get_device_properties(0).total_memory/1e9, 1)}

@app.post("/generate")
def generate(req: GenReq):
    t0 = time.time()
    img = pipe(
        req.prompt, negative_prompt=req.negative_prompt,
        num_inference_steps=req.steps, height=req.height, width=req.width,
    ).images[0]
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {"ok": True, "image_b64": b64, "took_s": round(time.time()-t0, 1),
            "vram_peak_gb": round(torch.cuda.max_memory_allocated()/1e9, 2)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
