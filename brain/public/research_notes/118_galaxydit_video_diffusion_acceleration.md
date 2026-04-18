# 118 — GalaxyDiT: Akselerasi Video Diffusion Transformer

**Tanggal:** 2026-04-18  
**Sumber:** Arxiv 2512.03451 — "GalaxyDiT: Training-Free Acceleration of Video Diffusion Transformers via Adaptive Proxy Selection"  
**Relevansi SIDIX:** Kapabilitas generasi video masa depan, efisiensi inference DiT

---

## Apa

GalaxyDiT adalah metode **tanpa training** untuk mempercepat inferensi **Video Diffusion Transformer (DiT)** — model seperti Wan2.1, CogVideoX, HunyuanVideo. Idenya: tidak semua timestep denoising membutuhkan komputasi penuh. Sebagian besar komputasi bisa di-*recycle* dari timestep sebelumnya.

**Pencapaian kunci:**
- **2.37× speedup** pada Wan2.1-14B (dari baseline 1.0×)
- Kualitas turun hanya **0.72%** di VBench-2.0
- Tanpa training ulang, tanpa fine-tuning — plug-and-play

---

## Mengapa

Video DiT modern (Wan2.1, HunyuanVideo) pakai ratusan timestep denoising. Tiap step = forward pass penuh di transformer besar (14B parameter). Biaya komputasi sangat tinggi.

**Insight utama GalaxyDiT:**
1. **Temporal redundancy** — output attention/MLP di timestep berurutan sangat mirip
2. **Proxy caching** — simpan output timestep T sebagai "proxy" untuk timestep T+1
3. **Adaptive selection** — pilih proxy terbaik (bukan cuma prev timestep) berdasarkan kesamaan

---

## Bagaimana

### Dua Teknik Utama

#### 1. Adaptive Proxy Selection
- Daripada selalu pakai timestep t-1 sebagai proxy, GalaxyDiT **mencari timestep terbaik** dari pool kandidat
- Proxy dipilih berdasarkan similarity score antar feature map
- Timestep di awal/akhir denoising = komputasi penuh; timestep tengah = pakai proxy

#### 2. CFG-Aligned Reuse
- **CFG (Classifier-Free Guidance)**: setiap step butuh 2 forward pass (conditional + unconditional)
- GalaxyDiT align reuse antara kedua pass ini → hemat ~50% dari overlap computation
- Alignment mempertahankan kualitas guidance

### Alur Inference
```
[Noise] → Step 1 (full compute) → Step 2 (proxy from Step 1) 
       → Step 3 (adaptive, check similarity) → ... → [Video]
```

### Framework
- Berbasis PyTorch
- Compatible dengan: Wan2.1-14B, CogVideoX-5B, HunyuanVideo
- Tidak butuh modifikasi model weights

---

## Benchmark

| Model | Baseline FPS | GalaxyDiT FPS | Speedup | Quality Drop |
|-------|-------------|---------------|---------|--------------|
| Wan2.1-14B | ~0.3 fps | ~0.71 fps | 2.37× | 0.72% |
| CogVideoX-5B | ~0.8 fps | ~1.7 fps | 2.1× | 0.8% |

*VBench-2.0 dipakai sebagai metric quality (higher = better)*

---

## Keterbatasan

- Speedup bervariasi per model architecture — transformer yang lebih homogen profitnya lebih besar
- Tidak bisa dipakai kalau timestep schedule non-standard (custom schedulers bisa butuh adaptasi)
- GPU memory tidak berkurang, hanya *latency* yang berkurang
- Proxy selection overhead ~5% dari total step (kecil tapi ada)

---

## Relevansi untuk SIDIX

### Jangka Pendek
- Belajar tentang **DiT architecture** (berbeda dari U-Net based diffusion)
- Pahami **CFG** dan mengapa diperlukan dalam conditional generation
- Referensi untuk skill: "video_generation_optimization"

### Jangka Panjang
Ketika SIDIX mulai support **Video AI capability**:
1. GalaxyDiT bisa di-apply ke Wan2.1 (open-source, bisa di-run sendiri)
2. Tanpa training = bisa dipakai langsung sebagai inference wrapper
3. 2.37× lebih cepat = lebih feasible untuk production deployment

### Mapping ke SIDIX Architecture
```python
# Conceptual — future video capability
class SIDIXVideoEngine:
    def __init__(self):
        self.model = load_wan21_14b()
        self.accelerator = GalaxyDiTAccelerator(
            proxy_pool_size=5,
            cfg_align=True
        )
    
    def generate(self, prompt, steps=50):
        return self.accelerator.run(self.model, prompt, steps)
```

---

## Konsep Kunci untuk SIDIX Corpus

| Term | Definisi |
|------|----------|
| DiT | Diffusion Transformer — pakai attention blocks, bukan convolution (seperti U-Net) |
| Timestep | Satu langkah dalam proses denoising (biasanya 20-50 steps) |
| Proxy | Output dari timestep sebelumnya yang di-reuse di timestep berikutnya |
| CFG | Classifier-Free Guidance — teknik conditional generation dengan 2 forward pass |
| VBench-2.0 | Benchmark evaluasi kualitas video generatif (resolution, motion, semantics) |

---

## Referensi
- Paper: arxiv.org/abs/2512.03451
- Model: Wan2.1 (open-source, Alibaba Tongyi)
- Evaluasi: VBench-2.0 benchmark suite
