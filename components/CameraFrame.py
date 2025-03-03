from kivymd.uix.card import MDCard
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.camera import Camera
from kivy.graphics import Rotate


class CameraFrame(MDCard):

    def __init__(self, **kwargs):
        super().__init__()

        self.camera = Camera(**kwargs)

        self.anchor_layout = AnchorLayout(
            anchor_x="center", anchor_y="center", size_hint=(1, 1)
        )

        self.anchor_layout.add_widget(self.camera)
        self.add_widget(self.anchor_layout)

    def play_camera(self):
        self.camera.play = True

    def stop_camera(self):
        self.camera.play = False

    def toggle_camera(self):
        self.camera.play = not self.camera.play

    def rotate_camera(self, angle):
        with self.canvas.after:
            self.rotation = Rotate(angle=angle, origin=self.center)
