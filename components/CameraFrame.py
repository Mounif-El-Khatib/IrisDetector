from camera4kivy import Preview


class CameraFrame(Preview):
    __events__ = ("on_texture_available",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analyzed_texture = None
        self.captured = False

    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
        if self.captured:
            self.analyzed_texture = texture
            self.captured = False
            self.dispatch("on_texture_available", texture)

    def capture(self):
        self.captured = True

    def on_texture_available(self, texture):
        pass
