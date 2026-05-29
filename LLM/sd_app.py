"""Stable Diffusion via OpenVINO GenAI — multi-model Gradio frontend.

Tabs:
  - Text → Image   (Text2ImagePipeline)
  - Image → Image  (Image2ImagePipeline, with reference image + strength)
"""
import os
import gc
import time
import random
import numpy as np
import gradio as gr
import openvino as ov
import openvino_genai as ov_genai
from PIL import Image
from openvino import Core

DEVICE = os.environ.get("OV_DEVICE", "GPU")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "7860"))
MODELS_ROOT = os.environ.get("MODELS_ROOT", "/opt/sd-openvino/models")


def _entry(path, label, steps, max_steps, cfg, size, tip):
    return dict(path=path, label=label, steps=steps, max_steps=max_steps,
                cfg=cfg, size=size, tip=tip)


TXT2IMG = {
    "sdxl-turbo": _entry(
        f"{MODELS_ROOT}/sdxl-turbo-int8",
        "SDXL-Turbo INT8  •  fastest realistic",
        4, 8, 1.0, 512,
        "1–4 steps. CFG ~1.0 (no negative prompt).",
    ),
    "sd15-fp16": _entry(
        f"{MODELS_ROOT}/sd15-fp16",
        "SD 1.5 FP16  •  balanced",
        25, 40, 7.5, 512,
        "Supports negative prompt.",
    ),
    "sd15-int8": _entry(
        f"{MODELS_ROOT}/sd15-int8",
        "SD 1.5 INT8  •  fastest, lowest quality",
        20, 30, 7.5, 512,
        "Smallest footprint.",
    ),
}

IMG2IMG = {
    "sdxl-turbo-i2i": _entry(
        f"{MODELS_ROOT}/sdxl-turbo-int8",
        "SDXL-Turbo INT8 (img2img)",
        4, 8, 1.0, 512,
        "Steps × strength ≥ 1. Strength 0.4–0.7 = preserve composition.",
    ),
    "sd15-fp16-i2i": _entry(
        f"{MODELS_ROOT}/sd15-fp16",
        "SD 1.5 FP16 (img2img)",
        25, 40, 7.5, 512,
        "Classic img2img. Strength 0.5–0.8 typical.",
    ),
}


def _filter(reg):
    return {k: v for k, v in reg.items() if os.path.isdir(v["path"])}


txt2img_models = _filter(TXT2IMG)
img2img_models = _filter(IMG2IMG)
if not txt2img_models and not img2img_models:
    raise SystemExit(f"No models found under {MODELS_ROOT}")
print(f"OpenVINO devices: {Core().available_devices}")
print(f"txt2img models: {list(txt2img_models)}")
print(f"img2img models: {list(img2img_models)}")

# Global pipe state — only one loaded at a time (memory constraint).
state = {"mode": None, "key": None, "pipe": None}


def load_pipe(mode: str, key: str) -> str:
    if state["mode"] == mode and state["key"] == key and state["pipe"] is not None:
        return f"already loaded: {mode}/{key}"
    state["pipe"] = None
    gc.collect()
    reg = txt2img_models if mode == "txt2img" else img2img_models
    cfg = reg[key]
    cls = ov_genai.Text2ImagePipeline if mode == "txt2img" else ov_genai.Image2ImagePipeline
    t0 = time.time()
    print(f"Loading {mode}/{key} ({cls.__name__}) on {DEVICE}...")
    state["pipe"] = cls(cfg["path"], DEVICE)
    state["mode"], state["key"] = mode, key
    msg = f"loaded {mode}/{key} in {time.time()-t0:.1f}s"
    print(msg)
    return msg


def _seed(s):
    return random.randint(0, 2**31 - 1) if int(s) < 0 else int(s)


def _gen_kwargs(steps, w, h, cfg, seed, negative):
    kw = dict(num_inference_steps=int(steps), width=int(w), height=int(h),
              guidance_scale=float(cfg), rng_seed=seed)
    if float(cfg) > 1.0 and (negative or "").strip():
        kw["negative_prompt"] = negative.strip()
    return kw


# Preload first txt2img model (UI default tab)
default_txt = next(iter(txt2img_models)) if txt2img_models else None
default_img = next(iter(img2img_models)) if img2img_models else None
if default_txt:
    load_pipe("txt2img", default_txt)


# ---------- Text → Image ----------
def gen_txt2img(model_key, prompt, negative, steps, w, h, cfg, seed, progress=gr.Progress()):
    if not prompt or not prompt.strip():
        raise gr.Error("Prompt kosong")
    load_pipe("txt2img", model_key)
    seed = _seed(seed)
    progress(0, desc=f"txt2img on {DEVICE}…")
    t = time.time()
    result = state["pipe"].generate(prompt.strip(), **_gen_kwargs(steps, w, h, cfg, seed, negative))
    dt = time.time() - t
    img = Image.fromarray(result.data[0])
    return img, f"{model_key} • seed={seed} • {int(w)}x{int(h)} • {int(steps)}s • {dt:.1f}s"


def on_txt_model_change(key):
    c = txt2img_models[key]
    info = load_pipe("txt2img", key)
    return (gr.update(value=c["steps"], maximum=c["max_steps"]),
            gr.update(value=c["cfg"]),
            gr.update(value=c["size"]),
            gr.update(value=c["size"]),
            f"{info}  •  {c['tip']}")


# ---------- Image → Image ----------
def _to_tensor(pil_img: Image.Image, w: int, h: int) -> ov.Tensor:
    img = pil_img.convert("RGB").resize((int(w), int(h)), Image.LANCZOS)
    arr = np.array(img)  # (H, W, 3) uint8
    arr = arr[np.newaxis, ...]  # (1, H, W, 3)
    return ov.Tensor(arr)


