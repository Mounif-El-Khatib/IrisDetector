from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivy.graphics.texture import Texture
from plyer import filechooser
from IrisDetector import process_frame
from jnius import autoclass, cast
from kivy.uix.camera import Camera
from kivy.utils import platform
from kivy.clock import Clock
from PIL import Image
import cv2
import os
import io
import numpy as np


def file_exists(path):
    exists = os.path.exists(path)
    if not exists:
        print(f"File does not exist: {path}")
    return exists


class MainWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def handle_selection(self, input_stream):
        if not input_stream:
            print("No file selected.")
            return
        try:
            image = Image.open(input_stream)
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            print("Frame shape:", frame.shape)
            processed_frame, result = process_frame(frame)
            buf = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            buf = cv2.flip(buf, 0)

            def update_texture(dt):
                texture = Texture.create(
                    size=(buf.shape[1], buf.shape[0]), colorfmt='rgb')
                texture.blit_buffer(
                    buf.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                self.ids.image.texture = texture
                self.ids.result.text = str(result)

            Clock.schedule_once(update_texture)

        except Exception as e:
            print(f"Error in handle_selection: {str(e)}")
            import traceback
            traceback.print_exc()
            self.ids.result.text = "Error processing image."


class IrisDetector(MDApp):
    def get_image(self):
        self.mActivity = None
        if platform == "android":
            from android.permissions import request_permissions, Permission  # pylint: disable=import-error # type: ignore
            request_permissions([Permission.READ_EXTERNAL_STORAGE,
                                Permission.WRITE_EXTERNAL_STORAGE])
            from android import mActivity  # pylint: disable=import-error # type: ignore
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            self.mActivity = mActivity
            intent = Intent(Intent.ACTION_PICK)
            intent.setType("image/*")
            self.mActivity.startActivityForResult(intent, 123)

            from android.activity import bind   # pylint: disable=import-error # type: ignore
            bind(on_activity_result=self.on_activity_result)
        else:
            self.root.handle_selection('./1.jpeg')

    def on_activity_result(self, request_code, result_code, data):
        if request_code == 123 and result_code == -1:
            uri = data.getData()
            content_resolver = self.mActivity.getContentResolver()
            input_stream = content_resolver.openInputStream(uri)
            self.root.handle_selection(input_stream)

    def build(self):
        return MainWidget()


if __name__ == '__main__':
    IrisDetector().run()
