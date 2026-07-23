#!/usr/bin/env python3
"""生成简易应用图标（基于猫咪精灵）。"""

from pathlib import Path

from PIL import Image

root = Path(__file__).resolve().parents[1]
cat = Image.open(root / "assets" / "cat.png").convert("RGBA")

# 正方形透明画布，居中贴合
size = 256
canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
# 裁掉过多透明边
bbox = cat.getbbox()
if bbox:
    cat = cat.crop(bbox)
cat.thumbnail((size - 16, size - 16), Image.Resampling.LANCZOS)
ox = (size - cat.width) // 2
oy = (size - cat.height) // 2
canvas.paste(cat, (ox, oy), cat)
out = root / "assets" / "icon.png"
canvas.save(out)
print(f"wrote {out}")