def gen_img2img(model_key, init_image, prompt, negative, steps, w, h, cfg, strength, seed,
                progress=gr.Progress()):
    if not prompt or not prompt.strip():
        raise gr.Error("Prompt kosong")
    if init_image is None:
        raise gr.Error("Reference image kosong")
    load_pipe("img2img", model_key)
    seed = _seed(seed)
    init_tensor = _to_tensor(init_image, w, h)
    progress(0, desc=f"img2img on {DEVICE} (strength={strength})…")
    t = time.time()
    kw = _gen_kwargs(steps, w, h, cfg, seed, negative)
    kw["strength"] = float(strength)
    kw["image"] = init_tensor
    result = state["pipe"].generate(prompt.strip(), **kw)
    dt = time.time() - t
    img = Image.fromarray(result.data[0])
    return img, f"{model_key} • seed={seed} • {int(w)}x{int(h)} • {int(steps)}s • strength={strength} • {dt:.1f}s"


def on_img_model_change(key):
    c = img2img_models[key]
    return (gr.update(value=c["steps"], maximum=c["max_steps"]),
            gr.update(value=c["cfg"]),
            gr.update(value=c["size"]),
            gr.update(value=c["size"]),
            f"{c['tip']}")


# ---------- UI ----------
with gr.Blocks(title="SD OpenVINO") as demo:
    gr.Markdown(f"# Stable Diffusion (OpenVINO `{DEVICE}` on Intel iGPU)")

    with gr.Tabs():
        # ===== TAB 1: Text → Image =====
        with gr.Tab("Text → Image"):
            if not txt2img_models:
                gr.Markdown("_No txt2img models installed._")
            else:
                d = txt2img_models[default_txt]
                with gr.Row():
                    txt_model = gr.Dropdown(
                        [(v["label"], k) for k, v in txt2img_models.items()],
                        value=default_txt, label="Model")
                    txt_info = gr.Textbox(label="Status",
                                          value=f"{default_txt} loaded  •  {d['tip']}",
                                          interactive=False)
                with gr.Row():
                    with gr.Column():
                        t_prompt = gr.Textbox(label="Prompt", lines=3,
                            value="professional portrait photo of a young woman, soft natural light, 50mm, sharp focus, 8k")
                        t_neg = gr.Textbox(label="Negative prompt", lines=2,
                            value="cartoon, anime, painting, blurry, low quality, deformed, ugly, watermark, text")
                        t_steps = gr.Slider(1, d["max_steps"], value=d["steps"], step=1, label="Steps")
                        with gr.Row():
                            t_w = gr.Slider(256, 1024, value=d["size"], step=64, label="Width")
                            t_h = gr.Slider(256, 1024, value=d["size"], step=64, label="Height")
                        t_cfg = gr.Slider(0.0, 15.0, value=d["cfg"], step=0.5, label="Guidance (CFG)")
                        t_seed = gr.Number(value=-1, label="Seed (-1 = random)", precision=0)
                        t_btn = gr.Button("Generate", variant="primary")
                    with gr.Column():
                        t_out = gr.Image(label="Result", type="pil", height=520)
                        t_meta = gr.Textbox(label="Info", interactive=False)

                txt_model.change(on_txt_model_change, [txt_model],
                                 [t_steps, t_cfg, t_w, t_h, txt_info])
                t_btn.click(gen_txt2img,
                            [txt_model, t_prompt, t_neg, t_steps, t_w, t_h, t_cfg, t_seed],
                            [t_out, t_meta])

        # ===== TAB 2: Image → Image (reference) =====
        with gr.Tab("Image → Image"):
            if not img2img_models:
                gr.Markdown("_No img2img models installed._")
            else:
                d = img2img_models[default_img]
                with gr.Row():
                    img_model = gr.Dropdown(
                        [(v["label"], k) for k, v in img2img_models.items()],
                        value=default_img, label="Model")
                    img_info = gr.Textbox(label="Tip", value=d["tip"], interactive=False)
                with gr.Row():
                    with gr.Column():
                        i_init = gr.Image(label="Reference image", type="pil", height=260)
                        i_prompt = gr.Textbox(label="Prompt", lines=2,
                            value="transform into a watercolor painting, vibrant colors")
                        i_neg = gr.Textbox(label="Negative prompt", lines=2,
                            value="blurry, low quality, deformed, watermark, text")
                        i_strength = gr.Slider(0.1, 1.0, value=0.6, step=0.05, label="Strength (0.1 = preserve, 1.0 = ignore init)")
                        i_steps = gr.Slider(1, d["max_steps"], value=d["steps"], step=1, label="Steps")
                        with gr.Row():
                            i_w = gr.Slider(256, 1024, value=d["size"], step=64, label="Width")
                            i_h = gr.Slider(256, 1024, value=d["size"], step=64, label="Height")
                        i_cfg = gr.Slider(0.0, 15.0, value=d["cfg"], step=0.5, label="Guidance (CFG)")
                        i_seed = gr.Number(value=-1, label="Seed (-1 = random)", precision=0)
                        i_btn = gr.Button("Generate", variant="primary")
                    with gr.Column():
                        i_out = gr.Image(label="Result", type="pil", height=520)
                        i_meta = gr.Textbox(label="Info", interactive=False)

                img_model.change(on_img_model_change, [img_model],
                                 [i_steps, i_cfg, i_w, i_h, img_info])
                i_btn.click(gen_img2img,
                            [img_model, i_init, i_prompt, i_neg, i_steps, i_w, i_h, i_cfg, i_strength, i_seed],
                            [i_out, i_meta])


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1).launch(server_name=HOST, server_port=PORT)
