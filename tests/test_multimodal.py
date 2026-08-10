from pathlib import Path

from PIL import Image

from last_price.multimodal import fused_features


def test_multimodal_fusion(tmp_path: Path):
    p = tmp_path / "item.png"
    Image.new("RGB", (32, 32), (120, 80, 40)).save(p)
    feats = fused_features(p, "brown leather shoe", 49.0, 12)
    assert "img_brightness" in feats
    assert feats["kw_fashion"] > 0
    assert feats["listed_price"] == 49.0
