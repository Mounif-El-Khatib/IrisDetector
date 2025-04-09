from camera4kivy import Preview


class CameraFrame(Preview):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analyzed_texture = None
        self.captured = False

    def capture(self):
        self.captured = True
