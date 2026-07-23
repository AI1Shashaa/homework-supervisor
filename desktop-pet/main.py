#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows 视频桌面萌宠：透明置顶、可拖动；根据素材视频切换动作。"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoFrame, QVideoSink
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QWidget


def resource_path(*parts: str) -> Path:
    """开发模式与 PyInstaller 打包后的资源路径。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent
    return base.joinpath(*parts)


class DesktopPet(QWidget):
    MIN_SCALE = 0.35
    MAX_SCALE = 2.4
    BASE_PET_WIDTH = 240

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("桌面萌宠")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)

        self._always_on_top = True
        self._scale = 1.0
        self._dragging = False
        self._drag_moved = False
        self._press_global = QPoint()
        self._press_pos = QPoint()
        self._click_armed = False

        self._bubble_text = ""
        self._bubble_visible = False
        self._bubble_alpha = 0.0
        self._click_index = 0

        self._frame = QImage()
        self._frame_size = QSize(320, 320)
        self._current_state = ""
        self._state_loop = True
        self._pending_return_idle = False

        self._load_config()
        self._setup_player()

        self._bubble_timer = QTimer(self)
        self._bubble_timer.setSingleShot(True)
        self._bubble_timer.timeout.connect(self._hide_bubble)

        self._idle_variant_timer = QTimer(self)
        self._idle_variant_timer.setSingleShot(True)
        self._idle_variant_timer.timeout.connect(self._maybe_switch_idle_variant)

        self._relayout()
        self._place_initial()
        self.play_state(self._config.get("default_state", "idle"), show_bubble=False)

    # ----- 配置 / 资源 -----
    def _load_config(self) -> None:
        cfg_path = resource_path("assets", "videos.json")
        if not cfg_path.is_file():
            raise FileNotFoundError(f"缺少配置文件: {cfg_path}")
        self._config = json.loads(cfg_path.read_text(encoding="utf-8"))
        self._states: dict = self._config.get("states", {})
        self._video_dir = resource_path("assets", "videos")
        missing = []
        for key, meta in self._states.items():
            path = self._video_dir / meta["file"]
            if not path.is_file():
                missing.append(f"{key}: {meta['file']}")
        if missing:
            tip = (
                "未找到视频素材，请先导入：\n"
                "  双击 scripts\\import_videos.bat\n"
                "或:\n"
                "  python scripts\\import_videos.py --from \"C:\\Users\\1\\Downloads\"\n\n"
                "缺少:\n- " + "\n- ".join(missing)
            )
            raise FileNotFoundError(tip)

        self._chroma_mode = str(self._config.get("chroma_key", "auto")).lower()
        self._chroma_threshold = int(self._config.get("chroma_threshold", 42))
        self._chroma_color: tuple[int, int, int] | None = None
        if self._chroma_mode == "green":
            self._chroma_color = (0, 255, 0)
        elif self._chroma_mode == "white":
            self._chroma_color = (255, 255, 255)
        elif self._chroma_mode == "black":
            self._chroma_color = (0, 0, 0)
        elif self._chroma_mode == "none":
            self._chroma_color = None

    def _setup_player(self) -> None:
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._audio.setVolume(0.0)  # 默认静音，避免素材自带音轨打扰
        self._player.setAudioOutput(self._audio)
        self._sink = QVideoSink(self)
        self._player.setVideoSink(self._sink)
        self._sink.videoFrameChanged.connect(self._on_video_frame)
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(self._on_player_error)

    def _video_path(self, state: str) -> Path:
        meta = self._states[state]
        return self._video_dir / meta["file"]

    # ----- 播放控制 -----
    def play_state(self, state: str, *, show_bubble: bool = True) -> None:
        if state not in self._states:
            return
        meta = self._states[state]
        path = self._video_path(state)
        self._current_state = state
        self._state_loop = bool(meta.get("loop", False))
        self._pending_return_idle = not self._state_loop
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self._player.setLoops(
            QMediaPlayer.Loops.Infinite if self._state_loop else QMediaPlayer.Loops.Once
        )
        self._player.play()

        if show_bubble:
            lines = self._config.get("dialogues", {}).get(state) or []
            if lines:
                self._show_bubble(random.choice(lines))

        self._schedule_idle_variant()

    def _schedule_idle_variant(self) -> None:
        self._idle_variant_timer.stop()
        variants = self._config.get("idle_variants") or ["idle"]
        if self._current_state not in variants:
            return
        lo, hi = self._config.get("idle_variant_seconds", [8, 18])
        delay = int(random.uniform(float(lo), float(hi)) * 1000)
        self._idle_variant_timer.start(max(2000, delay))

    def _maybe_switch_idle_variant(self) -> None:
        variants = [v for v in (self._config.get("idle_variants") or ["idle"]) if v in self._states]
        if len(variants) < 2:
            return
        if self._current_state not in variants:
            return
        choices = [v for v in variants if v != self._current_state] or variants
        self.play_state(random.choice(choices), show_bubble=False)

    def _on_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self._pending_return_idle:
            self._pending_return_idle = False
            default = self._config.get("default_state", "idle")
            self.play_state(default, show_bubble=False)

    def _on_player_error(self, *_args) -> None:
        err = self._player.errorString() or "未知播放错误"
        print(f"[desktop-pet] 播放失败: {err}", file=sys.stderr)

    # ----- 视频帧 / 抠像 -----
    def _on_video_frame(self, frame: QVideoFrame) -> None:
        if not frame.isValid():
            return
        image = frame.toImage()
        if image.isNull():
            return
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
        if self._chroma_mode != "none":
            image = self._apply_chroma(image)
        self._frame = image
        if image.width() > 0 and image.height() > 0:
            new_size = QSize(image.width(), image.height())
            if new_size != self._frame_size:
                self._frame_size = new_size
                self._relayout()
        self.update()

    def _sample_corner_color(self, arr: np.ndarray) -> tuple[int, int, int]:
        h, w, _ = arr.shape
        samples = [
            arr[2, 2],
            arr[2, w - 3],
            arr[h - 3, 2],
            arr[h - 3, w - 3],
            arr[2, w // 2],
            arr[h - 3, w // 2],
        ]
        mean = np.mean(samples, axis=0)
        return int(mean[2]), int(mean[1]), int(mean[0])  # R,G,B from BGRA

    def _qimage_to_bgra(self, image: QImage) -> np.ndarray:
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
        h, w = image.height(), image.width()
        bpl = image.bytesPerLine()
        ptr = image.constBits()
        buf = np.frombuffer(ptr, dtype=np.uint8, count=bpl * h).reshape(h, bpl)
        return np.array(buf[:, : w * 4].reshape(h, w, 4), copy=True)

    def _apply_chroma(self, image: QImage) -> QImage:
        arr = self._qimage_to_bgra(image)

        if self._chroma_mode == "auto" or self._chroma_color is None:
            key = self._sample_corner_color(arr)
        else:
            key = self._chroma_color

        # arr is BGRA；用 float 计算色差，避免整型溢出
        b = arr[:, :, 0].astype(np.float32)
        g = arr[:, :, 1].astype(np.float32)
        r = arr[:, :, 2].astype(np.float32)
        kr, kg, kb = (float(key[0]), float(key[1]), float(key[2]))
        dist = np.sqrt((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2)
        thr = float(self._chroma_threshold)
        soft = max(8.0, thr * 0.55)
        alpha = np.clip((dist - thr) / soft, 0.0, 1.0)
        arr[:, :, 3] = (alpha * 255.0).astype(np.uint8)

        out = QImage(
            arr.data,
            arr.shape[1],
            arr.shape[0],
            int(arr.strides[0]),
            QImage.Format.Format_ARGB32,
        )
        return out.copy()

    # ----- 尺寸 / 布局 -----
    def _pet_draw_size(self) -> QSize:
        w = max(64, int(self.BASE_PET_WIDTH * self._scale))
        src_w = max(1, self._frame_size.width())
        src_h = max(1, self._frame_size.height())
        h = max(64, int(w * src_h / src_w))
        return QSize(w, h)

    def _bubble_reserved_height(self) -> int:
        return max(56, int(72 * self._scale))

    def _margin(self) -> int:
        return max(16, int(24 * self._scale))

    def _relayout(self) -> None:
        pet = self._pet_draw_size()
        m = self._margin()
        bubble_h = self._bubble_reserved_height()
        bottom_m = max(8, int(12 * self._scale))
        w = pet.width() + m * 2
        h = pet.height() + bubble_h + bottom_m
        old_geo = self.geometry()
        old_bottom = old_geo.bottom() if old_geo.height() else None
        old_cx = old_geo.center().x() if old_geo.width() else None
        self.setFixedSize(w, h)
        if old_bottom is not None and old_cx is not None:
            self.move(old_cx - w // 2, old_bottom - h)

    def _place_initial(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.move(100, 100)
            return
        geo = screen.availableGeometry()
        x = geo.right() - self.width() - 40
        y = geo.bottom() - self.height() - 24
        self.move(x, y)

    def _pet_rect(self) -> QRect:
        pet = self._pet_draw_size()
        bottom_m = max(8, int(12 * self._scale))
        x = (self.width() - pet.width()) // 2
        y = self.height() - bottom_m - pet.height()
        return QRect(x, y, pet.width(), pet.height())

    # ----- 绘制 -----
    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        pet_rect = self._pet_rect()
        if not self._frame.isNull():
            pix = QPixmap.fromImage(self._frame).scaled(
                pet_rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = pet_rect.x() + (pet_rect.width() - pix.width()) // 2
            y = pet_rect.y() + (pet_rect.height() - pix.height()) // 2
            painter.drawPixmap(x, y, pix)
        else:
            painter.setPen(QPen(QColor(255, 255, 255, 180), 2, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(40, 40, 40, 80))
            painter.drawRoundedRect(pet_rect.adjusted(8, 8, -8, -8), 16, 16)
            painter.setPen(QColor(255, 255, 255, 220))
            painter.drawText(pet_rect, Qt.AlignmentFlag.AlignCenter, "加载中…")

        if self._bubble_visible and self._bubble_text:
            self._paint_bubble(painter, pet_rect)
        painter.end()

    def _paint_bubble(self, painter: QPainter, pet_rect: QRect) -> None:
        text = self._bubble_text
        font = QFont("Microsoft YaHei UI", max(10, int(12 * self._scale)))
        if not font.exactMatch():
            font = QFont("PingFang SC", max(10, int(12 * self._scale)))
        if not font.exactMatch():
            font = QFont("Sans Serif", max(10, int(12 * self._scale)))
        font.setBold(True)
        painter.setFont(font)

        metrics = painter.fontMetrics()
        pad_x, pad_y = 14, 10
        tw = metrics.horizontalAdvance(text)
        th = metrics.height()
        bw = tw + pad_x * 2
        bh = th + pad_y * 2

        bx = pet_rect.center().x() - bw // 2
        by = pet_rect.top() - bh - max(10, int(14 * self._scale))
        bx = max(8, min(bx, self.width() - bw - 8))
        by = max(6, by)

        path = QPainterPath()
        path.addRoundedRect(bx, by, bw, bh, 12, 12)
        tip_x = pet_rect.center().x()
        tip_x = max(bx + 16, min(tip_x, bx + bw - 16))
        tri = QPainterPath()
        tri.moveTo(tip_x - 7, by + bh - 1)
        tri.lineTo(tip_x + 7, by + bh - 1)
        tri.lineTo(tip_x, by + bh + 9)
        tri.closeSubpath()
        path = path.united(tri)

        alpha = int(255 * self._bubble_alpha)
        painter.setPen(QPen(QColor(40, 40, 40, alpha), 1.5))
        painter.setBrush(QColor(255, 255, 255, alpha))
        painter.drawPath(path)
        painter.setPen(QColor(30, 30, 30, alpha))
        painter.drawText(QRect(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, text)

    def _show_bubble(self, text: str) -> None:
        self._bubble_text = text
        self._bubble_visible = True
        self._bubble_alpha = 1.0
        self._bubble_timer.start(1800)
        self.update()

    def _hide_bubble(self) -> None:
        self._bubble_visible = False
        self._bubble_text = ""
        self.update()

    # ----- 互动 -----
    def _trigger_click_action(self) -> None:
        cycle = [s for s in (self._config.get("click_cycle") or []) if s in self._states]
        if not cycle:
            cycle = [s for s, m in self._states.items() if not m.get("loop", False)]
        if not cycle:
            return
        state = cycle[self._click_index % len(cycle)]
        self._click_index += 1
        self.play_state(state, show_bubble=True)

    # ----- 鼠标 -----
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_moved = False
            self._click_armed = True
            self._press_global = event.globalPosition().toPoint()
            self._press_pos = self.pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_global
            if abs(delta.x()) > 3 or abs(delta.y()) > 3:
                self._drag_moved = True
                self._click_armed = False
            self.move(self._press_pos + delta)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            was_click = self._click_armed and not self._drag_moved
            self._dragging = False
            self._click_armed = False
            if was_click and self._pet_hit_test(event.position().toPoint()):
                self._trigger_click_action()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _pet_hit_test(self, local_pos: QPoint) -> bool:
        return self._pet_rect().adjusted(-8, -8, 8, 8).contains(local_pos)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        delta = event.angleDelta().y()
        if delta == 0:
            return
        step = 0.08 if delta > 0 else -0.08
        self._set_scale(self._scale + step)
        event.accept()

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #ffffff; color: #222; border: 1px solid #ccc; }"
            "QMenu::item:selected { background: #e8e8e8; }"
        )

        action_menu = menu.addMenu("切换动作")
        for key, meta in self._states.items():
            label = meta.get("label", key)
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(key == self._current_state)
            act.triggered.connect(lambda checked=False, s=key: self.play_state(s))
            action_menu.addAction(act)

        size_menu = menu.addMenu("调整大小")
        group = QActionGroup(self)
        group.setExclusive(True)
        for label, value in (("小", 0.7), ("中", 1.0), ("大", 1.4), ("超大", 1.9)):
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(abs(self._scale - value) < 0.05)
            act.triggered.connect(lambda checked=False, v=value: self._set_scale(v))
            group.addAction(act)
            size_menu.addAction(act)

        chroma_menu = menu.addMenu("背景抠像")
        for mode, label in (
            ("auto", "自动（推荐）"),
            ("green", "绿幕"),
            ("white", "白底"),
            ("black", "黑底"),
            ("none", "关闭"),
        ):
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(self._chroma_mode == mode)
            act.triggered.connect(lambda checked=False, m=mode: self._set_chroma(m))
            chroma_menu.addAction(act)

        top_act = QAction("取消置顶" if self._always_on_top else "始终置顶", self)
        top_act.triggered.connect(self._toggle_always_on_top)
        menu.addAction(top_act)

        mute_act = QAction(
            "开启声音" if self._audio.volume() <= 0.01 else "静音",
            self,
        )
        mute_act.triggered.connect(self._toggle_mute)
        menu.addAction(mute_act)

        menu.addSeparator()
        quit_act = QAction("退出程序", self)
        quit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_act)

        menu.exec(event.globalPos())

    def _set_scale(self, value: float) -> None:
        self._scale = max(self.MIN_SCALE, min(self.MAX_SCALE, value))
        self._relayout()
        self.update()

    def _set_chroma(self, mode: str) -> None:
        self._chroma_mode = mode
        self._config["chroma_key"] = mode
        if mode == "green":
            self._chroma_color = (0, 255, 0)
        elif mode == "white":
            self._chroma_color = (255, 255, 255)
        elif mode == "black":
            self._chroma_color = (0, 0, 0)
        else:
            self._chroma_color = None
        self.update()

    def _toggle_mute(self) -> None:
        if self._audio.volume() <= 0.01:
            self._audio.setVolume(0.7)
        else:
            self._audio.setVolume(0.0)

    def _toggle_always_on_top(self) -> None:
        self._always_on_top = not self._always_on_top
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self._always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.hide()
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.show()


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    try:
        pet = DesktopPet()
    except FileNotFoundError as exc:
        QMessageBox.critical(None, "桌面萌宠", str(exc))
        return 1
    pet.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
