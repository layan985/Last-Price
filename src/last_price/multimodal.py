from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

KEYWORDS = {
    "electronics": ["phone", "laptop", "camera", "charger", "headphones"],
    "fashion": ["shoe", "shirt", "jacket", "dress", "bag"],
    "home": ["chair", "lamp", "table", "sofa", "kitchen"],
}


def image_features(path: str | Path) -> dict[str, float]:
    img = Image.open(path).convert("RGB").resize((64, 64))
    arr = np.asarray(img, dtype=float) / 255.0
    gray = np.asarray(img.convert("L"), dtype=float) / 255.0
    edges = np.asarray(img.convert("L").filter(ImageFilter.FIND_EDGES), dtype=float) / 255.0
    return {
        "img_r_mean": float(arr[:, :, 0].mean()),
        "img_g_mean": float(arr[:, :, 1].mean()),
        "img_b_mean": float(arr[:, :, 2].mean()),
        "img_brightness": float(gray.mean()),
        "img_contrast": float(gray.std()),
        "img_edge_density": float((edges > 0.15).mean()),
    }


def text_features(text: str) -> dict[str, float]:
    tokens = re.findall(r"[a-z]+", text.lower())
    total = max(len(tokens), 1)
    out = {"text_length": float(len(text)), "token_count": float(len(tokens))}
    for category, words in KEYWORDS.items():
        out[f"kw_{category}"] = float(sum(t in words for t in tokens) / total)
    return out


def fused_features(image_path: str | Path, text: str, price: float, inventory: int) -> dict[str, float]:
    out = {}
    out.update(image_features(image_path))
    out.update(text_features(text))
    out["listed_price"] = float(price)
    out["inventory_level"] = float(inventory)
    return out
