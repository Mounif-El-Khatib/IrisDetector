from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivy.graphics.texture import Texture
from plyer import filechooser
from IrisDetector import process_frame
from jnius import autoclass, cast
from kivy.uix.camera import Camera
from kivy.utils import platform
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivy.uix.gridlayout import GridLayout
from PIL import Image
from kivymd.uix.fitimage import FitImage
import cv2
import numpy as np
from kivy.utils import get_color_from_hex

GREEN = ["#A8D5BA", "#6BBF8A", "#4B9B6E", "#2E7D5C", "#1B5E3A"]


class MainWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = MDBoxLayout(
            orientation='vertical',
            padding='10dp',
            spacing='10dp',
            md_bg_color=get_color_from_hex(GREEN[0]),
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.layout)

        print("Setting up standard Image widget")

        self.image = FitImage(
            size_hint=(1, 0.7),
            radius=[10],
            mipmap=True
        )

        self.layout.add_widget(self.image)

        self.result_label = MDLabel(
            text='Result will appear here',
            halign='center',
            theme_text_color='Primary',
            size_hint=(1, 0.1),
            font_style='H5'
        )
        self.layout.add_widget(self.result_label)

        button_layout = GridLayout(
            cols=2,
            spacing='10dp',
            size_hint=(1, 0.1)
        )

        self.take_picture_btn = MDRaisedButton(
            text='Take Picture',
            md_bg_color=GREEN[3],
            font_size='20dp',
            size_hint=(0.5, 1)
        )
        button_layout.add_widget(self.take_picture_btn)

        self.select_picture_btn = MDRaisedButton(
            text='Select Picture',
            md_bg_color=GREEN[3],
            font_size='20dp',
            size_hint=(0.5, 1),
            on_release=lambda x: MDApp.get_running_app().get_image()
        )
        button_layout.add_widget(self.select_picture_btn)

        self.layout.add_widget(button_layout)

        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, *args):
        self.layout.size = self.size
        self.layout.pos = self.pos

    def preprocess_image(self, frame):
        if frame is None:
            return None

        frame = frame.astype(np.float32)
        frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
        frame = frame.astype(np.uint8)

        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        return frame

    def handle_selection(self, input_source):
        if not input_source:
            print("No input source.")
            return
        try:
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
                chunk_size = 8192
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

            frame = self.preprocess_image(frame)

            print("Image stats:", {
                "shape": frame.shape,
                "dtype": frame.dtype,
                "min": frame.min(),
                "max": frame.max(),
                "mean": frame.mean(),
                "std": frame.std()
            })

            processed_frame, result = process_frame(frame)
            print(f"Process result: {result}")

            buf = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            buf = cv2.flip(buf, 0)

            print(f"Creating texture with shape: {buf.shape}")

            def update_texture(dt):
                try:
                    texture = Texture.create(
                        size=(buf.shape[1], buf.shape[0]), colorfmt='rgb')
                    texture.blit_buffer(
                        buf.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                    print(f"Texture created: {texture.width}x{texture.height}")
                    self.image.source = texture
                    print("Texture assigned to standard image widget")
                    self.result_label.text = f"Iris to pupil ratio: {str(result)}"
                except Exception as tex_err:
                    print(f"Error in texture update: {tex_err}")
                    import traceback
                    traceback.print_exc()
            Clock.schedule_once(update_texture)

        except Exception as e:
            print(f"Error in handle_selection: {str(e)}")
            import traceback
            traceback.print_exc()
            self.result_label.text = "Error processing image."

    def take_picture(self, *args):
        print("Take Picture button clicked")

    def select_picture(self, *args):
        app = MDApp.get_running_app()
        app.get_image()


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
            print("Uri", uri)
            content_resolver = self.mActivity.getContentResolver()
            input_stream = content_resolver.openInputStream(uri)
            print("Input_stream:", input_stream)
            self.root.handle_selection(input_stream)

    def build(self):
        return MainWidget()


if __name__ == '__main__':
    IrisDetector().run()
