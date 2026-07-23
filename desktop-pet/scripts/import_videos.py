#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本机 Downloads 里的 10 段视频导入到 desktop-pet/assets/videos/。"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


DEFAULT_NAMES = [
    "video.mp4",
    "video (1).mp4",
    "video (2).mp4",
    "video (3).mp4",
    "video (4).mp4",
    "video (5).mp4",
    "video (6).mp4",
    "video (7).mp4",
    "video (8).mp4",
    "video (9).mp4",
]


def default_downloads() -> Path:
    home = Path.home()
    candidates = [
        home / "Downloads",
        Path(os.environ.get("USERPROFILE", "")) / "Downloads",
        Path(r"C:\Users\1\Downloads"),
    ]
    for path in candidates:
        if path and path.is_dir():
            return path
    return home / "Downloads"


def main() -> int:
    parser = argparse.ArgumentParser(description="导入桌面萌宠视频素材")
    parser.add_argument(
        "--from",
        dest="source_dir",
        default=str(default_downloads()),
        help="素材所在目录（默认自动探测 Downloads）",
    )
    parser.add_argument(
        "--to",
        dest="dest_dir",
        default=str(Path(__file__).resolve().parents[1] / "assets" / "videos"),
        help="导入目标目录",
    )
    args = parser.parse_args()

    src_dir = Path(args.source_dir)
    dest_dir = Path(args.dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not src_dir.is_dir():
        print(f"找不到素材目录: {src_dir}")
        return 1

    ok = 0
    missing: list[str] = []
    for name in DEFAULT_NAMES:
        src = src_dir / name
        if not src.is_file():
            missing.append(name)
            continue
        dest = dest_dir / name
        shutil.copy2(src, dest)
        print(f"已导入: {name}  ({src.stat().st_size // 1024} KB)")
        ok += 1

    print("-" * 40)
    print(f"成功 {ok}/{len(DEFAULT_NAMES)}，目标: {dest_dir}")
    if missing:
        print("未找到:")
        for name in missing:
            print(f"  - {name}")
        return 2
    print("全部素材已就绪，可以运行 python main.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
