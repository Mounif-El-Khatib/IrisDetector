from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivy.graphics.texture import Texture
from IrisDetector import process_frame
from jnius import autoclass
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
from camera4kivy import Preview
from components.PictureFrame import PictureFrame
from components.ButtonLayout import ButtonLayout

# import utility.preprocess_image
from colors import Colors


class IrisDetector(MDApp):

    def clear_frame(self):
        for c in list(self.placeholder.children):
            if c is not None:
                self.placeholder.remove_widget(c)
        self.infoText = ""

    def handle_selection(self, input_source):
        if self.preview is not None:
            self.preview.disconnect_camera()
        # self.clear_frame()
        if not input_source:
            return
        try:
            if isinstance(input_source, str):
                frame = cv2.imread(input_source)
            else:

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

            # frame = preprocess_image(frame)

            processed_frame, result = process_frame(frame)

            buf = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            buf = cv2.flip(buf, 0)

            def update_texture(dt):
                try:
                    texture = Texture.create(
                        size=(buf.shape[1], buf.shape[0]), colorfmt="rgb"
                    )
                    texture.blit_buffer(
                        buf.tobytes(), colorfmt="rgb", bufferfmt="ubyte"
                    )
                    self.pictureFrame.set_source(texture)
                    self.resultLabel.text = f"Iris to pupil ratio: {str(result)}"
                    for c in list(self.placeholder.children):
                        if c is not None:
                            self.placeholder.remove_widget(c)
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
            from android.permissions import (
                request_permissions,
                Permission,
            )

            request_permissions(
                [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
            )
            from android import mActivity

            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            self.mActivity = mActivity
            intent = Intent(Intent.ACTION_PICK)
            intent.setType("image/*")
            self.mActivity.startActivityForResult(intent, 123)

            from android.activity import (
                bind,
            )

            bind(on_activity_result=self.on_activity_result)
        else:
            self.handle_selection("./1.jpeg")

    def on_activity_result(self, request_code, result_code, data):
        if request_code == 123 and result_code == -1:
            uri = data.getData()
            print("Uri", uri)
            content_resolver = self.mActivity.getContentResolver()
            input_stream = content_resolver.openInputStream(uri)
            self.handle_selection(input_stream)

    def open_camera(self, instance):
        if platform == "android":
            from android.permissions import (
                request_permissions,
                Permission,
            )

            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE])
        self.clear_frame()
        self.preview = Preview(aspect_ratio="4:3")
        self.placeholder.add_widget(self.preview)
        self.preview.connect_camera(
            enable_analyze_pixels=True,
            sensor_resolution=(640, 480),
            analyze_pixels_callback=self.analyze_pixels,
        )

    def analyze_pixels(self, pixels, size, image_pos, image_scale, mirror):
        print("HELLO")
        frame = np.frombuffer(pixels, dtype=np.uint8)
        frame = frame.reshape(size[1], size[0], -1)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        processed_frame, result = process_frame(frame)

        buf = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        buf = cv2.flip(buf, 0)

        def update_texture(dt):
            try:
                texture = Texture.create(
                    size=(buf.shape[1], buf.shape[0]), colorfmt="rgb"
                )
                texture.blit_buffer(buf.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
                self.pictureFrame.set_source(texture)
                self.resultLabel.text = f"Iris to pupil ratio: {str(result)}"
                for c in list(self.placeholder.children):
                    if c is not None:
                        self.placeholder.remove_widget(c)
                self.placeholder.add_widget(self.pictureFrame)
            except Exception as tex_err:
                print(f"Error in texture update: {tex_err}")
                import traceback

                traceback.print_exc()

        print("Im here")
        Clock.schedule_once(update_texture)

    def take_picture(self, instance):
        self.preview.capture_photo()
        print("Captured photo")

    def build(self):
        self.preview = None
        # This is the main layout of the page
        self.orientation = "portrait"
        self.layout = MDBoxLayout(
            orientation="vertical",
            padding="10dp",
            spacing="10dp",
            md_bg_color=Colors.LIGHT_GRAY.value,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        # This is just a placeholder widget. Before selecting a picture, info text will appear. After selecing a picture, the info text will
        # dissappear and the picture frame will appear.
        self.placeholder = MDAnchorLayout(
            md_bg_color=(0, 0, 0, 0),
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, 1),
        )

        # Info label that appears by default before user interacts
        self.infoText = MDLabel(
            text="Select an image to process, or take a picture with the camera.",
            halign="center",
            font_style="H6",
            size_hint=(1, 0.4),
        )
        self.infoText.color = Colors.COOL_GRAY.value

        self.placeholder.add_widget(self.infoText)
        self.layout.add_widget(self.placeholder)

        # This defines the format of the picture. This will be rendered conditionally
        self.pictureFrame = PictureFrame(
            md_bg_color=Colors.MEDIUM_GRAY.value,
            size_hint=(1, 1),
            padding="8dp",
            radius=[18],
        )

        # This displays the ratio result right under the picture
        self.resultLabel = MDLabel(halign="center", font_style="H6", size_hint=(1, 0.4))
        self.layout.add_widget(self.resultLabel)
        captureButton = MDRaisedButton(on_release=self.take_picture)
        self.layout.add_widget(captureButton)

        # This is the button layout used, it consists of a grid made of 2 columns, where one button takes up 1 column
        self.buttonLayout = ButtonLayout(
            md_bg_color=Colors.CHARCOAL.value,
            on_select_picture=self.get_image,
            font_size="18dp",
            on_take_picture=self.open_camera,
        )
        self.layout.add_widget(self.buttonLayout)
        # self.camera = None
        return self.layout


if __name__ == "__main__":
    IrisDetector().run()
