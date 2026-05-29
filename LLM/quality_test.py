"""Compare INT8 8-step vs FP16 25-step on the same prompt+seed."""
import time, sys, os
import openvino_genai as ov_genai
from PIL import Image

PROMPT = "professional portrait photo of a young woman with brown hair, soft natural window light, 50mm, depth of field, photorealistic, sharp focus, 8k"
NEG = "cartoon, anime, painting, illustration, drawing, sketch, blurry, low quality, deformed, ugly, bad anatomy, watermark, text, signature"
SEED = 7

def run(model_dir, steps, size, tag, cfg=7.5):
    print(f"\n=== {tag} :: {model_dir.split('/')[-1]} :: {steps}s/{size}px ===")
    t = time.time()
    pipe = ov_genai.Text2ImagePipeline(model_dir, "GPU")
    print(f"  load: {time.time()-t:.1f}s")
    t = time.time()
    out = pipe.generate(PROMPT, negative_prompt=NEG, num_inference_steps=steps,
                        width=size, height=size, guidance_scale=cfg, rng_seed=SEED)
    dt = time.time() - t
    print(f"  gen:  {dt:.1f}s  ({dt/steps:.2f}s/step)")
    img = Image.fromarray(out.data[0])
    fn = f"/tmp/{tag}.png"
    img.save(fn)
    print(f"  saved {fn}  {img.size}")
    return fn

run("/opt/sd-openvino/models/sd15-fp16", 25, 512, "fp16_25step")
