import time, numpy as np
import openvino as ov
import openvino_genai as ov_genai
from PIL import Image

INIT = "/tmp/sdxl_turbo_4step.png"   # the earlier portrait
print(f"Loading SDXL-Turbo INT8 (img2img) on GPU ...")
t = time.time()
pipe = ov_genai.Image2ImagePipeline("/opt/sd-openvino/models/sdxl-turbo-int8", "GPU")
print(f"load: {time.time()-t:.1f}s")

src = Image.open(INIT).convert("RGB").resize((512, 512), Image.LANCZOS)
init = np.array(src)[np.newaxis, ...]  # NHWC uint8
init_t = ov.Tensor(init)

for strength in (0.4, 0.6, 0.8):
    print(f"\n=== strength={strength}, 4 steps ===")
    t = time.time()
    out = pipe.generate(
        "watercolor painting, soft brushstrokes, vibrant pastel colors, paper texture",
        image=init_t,
        num_inference_steps=4,
        strength=strength,
        guidance_scale=1.0,
        rng_seed=42,
    )
    dt = time.time() - t
    print(f"gen: {dt:.1f}s")
    Image.fromarray(out.data[0]).save(f"/tmp/i2i_s{int(strength*10)}.png")
    print(f"saved /tmp/i2i_s{int(strength*10)}.png")
