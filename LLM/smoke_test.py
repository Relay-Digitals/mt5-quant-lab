import time, sys
import openvino_genai as ov_genai
from PIL import Image

print("Loading SD 1.5 INT8 on GPU...")
t = time.time()
pipe = ov_genai.Text2ImagePipeline("/opt/sd-openvino/models/sd15-int8", "GPU")
print(f"Load: {time.time()-t:.1f}s")

print("Generating 384x384 / 8 steps...")
t = time.time()
out = pipe.generate(
    "a corgi astronaut on the moon, photorealistic",
    negative_prompt="blurry, low quality",
    num_inference_steps=8,
    width=384,
    height=384,
    guidance_scale=7.0,
    rng_seed=42,
)
dt = time.time() - t
print(f"Generate: {dt:.1f}s  ({dt/8:.2f}s/step)")

img = Image.fromarray(out.data[0])
img.save("/tmp/smoke.png")
print(f"Saved /tmp/smoke.png  size={img.size}  mode={img.mode}")
