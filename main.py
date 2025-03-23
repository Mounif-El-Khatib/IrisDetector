from threading import ExceptHookArgs

from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.toolbar import MDTopAppBar
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
from components.HistoryScreen import HistoryScreen
from components.PictureFrame import PictureFrame
from kivymd.uix.screen import Screen
from colors import Colors
from components.ResultFrame import ResultFrame
from components.SelectPictureScreen import SelectPictureScreen
import datetime
import os
import sqlite3


def init_db(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                result TEXT,
                timestamp TEXT
                )
            """
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)


def insert_image(db_path, filename, result):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO images (filename, result, timestamp) VALUES (?, ?, ?)
        """,
            (str(filename), str(result.get_text().split(": ")[1]), str(timestamp)),
        )
        conn.commit()
        conn.close()
        print(f"Saved {filename} with '{result.get_text()}' at {timestamp}")
    except Exception as e:
        print(e)


def get_storage_path():
    if platform == "android":
        from android.storage import app_storage_path

        context = autoclass("org.kivy.android.PythonActivity").mActivity
        return app_storage_path()
    else:
        return os.getcwd()


def get_db_path():
    storage_path = get_storage_path()
    return os.path.join(storage_path, "iris_detector.db")


class IrisDetector(MDApp):

    def __init__(self, **kwargs):
        super().__init__()
        self.cameraScreen = None

    def save_result(self, instance):
        if (
            self.resultLabel
            and self.resultLabel.get_text() != ""
            or self.cameraResultFrame
            and self.cameraResultFrame.get_text() != ""
        ):  # Make sure result exists
            date = datetime.datetime.now()
            timestamp = date.strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.png"
            if platform == "android":
                internal_path = get_storage_path()
            else:
                internal_path = os.getcwd()
            full_image_path = os.path.join(internal_path, filename)
            db_path = get_db_path()
            init_db(db_path)
            result = self.resultLabel
            if self.currentScreen == "take_picture":
                result = self.cameraResultFrame
            insert_image(db_path, filename, result)
            if self.currentScreen == "take_picture" and self.cameraPictureFrame:
                self.cameraPictureFrame.export_as_image().save(full_image_path)
            elif self.currentScreen == "select_picture" and self.pictureFrame:
                self.pictureFrame.export_as_image().save(full_image_path)

    def display_result(self, texture, result):
        if self.currentScreen == "take_picture":
            if self.cameraPlaceholder is not None:
                self.cameraPlaceholder.clear_widgets()
                if self.cameraPlaceholder is not None:
                    self.cameraPlaceholder.add_widget(self.cameraPictureFrame)
                self.cameraPictureFrame.set_source(texture)
                if self.cameraResultFrame is not None:
                    self.cameraResultFrame.set_text(
                        f"Iris to pupil ratio: {str(result)}"
                    )

        if self.currentScreen == "select_picture":
            if self.pictureFrame is not None:
                self.pictureFrame.set_source(texture)
                self.resultLabel.set_text(f"Iris to pupil ratio: {str(result)}")
                self.selectPictureScreen.set_padding([0])
                self.selectPictureScreen.set_placeholder(self.pictureFrame)

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
        self.currentScreen = "take_picture"
        if self.top_bar.right_action_items == []:
            self.top_bar.right_action_items = [
                ["refresh", self.reset_selection],
                ["content-save", self.save_result],
            ]
        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE])
        if self.preview is None:
            self.preview = CameraFrame(aspect_ratio="4:3")
            self.preview.bind(on_texture_available=self.update_ui_with_texture)
            if self.cameraPlaceholder is not None:
                self.cameraPlaceholder.add_widget(self.preview)
                self.preview.connect_camera(
                    sensor_resolution=(2048, 1536),
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
                    result = "a"
                    img_data, result = process_frame(img_data)
                    new_texture = Texture.create(
                        size=(img_data.shape[1], img_data.shape[0]), colorfmt="rgb"
                    )
                    new_texture.blit_buffer(
                        img_data.tobytes(), colorfmt="rgb", bufferfmt="ubyte"
                    )
                    self.display_result(new_texture, result)

                Clock.schedule_once(lambda dt: self.disconnect_camera, 0.5)

            except Exception as tex_err:
                print(f"Error in texture update: {tex_err}")
                import traceback

                traceback.print_exc()

        Clock.schedule_once(update_texture)

    def disconnect_camera(self, instance):
        if self.preview is not None:
            self.preview.disconnect_camera()
            self.preview = None

    def create_select_picture_screen(self):
        self.selectPictureScreen = SelectPictureScreen(on_click=self.get_image)
        self.pictureFrame = PictureFrame(
            md_bg_color=Colors.LIGHT_GRAY.value,
            size_hint=(1, 1),
            padding="2dp",
            radius=[8],
        )

        self.resultLabel = ResultFrame()
        self.selectPictureScreen.add_widget(self.resultLabel)
        return self.selectPictureScreen

    def create_camera_screen(self):
        self.cameraScreen = MDBoxLayout(
            orientation="vertical",
            padding="10dp",
            spacing="10dp",
            md_bg_color=Colors.CRISP_WHITE.value,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        self.cameraPictureFrame = PictureFrame(
            md_bg_color=Colors.LIGHT_GRAY.value,
            size_hint=(1, 1),
            padding="2dp",
            radius=[8],
        )
        self.cameraResultFrame = ResultFrame()
        self.cameraPlaceholder = MDAnchorLayout()
        captureButton = MDRaisedButton(on_release=self.take_picture)
        self.cameraScreen.add_widget(self.cameraPlaceholder)
        self.cameraScreen.add_widget(captureButton)
        self.cameraScreen.add_widget(self.cameraResultFrame)
        return self.cameraScreen

    def create_history_screen(self):
        box_layout = MDBoxLayout(orientation="vertical", md_bg_color=Colors.LIGHT_GRAY.value)
        history_screen = HistoryScreen()
        box_layout.add_widget(history_screen)
        return box_layout

    def print_curr_screen(self, instance):
        print(self.currentScreen)

    def reset_selection(self, instance):
        if self.currentScreen == "select_picture":
            if self.resultLabel.get_text() != "":
                self.selectPictureScreen.reset_screen()
                self.resultLabel.clear_result()
        if self.currentScreen == "take_picture":
            if self.cameraResultFrame and self.cameraResultFrame.get_text() != "":
                if self.cameraPlaceholder:
                    self.cameraPlaceholder.clear_widgets()
                    self.cameraPlaceholder.add_widget(self.preview)
                    self.cameraResultFrame.clear_result()

    def select_picture_screen(self, instance):
        self.currentScreen = "select_picture"
        self.disconnect_camera(instance)
        if self.top_bar.right_action_items == []:
            self.top_bar.right_action_items = [
                ["refresh", self.reset_selection],
                ["content-save", self.save_result],
            ]

    def history_screen(self, instance):
        self.currentScreen = "history"
        self.disconnect_camera(instance)
        self.top_bar.right_action_items = []


    def build(self):
        self.cameraScreen = None
        self.cameraResultFrame = None
        self.currentScreen = "select_picture"
        self.screen = Screen()
        self.preview = None
        self.layout = MDBoxLayout(orientation="vertical")
        self.pictureFrame = None
        self.cameraPictureFrame = None
        self.cameraPlaceholder = None
        self.top_bar = MDTopAppBar(
            title="Iris Detector",
            elevation=1,
            anchor_title="left",
            right_action_items=[
                ["refresh", self.reset_selection],
                ["content-save", self.save_result],
            ],
        )

        self.layout.add_widget(self.top_bar)

        self.bottomNavigation = MDBottomNavigation()

        self.selectPicture = MDBottomNavigationItem(
            name="select_picture", text="Select Picture", icon="image"
        )
        self.selectPicture.bind(on_tab_press=self.select_picture_screen)
        self.selectPicture.add_widget(self.create_select_picture_screen())
        self.bottomNavigation.add_widget(self.selectPicture)

        self.takePicture = MDBottomNavigationItem(
            name="take_picture", text="Take Picture", icon="camera"
        )
        self.takePicture.bind(on_tab_press=self.open_camera)

        self.takePicture.add_widget(self.create_camera_screen())
        self.bottomNavigation.add_widget(self.takePicture)

        self.history = MDBottomNavigationItem(
            name="history", text="History", icon="history"
        )
        self.history.bind(on_tab_press=self.history_screen)
        self.history.add_widget(self.create_history_screen())
        self.bottomNavigation.add_widget(self.history)

        self.layout.add_widget(self.bottomNavigation)

        self.screen.add_widget(self.layout)

        return self.screen


if __name__ == "__main__":
    IrisDetector().run()
