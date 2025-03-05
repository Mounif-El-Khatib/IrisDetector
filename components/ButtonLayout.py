from kivymd.uix.button import MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout


class ButtonLayout(MDGridLayout):
    def __init__(self, **kwargs):
        super().__init__()
        backgroundColor = kwargs.get("md_bg_color")
        takePicCallback = kwargs.get("on_take_picture")
        selectPicCallback = kwargs.get("on_select_picture")
        font_size = kwargs.get("font_size", "16dp")
        self.cols = 2
        self.spacing = "10dp"
        self.size_hint = (1, 0.2)

        self.take_picture_btn = MDRaisedButton(
            text="Take Picture",
            md_bg_color=backgroundColor,
            font_size=font_size,
            size_hint=(0.5, 1),
            on_release=(
                takePicCallback
                if takePicCallback
                else lambda _: print("Take picture callback not set")
            ),
        )

        self.add_widget(self.take_picture_btn)

        self.select_picture_btn = MDRaisedButton(
            text="Select Picture",
            md_bg_color=backgroundColor,
            font_size=font_size,
            size_hint=(0.5, 1),
            on_release=(
                selectPicCallback
                if selectPicCallback
                else lambda _: print("Select picture callback not set")
            ),
        )
        self.add_widget(self.select_picture_btn)
