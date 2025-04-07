from kivymd.uix.card import MDCard
from kivy.uix.anchorlayout import AnchorLayout
from kivymd.uix.fitimage import FitImage


class PictureFrame(MDCard):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.anchor_layout = AnchorLayout(
            anchor_x="center", anchor_y="center", size_hint=(1, 1)
        )

        self.image = FitImage(
            size_hint=(1, 1),
            radius=[4],
            mipmap=True,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            minimum_height=640,
            minimum_width=480,
        )

        self.anchor_layout.add_widget(self.image)
        self.add_widget(self.anchor_layout)

    def set_source(self, source):
        self.image.source = source

    @property
    def source(self):
        return self.image.source

    @source.setter
    def source(self, value):
        self.image.source = value

    def image_exists(self):
        exists = False
        if self.source() is not None:
            exists = True
        return exists
