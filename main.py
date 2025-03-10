from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.button import MDRaisedButton
from kivy.graphics.texture import Texture
from IrisDetector import process_frame
from jnius import autoclass
from kivy.utils import platform
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from PIL import Image
from kivymd.uix.anchorlayout import MDAnchorLayout
import io
import cv2
import numpy as np
from components.CameraFrame import CameraFrame
from components.PictureFrame import PictureFrame
from components.ButtonLayout import ButtonLayout
from kivymd.uix.screen import Screen

from colors import Colors
from components.ResultFrame import ResultFrame


class IrisDetector(MDApp):

    def display_result(self, texture, result):
        self.pictureFrame.set_source(texture)
        self.resultLabel.set_text(f"Iris to pupil ratio: {str(result)}")
        self.placeholder.clear_widgets()
        self.placeholder.add_widget(self.pictureFrame)

    def handle_selection(self, input_source):
        if self.preview is not None:
            self.preview.disconnect_camera()
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
                    self.display_result(texture, result)
                except Exception as tex_err:
                    print(f"Error in texture update: {tex_err}")
                    import traceback

                    traceback.print_exc()

            Clock.schedule_once(update_texture)

        except Exception as e:
            print(f"Error in handle_selection: {str(e)}")
            import traceback

            traceback.print_exc()
            self.resultLabel.set_text("Error processing image", Colors.SOFT_RED.value)

    def get_image(self, instance):
        self.mActivity = None
        if platform == "android":
            from android.permissions import request_permissions, Permission

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

            from android.activity import bind

            bind(on_activity_result=self.on_activity_result)
        else:
            self.handle_selection("./1.jpeg")

    def on_activity_result(self, request_code, result_code, data):
        if request_code == 123 and result_code == -1:
            uri = data.getData()
            print("Uri", uri)
            if self.mActivity:
                content_resolver = self.mActivity.getContentResolver()
                input_stream = content_resolver.openInputStream(uri)
                self.handle_selection(input_stream)

    def open_camera(self, instance):
        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE])
        self.preview = CameraFrame(aspect_ratio="4:3")
        self.preview.bind(on_texture_available=self.update_ui_with_texture)
        self.placeholder.add_widget(self.preview)
        self.preview.connect_camera(
            sensor_resolution=(1280, 960),
            enable_video=False,
            enable_analyze_pixels=True,
        )

    def take_picture(self, path):
        if self.preview is not None:
            self.preview.capture()

    def update_ui_with_texture(self, instance, texture):
        def update_texture(dt):
            try:
                if texture:
                    size = texture.size
                    buffer = texture.pixels
                    img_array = np.frombuffer(buffer, dtype=np.uint8).reshape(
                        size[1], size[0], 4
                    )

                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                    img_array = cv2.flip(img_array, 0)
                    image_pil = Image.fromarray(img_array)
                    img_byte_arr = io.BytesIO()
                    image_pil.save(img_byte_arr, format="PNG")
                    img_byte_arr = img_byte_arr.getvalue()

                    loaded_image = Image.open(io.BytesIO(img_byte_arr))
                    img_data = np.array(loaded_image)
                    img_data, result = process_frame(img_data)
                    new_texture = Texture.create(
                        size=(img_data.shape[1], img_data.shape[0]), colorfmt="rgb"
                    )
                    new_texture.blit_buffer(
                        img_data.tobytes(), colorfmt="rgb", bufferfmt="ubyte"
                    )
                    self.display_result(new_texture, result)

                Clock.schedule_once(lambda dt: self.disconnect_camera(), 0.5)

            except Exception as tex_err:
                print(f"Error in texture update: {tex_err}")
                import traceback

                traceback.print_exc()

        Clock.schedule_once(update_texture)

    def disconnect_camera(self):
        if self.preview is not None:
            self.preview.disconnect_camera()
            self.preview = None

    def create_select_picture_screen(self):
        self.layout = MDBoxLayout(
            orientation="vertical",
            padding="10dp",
            spacing="10dp",
            md_bg_color=Colors.CRISP_WHITE.value,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        self.placeholder = MDAnchorLayout(
            md_bg_color=(0, 0, 0, 0),
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, 1),
        )

        self.infoText = MDLabel(
            text="Select an image to process, or take a picture with the camera.",
            halign="center",
            font_style="H5",
            size_hint=(1, 1),
        )
        self.infoText.color = Colors.COOL_GRAY.value

        self.placeholder.add_widget(self.infoText)
        self.layout.add_widget(self.placeholder)

        self.pictureFrame = PictureFrame(
            md_bg_color=Colors.LIGHT_GRAY.value,
            size_hint=(1, 1),
            padding="2dp",
            radius=[8],
        )

        self.resultLabel = ResultFrame()
        self.layout.add_widget(self.resultLabel)
        return self.layout

    def create_camera_screen(self):
        self.layout = MDBoxLayout(
            orientation="vertical",
            padding="10dp",
            spacing="10dp",
            md_bg_color=Colors.CRISP_WHITE.value,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        captureButton = MDRaisedButton(on_release=self.take_picture)
        self.layout.add_widget(captureButton)
        return self.layout

    def create_history_screen(self):
        self.layout = MDBoxLayout()
        return self.layout

    def build(self):
        self.orientation = "portrait"
        self.preview = None

        self.screen = Screen()
        self.bottomNavigation = MDBottomNavigation()

        self.selectPicture = MDBottomNavigationItem(
            name="select_picture", text="Select Picture", icon="image"
        )
        self.selectPicture.add_widget(self.create_select_picture_screen())
        self.bottomNavigation.add_widget(self.selectPicture)

        self.takePicture = MDBottomNavigationItem(
            name="take_picture", text="Take Picture", icon="camera"
        )
        self.takePicture.add_widget(self.create_camera_screen())
        self.bottomNavigation.add_widget(self.takePicture)

        self.history = MDBottomNavigationItem(
            name="history", text="history", icon="history"
        )
        self.history.add_widget(self.create_history_screen())
        self.bottomNavigation.add_widget(self.history)

        # This is the button layout used, it consists of a grid made of 2 columns, where one button takes up 1 column
        # self.buttonLayout = ButtonLayout(
        #     md_bg_color=Colors.CHARCOAL.value,
        #     on_select_picture=self.get_image,
        #     font_size="18dp",
        #     on_take_picture=self.open_camera,
        # )
        # self.layout.add_widget(self.buttonLayout)
        self.screen.add_widget(self.bottomNavigation)
        return self.screen


if __name__ == "__main__":
    IrisDetector().run()
