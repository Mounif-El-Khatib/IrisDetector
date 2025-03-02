from kivymd.app import MDApp
from kivy.graphics.texture import Texture
from plyer import filechooser
from IrisDetector import process_frame
from jnius import autoclass, cast
from kivy.uix.camera import Camera
from kivy.utils import platform
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.widget import MDWidget
from PIL import Image
from kivymd.uix.anchorlayout import MDAnchorLayout
import cv2
import numpy as np
from kivy.utils import get_color_from_hex
from components.PictureFrame import PictureFrame
from components.ButtonLayout import ButtonLayout

from colors import Colors


DEBUG = True


class IrisDetector(MDApp):
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
            if DEBUG:
                print(
                    f"Platform: {'Android' if platform == 'android' else 'Desktop'}")

            if isinstance(input_source, str):
                print("Loading from file path")
                frame = cv2.imread(input_source)
                if DEBUG:
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
                if DEBUG:
                    print("Android image stats:", {
                        "min": frame.min(),
                        "max": frame.max(),
                        "mean": frame.mean()
                    })

            frame = self.preprocess_image(frame)

            if DEBUG:
                print("Image stats:", {
                    "shape": frame.shape,
                    "dtype": frame.dtype,
                    "min": frame.min(),
                    "max": frame.max(),
                    "mean": frame.mean(),
                    "std": frame.std()
                })

            processed_frame, result = process_frame(frame)

            if DEBUG:
                print(f"Process result: {result}")

            buf = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            buf = cv2.flip(buf, 0)

            if DEBUG:
                print(f"Creating texture with shape: {buf.shape}")

            def update_texture(dt):
                try:
                    texture = Texture.create(
                        size=(buf.shape[1], buf.shape[0]), colorfmt='rgb')
                    texture.blit_buffer(
                        buf.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                    if DEBUG:
                        print(
                            f"Texture created: {texture.width}x{texture.height}")
                    self.pictureFrame.set_source(texture)
                    if DEBUG:
                        print("Texture assigned to standard image widget")
                    self.resultLabel.text = f"Iris to pupil ratio: {str(result)}"
                    # Removes the info text to display the picture
                    self.placeholder.remove_widget(self.infoText)
                    # Replace the info text with the picture frame
                    self.placeholder.add_widget(self.pictureFrame)
                except Exception as tex_err:
                    print(f"Error in texture update: {tex_err}")
                    import traceback
                    traceback.print_exc()
            Clock.schedule_once(update_texture)

        except Exception as e:
            print(f"Error in handle_selection: {str(e)}")
            import traceback
            traceback.print_exc()
            self.resultLabel.text = "Error processing image."
            self.resultLabel.color = Colors.SOFT_RED.value

    def get_image(self, instance):
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
            self.handle_selection("./1.jpeg")

    def on_activity_result(self, request_code, result_code, data):
        if request_code == 123 and result_code == -1:
            uri = data.getData()
            print("Uri", uri)
            content_resolver = self.mActivity.getContentResolver()
            input_stream = content_resolver.openInputStream(uri)
            if DEBUG:
                print("Input_stream:", input_stream)
            self.handle_selection(input_stream)

    def build(self):
        # This is the main layout of the page
        self.layout = MDBoxLayout(
            orientation='vertical',
            padding='10dp',
            spacing='10dp',
            md_bg_color=Colors.LIGHT_GRAY.value,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        # This is just a placeholder widget. Before selecting a picture, info text will appear. After selecing a picture, the info text will
        # dissappear and the picture frame will appear.
        self.placeholder = MDAnchorLayout(
            md_bg_color=(0, 0, 0, 0),
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, 1)
        )

        # Info label that appears by default before user interacts
        self.infoText = MDLabel(
            text="Select an image to process, or take a picture with the camera.",
            halign='center',
            font_style='H6',
            size_hint=(1, 0.4)
        )
        self.infoText.color = Colors.COOL_GRAY.value

        self.placeholder.add_widget(self.infoText)
        self.layout.add_widget(self.placeholder)

        # This defines the format of the picture. This will be rendered conditionally
        self.pictureFrame = PictureFrame(
            md_bg_color=Colors.MEDIUM_GRAY.value,
            size_hint=(1, 1),
            padding='8dp',
            radius=[18]
        )

        # This displays the ratio result right under the picture
        self.resultLabel = MDLabel(
            halign='center',
            font_style='H6',
            size_hint=(1, 0.4)
        )
        self.layout.add_widget(self.resultLabel)

        # This is the button layout used, it consists of a grid made of 2 columns, where one button takes up 1 column
        buttonLayout = ButtonLayout(
            md_bg_color=Colors.DARK_GRAY.value, on_select_picture=self.get_image, font_size='18dp')
        self.layout.add_widget(buttonLayout)
        return self.layout


if __name__ == '__main__':
    IrisDetector().run()
