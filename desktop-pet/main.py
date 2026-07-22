#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows 桌面宠物：透明置顶、可拖动；待机摇尾巴/转头，点击互动。"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, QEasingCurve
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
    QTransform,
    QWheelEvent,
)
from PySide6.QtWidgets import QApplication, QMenu, QWidget


def resource_path(*parts: str) -> Path:
    """开发模式与 PyInstaller 打包后的资源路径。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent
    return base.joinpath(*parts)


DIALOGUES = [
    "喵？摸我干嘛～",
    "再点我就翻肚皮了！",
    "今日份罐头已到账？",
    "工作再忙，也要撸猫。",
    "我不是胖，是毛茸茸。",
    "嘘……正在思考宇宙。",
    "你的鼠标很暖和。",
    "跳一下，世界都轻了。",
    "别卷了，来陪我发呆。",
    "爪巴爪巴～你是我的人。",
    "检测到人类，启动卖萌。",
    "今天也是被rua的一天。",
    "尾巴摇起来，好运来！",
    "我在听哦，继续说～",
]


class DesktopPet(QWidget):
    MIN_SCALE = 0.35
    MAX_SCALE = 2.2
    BASE_PET_WIDTH = 220

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("桌面宠物")
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

        self._anim_kind = ""
        self._anim_t = 0.0
        self._anim_duration = 0.0
        self._offset = QPoint(0, 0)
        self._squash_x = 1.0
        self._squash_y = 1.0

        self._bubble_text = ""
        self._bubble_visible = False
        self._bubble_alpha = 0.0

        self._interaction_index = 0
        self._interactions = ("jump", "squash", "shake")

        # 待机动画：尾巴摇摆、头部轻晃
        self._idle_t0 = time.perf_counter()
        self._tail_angle = 0.0
        self._head_angle = 0.0
        self._head_bob_x = 0.0
        self._head_bob_y = 0.0
        self._idle_boost = 1.0  # 点击互动时短暂加速摇摆

        self._load_layers()

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._on_anim_tick)

        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(33)  # ~30fps 待机足够顺滑
        self._idle_timer.timeout.connect(self._on_idle_tick)
        self._idle_timer.start()

        self._bubble_timer = QTimer(self)
        self._bubble_timer.setSingleShot(True)
        self._bubble_timer.timeout.connect(self._hide_bubble)

        self._boost_timer = QTimer(self)
        self._boost_timer.setSingleShot(True)
        self._boost_timer.timeout.connect(self._reset_idle_boost)

        self._rebuild_pixmap()
        self._relayout()
        self._place_initial()

    def _load_layers(self) -> None:
        assets = resource_path("assets")
        meta_path = assets / "layers.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        def load(name: str) -> QImage:
            img = QImage(str(assets / name))
            if img.isNull():
                raise FileNotFoundError(f"找不到资源 assets/{name}")
            return img.convertToFormat(QImage.Format.Format_ARGB32)

        # 全图用于尺寸与兼容；分层用于待机动画
        self._source = load("cat.png")
        self._body_src = load("cat_body.png")
        self._head_src = load("cat_head.png")
        self._tail_src = load("cat_tail.png")

        self._src_w = meta["width"]
        self._src_h = meta["height"]
        self._tail_pivot_src = QPointF(meta["tail_pivot"]["x"], meta["tail_pivot"]["y"])
        self._head_pivot_src = QPointF(meta["head_pivot"]["x"], meta["head_pivot"]["y"])

    # ----- 尺寸 / 布局 -----
    def _pet_draw_size(self) -> QSize:
        w = max(48, int(self.BASE_PET_WIDTH * self._scale))
        ratio = self._source.height() / max(1, self._source.width())
        h = max(48, int(w * ratio))
        return QSize(w, h)

    def _bubble_reserved_height(self) -> int:
        return max(56, int(72 * self._scale))

    def _margin(self) -> int:
        return max(24, int(36 * self._scale))

    def _rebuild_pixmap(self) -> None:
        size = self._pet_draw_size()

        def scale_img(src: QImage) -> QPixmap:
            return QPixmap.fromImage(
                src.scaled(
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        self._pet_pixmap = scale_img(self._source)
        self._body_pix = scale_img(self._body_src)
        self._head_pix = scale_img(self._head_src)
        self._tail_pix = scale_img(self._tail_src)

        sx = size.width() / max(1, self._src_w)
        sy = size.height() / max(1, self._src_h)
        self._tail_pivot = QPointF(self._tail_pivot_src.x() * sx, self._tail_pivot_src.y() * sy)
        self._head_pivot = QPointF(self._head_pivot_src.x() * sx, self._head_pivot_src.y() * sy)

    def _relayout(self) -> None:
        pet = self._pet_draw_size()
        m = self._margin()
        bubble_h = self._bubble_reserved_height()
        # 上方留给气泡与跳跃；左右留给抖动与尾巴摆动
        jump_room = max(48, int(96 * self._scale))
        extra_x = max(36, int(56 * self._scale))
        bottom_m = max(8, int(10 * self._scale))
        w = pet.width() + m * 2 + extra_x * 2
        h = pet.height() + bubble_h + jump_room + bottom_m
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
        bottom_m = max(8, int(10 * self._scale))
        x = (self.width() - pet.width()) // 2 + self._offset.x()
        y = self.height() - bottom_m - pet.height() + self._offset.y()
        return QRect(x, y, pet.width(), pet.height())

    # ----- 绘制 -----
    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        pet_rect = self._pet_rect()
        cx = pet_rect.center().x()
        bottom = pet_rect.bottom()

        painter.save()
        painter.translate(cx, bottom)
        painter.scale(self._squash_x, self._squash_y)
        painter.translate(-pet_rect.width() / 2, -pet_rect.height())
        self._paint_pet_layers(painter, QRect(0, 0, pet_rect.width(), pet_rect.height()))
        painter.restore()

        if self._bubble_visible and self._bubble_text:
            self._paint_bubble(painter, pet_rect)

        painter.end()

    def _paint_pet_layers(self, painter: QPainter, local_rect: QRect) -> None:
        """在本地坐标系绘制：完整底图 → 摇尾巴 → 转头（叠加以避免接缝）。"""
        origin = QPointF(local_rect.topLeft())

        # 1) 完整角色打底，避免分层抠图产生白边/空洞
        painter.drawPixmap(local_rect.topLeft(), self._pet_pixmap)

        # 2) 尾巴：绕附着点旋转叠在上方
        painter.save()
        pivot = origin + self._tail_pivot
        painter.translate(pivot)
        painter.rotate(self._tail_angle)
        painter.translate(-pivot)
        painter.drawPixmap(local_rect.topLeft(), self._tail_pix)
        painter.restore()

        # 3) 头部：轻微旋转 + 位移叠在上方
        painter.save()
        pivot = origin + self._head_pivot
        painter.translate(pivot)
        painter.translate(self._head_bob_x, self._head_bob_y)
        painter.rotate(self._head_angle)
        painter.translate(-pivot)
        painter.drawPixmap(local_rect.topLeft(), self._head_pix)
        painter.restore()

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

    # ----- 待机动画 -----
    def _on_idle_tick(self) -> None:
        t = time.perf_counter() - self._idle_t0
        boost = self._idle_boost

        # 尾巴：主频 + 轻微二次谐波，看起来更像真猫摇尾巴
        self._tail_angle = (
            math.sin(t * 3.2 * boost) * 16.0
            + math.sin(t * 5.1 * boost + 0.6) * 4.0
        )

        # 头部：慢速左右轻转 + 轻微点头/侧移
        self._head_angle = (
            math.sin(t * 1.15 * boost + 0.4) * 5.5
            + math.sin(t * 0.55 + 1.2) * 2.0
        )
        self._head_bob_x = math.sin(t * 0.9 * boost) * (2.2 * self._scale)
        self._head_bob_y = math.sin(t * 1.7 * boost + 0.8) * (1.4 * self._scale)

        # 互动动画期间也保持刷新；无互动时只靠 idle 刷新
        if not self._anim_timer.isActive():
            self.update()

    def _reset_idle_boost(self) -> None:
        self._idle_boost = 1.0

    # ----- 互动动画 -----
    def _trigger_interaction(self) -> None:
        if self._anim_timer.isActive():
            return
        kind = self._interactions[self._interaction_index % len(self._interactions)]
        self._interaction_index += 1
        self._anim_kind = kind
        self._anim_t = 0.0
        if kind == "jump":
            self._anim_duration = 520.0
        elif kind == "squash":
            self._anim_duration = 620.0
        else:
            self._anim_duration = 480.0
        self._show_bubble(random.choice(DIALOGUES))
        # 点击时尾巴摇得更欢一会儿
        self._idle_boost = 1.85
        self._boost_timer.start(1600)
        self._anim_timer.start()

    def _ease_out_cubic(self, t: float) -> float:
        return 1.0 - (1.0 - t) ** 3

    def _ease_in_out(self, t: float) -> float:
        curve = QEasingCurve(QEasingCurve.Type.InOutSine)
        return float(curve.valueForProgress(t))

    def _on_anim_tick(self) -> None:
        self._anim_t += self._anim_timer.interval()
        t = min(1.0, self._anim_t / self._anim_duration)
        kind = self._anim_kind

        if kind == "jump":
            if t < 0.45:
                p = self._ease_out_cubic(t / 0.45)
                self._offset.setY(int(-90 * self._scale * p))
                self._squash_x, self._squash_y = 0.92, 1.08
            else:
                p = (t - 0.45) / 0.55
                p = self._ease_in_out(p)
                self._offset.setY(int(-90 * self._scale * (1.0 - p)))
                land = math.sin(p * math.pi)
                self._squash_x = 1.0 + 0.12 * land
                self._squash_y = 1.0 - 0.12 * land
        elif kind == "squash":
            if t < 0.35:
                p = t / 0.35
                self._squash_x = 1.0 + 0.35 * p
                self._squash_y = 1.0 - 0.35 * p
                self._offset.setY(int(12 * self._scale * p))
            else:
                p = (t - 0.35) / 0.65
                bounce = math.sin(p * math.pi) * (1.0 - p)
                self._squash_x = 1.35 - 0.35 * self._ease_out_cubic(p) - 0.08 * bounce
                self._squash_y = 0.65 + 0.35 * self._ease_out_cubic(p) + 0.08 * bounce
                self._offset.setY(int(12 * self._scale * (1.0 - self._ease_out_cubic(p))))
        elif kind == "shake":
            amp = 14 * self._scale
            self._offset.setX(int(math.sin(t * math.pi * 8) * amp * (1.0 - t)))
            self._squash_x = 1.0 + 0.04 * math.sin(t * math.pi * 8)
            self._squash_y = 1.0 - 0.03 * math.sin(t * math.pi * 8)

        self.update()
        if t >= 1.0:
            self._anim_timer.stop()
            self._anim_kind = ""
            self._offset = QPoint(0, 0)
            self._squash_x = 1.0
            self._squash_y = 1.0
            self.update()

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
                self._trigger_interaction()
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

        top_act = QAction("取消置顶" if self._always_on_top else "始终置顶", self)
        top_act.triggered.connect(self._toggle_always_on_top)
        menu.addAction(top_act)

        menu.addSeparator()
        quit_act = QAction("退出程序", self)
        quit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_act)

        menu.exec(event.globalPos())

    def _set_scale(self, value: float) -> None:
        self._scale = max(self.MIN_SCALE, min(self.MAX_SCALE, value))
        self._rebuild_pixmap()
        self._relayout()
        self.update()

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
    pet = DesktopPet()
    pet.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
