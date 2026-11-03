"""
Motion and animation helper for Qt widgets.
Encapsulates QPropertyAnimation lifecycle management, spring easing curves,
fade effects, and accordion transitions to ensure SOLID compliance and eliminate magic numbers.
"""

from typing import Callable, Optional

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


class MotionConstants:
    """Centralized animation durations, curve parameters, and thresholds."""

    # Durations (ms)
    DURATION_SPRING = 350
    DURATION_FADE = 320
    DURATION_EXPAND = 260
    DURATION_COLLAPSE = 240
    AUTO_EXPAND_HOVER_MS = 600

    # Spring parameters
    SPRING_OVERSHOOT = 1.08

    # Opacity levels
    OPACITY_FULL = 1.0
    OPACITY_DRAGGING = 0.72
    OPACITY_HIDDEN = 0.0

    # Drag hysteresis deadbands (px)
    DEADBAND_TAG_SWAP_PX = 14
    DEADBAND_GROUP_SWAP_PX = 22

    # Layout bounds
    MAX_WIDGET_SIZE = 16777215
    MIN_ACCORDION_HEIGHT = 38


class MotionHelper:
    """
    Stateless animation facade providing safe QPropertyAnimation execution.
    Guarantees C++ object lifetime safety and encapsulates common motion patterns.
    """

    @staticmethod
    def safe_stop(anim: Optional[QPropertyAnimation]) -> None:
        """Safely stops an animation, guarding against wrapped C++ deletion."""
        if anim is not None:
            try:
                anim.stop()
            except RuntimeError:
                pass

    @staticmethod
    def glide_pos(
        widget: QWidget,
        end_pos: QPoint,
        start_pos: Optional[QPoint] = None,
        duration: int = MotionConstants.DURATION_SPRING,
        overshoot: float = MotionConstants.SPRING_OVERSHOOT,
        anim_prop_name: str = "_pos_anim",
    ) -> Optional[QPropertyAnimation]:
        """
        Smoothly glides a widget to end_pos using an iOS-style spring deceleration curve.
        Replaces any running position animation on the widget.
        """
        if not widget.isVisible():
            widget.move(end_pos)
            return None

        actual_start = start_pos if start_pos is not None else widget.pos()
        if actual_start == end_pos:
            return None

        existing = getattr(widget, anim_prop_name, None)
        MotionHelper.safe_stop(existing)

        anim = QPropertyAnimation(widget, b"pos", widget)
        anim.setDuration(duration)
        curve = QEasingCurve(QEasingCurve.Type.OutBack)
        curve.setOvershoot(overshoot)
        anim.setEasingCurve(curve)
        anim.setStartValue(actual_start)
        anim.setEndValue(end_pos)

        setattr(widget, anim_prop_name, anim)

        def on_finished(w=widget, a=anim, prop=anim_prop_name):
            if getattr(w, prop, None) is a:
                setattr(w, prop, None)

        anim.finished.connect(on_finished)
        anim.start()
        return anim

    @staticmethod
    def fade_opacity(
        widget: QWidget,
        start_opacity: float,
        end_opacity: float,
        duration: int = MotionConstants.DURATION_FADE,
        on_finished: Optional[Callable[[], None]] = None,
        anim_prop_name: str = "_opacity_anim",
    ) -> Optional[QPropertyAnimation]:
        """
        Fades widget opacity between start_opacity and end_opacity.
        Automatically attaches QGraphicsOpacityEffect and removes it on completion if target is 1.0.
        """
        existing = getattr(widget, anim_prop_name, None)
        MotionHelper.safe_stop(existing)

        eff = widget.graphicsEffect()
        if not isinstance(eff, QGraphicsOpacityEffect):
            eff = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(eff)

        eff.setOpacity(start_opacity)

        anim = QPropertyAnimation(eff, b"opacity", widget)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutCubic))
        anim.setStartValue(start_opacity)
        anim.setEndValue(end_opacity)

        setattr(widget, anim_prop_name, anim)

        def on_fade_done(w=widget, a=anim, prop=anim_prop_name, target=end_opacity, cb=on_finished):
            if getattr(w, prop, None) is a:
                setattr(w, prop, None)
            if target >= 0.999:
                w.setGraphicsEffect(None)
            if cb:
                cb()

        anim.finished.connect(on_fade_done)
        anim.start()
        return anim

    @staticmethod
    def animate_accordion(
        container: QWidget,
        target_height: int,
        expanding: bool,
        duration: Optional[int] = None,
        on_step: Optional[Callable[[int], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
        anim_prop_name: str = "_collapse_anim",
    ) -> Optional[QPropertyAnimation]:
        """
        Smoothly animates an accordion container's maximumHeight and opacity simultaneously.
        """
        existing = getattr(container, anim_prop_name, None)
        MotionHelper.safe_stop(existing)

        dur = duration or (MotionConstants.DURATION_EXPAND if expanding else MotionConstants.DURATION_COLLAPSE)
        start_h = container.height() if container.isVisible() else 0

        if expanding:
            container.setVisible(True)
            if start_h >= target_height:
                start_h = 0
            container.setMaximumHeight(start_h)
            eff = QGraphicsOpacityEffect(container)
            eff.setOpacity(MotionConstants.OPACITY_HIDDEN)
            container.setGraphicsEffect(eff)
            end_h = target_height
        else:
            if start_h <= 0:
                container.setVisible(False)
                container.setMaximumHeight(MotionConstants.MAX_WIDGET_SIZE)
                container.setGraphicsEffect(None)
                if on_finished:
                    on_finished()
                return None
            eff = QGraphicsOpacityEffect(container)
            eff.setOpacity(MotionConstants.OPACITY_FULL)
            container.setGraphicsEffect(eff)
            end_h = 0

        anim = QPropertyAnimation(container, b"maximumHeight", container)
        anim.setDuration(dur)
        anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutCubic))
        anim.setStartValue(start_h)
        anim.setEndValue(end_h)

        setattr(container, anim_prop_name, anim)

        def on_anim_step(current_h):
            if expanding:
                span = max(1, target_height - start_h)
                prog = min(1.0, max(0.0, (current_h - start_h) / span))
            else:
                span = max(1, start_h)
                prog = min(1.0, max(0.0, current_h / span))
            eff.setOpacity(prog)
            if on_step:
                on_step(current_h)

        def on_anim_done(c=container, a=anim, prop=anim_prop_name, is_exp=expanding, cb=on_finished):
            if getattr(c, prop, None) is a:
                setattr(c, prop, None)
            if is_exp:
                c.setMaximumHeight(MotionConstants.MAX_WIDGET_SIZE)
            else:
                c.setVisible(False)
                c.setMaximumHeight(MotionConstants.MAX_WIDGET_SIZE)
            c.setGraphicsEffect(None)
            if cb:
                cb()

        anim.valueChanged.connect(on_anim_step)
        anim.finished.connect(on_anim_done)
        anim.start()
        return anim
