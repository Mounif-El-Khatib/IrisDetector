from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar
from kivy.metrics import dp


class AppSnackbar:
    def __init__(self, **kwargs):
        text = kwargs.get("text")
        self.snackbar = Snackbar(
            MDLabel(text=text, size_hint_x=1),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
        )

    def open(self):
        self.snackbar.open()

    def close(self):
        if self.snackbar:
            self.snackbar.dismiss()
