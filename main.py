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
import numpy as np
import io


def file_exists(path):
    exists = os.path.exists(path)
    if not exists:
        print(f"File does not exist: {path}")
    return exists


class MainWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def handle_selection(self, input_source):
        if not input_source:
            print("No input source.")
            return
        try:
            # Debug platform info
            print(
                f"Platform: {'Android' if platform == 'android' else 'Desktop'}")

            if isinstance(input_source, str):
                print("Loading from file path")
                frame = cv2.imread(input_source)
                print("Desktop image stats:", {
                    "min": frame.min(),
                    "max": frame.max(),
                    "mean": frame.mean()
                })
            else:
                print("Loading from input stream")
                buffer = bytearray()
                chunk_size = 8192  # Increased buffer size
                byte_array = bytearray(chunk_size)
                while True:
                    bytes_read = input_source.read(byte_array)
                    if bytes_read == -1:
                        break
                    buffer.extend(byte_array[:bytes_read])
                input_source.close()

                nparr = np.frombuffer(buffer, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                print("Android image stats:", {
                    "min": frame.min(),
                    "max": frame.max(),
                    "mean": frame.mean()
                })

            print(f"Frame shape: {frame.shape}")
            print(f"Frame dtype: {frame.dtype}")
            print(f"Frame value range: [{frame.min()}, {frame.max()}]")

            # Ensure consistent color space
            if frame is not None:
                # Normalize image to ensure consistent processing
                frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)

            processed_frame, result = process_frame(frame)
            print(f"Process result: {result}")

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
            self.root.handle_selection("./1.jpeg")

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
