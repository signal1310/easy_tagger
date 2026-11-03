import unittest

from tests import get_qapp

get_qapp()

from PyQt6.QtCore import QPoint, QPropertyAnimation
from PyQt6.QtWidgets import QWidget

from src.ui.animation import MotionConstants, MotionHelper


class TestMotionHelper(unittest.TestCase):
    def setUp(self):
        self.widget = QWidget()
        self.widget.resize(200, 100)
        self.widget.show()

    def tearDown(self):
        self.widget.deleteLater()

    def test_constants_invariants(self):
        self.assertGreater(MotionConstants.DURATION_SPRING, 0)
        self.assertGreater(MotionConstants.DURATION_FADE, 0)
        self.assertGreater(MotionConstants.DURATION_EXPAND, 0)
        self.assertGreater(MotionConstants.DURATION_COLLAPSE, 0)
        self.assertGreater(MotionConstants.AUTO_EXPAND_HOVER_MS, 0)
        self.assertGreater(MotionConstants.SPRING_OVERSHOOT, 1.0)
        self.assertEqual(MotionConstants.OPACITY_FULL, 1.0)
        self.assertEqual(MotionConstants.OPACITY_HIDDEN, 0.0)

    def test_glide_pos_lifecycle(self):
        self.widget.move(0, 0)
        target = QPoint(50, 50)
        anim = MotionHelper.glide_pos(self.widget, target, QPoint(0, 0))
        self.assertIsNotNone(anim)
        self.assertIsInstance(anim, QPropertyAnimation)
        self.assertEqual(getattr(self.widget, "_pos_anim", None), anim)

        # Calling safe_stop does not raise error
        MotionHelper.safe_stop(anim)

    def test_fade_opacity_lifecycle(self):
        anim = MotionHelper.fade_opacity(self.widget, 1.0, 0.72)
        self.assertIsNotNone(anim)
        self.assertEqual(getattr(self.widget, "_opacity_anim", None), anim)

        done_called = []
        # Calling fade to 1.0 triggers tear-down and callback
        anim2 = MotionHelper.fade_opacity(self.widget, 0.72, 1.0, on_finished=lambda: done_called.append(True))
        self.assertIsNotNone(anim2)
        anim2.stop()
        anim2.finished.emit()
        self.assertTrue(done_called)
        self.assertIsNone(self.widget.graphicsEffect())

    def test_animate_accordion_expand_and_collapse(self):
        # Expand
        steps = []
        anim_exp = MotionHelper.animate_accordion(
            self.widget, target_height=120, expanding=True, on_step=lambda h: steps.append(h)
        )
        self.assertIsNotNone(anim_exp)
        self.assertTrue(self.widget.isVisible())
        anim_exp.stop()

        # Collapse
        anim_col = MotionHelper.animate_accordion(
            self.widget, target_height=120, expanding=False
        )
        self.assertIsNotNone(anim_col)
        anim_col.stop()
        anim_col.finished.emit()
        self.assertFalse(self.widget.isVisible())


if __name__ == "__main__":
    unittest.main()

