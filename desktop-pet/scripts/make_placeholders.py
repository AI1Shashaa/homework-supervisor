#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 10 段占位视频，便于在无真实素材时开发调试。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


VIDEOS = [
    ("video.mp4", "IDLE", "70CEAA", "2.4"),
    ("video (1).mp4", "LOOK", "7EB8D4", "2.0"),
    ("video (2).mp4", "WALK", "F4A261", "2.2"),
    ("video (3).mp4", "RUN", "E76F51", "1.6"),
    ("video (4).mp4", "SIT", "90BE6D", "2.0"),
    ("video (5).mp4", "SLEEP", "9B8CDB", "2.8"),
    ("video (6).mp4", "EAT", "F9C74F", "2.0"),
    ("video (7).mp4", "HAPPY", "FF8FAB", "1.8"),
    ("video (8).mp4", "PET", "43AA8B", "2.0"),
    ("video (9).mp4", "SPECIAL", "577590", "1.8"),
]


def main() -> int:
    out_dir = Path(__file__).resolve().parents[1] / "assets" / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, label, color, duration in VIDEOS:
        dest = out_dir / name
        # 绿幕底 + 彩色圆形角色占位，方便验证自动抠像
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            (
                f"color=c=0x00FF00:s=360x360:d={duration},"
                f"drawbox=x=90:y=70:w=180:h=180:color=0x{color}:t=fill,"
                f"drawtext=text='{label}':fontsize=36:fontcolor=white:"
                f"x=(w-text_w)/2:y=(h-text_h)/2"
            ),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(dest),
        ]
        print("生成:", name)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr[-800:], file=sys.stderr)
            return result.returncode
    print(f"完成，共 {len(VIDEOS)} 个文件 → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
