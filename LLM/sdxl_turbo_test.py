import time, gc
import openvino_genai as ov_genai
from PIL import Image

PROMPT = "professional portrait photo of a young woman with brown hair, soft natural window light, 50mm, depth of field, photorealistic, sharp focus, 8k"
NEG = "cartoon, anime, painting, blurry, low quality, deformed, ugly, bad anatomy, watermark, text"
SEED = 7

print("Loading SDXL-Turbo INT8 on GPU...")
t = time.time()
pipe = ov_genai.Text2ImagePipeline("/opt/sd-openvino/models/sdxl-turbo-int8", "GPU")
print(f"load: {time.time()-t:.1f}s")

for steps in (1, 4):
    print(f"\n=== {steps} step(s), 512x512, cfg=1.0 ===")
    t = time.time()
    out = pipe.generate(PROMPT, num_inference_steps=steps,
                        width=512, height=512, guidance_scale=1.0, rng_seed=SEED)
    dt = time.time() - t
    print(f"gen: {dt:.1f}s")
    Image.fromarray(out.data[0]).save(f"/tmp/sdxl_turbo_{steps}step.png")
    print(f"saved /tmp/sdxl_turbo_{steps}step.png")
