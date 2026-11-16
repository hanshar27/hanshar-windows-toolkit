import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.ui_style import (
    ACCENT_AMBER,
    ACCENT_COLOR,
    ACCENT_PURPLE,
    BORDER_COLOR,
    CARD_COLOR,
    DEFAULT_BLUR_INTENSITY,
    PANEL_COLOR,
    SIDEBAR_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WINDOW_BACKGROUND,
)
from core.window_effects import acrylic_tint_alpha, apply_window_backdrop


class TestGlassStyle(unittest.TestCase):
    def test_application_uses_a_single_dark_glass_style(self):
        self.assertEqual(DEFAULT_BLUR_INTENSITY, 55)
        self.assertEqual(WINDOW_BACKGROUND, "#101014")
        self.assertEqual(SIDEBAR_COLOR, "#18181F")
        self.assertEqual(PANEL_COLOR, "#1E1E26")
        self.assertEqual(CARD_COLOR, "#23232E")
        self.assertEqual(BORDER_COLOR, "#32323F")
        self.assertEqual(ACCENT_COLOR, "#4C8DFF")
        self.assertEqual(ACCENT_PURPLE, "#B65CFF")
        self.assertEqual(ACCENT_AMBER, "#F2A93B")
        self.assertEqual(TEXT_PRIMARY, "#F4F4F8")
        self.assertEqual(TEXT_SECONDARY, "#A0A0B0")

    def test_blur_intensity_controls_acrylic_tint_strength(self):
        self.assertIsNone(acrylic_tint_alpha(0))
        self.assertGreater(acrylic_tint_alpha(20), acrylic_tint_alpha(80))
        self.assertEqual(acrylic_tint_alpha(-10), acrylic_tint_alpha(0))
        self.assertEqual(acrylic_tint_alpha(110), acrylic_tint_alpha(100))

    def test_acrylic_backdrop_keeps_the_window_background_clickable(self):
        window = Mock()
        window.winfo_id.return_value = 123
        get_ancestor = Mock(return_value=123)
        set_attribute = Mock(return_value=1)
        user32 = SimpleNamespace(
            GetAncestor=get_ancestor,
            SetWindowCompositionAttribute=set_attribute,
        )

        with (
            patch("core.window_effects.os", SimpleNamespace(name="nt")),
            patch("core.window_effects.ctypes.windll", SimpleNamespace(user32=user32)),
        ):
            self.assertTrue(apply_window_backdrop(window, 55))

        window.wm_attributes.assert_called_once_with("-transparentcolor", "")
        window.configure.assert_called_once_with(fg_color=WINDOW_BACKGROUND)
        get_ancestor.assert_called_once_with(123, 2)
        set_attribute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
