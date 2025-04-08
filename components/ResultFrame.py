from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

from colors import Colors


class ResultFrame(MDCard):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint = (1, None)
        self.size = (dp(300), dp(120))
        self.padding = dp(10)

        self.boxlayout = BoxLayout(orientation="vertical", spacing=dp(5))

        self.label = MDLabel(font_style="H6")

        self.result = MDLabel(font_style="H5")

        self.boxlayout.add_widget(self.label)
        self.boxlayout.add_widget(self.result)
        self.md_bg_color = (0, 0, 0, 0)

        self.add_widget(self.boxlayout)

    def set_text(self, text, color="#000000"):
        self.result.text = text
        self.result.color = color
        self.label.text = "Result:"
        self.radius = [8]
        self.line_color = Colors.LIGHT_GRAY.value
        self.md_bg_color = Colors.CRISP_WHITE.value

    def clear_result(self):
        self.result.text = ""
        self.label.text = ""
        self.line_color = (0, 0, 0, 0)
        self.md_bg_color = (0, 0, 0, 0)

    def get_result(self):
        return self.result.text
