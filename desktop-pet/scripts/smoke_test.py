#!/usr/bin/env python3
"""离屏冒烟：加载配置、播放一帧、验证抠像。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink
from PySide6.QtWidgets import QApplication

import numpy as np


def test_chroma() -> None:
    # 绿底 + 红方块
    arr = np.zeros((64, 64, 4), dtype=np.uint8)
    arr[:, :] = (0, 255, 0, 255)  # BGRA green
    arr[16:48, 16:48] = (0, 0, 255, 255)  # red
    img = QImage(arr.data, 64, 64, 64 * 4, QImage.Format.Format_ARGB32).copy()

    # 复用 main 中的抠像逻辑
    from main import DesktopPet

    class _Tmp(DesktopPet):
        def __init__(self):  # noqa: D107
            pass

    pet = _Tmp()
    pet._chroma_mode = "green"
    pet._chroma_color = (0, 255, 0)
    pet._chroma_threshold = 40
    out = DesktopPet._apply_chroma(pet, img)
    ptr = out.bits()
    out_arr = np.frombuffer(ptr, dtype=np.uint8).reshape(64, 64, 4)
    # 角落应接近透明，中心红块应保留 alpha
    assert out_arr[2, 2, 3] < 40, out_arr[2, 2, 3]
    assert out_arr[32, 32, 3] > 200, out_arr[32, 32, 3]
    print("chroma ok")


def test_play() -> None:
    app = QApplication.instance() or QApplication([])
    cfg = json.loads((ROOT / "assets" / "videos.json").read_text(encoding="utf-8"))
    player = QMediaPlayer()
    sink = QVideoSink()
    audio = QAudioOutput()
    audio.setVolume(0)
    player.setAudioOutput(audio)
    player.setVideoSink(sink)
    frames = {"n": 0}

    def on_frame(f):
        if f.isValid() and not f.toImage().isNull():
            frames["n"] += 1

    sink.videoFrameChanged.connect(on_frame)
    path = ROOT / "assets" / "videos" / cfg["states"]["idle"]["file"]
    assert path.is_file(), path
    player.setSource(QUrl.fromLocalFile(str(path.resolve())))
    player.play()

    def done():
        print("frames", frames["n"])
        assert frames["n"] > 0, "未收到视频帧"
        app.quit()

    QTimer.singleShot(2500, done)
    code = app.exec()
    assert code == 0
    print("play ok")


def test_construct_pet() -> None:
    app = QApplication.instance() or QApplication([])
    from main import DesktopPet, discover_video_dir

    video_dir = discover_video_dir()
    assert video_dir.is_dir(), video_dir
    print("discover ok", video_dir)

    pet = DesktopPet()
    assert pet._current_state in pet._states
    print("pet construct ok", pet._current_state, "from", pet._video_source)
    pet.close()


def main() -> int:
    test_chroma()
    test_play()
    test_construct_pet()
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
