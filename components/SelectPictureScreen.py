from kivy.uix.button import ButtonBehavior
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.boxlayout import BoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from colors import Colors


class MD3Card(MDCard, ButtonBehavior):
    def __init__(self, callback=None):
        super().__init__()
        self.md_bg_color = Colors.LIGHT_GRAY.value
        self.callback = callback

    def on_press(self):
        if self.callback:
            self.callback(self)


class SelectPictureScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__()
        on_click = kwargs.get("on_click")
        self.orientation = "vertical"
        self.padding = "10dp"
        self.spacing = "10dp"
        self.md_bg_color = Colors.CRISP_WHITE.value

        self.placeholder = MDAnchorLayout(
            md_bg_color=(0, 0, 0, 0),
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, 1),
            padding=(30, 60, 30, 60),
        )
        self.infoText = MDLabel(
            text="Select an image to process", font_style="H4", halign="center"
        )

        self.mdcard = MD3Card(callback=on_click)
        self.mdcard.add_widget(self.infoText)
        self.placeholder.add_widget(self.mdcard)
        self.add_widget(self.placeholder)

    def clear_placeholder(self):
        self.placeholder.clear_widgets()

    def reset_screen(self):
        self.clear_placeholder()
        self.placeholder.add_widget(self.mdcard)
        self.set_padding([30, 60, 30, 60])

    def set_placeholder(self, widget):
        self.clear_placeholder()
        self.placeholder.add_widget(widget)

    def set_padding(self, padding: list):
        self.placeholder.padding = padding
